#!/usr/bin/env python3
"""
Generate a human-friendly experiment report with framework analysis.

Usage:
    python scripts/generate_human_report.py --experiment-id <id> [--models m1,m2]
    python scripts/generate_human_report.py --experiment-id pilot_20251126_045946 --models gpt-oss-20gb
"""

import argparse
import json
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.metrics import MetricsCalculator
from src.analysis.frameworks import (
    FrameworkClassifier,
    EmbeddingFrameworkClassifier,
)
from src.data.storage import ExperimentStorage
from src.data.schemas import ExperimentRun, PerturbationType
from src.dilemmas.loader import DilemmaLoader


def parse_models_arg(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    models = [m.strip() for m in value.split(",") if m.strip()]
    return models or None


def classify_frameworks(
    experiment_id: str,
    runs: List[ExperimentRun],
    mode: str = "embedding",
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> Dict[str, Dict]:
    """
    Classify frameworks for runs, caching to analysis/framework_analysis.jsonl.

    Returns a mapping run_id -> record.
    """
    storage = ExperimentStorage()
    exp_dir = storage.create_experiment_directory(experiment_id)
    label_file = exp_dir / "analysis" / "framework_analysis.jsonl"

    # Load cache
    cached = {}
    if label_file.exists():
        for line in label_file.read_text().splitlines():
            try:
                obj = json.loads(line)
                cached[obj["run_id"]] = obj
            except Exception:
                continue

    # Select classifier
    if mode == "embedding":
        classifier = EmbeddingFrameworkClassifier(embed_model)
        method_label = f"embedding:{embed_model}"
    else:
        classifier = FrameworkClassifier()
        method_label = "heuristic"

    labels_by_run = {}
    records = []

    for run in runs:
        cached_rec = cached.get(run.run_id)
        needs_reclassify = (
            cached_rec is None
            or "analysed_moral_framework" not in cached_rec
            or "moral_framework_analysis_confidence" not in cached_rec
        )

        if needs_reclassify:
            result = classifier.classify_reasoning(run.response.reasoning)
            method = result.method

            record = {
                "run_id": run.run_id,
                "run_timestamp": run.timestamp.isoformat(),
                "experiment_id": experiment_id,
                "model_name": run.model_name,
                "model_version": run.model_version,
                "provider": run.provider,
                "dilemma_id": run.dilemma_id,
                "dilemma_category": run.dilemma_category.value,
                "temperature": run.temperature,
                "perturbation_type": run.perturbation_type.value,
                "position_order": run.position_order,
                "parsed_choice": run.response.parsed_choice.value,
                "reasoning": run.response.reasoning,
                "analysed_moral_framework": result.label.value,
                "moral_framework_analysis_confidence": result.confidence,
                "moral_framework_method": method,
                "matched_keywords": result.matched_keywords,
            }
        else:
            record = dict(cached_rec)
            record.setdefault("run_timestamp", run.timestamp.isoformat())
            record.setdefault("model_version", run.model_version)
            record.setdefault("provider", run.provider)
            record.setdefault("dilemma_category", run.dilemma_category.value)
            record.setdefault("perturbation_type", run.perturbation_type.value)
            record.setdefault("position_order", run.position_order)
            record.setdefault("parsed_choice", run.response.parsed_choice.value)
            record.setdefault("reasoning", run.response.reasoning)
            record.setdefault("analysed_moral_framework", cached_rec.get("label") if cached_rec else None)
            record.setdefault("moral_framework_analysis_confidence", cached_rec.get("confidence") if cached_rec else None)
            record.setdefault("moral_framework_method", cached_rec.get("method") if cached_rec else method_label)

        labels_by_run[run.run_id] = record
        records.append(record)

    # Persist cache (overwrite)
    label_file.write_text("\n".join(json.dumps(r) for r in records))
    return labels_by_run


def build_summary(
    runs: List[ExperimentRun],
    labels_by_run: Dict[str, Dict],
    calculator: MetricsCalculator,
) -> List[Tuple[str, str, float, Dict, float, float, Dict]]:
    """
    Build summary rows per model/dilemma/temperature.

    Returns list of tuples:
        (model_name, dilemma_id, temperature, framework_counts, ccr, refusal, choice_framework_pairs)
    """
    grouped = defaultdict(list)
    for run in runs:
        key = (run.model_name, run.dilemma_id, run.temperature)
        grouped[key].append(run)

    summary_rows = []
    for (model_name, dilemma_id, temperature), group_runs in grouped.items():
        ccr = calculator.calculate_choice_consistency_rate(group_runs)
        refusal = calculator.calculate_refusal_rate(group_runs)
        framework_counts = Counter()
        choice_framework_pairs = Counter()
        for r in group_runs:
            rec = labels_by_run.get(r.run_id)
            if not rec:
                continue
            label = rec.get("analysed_moral_framework") or rec.get("label")
            framework_counts[label] += 1
            pair_key = (label, r.response.parsed_choice.value)
            choice_framework_pairs[pair_key] += 1

        summary_rows.append(
            (model_name, dilemma_id, temperature, dict(framework_counts), ccr, refusal, dict(choice_framework_pairs))
        )
    return summary_rows


def render_report(
    experiment_id: str,
    runs: List[ExperimentRun],
    labels_by_run: Dict[str, Dict],
    summary_rows: List[Tuple[str, str, float, Dict, float, float, Dict]],
    framework_mode: str,
    framework_model: str,
    dilemmas: Dict[str, Dict],
    output_path: Path,
) -> None:
    """Render markdown report and write to output_path."""
    generated_at = datetime.utcnow().isoformat()
    models = sorted({r.model_name for r in runs})
    temps = sorted({r.temperature for r in runs})
    dilemmas_used = sorted({r.dilemma_id for r in runs})

    lines: List[str] = []
    lines.append(f"# Experiment Report: {experiment_id}")
    lines.append("")
    lines.append(f"- Generated at (UTC): {generated_at}")
    lines.append(f"- Models: {', '.join(models)}")
    lines.append(f"- Temperatures: {', '.join(str(t) for t in temps)}")
    lines.append(f"- Total runs: {len(runs)}")
    lines.append(f"- Moral Decision Framework analysis mode: {framework_mode} ({framework_model})")
    lines.append("")
    lines.append("## Dilemmas")
    for did in dilemmas_used:
        info = dilemmas.get(did, {})
        title = info.get("title", "")
        desc = info.get("description", "")
        choice_a = info.get("choice_a", "")
        choice_b = info.get("choice_b", "")
        lines.append(f"- **{did}** — {title}".strip())
        if desc:
            lines.append(f"  - {desc}")
        if choice_a or choice_b:
            lines.append(f"  - CHOICE A: {choice_a}")
            lines.append(f"  - CHOICE B: {choice_b}")
        lines.append("")
    lines.append("")

    # Summary section
    lines.append("## Summary Analysis")
    for row in summary_rows:
        model_name, dilemma_id, temperature, framework_counts, ccr, refusal, choice_framework_pairs = row
        lines.append(f"### {model_name} | {dilemma_id} | Temp={temperature}")
        lines.append(f"- Choice Consistency Rate: {ccr:.2%}")
        lines.append(f"- Refusal Rate: {refusal:.2%}")
        lines.append(f"- Framework distribution: {framework_counts}")
        if choice_framework_pairs:
            lines.append(f"- Choice x Framework counts: {choice_framework_pairs}")
        lines.append("")

    # Per-run detail
    lines.append("## Runs (with framework analysis)")
    runs_sorted = sorted(runs, key=lambda r: (r.model_name, r.dilemma_id, r.temperature, r.run_number))
    for run in runs_sorted:
        rec = labels_by_run.get(run.run_id, {})
        label = rec.get("analysed_moral_framework") or rec.get("label")
        conf = rec.get("moral_framework_analysis_confidence") or rec.get("confidence")
        lines.append(f"### Run {run.run_id}")
        lines.append(f"- Model: {run.model_name} (provider: {run.provider}, version: {run.model_version})")
        lines.append(f"- Timestamp: {run.timestamp.isoformat()}")
        lines.append(f"- Dilemma: {run.dilemma_id} ({run.dilemma_category.value})")
        lines.append(f"- Perturbation: {run.perturbation_type.value} | Position: {run.position_order} | Temp: {run.temperature}")
        lines.append(f"- Choice: {run.response.parsed_choice.value}")
        lines.append(f"- Moral framework: {label} (confidence: {conf})")
        lines.append(f"- Reasoning:\n{run.response.reasoning}")
        lines.append("")

    output_path.write_text("\n".join(lines))
    print(f"Wrote report to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate human-friendly experiment report with framework analysis"
    )
    parser.add_argument("--experiment-id", required=True, help="Experiment ID to analyze")
    parser.add_argument(
        "--models",
        help="Comma-separated list of models to include (default: all models in runs)",
    )
    parser.add_argument(
        "--frameworks-mode",
        choices=["heuristic", "embedding"],
        default="embedding",
        help="Framework classifier mode",
    )
    parser.add_argument(
        "--frameworks-embed-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Embedding model name for framework classification",
    )
    parser.add_argument(
        "--output",
        help="Output path for report (default: data/results/<id>/analysis/report_<models>.md)",
    )

    args = parser.parse_args()

    models_filter = parse_models_arg(args.models)

    storage = ExperimentStorage()
    calculator = MetricsCalculator()
    loader = DilemmaLoader()

    config = storage.load_experiment_config(args.experiment_id)
    all_runs = storage.load_runs(args.experiment_id)

    if models_filter:
        runs = [r for r in all_runs if r.model_name in models_filter]
    else:
        runs = all_runs

    if not runs:
        print("No runs found for the requested filters.")
        return

    labels_by_run = classify_frameworks(
        args.experiment_id,
        runs,
        mode=args.frameworks_mode,
        embed_model=args.frameworks_embed_model,
    )

    summary_rows = build_summary(runs, labels_by_run, calculator)

    # Dilemma info for rendering
    dilemmas_info = {}
    for did in config.dilemma_ids:
        try:
            d = loader.get_dilemma(did)
            dilemmas_info[did] = {
                "title": d.title,
                "description": d.description,
                "choice_a": d.choice_a,
                "choice_b": d.choice_b,
            }
        except Exception:
            dilemmas_info[did] = {}

    # Output path
    exp_dir = storage.create_experiment_directory(args.experiment_id)
    if args.output:
        output_path = Path(args.output)
    else:
        model_suffix = "all" if not models_filter else "_".join(models_filter)
        if model_suffix == "all":
            output_path = exp_dir / "analysis" / "report_and_summary.md"
        else:
            output_path = exp_dir / "analysis" / f"report_and_summary_{model_suffix}.md"

    render_report(
        args.experiment_id,
        runs,
        labels_by_run,
        summary_rows,
        args.frameworks_mode,
        args.frameworks_embed_model,
        dilemmas_info,
        output_path,
    )


if __name__ == "__main__":
    main()
