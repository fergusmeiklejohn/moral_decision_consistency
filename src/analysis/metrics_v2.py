"""
V2 Metrics Calculator.

Computes aggregate metrics from V2 scoring results including:
- Dimension averages
- Profile distribution
- Red flag frequency
- Symmetric vs asymmetric comparison
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from statistics import mean, stdev

from ..data.schemas import (
    V2ScoringResult,
    V2AnalysisResult,
    DilemmaStructure,
    ReasonerProfile,
    ExperimentRunV2,
)
from ..data.storage import ExperimentStorage
from ..dilemmas.loader_v2 import DilemmaLoaderV2


class V2MetricsCalculator:
    """Calculates aggregate metrics for V2 experiments."""

    def __init__(
        self,
        dilemma_loader: Optional[DilemmaLoaderV2] = None,
        storage: Optional[ExperimentStorage] = None,
    ):
        """
        Initialize V2 Metrics Calculator.

        Args:
            dilemma_loader: V2 dilemma loader (for structure info)
            storage: Experiment storage
        """
        self.dilemma_loader = dilemma_loader or DilemmaLoaderV2()
        self.storage = storage or ExperimentStorage()

    def calculate_dimension_averages(
        self,
        results: List[V2ScoringResult],
    ) -> Dict[str, Optional[float]]:
        """
        Calculate average scores for each dimension.

        Args:
            results: List of V2ScoringResult

        Returns:
            Dict mapping dimension names to average scores
        """
        dimensions = [
            "principle_articulation",
            "consistency",
            "perspectival_range",
            "meta_awareness",
        ]

        averages = {}
        for dim in dimensions:
            scores = []
            for result in results:
                if dim in result.dimension_scores:
                    score = result.dimension_scores[dim].score
                    if score is not None:
                        scores.append(score)

            averages[dim] = mean(scores) if scores else None

        return averages

    def calculate_dimension_std(
        self,
        results: List[V2ScoringResult],
    ) -> Dict[str, Optional[float]]:
        """
        Calculate standard deviation for each dimension.

        Args:
            results: List of V2ScoringResult

        Returns:
            Dict mapping dimension names to standard deviation
        """
        dimensions = [
            "principle_articulation",
            "consistency",
            "perspectival_range",
            "meta_awareness",
        ]

        std_devs = {}
        for dim in dimensions:
            scores = []
            for result in results:
                if dim in result.dimension_scores:
                    score = result.dimension_scores[dim].score
                    if score is not None:
                        scores.append(score)

            if len(scores) >= 2:
                std_devs[dim] = stdev(scores)
            else:
                std_devs[dim] = None

        return std_devs

    def calculate_profile_distribution(
        self,
        results: List[V2ScoringResult],
    ) -> Dict[str, int]:
        """
        Calculate distribution of reasoner profiles.

        Args:
            results: List of V2ScoringResult

        Returns:
            Dict mapping profile names to counts
        """
        distribution = defaultdict(int)

        for result in results:
            if result.reasoner_profile:
                distribution[result.reasoner_profile.value] += 1
            else:
                distribution["unclassified"] += 1

        return dict(distribution)

    def calculate_red_flag_frequency(
        self,
        results: List[V2ScoringResult],
    ) -> Dict[str, int]:
        """
        Calculate frequency of each red flag.

        Args:
            results: List of V2ScoringResult

        Returns:
            Dict mapping flag names to counts
        """
        frequency = defaultdict(int)

        for result in results:
            for flag in result.red_flags:
                frequency[flag] += 1

        return dict(frequency)

    def calculate_structure_comparison(
        self,
        results: List[V2ScoringResult],
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare scores between symmetric and asymmetric dilemmas.

        Args:
            results: List of V2ScoringResult

        Returns:
            Dict with 'symmetric' and 'asymmetric' keys, each containing dimension averages
        """
        symmetric_results = []
        asymmetric_results = []

        for result in results:
            try:
                dilemma = self.dilemma_loader.get_dilemma(result.dilemma_id)
                if dilemma.structure == DilemmaStructure.SYMMETRIC:
                    symmetric_results.append(result)
                else:
                    asymmetric_results.append(result)
            except KeyError:
                continue

        return {
            "symmetric": self.calculate_dimension_averages(symmetric_results),
            "asymmetric": self.calculate_dimension_averages(asymmetric_results),
        }

    def calculate_model_comparison(
        self,
        results: List[V2ScoringResult],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare metrics across different models.

        Args:
            results: List of V2ScoringResult

        Returns:
            Dict mapping model names to their metrics
        """
        by_model = defaultdict(list)

        for result in results:
            by_model[result.model_name].append(result)

        comparison = {}
        for model, model_results in by_model.items():
            comparison[model] = {
                "count": len(model_results),
                "dimension_averages": self.calculate_dimension_averages(model_results),
                "dimension_std": self.calculate_dimension_std(model_results),
                "profile_distribution": self.calculate_profile_distribution(model_results),
                "red_flag_frequency": self.calculate_red_flag_frequency(model_results),
            }

        return comparison

    def calculate_dilemma_difficulty(
        self,
        results: List[V2ScoringResult],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate which dilemmas were harder/easier based on scores.

        Args:
            results: List of V2ScoringResult

        Returns:
            Dict mapping dilemma IDs to difficulty metrics
        """
        by_dilemma = defaultdict(list)

        for result in results:
            by_dilemma[result.dilemma_id].append(result)

        difficulty = {}
        for dilemma_id, dilemma_results in by_dilemma.items():
            avgs = self.calculate_dimension_averages(dilemma_results)
            overall_avg = mean([v for v in avgs.values() if v is not None]) if any(avgs.values()) else None

            difficulty[dilemma_id] = {
                "count": len(dilemma_results),
                "dimension_averages": avgs,
                "overall_average": overall_avg,
                "red_flag_rate": sum(1 for r in dilemma_results if r.red_flags) / len(dilemma_results) if dilemma_results else 0,
            }

        return difficulty

    def compute_analysis(
        self,
        experiment_id: str,
        model_name: Optional[str] = None,
        dilemma_id: Optional[str] = None,
    ) -> V2AnalysisResult:
        """
        Compute full analysis for an experiment.

        Args:
            experiment_id: Experiment ID
            model_name: Filter by model (optional)
            dilemma_id: Filter by dilemma (optional)

        Returns:
            V2AnalysisResult with all metrics
        """
        # Load scoring results
        results = self.storage.load_scoring_results_v2(experiment_id)

        # Filter if needed
        if model_name:
            results = [r for r in results if r.model_name == model_name]
        if dilemma_id:
            results = [r for r in results if r.dilemma_id == dilemma_id]

        if not results:
            return V2AnalysisResult(
                experiment_id=experiment_id,
                model_name=model_name or "all",
                dilemma_id=dilemma_id,
            )

        # Calculate metrics
        dim_avgs = self.calculate_dimension_averages(results)
        profile_dist = self.calculate_profile_distribution(results)
        flag_freq = self.calculate_red_flag_frequency(results)
        structure_comp = self.calculate_structure_comparison(results)

        return V2AnalysisResult(
            experiment_id=experiment_id,
            model_name=model_name or "all",
            dilemma_id=dilemma_id,
            avg_principle_articulation=dim_avgs.get("principle_articulation"),
            avg_consistency=dim_avgs.get("consistency"),
            avg_perspectival_range=dim_avgs.get("perspectival_range"),
            avg_meta_awareness=dim_avgs.get("meta_awareness"),
            profile_distribution=profile_dist,
            red_flag_frequency=flag_freq,
            symmetric_vs_asymmetric_scores=structure_comp,
        )

    def generate_summary_report(
        self,
        experiment_id: str,
    ) -> str:
        """
        Generate a human-readable summary report.

        Args:
            experiment_id: Experiment ID

        Returns:
            Formatted report string
        """
        results = self.storage.load_scoring_results_v2(experiment_id)

        if not results:
            return f"No scoring results found for experiment {experiment_id}"

        lines = [
            f"V2 Experiment Analysis: {experiment_id}",
            "=" * 60,
            "",
        ]

        # Overall stats
        lines.append(f"Total scored responses: {len(results)}")
        lines.append("")

        # Dimension averages
        dim_avgs = self.calculate_dimension_averages(results)
        dim_std = self.calculate_dimension_std(results)

        lines.append("Dimension Scores (1-5 scale):")
        lines.append("-" * 40)
        for dim in ["principle_articulation", "consistency", "perspectival_range", "meta_awareness"]:
            avg = dim_avgs.get(dim)
            std = dim_std.get(dim)
            if avg is not None:
                std_str = f" (±{std:.2f})" if std else ""
                lines.append(f"  {dim.replace('_', ' ').title()}: {avg:.2f}{std_str}")
        lines.append("")

        # Profile distribution
        profile_dist = self.calculate_profile_distribution(results)
        lines.append("Reasoner Profile Distribution:")
        lines.append("-" * 40)
        total = sum(profile_dist.values())
        for profile, count in sorted(profile_dist.items(), key=lambda x: -x[1]):
            pct = (count / total * 100) if total > 0 else 0
            lines.append(f"  {profile.replace('_', ' ').title()}: {count} ({pct:.1f}%)")
        lines.append("")

        # Red flag frequency
        flag_freq = self.calculate_red_flag_frequency(results)
        if flag_freq:
            lines.append("Red Flag Frequency:")
            lines.append("-" * 40)
            for flag, count in sorted(flag_freq.items(), key=lambda x: -x[1]):
                pct = (count / len(results) * 100)
                lines.append(f"  {flag.replace('_', ' ').title()}: {count} ({pct:.1f}%)")
            lines.append("")

        # Structure comparison
        structure_comp = self.calculate_structure_comparison(results)
        lines.append("Symmetric vs Asymmetric Dilemmas:")
        lines.append("-" * 40)
        for structure, avgs in structure_comp.items():
            overall = mean([v for v in avgs.values() if v is not None]) if any(avgs.values()) else None
            if overall:
                lines.append(f"  {structure.title()}: {overall:.2f} avg")
        lines.append("")

        # Model comparison
        model_comp = self.calculate_model_comparison(results)
        if len(model_comp) > 1:
            lines.append("Model Comparison:")
            lines.append("-" * 40)
            for model, metrics in model_comp.items():
                avgs = metrics["dimension_averages"]
                overall = mean([v for v in avgs.values() if v is not None]) if any(avgs.values()) else None
                if overall:
                    lines.append(f"  {model}: {overall:.2f} avg ({metrics['count']} responses)")
            lines.append("")

        # Dilemma difficulty
        diff = self.calculate_dilemma_difficulty(results)
        if diff:
            lines.append("Dilemma Difficulty (by average score):")
            lines.append("-" * 40)
            sorted_diff = sorted(
                diff.items(),
                key=lambda x: x[1]["overall_average"] if x[1]["overall_average"] else 0,
                reverse=True
            )
            for dilemma_id, metrics in sorted_diff:
                if metrics["overall_average"]:
                    lines.append(f"  {dilemma_id}: {metrics['overall_average']:.2f}")

        return "\n".join(lines)


def analyze_experiment_v2(experiment_id: str) -> V2AnalysisResult:
    """
    Convenience function to analyze a V2 experiment.

    Args:
        experiment_id: Experiment ID

    Returns:
        V2AnalysisResult
    """
    calculator = V2MetricsCalculator()
    return calculator.compute_analysis(experiment_id)


def print_experiment_report(experiment_id: str) -> None:
    """
    Print a summary report for a V2 experiment.

    Args:
        experiment_id: Experiment ID
    """
    calculator = V2MetricsCalculator()
    report = calculator.generate_summary_report(experiment_id)
    print(report)
