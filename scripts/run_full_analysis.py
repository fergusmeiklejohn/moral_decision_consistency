#!/usr/bin/env python3
"""
Run full analysis pipeline: metrics, framework classification, and human-friendly report.

Usage:
    python scripts/run_full_analysis.py --experiment-id <id> [--models m1,m2]
"""

import argparse
import subprocess
import sys
from pathlib import Path


def parse_models(value):
    if not value:
        return None
    models = [m.strip() for m in value.split(",") if m.strip()]
    return models or None


def main():
    parser = argparse.ArgumentParser(
        description="Run full analysis (metrics + report) for an experiment"
    )
    parser.add_argument("--experiment-id", required=True, help="Experiment ID")
    parser.add_argument(
        "--models",
        help="Comma-separated list of models to include in the report (analysis step always considers all runs)",
    )
    parser.add_argument(
        "--frameworks-mode",
        choices=["heuristic", "embedding"],
        default="embedding",
        help="Framework classifier mode for both analysis and report",
    )
    parser.add_argument(
        "--frameworks-embed-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Embedding model name for framework classification",
    )

    args = parser.parse_args()
    models_filter = parse_models(args.models)

    # Step 1: metrics + framework classification
    analyze_cmd = [
        sys.executable,
        "scripts/analyze_results.py",
        "--experiment-id",
        args.experiment_id,
        "--frameworks",
        "--frameworks-mode",
        args.frameworks_mode,
        "--frameworks-embed-model",
        args.frameworks_embed_model,
    ]
    subprocess.run(analyze_cmd, check=True)

    # Step 2: human-friendly report
    report_cmd = [
        sys.executable,
        "scripts/generate_human_report.py",
        "--experiment-id",
        args.experiment_id,
        "--frameworks-mode",
        args.frameworks_mode,
        "--frameworks-embed-model",
        args.frameworks_embed_model,
    ]
    if models_filter:
        report_cmd += ["--models", ",".join(models_filter)]
    subprocess.run(report_cmd, check=True)


if __name__ == "__main__":
    main()
