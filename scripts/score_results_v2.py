#!/usr/bin/env python3
"""
Score V2 experiment results.

Runs heuristic screening and optional LLM judge scoring on experiment runs.
Can be run as a separate pass after data collection.

Examples:
    # Score with heuristic screening only (fast)
    python scripts/score_results_v2.py --experiment-id v2_20241201_120000

    # Score with LLM judge
    python scripts/score_results_v2.py --experiment-id v2_20241201_120000 --judge-model claude-sonnet-4-5

    # Rescore with different judge
    python scripts/score_results_v2.py --experiment-id v2_20241201_120000 --judge-model gpt-4o --rescore
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.loader import ConfigLoader
from src.analysis.scoring_v2 import V2Scorer, score_experiment_v2


def main():
    parser = argparse.ArgumentParser(
        description="Score V2 moral reasoning experiment results"
    )

    parser.add_argument(
        "--experiment-id",
        required=True,
        help="ID of the experiment to score"
    )

    parser.add_argument(
        "--judge-model",
        help="Model to use for LLM judge scoring (e.g., claude-sonnet-4-5)"
    )

    parser.add_argument(
        "--judge-temperature",
        type=float,
        default=0.0,
        help="Temperature for judge model (default: 0.0)"
    )

    parser.add_argument(
        "--skip-llm-judge",
        action="store_true",
        help="Only run heuristic screening, skip LLM judge"
    )

    parser.add_argument(
        "--rescore",
        action="store_true",
        help="Rescore all runs (by default, skips already scored runs)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without actually scoring"
    )

    args = parser.parse_args()

    config_loader = ConfigLoader()

    try:
        from src.data.storage import ExperimentStorage
        storage = ExperimentStorage()

        # Load runs to see what we have
        runs = storage.load_runs_v2(args.experiment_id)

        if not runs:
            print(f"No runs found for experiment '{args.experiment_id}'")
            print("\nAvailable experiments:")
            # List experiments with V2 runs
            data_dir = storage.base_dir / args.experiment_id
            if not data_dir.exists():
                print("  (no experiment directories found)")
            sys.exit(1)

        print(f"Found {len(runs)} runs for experiment '{args.experiment_id}'")

        # Check existing scoring
        existing_scores = storage.load_scoring_results_v2(args.experiment_id)
        scored_run_ids = {s.run_id for s in existing_scores}

        if existing_scores and not args.rescore:
            runs_to_score = [r for r in runs if r.run_id not in scored_run_ids]
            print(f"  {len(existing_scores)} already scored")
            print(f"  {len(runs_to_score)} to score")
        else:
            runs_to_score = runs
            if args.rescore:
                print("  Rescoring all runs")

        if args.dry_run:
            print("\n" + "=" * 60)
            print("DRY RUN - Would score:")
            print("=" * 60)
            print(f"\nRuns to score: {len(runs_to_score)}")
            print(f"Judge model: {args.judge_model or '(none - heuristic only)'}")
            print(f"Skip LLM judge: {args.skip_llm_judge}")
            return

        if not runs_to_score:
            print("\nNo runs to score. Use --rescore to rescore all runs.")
            return

        # Determine if we should run LLM judge
        run_llm_judge = args.judge_model is not None and not args.skip_llm_judge

        if run_llm_judge:
            print(f"\nScoring with LLM judge: {args.judge_model}")
        else:
            print("\nScoring with heuristic screening only")

        # Create scorer
        scorer = V2Scorer(
            config_loader=config_loader,
            judge_model=args.judge_model,
            judge_temperature=args.judge_temperature,
            run_llm_judge=run_llm_judge,
        )

        # Score runs
        results = scorer.score_runs_batch(
            runs=runs_to_score,
            experiment_id=args.experiment_id,
            save_results=True,
        )

        print(f"\n✓ Scoring complete: {len(results)} runs scored")

        # Quick summary
        if results:
            profiles = {}
            for r in results:
                if r.reasoner_profile:
                    p = r.reasoner_profile.value
                    profiles[p] = profiles.get(p, 0) + 1

            if profiles:
                print("\nProfile distribution:")
                for profile, count in sorted(profiles.items(), key=lambda x: -x[1]):
                    print(f"  {profile}: {count}")

        print(f"\nNext step: Analyze results with:")
        print(f"  python scripts/analyze_results_v2.py --experiment-id {args.experiment_id}")

    except KeyboardInterrupt:
        print("\n\nScoring interrupted by user")
    except Exception as e:
        print(f"\n✗ Scoring failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
