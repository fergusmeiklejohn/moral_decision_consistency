# Decisions and Implementation Stubs

This document lists areas that require your input, decisions, or additional implementation. These have been left as stubs or TODOs to discuss together.

## 1. Model Selection and Configuration

### 1.1 Which Models to Test?
**Status:** Stub - needs your decision

**Location:** `config/experiment.yaml`

**Current State:**
- Pilot study configured with: `gpt-4o`, `claude-3.5-sonnet`
- Phase I configured with: `gpt-4o`, `claude-3.5-sonnet`, `gemini-1.5-pro`
- Local models commented out

**Decisions Needed:**
1. Which specific OpenAI models? (gpt-4o, gpt-4-turbo, gpt-3.5-turbo, o1, o3?)
2. Which Claude versions? (3.5 Sonnet, 3 Opus, 3 Haiku?)
3. Which Google models? (Gemini 1.5 Pro, Flash, 2.0?)
4. Do you want to test local models? Which ones?
   - Llama 3 (8B, 70B)?
   - Qwen 2.5 (7B, 14B, 72B)?
   - Mistral models?
   - Others (Phi, DeepSeek, etc.)?
5. Do you have API access to all needed models?

**Budget Considerations:**
- Full Phase I study: ~2,400 queries per model
- Estimated cost: $15-20 per cloud model (for GPT-4o class)
- Total for 5 models: ~$75-100

---

### 1.2 Local Model Infrastructure
**Status:** Stub - infrastructure not set up

**Decisions Needed:**
1. Do you want to run local models?
2. Which inference engine?
   - vLLM (faster, GPU required)
   - Ollama (easier setup, slower)
   - Other (TGI, llama.cpp)?
3. What hardware do you have available?
   - GPU memory?
   - Can you run 7B models? 70B models?

**If Yes to Local Models:**
- Need to set up inference server
- Need to configure endpoints in `config/models.yaml`
- May need quantization (4-bit, 8-bit) for larger models

---

## 2. Dilemma Design and Content

### 2.1 Dilemma Refinement
**Status:** Implemented with examples, may need refinement

**Location:** `data/dilemmas/dilemmas.json`

**Current State:**
- 20 dilemmas created across 4 categories
- Some have perturbation variants defined
- Based on proposal specifications

**Decisions Needed:**
1. Review each dilemma for:
   - Clarity of presentation
   - Binary choice framing
   - Potential bias in wording
   - Cultural sensitivity
2. Are the perturbations appropriate?
   - Relevant changes truly morally relevant?
   - Irrelevant changes truly irrelevant?
3. Should we add more dilemmas? Fewer?
4. Should we pilot test with humans first to validate difficulty?

**Potential Issues:**
- Some dilemmas may be culturally specific
- Some may have obvious "correct" answers
- Wording may inadvertently bias responses

---

### 2.2 Missing Perturbation Variants
**Status:** Incomplete - not all dilemmas have perturbation variants

**Current State:**
- Only 4 dilemmas have perturbation variants defined
- Phase II requires all test dilemmas to have variants

**Decisions Needed:**
1. Which dilemmas to use in Phase II?
2. Need to create perturbation variants for each:
   - What constitutes a "relevant" change for each dilemma?
   - What constitutes an "irrelevant" change?
3. Should we create multiple variants per perturbation type?

**Action Items:**
- Create perturbation variants for remaining dilemmas
- Validate that perturbations are appropriate
- Document expected effects

---

### 2.3 Synthetic Error Injection (Phase II)
**Status:** Not implemented

**Location:** Would be in `src/experiments/phase2_perturbation.py`

**What's Missing:**
The proposal describes "Perturbation Type C: Synthetic Internal Step Error" where you:
1. Get the model to generate step-by-step reasoning
2. Inject a known error into one step
3. Test if model can localize and repair the error

**Decisions Needed:**
1. Is this feature a priority for the initial implementation?
2. If yes, how should we structure it?
   - Two-pass approach (generate reasoning, then test repair)?
   - Specific error types to inject?
3. Should we implement this now or in a future iteration?

**Complexity:**
- Requires reasoning graph extraction
- Requires structured prompting for step-by-step reasoning
- Needs error injection logic
- More complex than basic perturbation testing

**My Recommendation:** Start with basic perturbations (relevant/irrelevant), add synthetic errors later if needed.

---

## 3. Experimental Design Details

### 3.1 Sample Size and Statistical Power
**Status:** Using values from proposal, not validated

**Current Configuration:**
- 30 runs per condition
- 4 temperature settings
- 20 dilemmas

**Decisions Needed:**
1. Is 30 runs sufficient for statistical power?
2. Should we do power analysis first?
3. Are 4 temperature settings necessary or could we reduce?
4. Pilot study uses 10 runs - is this enough to validate the methodology?

