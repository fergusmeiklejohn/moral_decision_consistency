#!/usr/bin/env python3
"""
Main script to run moral decision consistency experiments.

Usage:
    python scripts/run_experiment.py --phase pilot
    python scripts/run_experiment.py --phase phase1
    python scripts/run_experiment.py --phase phase2
    python scripts/run_experiment.py --config custom_config.yaml
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from src.experiments.phase1_consistency import run_phase1_experiment
from src.experiments.phase2_perturbation import run_phase2_experiment
from src.config.loader import ConfigLoader


def main():
    parser = argparse.ArgumentParser(
        description="Run moral decision consistency experiments"
    )

    parser.add_argument(
        "--phase",
        choices=["pilot", "phase1", "phase2"],
        help="Which experiment phase to run"
    )

    parser.add_argument(
        "--config",
        help="Path to custom config file (overrides --phase)"
    )

    parser.add_argument(
        "--models",
        help="Comma-separated list of models to override config"
    )

    args = parser.parse_args()

    # Determine experiment name
    if args.config:
        # TODO: Load custom config
        print("Custom config not yet implemented")
        return
    elif args.phase == "pilot":
        experiment_name = "pilot"
    elif args.phase == "phase1":
        experiment_name = "phase1_consistency"
    elif args.phase == "phase2":
        experiment_name = "phase2_perturbation"
    else:
        parser.print_help()
        return

    # Run experiment
    try:
        if experiment_name in ["pilot", "phase1_consistency"]:
            experiment_id = run_phase1_experiment(experiment_name)
        else:
            experiment_id = run_phase2_experiment()

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
