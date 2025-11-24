# Setup Guide

Quick guide to get the moral decision consistency research framework up and running.

## Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) for dependency and venv management
- API keys for cloud models (OpenAI, Anthropic, Google)
- (Optional) GPU for local models

## Installation Steps

### 1. Create and Sync the Environment with uv

```bash
# From the project root directory
uv venv                    # creates .venv
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows

# Install all dependencies from pyproject.toml + uv.lock
uv sync

# Note: requirements.txt is removed; please use uv to avoid dependency drift.
```

### 2. Configure API Keys

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
```

Add your API keys to `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_API_KEY=your-google-key-here
```

### 3. Verify Installation

Test that everything is installed correctly:

```bash
uv run python scripts/run_experiment.py --help
```

You should see the help message with available options.

### 4. Test with Mock Model

Before spending money on API calls, test with the mock model:

```bash
# Edit config/experiment.yaml
# Change the pilot models to: ["mock"]

uv run python scripts/run_experiment.py --phase pilot
```

This will run a simulated experiment with random responses to verify the pipeline works.

## Running Your First Real Experiment

### Option 1: Run Pilot Study

The pilot study tests 2 models × 5 dilemmas × 2 temperatures × 10 runs = 200 queries

```bash
# Edit config/experiment.yaml to set your models
# For example:
#   models:
#     - gpt-4o
#     - claude-3.5-sonnet

python scripts/run_experiment.py --phase pilot
```

Estimated cost: ~$2-5 depending on models

### Option 2: Run Full Phase I

The full Phase I study tests many models × 20 dilemmas × 4 temperatures × 30 runs = thousands of queries

```bash
python scripts/run_experiment.py --phase phase1
```

⚠️ **Warning:** This will make many API calls. Make sure you've:
1. Set appropriate rate limits in `config/experiment.yaml`
2. Verified your API budget
3. Run the pilot first!

## Analyzing Results

After running an experiment:

```bash
# List all experiments
uv run python scripts/analyze_results.py --list

# Analyze a specific experiment
uv run python scripts/analyze_results.py --experiment-id <experiment_id>
```

Results are saved in `data/results/<experiment_id>/`

## Setting Up Local Models (Optional)

### Using vLLM

1. Install vLLM:
```bash
uv add vllm  # install into your uv-managed environment
```

2. Start vLLM server:
```bash
vllm serve meta-llama/Llama-3-8b-instruct \
    --host 0.0.0.0 \
    --port 8000
```

3. Update `config/models.yaml` with the model name and endpoint

### Using Ollama

1. Install Ollama from https://ollama.ai

2. Pull a model:
```bash
ollama pull llama3
```

3. Ollama runs automatically on `localhost:11434`

4. Update `config/models.yaml` with the model name

### Pilot with Qwen3 14B Q5 via Ollama

The default local-first pilot uses the Qwen3 14B Q5 model running in Ollama. Follow these steps end-to-end:

1. **Pull the pilot model**  
   ```bash
   ollama pull qwen3:14b-instruct-q5_K_M  # or the shorter tag if already cached
   ```  
   If you already have a local model directory, confirm that `ollama list` shows `qwen3-14b-q5`.

2. **Confirm model configuration**  
   Make sure `config/models.yaml` includes the Ollama entry (already present in repo defaults):  
   ```yaml
   ollama:
     endpoint: http://localhost:11434/api/generate
     models:
       qwen3-14b-q5:
         name: qwen3-14b-q5
         supports_seed: true
         default_max_tokens: 500
   ```  
   Adjust the `name` if you use a different local tag.

3. **Verify connectivity**  
   Start Ollama (it auto-starts on pull) and run:  
   ```bash
   python scripts/verify_setup.py
   ```  
   Look for the `✓ Ollama/Qwen3 reachable` message. If you see a warning instead, ensure the Ollama daemon is running and that the model finished pulling.

4. **Run the pilot locally**  
   ```bash
   # Use the pilot config directly (default models already include qwen3-14b-q5)
   python scripts/run_experiment.py --phase pilot
   ```  
   To override models without editing YAML, pass `--models qwen3-14b-q5` (comma-separated for additional models).

5. **Inspect and iterate**  
   After the run, results live in `data/results/<experiment_id>/`. Re-run `verify_setup.py` whenever you change local model settings to ensure connectivity stays healthy.

## Troubleshooting

### "Module not found" errors

Make sure you're running scripts from the project root:
```bash
cd /path/to/moral_decision_consistency
python scripts/run_experiment.py --phase pilot
```

### API rate limit errors

Reduce `rate_limit_per_minute` in `config/experiment.yaml`

### Out of memory (local models)

Try smaller models or use quantization:
```bash
# For vLLM
vllm serve meta-llama/Llama-3-8b-instruct --quantization awq
```

### Sentence transformers download

On first run, sentence-transformers will download the embedding model (~80MB).
This is normal and only happens once.

## Next Steps

1. Read `DECISIONS.md` for areas that need your input
2. Review the dilemmas in `data/dilemmas/dilemmas.json`
3. Run a pilot experiment
4. Analyze the results
5. Refine and run the full study

## Getting Help

- Check `README.md` for architecture overview
- Check `DECISIONS.md` for implementation stubs
- Review the code in `src/` directories
- Each module has docstrings explaining functionality

## File Structure Quick Reference

```
moral_decision_consistency/
├── config/
│   ├── models.yaml          # Model configurations and API keys
│   └── experiment.yaml      # Experiment parameters
├── data/
│   ├── dilemmas/
│   │   └── dilemmas.json   # All moral dilemmas
│   └── results/            # Experiment results (auto-generated)
├── src/
│   ├── models/             # LLM provider implementations
│   ├── dilemmas/           # Dilemma loading and perturbation
│   ├── experiments/        # Phase I and II runners
│   ├── data/               # Data schemas and storage
│   └── analysis/           # Metrics and analysis
├── scripts/
│   ├── run_experiment.py   # Main experiment runner
│   └── analyze_results.py  # Analysis script
└── .env                    # Your API keys (create from .env.example)
```

Happy researching! 🔬
