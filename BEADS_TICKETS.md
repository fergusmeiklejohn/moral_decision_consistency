# Beads Tickets: Moral Decision Consistency Framework

This file captures Beads tickets derived from `DECISIONS.md` and the current codebase, focused on getting to a working local pilot with Qwen3 14B Q5 via Ollama plus one backlog item.

---

## 1) Enable config‑driven provider mapping so Ollama/Qwen3 can be used in experiments

**Priority:** High (blocking for using configured local models)  
**Area:** Provider selection, configuration

**Problem**  
`get_provider_from_model_name` in `src/models/__init__.py:70-99` uses a hard‑coded name heuristic and maps any `qwen` model to the `vllm` provider. Models configured under the `ollama` section in `config/models.yaml` (e.g. `qwen3` via Ollama) therefore cannot be used by experiments even if correctly defined in `models.yaml`.

**Scope / Files**
- `src/models/__init__.py` – provider inference logic
- `src/experiments/phase1_consistency.py` – provider initialization
- `src/experiments/phase2_perturbation.py` – provider initialization
- `src/config/loader.py` – access to `models.yaml`

**Tasks**
- Add a config‑aware helper (e.g. `get_provider_for_model_from_config`) that:
  - Uses `ConfigLoader.load_models_config()` to load `config/models.yaml`.
  - Searches provider sections (`openai`, `anthropic`, `google`, `vllm`, `ollama`, `mock`, etc.) for a `models` entry whose key matches the requested `model_name`.
  - Returns that provider name when found.
- Update Phase 1 and Phase 2 runners to call this helper when initializing providers, falling back to the existing heuristic only if the model name is not present in `models.yaml`.
- Keep error messages informative when a model cannot be found under any provider.

**Acceptance Criteria**
- Adding a model entry under `ollama.models` in `config/models.yaml` (e.g. `qwen3-14b-q5`) and including that name in `pilot.models` in `config/experiment.yaml` correctly instantiates `OllamaProvider` instead of `LocalVLLMProvider`.
- `python scripts/run_experiment.py --phase pilot` with `models: ["qwen3-14b-q5"]` completes provider initialization without `KeyError` and clearly reports that `qwen3-14b-q5` is using provider `ollama`.

---

## 2) Add Qwen3 14B Q5 Ollama config and switch the pilot to the local model

**Priority:** High (core to the decided pilot design)  
**Area:** Configuration

**Problem**  
`DECISIONS.md` states that the pilot will use a local model “Qwen3 14B Q5” via Ollama, but `config/models.yaml` and `config/experiment.yaml` still reference only cloud models for the pilot and generic local placeholders (`llama3`, `qwen2`). The pilot configuration does not yet reflect the agreed local‑first plan.

**Scope / Files**
- `config/models.yaml` – local model definitions under `ollama:`
- `config/experiment.yaml` – `pilot.models` list

**Tasks**
- In `config/models.yaml`, under the `ollama:` section:
  - Add a concrete model entry for the Qwen3 14B Q5 Ollama tag you intend to use (e.g. `qwen3-14b-q5`), with fields like:
    - `name: qwen3-14b-q5` (or the exact Ollama model name)
    - `supports_seed: true`
    - `default_max_tokens: 500` (or another sensible default)
  - Optionally deprecate or rename the existing `qwen2` placeholder to avoid confusion.
- Update `config/experiment.yaml`:
  - Change `pilot.models` from `[gpt-4o, claude-3.5-sonnet]` to use the local Qwen entry (e.g. `[qwen3-14b-q5]`) for the initial local‑only pilot.
  - Optionally keep comments indicating how to re‑add cloud models later.

**Acceptance Criteria**
- With Ollama running and the Qwen3 14B Q5 model pulled, `python scripts/run_experiment.py --phase pilot` runs successfully using only the local Qwen model.
- The stored config for the resulting experiment (`data/results/<experiment_id>/config.json`) lists only the Qwen3 model in `models`.

---

## 3) Add `requests` to dependencies and setup checks so local providers import cleanly

**Priority:** High (prevents runtime import errors for local models)  
**Area:** Dependencies, setup verification

**Problem**  
`src/models/local_model.py` imports `requests` for both `LocalVLLMProvider` and `OllamaProvider`, but `requirements.txt` does not list `requests`. A fresh environment that only installs `requirements.txt` will fail when trying to use any local provider. `scripts/verify_setup.py` also does not currently check for `requests`.

