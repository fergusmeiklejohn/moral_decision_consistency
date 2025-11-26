#!/usr/bin/env python3
"""
Script to analyze experiment results.

Usage:
    python scripts/analyze_results.py --experiment-id <experiment_id>
    python scripts/analyze_results.py --list
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from collections import defaultdict
import json

from src.data.storage import ExperimentStorage
from src.analysis.metrics import MetricsCalculator
from src.data.schemas import AnalysisResult, PerturbationType


def analyze_experiment(experiment_id: str):
    """Analyze an experiment and generate reports."""
    print(f"\n{'='*80}")
    print(f"Analyzing Experiment: {experiment_id}")
    print(f"{'='*80}\n")

    storage = ExperimentStorage()
    calculator = MetricsCalculator()

    # Load experiment data
    print("Loading experiment data...")
    try:
        config = storage.load_experiment_config(experiment_id)
        all_runs = storage.load_runs(experiment_id)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    print(f"  Loaded {len(all_runs)} runs")

    # Get summary
    summary = storage.get_experiment_summary(experiment_id)
    print("\nExperiment Summary:")
    for key, value in summary.items():
        if not isinstance(value, (list, dict)):
            print(f"  {key}: {value}")

    # Analyze by model and dilemma
    print("\n" + "="*80)
    print("Consistency Analysis")
    print("="*80 + "\n")

    results = []

    # Group runs by model, dilemma, and temperature
    grouped = defaultdict(list)
    for run in all_runs:
        if run.perturbation_type.value == "none":  # Phase I analysis
            key = (run.model_name, run.dilemma_id, run.temperature)
            grouped[key].append(run)

    for (model_name, dilemma_id, temperature), runs in grouped.items():
        if len(runs) < 2:
            continue

        # Calculate metrics
        ccr = calculator.calculate_choice_consistency_rate(runs)
        refusal_rate = calculator.calculate_refusal_rate(runs)
        error_rate = calculator.calculate_error_rate(runs)
        reasoning_sim = calculator.calculate_reasoning_similarity(runs)
        flip_pattern = calculator.calculate_flip_pattern(runs)

        print(f"\nModel: {model_name}")
        print(f"Dilemma: {dilemma_id}")
        print(f"Temperature: {temperature}")
        print(f"  Runs: {len(runs)}")
        print(f"  Choice Consistency Rate: {ccr:.2%}")
        print(f"  Refusal Rate: {refusal_rate:.2%}")
        print(f"  Error Rate: {error_rate:.2%}")
        if reasoning_sim is not None:
            print(f"  Reasoning Similarity: {reasoning_sim:.2%}")
        print(f"  Flips: {flip_pattern['num_flips']} ({flip_pattern['flip_rate']:.2%})")

        # Save analysis result
        analysis = AnalysisResult(
            experiment_id=experiment_id,
            model_name=model_name,
            dilemma_id=dilemma_id,
            choice_consistency_rate=ccr,
            reasoning_similarity_score=reasoning_sim,
            refusal_rate=refusal_rate,
            statistical_tests={
                "flip_pattern": flip_pattern
            }
        )
        results.append(analysis)

    # Aggregate analysis by model
    print("\n" + "="*80)
    print("Aggregate Analysis by Model (Temperature=0)")
    print("="*80 + "\n")

    for model_name in summary["models"]:
        # Get all runs for this model at temp=0
        model_runs_temp0 = [
            run for run in all_runs
            if run.model_name == model_name
            and run.temperature == 0.0
            and run.perturbation_type.value == "none"
        ]

        if not model_runs_temp0:
            continue

        # Group by dilemma
        ccrs = []
        refusal_rates = []

        dilemma_groups = defaultdict(list)
        for run in model_runs_temp0:
            dilemma_groups[run.dilemma_id].append(run)

        for dilemma_id, dilemma_runs in dilemma_groups.items():
            if len(dilemma_runs) >= 2:
                ccr = calculator.calculate_choice_consistency_rate(dilemma_runs)
                refusal_rate = calculator.calculate_refusal_rate(dilemma_runs)
                ccrs.append(ccr)
                refusal_rates.append(refusal_rate)

        if ccrs:
            avg_ccr = sum(ccrs) / len(ccrs)
            avg_refusal = sum(refusal_rates) / len(refusal_rates)

            print(f"Model: {model_name}")
            print(f"  Average CCR: {avg_ccr:.2%}")
            print(f"  Average Refusal Rate: {avg_refusal:.2%}")
            print(f"  Dilemmas analyzed: {len(ccrs)}")

            # Determine interpretation
            if avg_ccr >= 0.95:
                interpretation = "HIGH CONSISTENCY - Strong replication risk"
            elif avg_ccr >= 0.70:
                interpretation = "MODERATE CONSISTENCY"
            else:
                interpretation = "LOW CONSISTENCY - Unstable reasoning"

            print(f"  Interpretation: {interpretation}\n")

    # Cross-model analysis
    print("="*80)
    print("Cross-Model Agreement Analysis (Temperature=0)")
    print("="*80 + "\n")

    # Group by dilemma
    for dilemma_id in summary["dilemmas"]:
        runs_by_model = defaultdict(list)

        for run in all_runs:
            if (run.dilemma_id == dilemma_id
                and run.temperature == 0.0
                and run.perturbation_type.value == "none"):
                runs_by_model[run.model_name].append(run)

        if len(runs_by_model) >= 2:
            agreement = calculator.calculate_cross_model_agreement(runs_by_model)

            print(f"Dilemma: {dilemma_id}")
            print(f"  Models tested: {agreement['num_models']}")
            if agreement['agreement_rate'] is not None:
                print(f"  Agreement rate: {agreement['agreement_rate']:.2%}")
                print(f"  Monoculture risk: {agreement['monoculture_risk']}")
                print(f"  Modal choices: {agreement['modal_choices']}")
            print()

    # Token usage summary (input vs output)
    print("="*80)
    print("Token Usage Summary")
    print("="*80 + "\n")

    overall_tokens = {
        "total": 0,
        "input": 0,
        "output": 0,
        "missing_total": 0,
        "missing_breakdown": 0
    }
    tokens_by_model = defaultdict(
        lambda: {
            "total": 0,
            "input": 0,
            "output": 0,
            "missing_total": 0,
            "missing_breakdown": 0
        }
    )

    for run in all_runs:
        response = run.response

        if response.tokens_used is not None:
            overall_tokens["total"] += response.tokens_used
            tokens_by_model[run.model_name]["total"] += response.tokens_used
        else:
            overall_tokens["missing_total"] += 1
            tokens_by_model[run.model_name]["missing_total"] += 1

        if response.input_tokens is not None:
            overall_tokens["input"] += response.input_tokens
            tokens_by_model[run.model_name]["input"] += response.input_tokens

        if response.output_tokens is not None:
            overall_tokens["output"] += response.output_tokens
            tokens_by_model[run.model_name]["output"] += response.output_tokens
        if response.input_tokens is None and response.output_tokens is None:
            overall_tokens["missing_breakdown"] += 1
            tokens_by_model[run.model_name]["missing_breakdown"] += 1

    print(
        f"Overall: total={overall_tokens['total']:,} | "
        f"input={overall_tokens['input']:,} | "
        f"output={overall_tokens['output']:,} | "
        f"runs missing total={overall_tokens['missing_total']} | "
        f"runs missing input/output breakdown={overall_tokens['missing_breakdown']}"
    )
    for model_name, stats in sorted(tokens_by_model.items()):
        print(
            f"  {model_name}: total={stats['total']:,} | "
            f"input={stats['input']:,} | "
            f"output={stats['output']:,} | "
            f"runs missing total={stats['missing_total']} | "
            f"runs missing input/output breakdown={stats['missing_breakdown']}"
        )
    print()

    # Type C synthetic error metrics
    type_c_runs = [
        run for run in all_runs
        if run.perturbation_type == PerturbationType.SYNTHETIC_ERROR
    ]

    if type_c_runs:
        print("="*80)
        print("Type C Synthetic Error Metrics")
        print("="*80 + "\n")

        for model_name in summary["models"]:
            model_runs = [
                run for run in type_c_runs
                if run.model_name == model_name
            ]
            metrics = calculator.calculate_type_c_metrics(model_runs)
            if not metrics["total_runs"]:
                continue

            print(f"Model: {model_name}")
            print(f"  Runs analyzed: {metrics['total_runs']}")
            print(f"  Localization Accuracy: {metrics['localization_accuracy']:.2%}")
            print(f"  Repair Success Rate: {metrics['repair_success_rate']:.2%}")
            print(f"  Minimality Score: {metrics['minimality_score']:.2f}")
            print(f"  Counterfactual Coherence: {metrics['counterfactual_coherence']:.2f}")
            print(f"  Explanation Alignment: {metrics['explanation_alignment']:.2f}\n")

            results.append(
                AnalysisResult(
                    experiment_id=experiment_id,
                    model_name=model_name,
                    localization_accuracy=metrics["localization_accuracy"],
                    repair_success_rate=metrics["repair_success_rate"],
                    minimality_score=metrics["minimality_score"],
                    counterfactual_coherence=metrics["counterfactual_coherence"],
                    statistical_tests={"type_c": metrics}
                )
            )

    # Save all results
    print("="*80)
    print("Saving Analysis Results")
    print("="*80 + "\n")

    for result in results[:5]:  # Save first 5 as examples
        storage.save_analysis_result(
            experiment_id,
            result,
            f"analysis_{result.model_name}_{result.dilemma_id}.json"
        )

    print(f"Analysis complete. Results saved to data/results/{experiment_id}/analysis/")


def list_experiments():
    """List all available experiments."""
    storage = ExperimentStorage()
    experiments = storage.list_experiments()

    if not experiments:
        print("No experiments found.")
        return

    print(f"\nAvailable experiments ({len(experiments)}):\n")

    for exp_id in experiments:
        try:
            summary = storage.get_experiment_summary(exp_id)
            print(f"  {exp_id}")
            print(f"    Runs: {summary['total_runs']}")
            print(f"    Models: {summary['num_models']}")
            print(f"    Dilemmas: {summary['num_dilemmas']}")
            print()
        except Exception as e:
            print(f"  {exp_id} (error loading summary)")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze experiment results"
    )

    parser.add_argument(
        "--experiment-id",
        help="Experiment ID to analyze"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available experiments"
    )

    args = parser.parse_args()

    if args.list:
        list_experiments()
    elif args.experiment_id:
        analyze_experiment(args.experiment_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
