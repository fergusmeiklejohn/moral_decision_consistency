# Moral Decision Consistency Research Framework

A comprehensive research tooling framework for studying moral decision consistency and replication risk in frontier AI systems.

## Overview

This framework implements the methodology described in:
- **Phase I**: Moral Decision Consistency Testing
- **Phase II**: Causal-Structure Perturbation Testing

It provides a unified **Moral Systems Safety (MSS)** evaluation suite that can work with any LLM.

## Architecture

The system is designed with complete model abstraction, allowing you to:
- ✅ Swap models easily via configuration
- ✅ Run experiments on any LLM (cloud or local)
- ✅ Collect standardized data across all models
- ✅ Generate comparative reports

### Directory Structure

```
moral_decision_consistency/
├── src/                    # Core source code
│   ├── config/            # Configuration management
│   ├── models/            # Model abstraction layer
│   ├── dilemmas/          # Dilemma management and perturbation
│   ├── experiments/       # Experiment runners (Phase I & II)
│   ├── data/              # Data storage and schemas
│   ├── analysis/          # Analysis, metrics, and visualization
│   └── utils/             # Parsing and utilities
├── data/
│   ├── dilemmas/          # Dilemma definitions
│   └── results/           # Experiment results (auto-generated)
├── config/                # Configuration files
├── scripts/               # Executable scripts
└── notebooks/             # Analysis notebooks
```

## Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Configure Models

Edit `config/models.yaml` to add your API keys and model configurations.

### 3. Run Pilot Experiment

```bash
# Uses the models defined in config/experiment.yaml (currently local Qwen3 14B Q5)
python scripts/run_experiment.py --phase pilot

# Temporarily test different models without editing configuration
python scripts/run_experiment.py --phase pilot --models gpt-4o,claude-3.5-sonnet
```

Need a local-first walkthrough? See **SETUP.md → “Pilot with Qwen3 14B Q5 via Ollama”** for pulling the model, verifying connectivity, and running the pilot end-to-end.

### 4. Analyze Results

```bash
python scripts/analyze_results.py --experiment-id <experiment_id>
```

## Model Support

The framework supports:

### Cloud Models
- **OpenAI**: GPT-4, GPT-4o, GPT-3.5-turbo, etc.
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus, etc.
- **Google**: Gemini 1.5 Pro, Gemini 1.5 Flash, etc.
- **DeepSeek**: DeepSeek Chat, DeepSeek Reasoner, etc.

### Local Models
- Any model via vLLM
- Any model via Ollama
- Custom inference endpoints

## Features

### Phase I: Consistency Testing
- Run 20 moral dilemmas × 30 repetitions × 4 temperature settings
- Automatic parsing and validation
- Real-time progress tracking
- Rate limiting and retry logic
- Data backup every 100 queries

### Phase II: Perturbation Testing
- Morally relevant fact changes
- Morally irrelevant detail changes
- Synthetic internal step error injection
- Reasoning graph extraction
- Causal sensitivity measurement

### Analysis
- Choice Consistency Rate (CCR)
- Reasoning similarity (semantic embeddings)
- Refusal rate tracking
- Statistical tests (chi-square, Fisher's exact, etc.)
- Cross-model monoculture detection
- MSS Quadrant visualization

## Configuration

All experiments are configured via YAML files:

- `config/models.yaml` - Model definitions and API keys
- `config/experiment.yaml` - Experimental parameters
- `data/dilemmas/dilemmas.json` - Dilemma definitions

CLI overrides:

- `--models model1,model2` temporarily replaces the `models` list for the current run.
- `--config path/to/experiments.yaml` points to an alternate experiment configuration file. The file can either
  follow the structure of `config/experiment.yaml` (multiple experiments) or contain a single experiment definition. If multiple
  experiments are present, keep using `--phase` to choose which one to run.

## Data Schema

All results are stored in structured JSON format with:
- ISO 8601 timestamps
- Model name and version
- Dilemma ID and category
- Temperature and sampling parameters
- Raw response and parsed choice
- Reasoning text
- Response time and token usage

## Citation

If you use this framework, please cite:
```
[Citation to be added after publication]
```

## License

[License to be determined]
