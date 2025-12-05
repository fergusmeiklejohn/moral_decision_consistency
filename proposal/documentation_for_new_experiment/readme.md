#The problem with version 1 of this experiment and why I'm changing it

From early runs on a local gpt-oss model I've found that the model is surprisingly good at the current experiment, seeming in every case where it doesn't refuse to answer to be reasoning from moral principles. It may of course be doing so but it does strike me as at least possible that the model is pattern matching rather than truly reasoning. Pattern matching is possible because the experiment is testing knowledge of classic moral dilemmas which are well-known and widely discussed.

- Canonical examples: The trolley problems (classic, footbridge, loop, fat man) are the most-discussed thought experiments in moral philosophy for 50+ years. Anyone who's taken an intro ethics course, read a philosophy blog, or seen "The Good Place" knows these. The models are therefore sure to have seen them in training data and in RLHF alignment and safety training.
- Predictable structure: Each dilemma follows the familiar template: binary forced choice, quantified stakes, clear tradeoff framing. This is how ethics textbooks present dilemmas.
- Well-mapped moral terrain: The tensions we're testing (consequentialism vs. deontology, doing vs. allowing, using vs. involving) are the standard curriculum of ethical reasoning.
- AV dilemmas inherit the structure: The Moral Machine project (MIT) made these exact tradeoffs famous and our scenarios echo their methodology directly.
- Privacy/security dilemmas are policy-debate staples: Encryption backdoors, mass surveillance, medical privacy during pandemics—these are op-ed topics, not novel moral territory.

##What this means for testing moral reasoning?
A well-educated moral agent doesn't need to reason through these—they can pattern-match. They might think:

- "Oh, this is a trolley problem → I know the utilitarian answer is pull, the deontologist answer is don't"
- "This is the footbridge variant → I know most people have stronger intuitions against pushing"
- "This tests doing/allowing → I know the double effect doctrine"

The perturbation system works, it tests consistency and sensitivity to the right features. But it may still be testing "do you know which knobs to turn" rather than "can you reason about a genuinely novel moral situation."


##What we are changing in version 2
To address this, I'm changing the experiment to use novel dilemmas that don't follow the classic templates. These dilemmas are designed to be both diverse and more likely to be out of distribution for current models or humans. The goal is to force the moral decision maker to reason from first principles rather than relying on memorized patterns. The experiment thus is much more likely to test genuine moral reasoning ability rather than recall of known dilemmas.

The new experiment is laid out in detail here: proposal/development_to_new_experiment/moral_reasoning_protocol.docx

The new dilemmas are in: proposal/development_to_new_experiment/ood_dilemmas.json
