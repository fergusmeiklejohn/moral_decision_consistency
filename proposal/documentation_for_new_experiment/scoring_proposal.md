# Scoring Proposal for New Experiment: Heuristic vs. LLM-Judge Approaches

## The Case for Starting with Heuristic Scoring Only

**Speed and interpretability**: You can see exactly why a score was assigned. When debugging or validating, you're not stacking one black box on top of another.

**Baseline establishment**: Heuristic scoring gives you a floor. You'll know what cheap, fast, transparent scoring can achieve before investing in more complex approaches.

**Avoiding circular contamination**: If you're testing whether LLMs reason from principles vs. pattern-match, using an LLM judge introduces a risk—the judge might reward responses that *sound like* good reasoning (because they match patterns in training data) rather than responses that *are* good reasoning. You'd be measuring "does this response match what LLMs think good reasoning looks like" rather than "is this good reasoning."

## The Case for LLM-Judge from the Start

**Your dimensions resist heuristics**: Consider what you're scoring:

| Dimension | Heuristic Feasibility |
|-----------|----------------------|
| Principle Articulation | Moderate—you can detect explicit principle statements, but distinguishing "precise with scope conditions" (5) from "clear but loose fit" (3) requires semantic understanding |
| Consistency | Very hard—requires comparing responses across dilemmas, detecting structural similarity, evaluating whether stated differences are principled or post-hoc |
| Perspectival Range | Hard—distinguishing steelmanning from strawmanning requires understanding argument quality |
| Meta-Awareness | Moderate—you can detect framework terms, but evaluating whether they're correctly applied requires understanding |

Heuristics would likely collapse to surface features: "Did they use the word 'principle'? Did they mention multiple frameworks? Did they use hedging language?" These are gameable and don't capture what you actually care about.

**You're already using novel dilemmas to avoid pattern-matching**: The whole point of your OOD design is that agents can't rely on cached answers. An LLM judge evaluating reasoning *quality* is a different task than an LLM generating *answers*—the contamination risk is lower than it might seem.

## My Recommendation: Hybrid from the Start, but Structured Carefully

Build both, but use them differently:

**Heuristic layer (automated, fast, every response)**:
- Structural checks: Did they answer the question? Did they engage with the probes?
- Surface features: Response length, presence of explicit principle statements, acknowledgment of uncertainty, mention of stakeholders
- Red flag detection: Refusal to engage, pattern-matching phrases ("this is like the trolley problem"), premature closure

This layer doesn't *score*—it *screens and annotates*. It tells you "this response has features X, Y, Z" without claiming to evaluate quality.

**LLM-judge layer (more expensive, used strategically)**:
- Runs on responses that pass heuristic screening
- Uses a carefully constructed rubric prompt that operationalizes your 1-5 scales
- Critically: **generates reasoning before scores**—the judge must explain *why* it's assigning each score, and those explanations become auditable artifacts
- Even more critically: **use a different model family than your test subjects** if possible, to reduce correlated biases

**Human calibration layer (expensive, periodic)**:
- Expert raters score a sample of responses
- Compare against LLM-judge scores to measure agreement and identify systematic biases
- Use disagreements to refine the LLM-judge prompt

## A Concrete Implementation Suggestion

```
Response comes in
       │
       ▼
┌─────────────────────┐
│  Heuristic Screen   │ ──→ Annotations: {engaged: true, 
│  (fast, every run)  │      explicit_principles: true,
└─────────────────────┘      red_flags: [], ...}
       │
       ▼
┌─────────────────────┐
│   LLM Judge         │ ──→ Per-dimension scores + reasoning
│   (with rubric)     │      {principle_articulation: 4,
└─────────────────────┘       reasoning: "Agent stated X 
       │                      principle and connected it to
       ▼                      Y feature of case, but did
┌─────────────────────┐       not acknowledge competing
│  Store Everything   │       considerations..."}
└─────────────────────┘
       │
       ▼ (periodically)
┌─────────────────────┐
│  Human Calibration  │ ──→ Disagreement analysis
└─────────────────────┘      Rubric refinement
```

## Why Not Heuristics Alone

The honest answer: your dimensions are too semantic. "Steelmans opposing view" vs. "accurately describes but doesn't engage strongest form" is not a keyword distinction. You'd end up with a heuristic system that's either:
- So loose it can't discriminate (assigns similar scores to very different responses)
- So brittle it's easily gamed (agents learn to include magic phrases)

Neither serves your goal of understanding *how* agents reason.

## The Contamination Risk, Addressed

Your worry about LLM judges might be: "If I use an LLM to judge LLM responses, I'm just measuring LLM-to-LLM agreement, not actual reasoning quality."

This is a real concern, but it's mitigated by:

1. **Your dilemmas are novel**—the judge can't rely on cached "correct answers"
2. **You're scoring process, not conclusions**—you're not asking "did they get it right" but "did they reason well," which is more about structural features of the response
3. **The judge explains its scores**—you can audit whether the judge's reasoning is sensible
4. **Human calibration catches systematic bias**—if the LLM judge consistently over-rewards certain patterns, you'll see it in disagreement analysis
5. **Cross-family judging helps**—using Claude to judge GPT responses (or vice versa) reduces correlated training artifacts

---

# Appendix: Scoring Judge System and Prompt
 `proposal/documentation_for_new_experiment/Scoring/judge_prompt.md`
 `proposal/documentation_for_new_experiment/Scoring/judge_system.json`
