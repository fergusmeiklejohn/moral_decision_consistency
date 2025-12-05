"""
Analysis module for moral decision consistency experiments.

V2 modules:
- heuristic_screen: Fast automated screening for V2 responses
- llm_judge: LLM-based scoring for V2 responses
- scoring_v2: V2 scoring orchestration
- metrics_v2: V2 metrics calculation and reporting
"""

from .heuristic_screen import heuristic_screen, screen_responses, summarize_screening_results
from .llm_judge import LLMJudge, build_judge_prompt, extract_scores, extract_red_flags
from .scoring_v2 import V2Scorer, score_experiment_v2, classify_reasoner_profile
from .metrics_v2 import V2MetricsCalculator, analyze_experiment_v2, print_experiment_report

__all__ = [
    # Heuristic screening
    "heuristic_screen",
    "screen_responses",
    "summarize_screening_results",
    # LLM Judge
    "LLMJudge",
    "build_judge_prompt",
    "extract_scores",
    "extract_red_flags",
    # Scoring
    "V2Scorer",
    "score_experiment_v2",
    "classify_reasoner_profile",
    # Metrics
    "V2MetricsCalculator",
    "analyze_experiment_v2",
    "print_experiment_report",
]
