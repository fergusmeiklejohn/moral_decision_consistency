#!/usr/bin/env python3
"""
Main script to run moral decision consistency experiments.

Examples:
    python scripts/run_experiment.py --phase pilot
    python scripts/run_experiment.py --phase pilot --models qwen3-14b-q5
    python scripts/run_experiment.py --config custom_experiment.yaml
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.loader import ConfigLoader
from src.data.schemas import ExperimentConfig
from src.experiments.phase1_consistency import Phase1Runner
from src.experiments.phase2_perturbation import Phase2Runner


PHASE_NAME_MAP = {
    "pilot": "pilot",
    "phase1": "phase1_consistency",
    "phase2": "phase2_perturbation",
}


def parse_models_override(value: Optional[str]) -> Optional[List[str]]:
    """Parse comma separated --models flag."""
    if not value:
        return None

    models = [model.strip() for model in value.split(",") if model.strip()]
    if not models:
        raise ValueError("Provided --models override is empty after parsing.")
    return models


def load_custom_configs(
    loader: ConfigLoader,
    config_path: Path,
) -> Tuple[Dict[str, Dict], Optional[str]]:
    """Load a custom experiment config file.

    Returns a dictionary keyed by experiment name and an optional default key
    if the file defined a single experiment.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    if not config_path.is_file():
        raise ValueError(f"--config expects a file path, got directory: {config_path}")

    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    if config_data is None:
        raise ValueError(f"Config file '{config_path}' is empty.")

    config_data = loader._substitute_env_vars(config_data)  # type: ignore[attr-defined]

    if isinstance(config_data, dict) and "experiment_type" in config_data:
        default_name = (
            config_data.get("experiment_id")
            or config_data.get("experiment_type")
            or "custom_experiment"
        )
        return {default_name: config_data}, default_name

    if not isinstance(config_data, dict):
        raise ValueError(
            f"Custom config '{config_path}' must define a mapping of experiments."
        )

    return config_data, None


def main():
    parser = argparse.ArgumentParser(
        description="Run moral decision consistency experiments"
    )

    parser.add_argument(
        "--phase",
        choices=["pilot", "phase1", "phase2"],
        help="Which experiment phase to run (ignored if --config defines a single experiment)"
    )

    parser.add_argument(
        "--config",
        help=(
            "Path to custom experiment config YAML. "
            "Can contain a single experiment definition or the same structure as config/experiment.yaml."
        )
    )

    parser.add_argument(
        "--models",
        help="Comma-separated list of models to override config for this run"
    )

    args = parser.parse_args()

    config_loader = ConfigLoader()

    # Determine experiment configs source
    experiment_name: Optional[str] = None
    if args.config:
        custom_path = Path(args.config).expanduser()
        custom_configs, default_experiment = load_custom_configs(
            config_loader, custom_path
        )
        config_loader.experiment_configs = custom_configs  # type: ignore[attr-defined]

        if args.phase:
            experiment_name = PHASE_NAME_MAP[args.phase]
        else:
            if default_experiment is None:
                parser.error(
                    "--config includes multiple experiments. Please also provide --phase."
                )
            experiment_name = default_experiment
    else:
        if not args.phase:
            parser.error("Please provide --phase when not using --config.")
        experiment_name = PHASE_NAME_MAP[args.phase]

    models_override = parse_models_override(args.models)

    try:
        experiment_config = config_loader.get_experiment_config(experiment_name)
        if models_override:
            experiment_config.models = models_override
            print(f"Overriding models: {', '.join(models_override)}")

        if experiment_config.experiment_type in {"pilot", "phase1_consistency"}:
            runner = Phase1Runner(
                config=experiment_config,
                config_loader=config_loader,
            )
        else:
            runner = Phase2Runner(
                config=experiment_config,
                config_loader=config_loader,
            )

        experiment_id = runner.run_experiment()

        print(f"\n✓ Experiment complete: {experiment_id}")
        print(f"\nTo analyze results, run:")
        print(f"  python scripts/analyze_results.py --experiment-id {experiment_id}")

    except KeyboardInterrupt:
        print("\n\nExperiment interrupted by user")
    except Exception as e:
        print(f"\n✗ Experiment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