**Scope / Files**
- `src/models/local_model.py` – imports at the top of the file
- `requirements.txt` – core dependencies section
- `scripts/verify_setup.py` – `verify_imports()` required packages

**Tasks**
- Add `requests>=2.0.0` (or another stable version) to `requirements.txt` under “Core dependencies”.
- Update `scripts/verify_setup.py`:
  - In `verify_imports()`, extend `required_packages` with `("requests", "requests")` so missing `requests` is reported as REQUIRED.

**Acceptance Criteria**
- After `pip install -r requirements.txt`, running `python scripts/verify_setup.py` shows `requests` as present under “Checking Python imports...”.
- Importing and constructing `OllamaProvider` or `LocalVLLMProvider` in a Python REPL works without `ImportError`.

---

## 4) Implement `--models` CLI override in `run_experiment.py` for flexible local runs

**Priority:** Medium‑High (quality‑of‑life for piloting and local/cloud switches)  
**Area:** CLI script

**Problem**  
The README describes `--models` usage (e.g. `python scripts/run_experiment.py --phase pilot --models gpt-4o,claude-3.5-sonnet`), and `scripts/run_experiment.py` defines the `--models` argument, but the argument is never used. Similarly, `--config` prints “Custom config not yet implemented”. This makes it harder to quickly run “pilot with Qwen3 only” or to temporarily override configured models without editing YAML.

**Scope / Files**
- `scripts/run_experiment.py` – main CLI entrypoint
- `README.md` – quick‑start examples that mention `--models`

**Tasks**
- Refactor `run_experiment.py` so it:
  - Uses `ConfigLoader` to load the chosen experiment config (`pilot`, `phase1_consistency`, or `phase2_perturbation`) before running.
  - If `--models` is provided, parses the comma‑separated list and overrides `config.models` with that list.
  - Passes the (possibly overridden) `ExperimentConfig` instance into the appropriate runner rather than letting the runner reload from disk.
- Decide on the desired behavior for `--config`:
  - Either implement basic support for loading an alternate YAML file (e.g. `ConfigLoader(config_dir=...)` or direct load by path), or
  - Remove `--config` from the CLI and README if you don’t plan to support it now.
- Ensure README examples match the implemented behavior.

**Acceptance Criteria**
- `python scripts/run_experiment.py --phase pilot --models qwen3-14b-q5` runs a pilot using only the specified local Qwen model, without editing `config/experiment.yaml`.
- Using `--models` with cloud models (e.g. `gpt-5,claude-4.5,gemini-3.0` once configured) also works as expected.
- CLI help and README usage are consistent with the implemented behavior.

---

## 5) Extend `verify_setup.py` to check local model connectivity (Ollama + Qwen3)

**Priority:** Medium (helps catch local issues before long runs)  
**Area:** Setup verification, local models

**Problem**  
`scripts/verify_setup.py` currently verifies imports, project structure, basic config loading, dilemmas, and the mock provider. It does not check that local providers (especially the chosen Qwen3 via Ollama) are reachable. Misconfigurations will only surface once a full experiment is started.

**Scope / Files**
- `scripts/verify_setup.py` – `verify_models()` and configuration checks
- `config/models.yaml` – local model entries under `vllm:` and `ollama:`

**Tasks**
- Enhance `verify_models()` to:
  - Use `ConfigLoader` to load `models.yaml`.
  - Detect whether `ollama` and/or `vllm` providers are configured with at least one model.
  - For the Qwen3 entry added in Ticket 2, attempt a light connectivity check, for example:
    - `create_provider("ollama", "<qwen3-model-name>", ...)` using config data, then
    - Either `provider.validate_connection()` or a tiny `generate()` call with `max_tokens` small and a simple prompt like “Respond with: OK”.
  - Print clear messages such as:
    - `✓ Ollama/Qwen3 reachable`
    - `⚠ Ollama/Qwen3 not reachable; is Ollama running and is the model pulled?`
- Keep local model checks non‑fatal: warnings are acceptable so that lack of local setup does not stop all verification.

**Acceptance Criteria**
- When Ollama is running and Qwen3 is configured and pulled, `python scripts/verify_setup.py` reports a successful connectivity check for the local model.
- When Ollama is not running or the model is missing, the script reports a warning that explicitly identifies the local Qwen model, while other checks still complete.