**Statistical Considerations:**
- Need to detect consistency differences
- Multiple comparisons (many dilemmas × models × temperatures)
- May need Bonferroni or FDR correction

---

### 3.2 Control Measures
**Status:** Implemented as specified, needs validation

**Current Controls:**
- Fixed random seed (for models that support it)
- Identical system prompt
- No conversation history
- Timestamp logging
- Randomized dilemma order
- Position bias testing (reversed choices)

**Decisions Needed:**
1. What should the system prompt be?
   - Currently using minimal framing
   - Should we add any context? ("You are an AI assistant...")
   - Should we emphasize that it's for research?
2. How to handle model refusals?
   - Currently tracked separately
   - Should we retry with different framing?
   - Frame as "thought experiment"?
3. Time-of-day effects?
   - Should we randomize query timing?
   - Spread over multiple days?

---

### 3.3 Rate Limiting and Cost Management
**Status:** Implemented with default values

**Current Settings:**
- 60 requests per minute (configurable)
- 3 retry attempts
- Exponential backoff

**Decisions Needed:**
1. What's your API rate limit for each provider?
2. What's your budget per model?
3. Should we implement cost tracking?
4. Pause/resume functionality if hitting limits?

---

## 4. Analysis and Metrics

### 4.1 Statistical Tests
**Status:** Partially implemented, needs completion

**Implemented:**
- Choice Consistency Rate (CCR)
- Reasoning similarity (semantic embeddings)
- Refusal rate
- Flip pattern analysis
- Cross-model agreement

**Not Implemented (from proposal):**
- Chi-square goodness of fit test
- Cochran's Q test
- Fisher's exact test
- Friedman test
- Linear regression (temperature → consistency)
- Spearman correlation (human disagreement vs LLM consistency)

**Decisions Needed:**
1. Which statistical tests are priority?
2. Do you have access to human disagreement data for dilemmas?
3. Should we implement all tests now or add iteratively?
4. Multiple comparison corrections?

**Action Items:**
- Implement remaining statistical tests in `src/analysis/statistics.py`
- Add hypothesis testing framework
- Document statistical methodology

---

### 4.2 Reasoning Analysis
**Status:** Basic similarity implemented, qualitative analysis stub

**Current State:**
- Semantic similarity using sentence-transformers
- Model: `all-MiniLM-L6-v2` (can be changed)

**Not Implemented:**
- Moral framework detection (utilitarian vs deontological)
- Reasoning graph extraction
- Causal dependency analysis

**Decisions Needed:**
1. How important is qualitative reasoning analysis?
2. Should we use LLMs to code reasoning frameworks?
   - Use GPT-4 to classify reasoning as utilitarian/deontological?
   - Manual coding by researchers?
3. Which frameworks to look for?
   - Utilitarian
   - Deontological
   - Virtue ethics
   - Care ethics
   - Others?

**Complexity:**
- May require manual annotation
- Could use LLM-based coding (but adds cost and complexity)
- Reasoning graph extraction is non-trivial

---

### 4.3 Visualization and Reporting
**Status:** Stub - basic text reports only

**Current State:**
- Text-based analysis output
- JSON data storage

**Missing:**
- Graphs and charts
- MSS Quadrant visualization
- Consistency heatmaps
- Cross-model comparison plots
- Temperature effect curves
- Interactive dashboards

**Decisions Needed:**
1. What visualizations are most important?
2. Static images (matplotlib/seaborn) or interactive (plotly)?
3. Should we create a dashboard (Streamlit, Gradio)?
4. Output format for paper (publication-quality figures)?

**Suggested Visualizations:**
- Heatmap: Model × Dilemma → CCR
- Line plot: Temperature → Consistency
- Bar chart: Cross-model agreement per dilemma
- Scatter: MSS Quadrant (stability vs sensitivity)
- Box plots: CCR distribution per model
- Confusion matrices: Choice transitions

---

## 5. Data Management and Reproducibility

### 5.1 Data Storage Format
**Status:** Implemented with JSONL, may need alternatives

**Current Format:**
- JSONL (JSON Lines) for experiment runs
- JSON for configs and analysis
- Incremental append-friendly

**Decisions Needed:**
1. Is JSONL sufficient or need database?
2. Should we add SQLite for better querying?
3. Export formats needed?
   - CSV for spreadsheet analysis?
   - Parquet for data science tools?
   - HDF5 for large datasets?

---

### 5.2 Data Versioning and Reproducibility
**Status:** Basic backup system, no formal versioning

**Current State:**
- Auto-backup every N queries
- Experiment ID timestamped
- Config saved with results

