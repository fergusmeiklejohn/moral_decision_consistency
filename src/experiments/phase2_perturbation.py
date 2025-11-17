"""
Phase II: Causal-Structure Perturbation Testing.

Tests whether LLMs appropriately respond to morally relevant vs irrelevant changes
in moral dilemmas, measuring causal sensitivity of moral reasoning.
"""

import random
import time
import uuid
from datetime import datetime
from typing import List, Optional
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import create_provider, get_provider_from_model_name
from ..dilemmas.loader import DilemmaLoader
from ..data.schemas import (
    ExperimentRun,
    ExperimentConfig,
    PerturbationType,
    ModelResponse
)
from ..data.storage import ExperimentStorage
from ..config.loader import ConfigLoader


class Phase2Runner:
    """Runs Phase II perturbation experiments."""

    def __init__(
        self,
        config: ExperimentConfig,
        config_loader: Optional[ConfigLoader] = None,
        dilemma_loader: Optional[DilemmaLoader] = None,
        storage: Optional[ExperimentStorage] = None
    ):
        """
        Initialize Phase II experiment runner.

        Args:
            config: Experiment configuration
            config_loader: Configuration loader (optional)
            dilemma_loader: Dilemma loader (optional)
            storage: Experiment storage (optional)
        """
        self.config = config
        self.config_loader = config_loader or ConfigLoader()
        self.dilemma_loader = dilemma_loader or DilemmaLoader()
        self.storage = storage or ExperimentStorage()

        # Validate config
        if config.experiment_type != "phase2_perturbation":
            raise ValueError(
                f"Invalid experiment type for Phase2Runner: {config.experiment_type}"
            )

        if not config.test_perturbations:
            raise ValueError("Phase2Runner requires test_perturbations=True")

        # Initialize model providers
        self.providers = {}
        self._initialize_providers()

        # Save config
        self.storage.save_experiment_config(config.experiment_id, config)

    def _initialize_providers(self) -> None:
        """Initialize LLM providers for all models in the experiment."""
        print("Initializing model providers...")

        for model_name in self.config.models:
            try:
                provider_name = get_provider_from_model_name(model_name)
                model_config = self.config_loader.get_model_config(provider_name, model_name)

                provider = create_provider(
                    provider_name=provider_name,
                    model_name=model_config.get("name", model_name),
                    api_key=model_config.get("api_key"),
                    **{k: v for k, v in model_config.items()
                       if k not in ["name", "api_key"]}
                )

                self.providers[model_name] = provider
                print(f"  ✓ Initialized {model_name} ({provider_name})")

            except Exception as e:
                print(f"  ✗ Failed to initialize {model_name}: {e}")
                raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _run_single_query(
        self,
        provider,
        prompt: str,
        temperature: float,
        seed: Optional[int] = None
    ) -> ModelResponse:
        """Run a single query with retry logic."""
        return provider.generate(
            prompt=prompt,
            temperature=temperature,
            top_p=self.config.top_p,
            max_tokens=500,
            seed=seed
        )

    def run_experiment(self) -> str:
        """
        Run the full Phase II experiment.

        Returns:
            Experiment ID
        """
        experiment_id = self.config.experiment_id
        print(f"\n{'='*80}")
        print(f"Starting Phase II Perturbation Testing: {experiment_id}")
        print(f"{'='*80}\n")

        # Calculate total runs
        total_runs = (
            len(self.config.models) *
            len(self.config.dilemma_ids) *
            len(self.config.perturbation_types) *
            len(self.config.temperatures) *
            self.config.num_runs
        )

        print(f"Configuration:")
        print(f"  Models: {len(self.config.models)}")
        print(f"  Dilemmas: {len(self.config.dilemma_ids)}")
        print(f"  Perturbation types: {[p.value for p in self.config.perturbation_types]}")
        print(f"  Temperatures: {self.config.temperatures}")
        print(f"  Runs per condition: {self.config.num_runs}")
        print(f"  Total queries: {total_runs}\n")

        # Prepare dilemma order
        dilemma_order = self.config.dilemma_ids.copy()
        if self.config.randomize_dilemma_order:
            random.shuffle(dilemma_order)

        # Run experiments
        runs_completed = 0
        backup_counter = 0

        with tqdm(total=total_runs, desc="Overall Progress") as pbar:
            for model_name in self.config.models:
                provider = self.providers[model_name]
                model_info = provider.get_model_info()

                for dilemma_id in dilemma_order:
                    for perturbation_type in self.config.perturbation_types:
                        # Get prompt with perturbation
                        try:
                            prompt = self.dilemma_loader.get_prompt_for_perturbation(
                                dilemma_id=dilemma_id,
                                perturbation_type=perturbation_type,
                                reversed_order=False
                            )

                            dilemma = self.dilemma_loader.get_dilemma(dilemma_id)

                        except ValueError as e:
                            # Perturbation not available for this dilemma
                            print(f"\n⚠ Skipping {dilemma_id} + {perturbation_type.value}: {e}")
                            pbar.update(
                                len(self.config.temperatures) * self.config.num_runs
                            )
                            continue

                        for temperature in self.config.temperatures:
                            # Run multiple times
                            for run_num in range(1, self.config.num_runs + 1):
                                # Determine seed
                                seed = None
                                if self.config.fixed_seed is not None:
                                    seed = self.config.fixed_seed + run_num

                                # Run query
                                try:
                                    response = self._run_single_query(
                                        provider=provider,
                                        prompt=prompt,
                                        temperature=temperature,
                                        seed=seed
                                    )

                                    # Create run record
                                    run = ExperimentRun(
                                        experiment_id=experiment_id,
                                        run_id=str(uuid.uuid4()),
                                        model_name=model_name,
                                        model_version=model_info.get("version"),
                                        provider=model_info["provider"],
                                        dilemma_id=dilemma_id,
                                        dilemma_category=dilemma.category,
                                        perturbation_type=perturbation_type,
                                        position_order="original",
                                        temperature=temperature,
                                        top_p=self.config.top_p,
                                        random_seed=seed,
                                        run_number=run_num,
                                        response=response
                                    )

                                    # Save run
                                    self.storage.save_run(experiment_id, run)
                                    runs_completed += 1

                                    # Create backup periodically
                                    if runs_completed % self.config.backup_every_n_queries == 0:
                                        backup_counter += 1
                                        self.storage.create_backup(
                                            experiment_id,
                                            f"auto_backup_{backup_counter}"
                                        )

                                except Exception as e:
                                    print(f"\n✗ Error on run: {e}")
                                    # Save error run
                                    error_run = ExperimentRun(
                                        experiment_id=experiment_id,
                                        run_id=str(uuid.uuid4()),
                                        model_name=model_name,
                                        model_version=model_info.get("version"),
                                        provider=model_info["provider"],
                                        dilemma_id=dilemma_id,
                                        dilemma_category=dilemma.category,
                                        perturbation_type=perturbation_type,
                                        position_order="original",
                                        temperature=temperature,
                                        top_p=self.config.top_p,
                                        random_seed=seed,
                                        run_number=run_num,
                                        response=ModelResponse(
                                            raw_text=str(e),
                                            parsed_choice="ERROR",
                                            reasoning=str(e),
                                            timestamp=datetime.utcnow(),
                                            response_time_seconds=0.0
                                        ),
                                        error=str(e)
                                    )
                                    self.storage.save_run(experiment_id, error_run)

                                # Update progress
                                pbar.update(1)

                                # Rate limiting
                                time.sleep(60.0 / self.config.rate_limit_per_minute)

        # Final backup
        self.storage.create_backup(experiment_id, "final_backup")

        # Print summary
        print(f"\n{'='*80}")
        print(f"Experiment Complete: {experiment_id}")
        print(f"{'='*80}\n")

        summary = self.storage.get_experiment_summary(experiment_id)
        print("Summary:")
        for key, value in summary.items():
            if not isinstance(value, (list, dict)):
                print(f"  {key}: {value}")

        return experiment_id


def run_phase2_experiment() -> str:
    """
    Convenience function to run Phase II experiment from config.

    Returns:
        Experiment ID
    """
    config_loader = ConfigLoader()
    experiment_config = config_loader.get_experiment_config("phase2_perturbation")

    runner = Phase2Runner(
        config=experiment_config,
        config_loader=config_loader
    )

    return runner.run_experiment()