---

## 6) Document “Pilot with Qwen3 14B Q5 via Ollama” workflow

**Priority:** Medium (documentation, but directly tied to agreed workflow)  
**Area:** Docs (`SETUP.md`, `README.md`)

**Problem**  
`SETUP.md` documents using Ollama with `llama3` as an example (`SETUP.md:129-140`), but your decisions specify piloting with Qwen3 14B Q5 via Ollama. There is no single, explicit workflow for someone to follow to run the local Qwen pilot end‑to‑end.

**Scope / Files**
- `SETUP.md` – “Setting Up Local Models (Optional)” section
- `README.md` – Quick start and “Model Support” sections

**Tasks**
- Add a short, explicit subsection to `SETUP.md`, e.g. “Pilot with Qwen3 14B Q5 via Ollama”, that covers:
  - Installing Ollama and running `ollama pull <qwen3-14b-q5-tag>` (exact tag TBD).
  - Confirming the Qwen3 entry exists under `ollama.models` in `config/models.yaml`.
  - Either:
    - Setting `pilot.models: ["<qwen3-14b-q5-tag>"]` in `config/experiment.yaml`, or
    - Running `python scripts/run_experiment.py --phase pilot --models <qwen3-14b-q5-tag>` (after Ticket 4 is implemented).
  - Running `python scripts/verify_setup.py` first to check everything, then the pilot.
- Optionally add a short note in `README.md` under “Local Models” linking to this subsection.

**Acceptance Criteria**
- A new “Qwen3 local pilot” subsection exists in `SETUP.md` and references the correct model name and commands.
- Following that subsection from a clean machine (with Python and Ollama installed) is sufficient to run a local Qwen pilot without modifying code.

---

## 7) Synthetic Internal Step Error (Type C): recommendation + minimal spec (Backlog)

**Priority:** Backlog (not needed for initial local pilot)  
**Area:** Phase II experimentation, reasoning graphs, metrics  
**Reference:** `DECISIONS.md` Synthetic Error Injection section

**Problem**  
Phase II includes a planned “Perturbation Type C: Synthetic Internal Step Error” mechanism. It is explicitly specced in `DECISIONS.md` but not implemented. This feature is more complex than simple perturbations and is not needed to start the local pilot, but should be tracked for later Phase II work.

**Scope / Files**
- `src/experiments/phase2_perturbation.py` – experiment runner and perturbation handling
- `src/data/schemas.py` – `ReasoningStep` and `ReasoningGraph`
- `src/analysis/metrics.py` – Phase II metrics (localization, repair, minimality, etc.)

**Minimal Spec (from DECISIONS.md)**
- **Pass 1 (structured reasoning graph):**
  - Prompt the model to produce **3–6 named steps** with **dependency edges** and **one‑line claims** (no free‑form chain‑of‑thought).
  - Output schema per step: `{"step": n, "claim": "...", "depends_on": [..]}`.
- **Error Injection:**
  - Apply a single error transform to a target step *k*:
    - `probability_swap` (e.g. A 55% ↔ 45%)
    - `sign_flip` (cost/benefit)
    - `culpability_misattribution` (innocent ↔ responsible)
    - `premise_drop` (remove a cited fact)
    - `numerical_offset` (+/− small delta)
- **Pass 2 (repair prompt):**
  - Provide the modified step set and instruct the model:  
    “Here is your step set with a mistake in **Step k**. Identify the error, minimally repair downstream steps only, and re‑decide A/B.”
- **Metrics:**
  - Localization accuracy
  - Repair success
  - **Minimality Score** (token‑distance outside affected subtree)
  - **Counterfactual Coherence**
  - **Explanation–Perturbation Alignment**

**Tasks**
- Implement Type C perturbation support in `Phase2Runner`, including:
  - Alternate prompting mode for structured steps.
  - Error injection logic over `ReasoningGraph`.
  - Second‑pass repair prompt and logging.
- Extend metrics in `src/analysis/metrics.py` to compute the listed Phase II measures from the logged data.

**Acceptance Criteria**
- Phase II can be run with `perturbation_types` including `synthetic_error`, generating structured reasoning graphs, injected errors, and repair passes.
- Analysis includes localization accuracy, repair success, minimality, and coherence metrics for Type C runs.