**Missing:**
- Git LFS for data versioning
- DVC (Data Version Control)
- Checksums/hashes for data integrity
- Formal provenance tracking

**Decisions Needed:**
1. How formal should reproducibility be?
2. Planning to publish data? (need strong provenance)
3. Should we use DVC or similar?

---

### 5.3 Data Privacy and Ethics
**Status:** No sensitive data, but needs formal documentation

**Decisions Needed:**
1. Where will data be stored long-term?
2. Will you publish the raw responses?
   - Some models may generate unexpected content
   - Need review before publication?
3. License for released data?
   - CC-BY-4.0?
   - CC0 (public domain)?
   - Other?
4. Should we anonymize model versions?
   - Keep exact version numbers?
   - Generic labels?

---

## 6. Implementation Priorities

### 6.1 What to Build Next?
**Current Status:** Core infrastructure complete

**What's Working:**
- Model abstraction (can swap any LLM)
- Dilemma management
- Phase I consistency experiments
- Basic Phase II perturbation experiments
- Data storage and retrieval
- Basic analysis metrics

**What's Stubbed/Missing:**
1. Statistical tests (medium priority)
2. Visualization (medium-high priority)
3. Synthetic error injection (low priority - can skip)
4. Reasoning graph extraction (medium priority)
5. Moral framework coding (low-medium priority)
6. Advanced analysis (cross-temporal, etc.)

**Suggested Priority Order:**
1. **Run pilot study** to validate methodology
2. **Implement key visualizations** for initial results
3. **Add statistical tests** for rigor
4. **Refine dilemmas** based on pilot
5. **Run full Phase I**
6. **Implement remaining Phase II features** as needed

**Your Input Needed:**
- Which features are must-have vs nice-to-have?
- What's your timeline?
- Any features I should deprioritize?

---

## 7. Technical Stubs and TODOs

### 7.1 Code TODOs

**In `scripts/run_experiment.py`:**
- Line 28: Custom config loading not implemented
- Line 35: Model override from CLI not implemented

**In `src/models/openai_model.py`:**
- Error handling could be more sophisticated
- No retry on rate limits (handled by tenacity in experiment runner)

**In `src/analysis/metrics.py`:**
- Phase II metrics (localization, repair, minimality) defined but not fully implemented
- Need to build actual calculation logic when we have Phase II data

**In `src/experiments/phase2_perturbation.py`:**
- Synthetic error injection not implemented
- Reasoning graph extraction not implemented

---

### 7.2 Testing
**Status:** No tests written

**Decisions Needed:**
1. Should we write unit tests?
2. Integration tests?
3. Test coverage goals?

**Suggested Tests:**
- Model provider mocking
- Dilemma loading
- Metrics calculation with known data
- End-to-end pilot experiment

---

## 8. Quick Start Decisions

### To Run Your First Experiment, We Need:

**Minimum Requirements:**
1. ✅ Choose 1-2 models to test (e.g., GPT-4o, Claude 3.5 Sonnet)
2. ✅ Set up API keys in `.env` file
3. ✅ Review/approve pilot dilemmas (5 dilemmas)
4. ✅ Confirm pilot configuration (10 runs, 2 temperatures)

**Optional But Recommended:**
5. ⚠️ Review dilemma wording for bias
6. ⚠️ Decide on system prompt framing
7. ⚠️ Set budget limits

**Can Decide Later:**
8. Full model selection for Phase I
9. Visualization preferences
10. Statistical test selection
11. Publication data format

---

## 9. Summary: Critical vs Can-Wait Decisions

### Critical (Needed to Start):
1. ✅ Model selection for pilot (at least 2 models)
2. ✅ API key configuration
3. ✅ Review pilot dilemmas
4. ⚠️ System prompt wording (currently minimal)

### Important (Needed for Phase I):
5. Full model selection
6. Dilemma refinement
7. Statistical test selection
8. Budget/rate limit configuration

### Can Wait (Nice to Have):
9. Visualization design
10. Reasoning framework coding
11. Advanced Phase II features
12. Publication data formats
13. Synthetic error injection

---

## Next Steps

I recommend we:

1. **Review the pilot configuration** (`config/experiment.yaml` - pilot section)
2. **Set up your API keys** (copy `.env.example` to `.env`)
3. **Review the 5 pilot dilemmas** in `data/dilemmas/dilemmas.json`
4. **Make a decision on system prompting** (see 3.2 above)
5. **Run a test with mock model** to validate the pipeline
6. **Run actual pilot** with 1-2 real models
7. **Review pilot results** and refine
8. **Plan Phase I** based on pilot learnings

**Questions for You:**
- Which models do you have API access to?
- What's your timeline for completing this research?
- What's your budget for API costs?
- Do you want to start with a mock test run first?
- Any specific concerns or priorities I should know about?
