"""
Phase V2: Moral Reasoning Experiment Runner.

Tests genuine moral reasoning on novel out-of-distribution dilemmas
using open-ended questions and structured probe sequences.
"""

import time
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import (
    create_provider,
    get_configured_provider,
    get_provider_from_model_name,
)
from ..dilemmas.loader_v2 import DilemmaLoaderV2
from ..data.schemas import (
    ExperimentRunV2,
    ExperimentConfigV2,
    V2Response,
    ProbeResponse,
    ModelResponse,
)
from ..data.storage import ExperimentStorage
from ..config.loader import ConfigLoader


class PhaseV2Runner:
    """Runs V2 moral reasoning experiments with probe sequences."""

    def __init__(
        self,
        config: ExperimentConfigV2,
        config_loader: Optional[ConfigLoader] = None,
        dilemma_loader: Optional[DilemmaLoaderV2] = None,
        storage: Optional[ExperimentStorage] = None
    ):
        """
        Initialize V2 experiment runner.

        Args:
            config: V2 experiment configuration
            config_loader: Configuration loader (optional)
            dilemma_loader: V2 dilemma loader (optional)
            storage: Experiment storage (optional)
        """
        self.config = config
        self.config_loader = config_loader or ConfigLoader()
        self.dilemma_loader = dilemma_loader or DilemmaLoaderV2()
        self.storage = storage or ExperimentStorage()

        # Validate config
        if config.experiment_type != "v2_moral_reasoning":
            raise ValueError(
                f"Invalid experiment type for PhaseV2Runner: {config.experiment_type}"
            )

        # Initialize model providers
        self.providers = {}
        self._initialize_providers()

        # Save config
        self.storage.save_experiment_config_v2(config.experiment_id, config)

    def _initialize_providers(self) -> None:
        """Initialize LLM providers for all models in the experiment."""
        print("Initializing model providers...")

        for model_name in self.config.models:
            provider_name = None
            try:
                provider_name = self._resolve_provider_name(model_name)
                model_config = self.config_loader.get_model_config(provider_name, model_name)

                provider = create_provider(
                    provider_name=provider_name,
                    model_name=model_config.get("name", model_name),
                    api_key=model_config.get("api_key"),
                    **{
                        k: v
                        for k, v in model_config.items()
                        if k not in ["name", "api_key"]
                    }
                )

                self.providers[model_name] = provider
                print(f"  ✓ Initialized {model_name} ({provider_name})")

            except KeyError as config_error:
                detail = (
                    f"Model '{model_name}' is not defined under provider '{provider_name}' "
                    "in config/models.yaml. Add a configuration entry for this model to run the experiment."
                )
                print(f"  ✗ Failed to initialize {model_name}: {detail}")
                raise KeyError(detail) from config_error
            except Exception as e:
                print(f"  ✗ Failed to initialize {model_name}: {e}")
                raise

    def _resolve_provider_name(self, model_name: str) -> str:
        """Prefer config-defined provider mapping before falling back to heuristics."""
        provider_info = get_configured_provider(model_name, self.config_loader)
        if provider_info:
            provider_name, _ = provider_info
            return provider_name

        return get_provider_from_model_name(model_name)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _run_conversation_turn(
        self,
        provider,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> ModelResponse:
        """
        Run a single conversation turn with retry logic.

        Args:
            provider: LLM provider
            messages: Conversation history
            temperature: Temperature setting
            max_tokens: Maximum tokens to generate

        Returns:
            ModelResponse
        """
        return provider.generate_conversation(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _run_dilemma_session(
        self,
        provider,
        dilemma_id: str,
        temperature: float,
    ) -> V2Response:
        """
        Run a complete dilemma session with initial response and probes.

        Each dilemma gets a fresh conversation (no cross-contamination).

        Args:
            provider: LLM provider
            dilemma_id: ID of the dilemma
            temperature: Temperature setting

        Returns:
            V2Response containing initial response and all probe responses
        """
        session_start = time.time()
        total_tokens = 0
        messages = []

        # Step 1: Initial open-ended prompt
        initial_prompt = self.dilemma_loader.get_initial_prompt(dilemma_id)
        messages.append({"role": "user", "content": initial_prompt})

        initial_response = self._run_conversation_turn(
            provider=provider,
            messages=messages,
            temperature=temperature,
            max_tokens=self.config.max_initial_response_tokens,
        )

        # Add assistant response to conversation
        messages.append({"role": "assistant", "content": initial_response.raw_text})

        initial_tokens = initial_response.tokens_used or 0
        total_tokens += initial_tokens

        # Rate limiting
        time.sleep(60.0 / self.config.rate_limit_per_minute)

        # Step 2: Run probe questions in fixed order
        probe_responses = []
        probes = self.dilemma_loader.get_probes_in_order()

        for probe in probes:
            probe_start = time.time()

            # Get probe prompt (with dilemma-specific injections)
            probe_prompt = self.dilemma_loader.get_probe_prompt(
                probe_id=probe.id,
                dilemma_id=dilemma_id,
                prior_response=initial_response.raw_text,
            )

            messages.append({"role": "user", "content": probe_prompt})

            probe_response = self._run_conversation_turn(
                provider=provider,
                messages=messages,
                temperature=temperature,
                max_tokens=self.config.max_probe_response_tokens,
            )

            # Add to conversation history
            messages.append({"role": "assistant", "content": probe_response.raw_text})

            probe_time = time.time() - probe_start
            probe_tokens = probe_response.tokens_used or 0
            total_tokens += probe_tokens

            probe_responses.append(ProbeResponse(
                probe_id=probe.id,
                question_text=probe_prompt,
                response_text=probe_response.raw_text,
                followup_asked=False,
                followup_response=None,
                response_time_seconds=probe_time,
                tokens_used=probe_tokens,
            ))

            # Rate limiting
            time.sleep(60.0 / self.config.rate_limit_per_minute)

        session_time = time.time() - session_start

        return V2Response(
            initial_response=initial_response.raw_text,
            initial_response_time_seconds=initial_response.response_time_seconds,
            initial_tokens_used=initial_tokens,
            probe_responses=probe_responses,
            total_response_time_seconds=session_time,
            total_tokens_used=total_tokens,
        )

    def run_experiment(self) -> str:
        """
        Run the full V2 experiment.

        Returns:
            Experiment ID
        """
        experiment_id = self.config.experiment_id
        print(f"\n{'='*80}")
        print(f"Starting V2 Moral Reasoning Experiment: {experiment_id}")
        print(f"{'='*80}\n")

        # Get dilemmas in fixed presentation order
        if self.config.dilemma_ids:
            dilemma_ids = self.config.dilemma_ids
        else:
            dilemma_ids = self.dilemma_loader.get_dilemma_ids()

        # Calculate total runs
        # Each run = 1 initial + 6 probes = 7 API calls
        num_probes = len(self.dilemma_loader.get_probes_in_order())
        total_runs = len(self.config.models) * len(dilemma_ids) * self.config.num_runs
        total_api_calls = total_runs * (1 + num_probes)

        print(f"Configuration:")
        print(f"  Models: {len(self.config.models)}")
        print(f"  Dilemmas: {len(dilemma_ids)}")
        print(f"  Probes per dilemma: {num_probes}")
        print(f"  Runs per condition: {self.config.num_runs}")
        print(f"  Temperature: {self.config.temperature}")
        print(f"  Total dilemma sessions: {total_runs}")
        print(f"  Total API calls: {total_api_calls}\n")

        # Run experiments
        runs_completed = 0
        backup_counter = 0

        with tqdm(total=total_runs, desc="Overall Progress") as pbar:
            for model_name in self.config.models:
                provider = self.providers[model_name]
                model_info = provider.get_model_info()

                for dilemma_id in dilemma_ids:
                    dilemma = self.dilemma_loader.get_dilemma(dilemma_id)

                    for run_num in range(1, self.config.num_runs + 1):
                        try:
                            # Run complete dilemma session
                            v2_response = self._run_dilemma_session(
                                provider=provider,
                                dilemma_id=dilemma_id,
                                temperature=self.config.temperature,
                            )

                            # Create run record
                            run = ExperimentRunV2(
                                experiment_id=experiment_id,
                                run_id=str(uuid.uuid4()),
                                model_name=model_name,
                                model_version=model_info.get("version"),
                                provider=model_info["provider"],
                                dilemma_id=dilemma_id,
                                dilemma_category=dilemma.category,
                                dilemma_structure=dilemma.structure,
                                temperature=self.config.temperature,
                                run_number=run_num,
                                response=v2_response,
                                scoring=None,  # Scoring done in separate pass
                            )

                            # Save run
                            self.storage.save_run_v2(experiment_id, run)
                            runs_completed += 1

                            # Create backup periodically
                            if runs_completed % self.config.backup_every_n_queries == 0:
                                backup_counter += 1
                                self.storage.create_backup_v2(
                                    experiment_id,
                                    f"auto_backup_{backup_counter}"
                                )

                        except Exception as e:
                            print(f"\n✗ Error on run {model_name}/{dilemma_id}/{run_num}: {e}")
                            # Save error run
                            error_run = ExperimentRunV2(
                                experiment_id=experiment_id,
                                run_id=str(uuid.uuid4()),
                                model_name=model_name,
                                model_version=model_info.get("version"),
                                provider=model_info["provider"],
                                dilemma_id=dilemma_id,
                                dilemma_category=dilemma.category,
                                dilemma_structure=dilemma.structure,
                                temperature=self.config.temperature,
                                run_number=run_num,
                                response=V2Response(
                                    initial_response=str(e),
                                    initial_response_time_seconds=0.0,
                                    initial_tokens_used=0,
                                    probe_responses=[],
                                    total_response_time_seconds=0.0,
                                    total_tokens_used=0,
                                ),
                                error=str(e)
                            )
                            self.storage.save_run_v2(experiment_id, error_run)

                        # Update progress
                        pbar.update(1)

        # Final backup
        self.storage.create_backup_v2(experiment_id, "final_backup")

        # Print summary
        print(f"\n{'='*80}")
        print(f"Experiment Complete: {experiment_id}")
        print(f"{'='*80}\n")

        summary = self.storage.get_experiment_summary_v2(experiment_id)
        print("Summary:")
        for key, value in summary.items():
            if not isinstance(value, (list, dict)):
                print(f"  {key}: {value}")

        return experiment_id


def run_v2_experiment(experiment_name: str = "v2_moral_reasoning") -> str:
    """
    Convenience function to run a V2 experiment from config.

    Args:
        experiment_name: Name of experiment in config (default: "v2_moral_reasoning")

    Returns:
        Experiment ID
    """
    config_loader = ConfigLoader()

    # Load config and create ExperimentConfigV2
    raw_config = config_loader.get_experiment_config_raw(experiment_name)

    config = ExperimentConfigV2(
        experiment_id=raw_config.get("experiment_id", f"v2_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"),
        models=raw_config.get("models", []),
        dilemma_ids=raw_config.get("dilemma_ids"),
        temperature=raw_config.get("temperature", 0.3),
        num_runs=raw_config.get("num_runs", 3),
        max_initial_response_tokens=raw_config.get("max_initial_response_tokens", 1000),
        max_probe_response_tokens=raw_config.get("max_probe_response_tokens", 500),
        run_llm_judge=raw_config.get("run_llm_judge", True),
        judge_model=raw_config.get("judge_model"),
        judge_temperature=raw_config.get("judge_temperature", 0.0),
        rate_limit_per_minute=raw_config.get("rate_limit_per_minute", 20),
        retry_attempts=raw_config.get("retry_attempts", 3),
        backup_every_n_queries=raw_config.get("backup_every_n_queries", 10),
    )

    runner = PhaseV2Runner(
        config=config,
        config_loader=config_loader
    )

    return runner.run_experiment()
