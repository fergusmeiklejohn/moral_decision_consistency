#!/usr/bin/env python3
"""
Analyze V2 experiment results.

Generates metrics, reports, and visualizations from scored V2 experiment data.

Examples:
    # Print summary report
    python scripts/analyze_results_v2.py --experiment-id v2_20241201_120000

    # Detailed analysis by model
    python scripts/analyze_results_v2.py --experiment-id v2_20241201_120000 --by-model

    # Export metrics to JSON
    python scripts/analyze_results_v2.py --experiment-id v2_20241201_120000 --export metrics.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.loader import ConfigLoader
from src.analysis.metrics_v2 import (
    V2MetricsCalculator,
    analyze_experiment_v2,
    print_experiment_report,
)
from src.data.storage import ExperimentStorage


def main():
    parser = argparse.ArgumentParser(
        description="Analyze V2 moral reasoning experiment results"
    )

    parser.add_argument(
        "--experiment-id",
        required=True,
        help="ID of the experiment to analyze"
    )

    parser.add_argument(
        "--by-model",
        action="store_true",
        help="Show detailed breakdown by model"
    )

    parser.add_argument(
        "--by-dilemma",
        action="store_true",
        help="Show detailed breakdown by dilemma"
    )

    parser.add_argument(
        "--export",
        metavar="FILE",
        help="Export analysis results to JSON file"
    )

    parser.add_argument(
        "--model",
        help="Filter analysis to specific model"
    )

    parser.add_argument(
        "--dilemma",
        help="Filter analysis to specific dilemma"
    )

    args = parser.parse_args()

    try:
        storage = ExperimentStorage()
        calculator = V2MetricsCalculator(storage=storage)

        # Check if we have scoring results
        results = storage.load_scoring_results_v2(args.experiment_id)

        if not results:
            print(f"No scoring results found for experiment '{args.experiment_id}'")
            print("\nDid you run scoring? Try:")
            print(f"  python scripts/score_results_v2.py --experiment-id {args.experiment_id}")
            sys.exit(1)

        print(f"Analyzing {len(results)} scored responses...\n")

        # Apply filters
        if args.model:
            results = [r for r in results if r.model_name == args.model]
            if not results:
                print(f"No results found for model '{args.model}'")
                sys.exit(1)

        if args.dilemma:
            results = [r for r in results if r.dilemma_id == args.dilemma]
            if not results:
                print(f"No results found for dilemma '{args.dilemma}'")
                sys.exit(1)

        # Generate main report
        report = calculator.generate_summary_report(args.experiment_id)
        print(report)

        # Detailed model breakdown
        if args.by_model:
            print("\n" + "=" * 60)
            print("DETAILED MODEL ANALYSIS")
            print("=" * 60)

            model_comp = calculator.calculate_model_comparison(results)
            for model, metrics in sorted(model_comp.items()):
                print(f"\n### {model}")
                print(f"Responses: {metrics['count']}")

                print("\nDimension Scores:")
                for dim, avg in metrics['dimension_averages'].items():
                    if avg is not None:
                        std = metrics['dimension_std'].get(dim)
                        std_str = f" (±{std:.2f})" if std else ""
                        print(f"  {dim.replace('_', ' ').title()}: {avg:.2f}{std_str}")

                print("\nProfiles:")
                for profile, count in metrics['profile_distribution'].items():
                    pct = count / metrics['count'] * 100
                    print(f"  {profile}: {count} ({pct:.1f}%)")

                if metrics['red_flag_frequency']:
                    print("\nRed Flags:")
                    for flag, count in metrics['red_flag_frequency'].items():
                        print(f"  {flag}: {count}")

        # Detailed dilemma breakdown
        if args.by_dilemma:
            print("\n" + "=" * 60)
            print("DETAILED DILEMMA ANALYSIS")
            print("=" * 60)

            dilemma_diff = calculator.calculate_dilemma_difficulty(results)
            sorted_dilemmas = sorted(
                dilemma_diff.items(),
                key=lambda x: x[1]['overall_average'] if x[1]['overall_average'] else 0,
                reverse=True
            )

            for dilemma_id, metrics in sorted_dilemmas:
                print(f"\n### {dilemma_id}")
                print(f"Responses: {metrics['count']}")
                if metrics['overall_average']:
                    print(f"Overall Average: {metrics['overall_average']:.2f}")
                print(f"Red Flag Rate: {metrics['red_flag_rate']:.1%}")

                print("\nDimension Scores:")
                for dim, avg in metrics['dimension_averages'].items():
                    if avg is not None:
                        print(f"  {dim.replace('_', ' ').title()}: {avg:.2f}")

        # Export to JSON
        if args.export:
            analysis = calculator.compute_analysis(
                experiment_id=args.experiment_id,
                model_name=args.model,
                dilemma_id=args.dilemma,
            )

            export_data = {
                "experiment_id": analysis.experiment_id,
                "model_name": analysis.model_name,
                "dilemma_id": analysis.dilemma_id,
                "dimension_averages": {
                    "principle_articulation": analysis.avg_principle_articulation,
                    "consistency": analysis.avg_consistency,
                    "perspectival_range": analysis.avg_perspectival_range,
                    "meta_awareness": analysis.avg_meta_awareness,
                },
                "profile_distribution": analysis.profile_distribution,
                "red_flag_frequency": analysis.red_flag_frequency,
                "symmetric_vs_asymmetric": analysis.symmetric_vs_asymmetric_scores,
                "timestamp": analysis.timestamp.isoformat(),
            }

            # Add detailed breakdowns if requested
            if args.by_model:
                export_data["model_comparison"] = calculator.calculate_model_comparison(results)
            if args.by_dilemma:
                export_data["dilemma_difficulty"] = calculator.calculate_dilemma_difficulty(results)

            with open(args.export, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            print(f"\n✓ Analysis exported to {args.export}")

    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user")
    except Exception as e:
        print(f"\n✗ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
