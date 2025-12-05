#!/usr/bin/env python3
"""
Run V2 moral reasoning experiments.

Tests genuine moral reasoning on novel out-of-distribution dilemmas
using open-ended questions and structured probe sequences.

Examples:
    python scripts/run_experiment_v2.py --config v2_pilot
    python scripts/run_experiment_v2.py --config v2_moral_reasoning
    python scripts/run_experiment_v2.py --config v2_pilot --models claude-sonnet-4-5
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.loader import ConfigLoader
from src.data.schemas import ExperimentConfigV2
from src.experiments.phase_v2_reasoning import PhaseV2Runner


def parse_models_override(value: Optional[str]) -> Optional[List[str]]:
    """Parse comma separated --models flag."""
    if not value:
        return None

    models = [model.strip() for model in value.split(",") if model.strip()]
    if not models:
        raise ValueError("Provided --models override is empty after parsing.")
    return models


def main():
    parser = argparse.ArgumentParser(
        description="Run V2 moral reasoning experiments"
    )

    parser.add_argument(
        "--config",
        default="v2_pilot",
        help="Experiment config name from experiment.yaml (default: v2_pilot)"
    )

    parser.add_argument(
        "--models",
        help="Comma-separated list of models to override config for this run"
    )

    parser.add_argument(
        "--num-runs",
        type=int,
        help="Override number of runs per dilemma"
    )

    parser.add_argument(
        "--temperature",
        type=float,
        help="Override temperature setting"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print configuration without running the experiment"
    )

    args = parser.parse_args()

    config_loader = ConfigLoader()

    try:
        # Load raw config
        raw_config = config_loader.get_experiment_config_raw(args.config)

        # Validate experiment type
        if raw_config.get("experiment_type") != "v2_moral_reasoning":
            print(f"Error: Config '{args.config}' is not a V2 experiment.")
            print(f"  experiment_type: {raw_config.get('experiment_type')}")
            print("\nAvailable V2 configs: v2_pilot, v2_moral_reasoning")
            sys.exit(1)

        # Apply overrides
        models_override = parse_models_override(args.models)
        if models_override:
            raw_config["models"] = models_override
            print(f"Overriding models: {', '.join(models_override)}")

        if args.num_runs is not None:
            raw_config["num_runs"] = args.num_runs
            print(f"Overriding num_runs: {args.num_runs}")

        if args.temperature is not None:
            raw_config["temperature"] = args.temperature
            print(f"Overriding temperature: {args.temperature}")

        # Generate experiment ID if not present
        if "experiment_id" not in raw_config:
            raw_config["experiment_id"] = f"v2_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Create config object
        config = ExperimentConfigV2(
            experiment_id=raw_config["experiment_id"],
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

        if args.dry_run:
            print("\n" + "=" * 60)
            print("DRY RUN - Configuration Preview")
            print("=" * 60)
            print(f"\nExperiment ID: {config.experiment_id}")
            print(f"Models: {config.models}")
            print(f"Dilemma IDs: {config.dilemma_ids or 'all (from dilemmas_v2.json)'}")
            print(f"Temperature: {config.temperature}")
            print(f"Num runs: {config.num_runs}")
            print(f"Run LLM Judge: {config.run_llm_judge}")
            if config.run_llm_judge:
                print(f"Judge model: {config.judge_model}")
            print(f"\nTo run this experiment, remove --dry-run flag")
            return

        # Run experiment
        runner = PhaseV2Runner(
            config=config,
            config_loader=config_loader,
        )

        experiment_id = runner.run_experiment()

        print(f"\n✓ Experiment complete: {experiment_id}")
        print(f"\nNext steps:")
        print(f"  1. Score results:")
        print(f"     python scripts/score_results_v2.py --experiment-id {experiment_id}")
        print(f"  2. Analyze results:")
        print(f"     python scripts/analyze_results_v2.py --experiment-id {experiment_id}")

    except KeyboardInterrupt:
        print("\n\nExperiment interrupted by user")
    except Exception as e:
        print(f"\n✗ Experiment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
