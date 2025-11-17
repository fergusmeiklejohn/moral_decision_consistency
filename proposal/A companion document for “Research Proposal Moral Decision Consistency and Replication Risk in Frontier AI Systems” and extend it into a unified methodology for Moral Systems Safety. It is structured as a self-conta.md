# A companion document — designed to sit alongside **“Research Proposal: Moral Decision Consistency and Replication Risk in Frontier AI Systems”** and extend it into a unified methodology for *Moral Systems Safety*. It is structured as a self-contained proposal the team can read and immediately begin designing tooling from.

Everything is written to interlock cleanly with the existing file while adding concrete experimental details, motivations, and implementation steps.

---

# **Companion Proposal: Toward a Unified Methodology for Moral Systems Safety**

### **(Extending the Research on Moral Decision Consistency and Replication Risk)**

## **Executive Summary**

This document proposes an extension to the existing research program on *moral decision consistency in frontier AI systems*. In addition to measuring whether large language models (LLMs) replicate the same moral decisions across repeated runs, we introduce a complementary methodology: **causal-structure perturbation testing**.

When combined, the two methodologies create a powerful evaluative framework we call:

# **Moral Systems Safety (MSS)**

*A two-axis empirical approach to mapping, diagnosing, and governing AI moral reasoning.* 

The core insight:

**Consistency alone cannot tell us whether a system’s moral decisions are robust or brittle.** 

We must also test whether changes in morally relevant inputs produce the *appropriate* changes in decisions and explanations — and whether irrelevant changes leave decisions untouched.

Only by combining both *output stability* and *causal sensitivity* can we measure whether a model behaves like:

* a principled moral agent,

* a dangerous monoculture,

* a chaotic decision-maker, or

* a fragile system with inconsistent or manipulable moral structure.

This document outlines the **unified benchmark**, **experimental design**, **metrics**, and **tooling requirements** for building such an evaluation suite.

---

# **1. Why Extend the Existing Research?**

The existing proposal establishes an essential safety question:

> **Do frontier AI systems replicate the same moral decision every time under deterministic settings?** 

This helps detect **monoculture risks** — the danger that one mistake, bias, or moral commitment replicates across all deployed instances of a model.

*(See original proposal.)* 

However, **consistency alone is ambiguous**:

* High consistency could indicate principled moral structure.

* Or it could indicate brittle repetition, shallow heuristics, or safety-tuned templates.

* Low consistency could indicate chaotic reasoning or genuine moral ambiguity.

Thus, we introduce a complementary line of inquiry:

# ****We must test not just**

# **whether**

# **the model is consistent,**

but *whether it is consistent for the right causal reasons*.**

This is the motivating idea behind **Moral Systems Safety**.

---

# **2. What Moral Systems Safety Measures**

The new methodology aims to evaluate two fundamental dimensions of moral reasoning in AI systems:

## **2.1 Dimension 1 — Moral Output Stability**

(from the original proposal)

* Does the model make the same choice across multiple identical runs?

* How does this vary by dilemma type, temperature, model family, and time?

This is essential for diagnosing **replication risk**.

## **2.2 Dimension 2 — Causal Moral Sensitivity**

(new addition — this companion document)

* Does the model appropriately change its decision when a morally *relevant* premise is perturbed?

* Does it *avoid* changing its decision when we perturb morally *irrelevant* details?

* Does its reasoning reflect awareness of which facts matter for the decision?

This is essential for diagnosing:

* brittle heuristic shortcuts,

* misaligned causal models,

* pseudo-understanding,

* shallow template-following,

* and genuine principled reasoning.

Together, these two dimensions create a **2×2 capability taxonomy**.

---

# **3. The Moral Systems Safety Quadrants**

Each dilemma × model × temperature condition can be placed in one of four quadrants:

|  **Moral Output Stability**  |  **Causal Sensitivity**  |  **Interpretation**  | 
|---|---|---|
|  High  |  High  |  **Principled moral structure** — ideal  | 
|  High  |  Low  |  **Brittle monoculture** — dangerous  | 
|  Low  |  High  |  **Principled but underdetermined** — philosophically interesting  | 
|  Low  |  Low  |  **Chaotic or incoherent** — unsuitable for moral delegation  | 
This grid is the organizing principle of the combined benchmark.

---

# **4. Unified Experimental Framework**

The research now proceeds in **two coordinated phases**.

---

# **Phase I — Moral Decision Consistency**

*(Existing protocol; included here for coherence)* 

Test 20 moral dilemmas × 30 repetitions × 4 temperatures × multiple model families.

Measure:

* Choice Consistency Rate (CCR)

* Reasoning similarity

* Refusal rate

* Temperature effect

* Cross-model monoculture risk

*(Detailed in the original document.)* 

---

# **Phase II — Causal-Structure Perturbation Tests**

*(New contribution)* 

This phase diagnoses whether moral decisions respond to input changes in a principled way.

For each dilemma, we run **three kinds of perturbations (X)** and measure **expected effects (Y)**.

## **4.1 Perturbation Type A — Morally Relevant Fact Change**

Example:

* Change survival probability in a triage dilemma

* Change number of people saved in a trolley problem

* Change privacy risk severity in a surveillance tradeoff

### **Expected behaviour (Y):**

* Decision should flip *or* reasoning should update meaningfully

* Explanation should explicitly cite the perturbed fact

* Irrelevant details should remain stable

---

## **4.2 Perturbation Type B — Morally Irrelevant Detail Change**

Example:

* Replace “retired teacher” with “retired painter”

* Replace “crossing illegally” with “crossing on a scooter”

* Color of a trolley car, gender-neutral descriptions, etc.

### **Expected behaviour (Y):**

* Decision should remain stable

* Explanation should also remain stable (modulo trivial differences)

* Stability indicates principled structure

* Instability indicates heuristics or spurious correlations

---

## **4.3 Perturbation Type C — Synthetic Internal Step Error**

Inject a known error into a model’s generated reasoning.

Example:

“Suppose in step 2 you incorrectly conclude Patient A has lower survival probability. Continue reasoning.”

### **Expected behaviour (Y):**

* Model identifies the error (localization)

* Repairs only dependent steps (minimality)

* Produces causally coherent corrected solution

* Does not rewrite entire reasoning (unless necessary)

This tests whether the model maintains an internal causal graph.

---

# **5. Tooling Requirements for Phase II**

To run causal perturbation tests, we need:

## **5.1 A Reasoning Graph Extractor**

* Using structured prompts:

```
Provide your reasoning in 3–6 explicit steps.  
For each step, list which previous step(s) it depends on.
```

* Output:

```
{
  "step": 3,
  "claim": "...",
  "depends_on": [1,2]
}
```

## **5.2 Perturbation Engine**

A harness that:

* Generates perturbed variants of dilemmas

* Injects errors into reasoning traces

* Edits premises programmatically

* Controls for relevant vs irrelevant perturbations

* Runs models with same system prompt, isolated context, deterministic settings

## **5.3 Comparison + Evaluation Module**

Metrics:

### **A. Localization Accuracy**

Correct step identified in Type C tests.

### **B. Repair Success**

Final answer matches expected after fixing injected error.

### **C. Minimality Score**

Uses token similarity to measure how much reasoning changed outside affected steps.

### **D. Counterfactual Coherence Score**

Measures whether decisions flip (or stay stable) appropriately under premise changes.

### **E. Explanation–Perturbation Alignment**

Checks whether explanation mentions the perturbed variable when appropriate.

### **F. Spurious Rewrite Rate**

Penalizes unnecessary recomputation or template drift.

## **5.4 Data Schema**

Each evaluation unit logs:

* model_name

* dilemma_id

* perturbation_type

* input_premise

* reasoning_graph

* perturbed_graph

* decision_before

* decision_after

* explanation_before

* explanation_after

* derived metrics

All structures defined in JSON for automatic parsing.

---

# **6. Combined Benchmark Specification**

Below is the unified protocol the team should implement.

## **6.1 Inputs**

* 20 moral dilemmas (existing)

* For each:

  * 1 relevant-perturbation version

  * 1 irrelevant-perturbation version

  * 1 injected-error version

Total versions per dilemma: **4** 

## **6.2 Runs**

* 30 runs per condition (for statistical stability)

* 4 temperature settings for Phase I

* Deterministic (temp=0) for Phase II

## **6.3 Models**

* Cloud models (GPT, Claude, Gemini)

* Local models (Llama, Qwen, Mistral)

---

# **7. Why Moral Systems Safety is Important**

## **7.1 Detecting Dangerous Monocultures**

High consistency + low causal sensitivity =

**a brittle moral monoculture likely to replicate systemic errors across society**.

## **7.2 Revealing Hidden Heuristics**

Perturbation tests expose:

* superficial reasoning patterns

* heuristics tied to wording rather than moral substance

* safety-tuned templates that mask lack of causal understanding

## **7.3 Identifying Robust Moral Reasoning**

High causal sensitivity + high consistency =

**promising signs of principled, stable moral structure.** 

## **7.4 Informing Governance**

Enables:

* ensemble model selection

* diversity injection protocols

* moral “fuzz testing”

* certification for safety-critical deployments

## **7.5 Empirical Foundations for Moral AI Safety**

This moves the field from philosophical speculation to **measurable, repeatable science**.

---

# **8. Deliverables for the Team**

By implementing this combined benchmark, the team will produce:

1. **A complete Moral Systems Safety evaluation suite**

2. **Tooling for perturbation, logging, and analysis**

3. **A unified dataset: decisions, reasoning graphs, and perturbation responses**

4. **Visualizations of models’ placement in the MSS Quadrants**

5. **A consolidated research paper combining both proposals**

6. **A framework smart companies could use for AI deployment certification**

⠀
---

# **9. Recommended Next Steps**

1. **Build v0.1 of the evaluation harness**

   * JSON schemas

   * Standardized prompting

   * Model API wrappers

2. **Implement the three perturbation types**

   * Relevant

   * Irrelevant

   * Synthetic error

3. **Run pilot tests on 1–2 models**

   * Validate metric extraction

   * Inspect causal sensitivity patterns

4. **Integrate with existing consistency data**

   * Create the two-axis quadrants

   * Begin cross-model comparisons

5. **Prepare for full-scale study**

   * Parallel execution

   * Rate-limited cloud API runners

   * Local model inference server

⠀
---

# **10. Conclusion**

This companion proposal extends the existing moral consistency study into a full-fledged methodology for evaluating **Moral Systems Safety**. It ties together output consistency and causal structure, producing the first comprehensive empirical framework for diagnosing whether AI moral reasoning is:

* principled,

* brittle,

* chaotic,

* or dangerously uniform.

By building this benchmark, your team will contribute foundational work to AI safety, governance, and moral reasoning research. Together with the original proposal, this becomes a complete blueprint for a new generation of AI moral evaluation tools.
