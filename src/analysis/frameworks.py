"""
Heuristic moral framework classifier.

Assigns a coarse moral framework label to a reasoning string using simple
keyword-based signals. Designed to be cheap and offline so we can label
pilot data without extra API calls. Higher-fidelity labeling (LLM/judge or
embeddings) can be added later.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple


class FrameworkLabel(str, Enum):
    """Supported moral framework labels."""

    UTILITARIAN = "utilitarian"
    DEONTOLOGICAL = "deontological"
    VIRTUE = "virtue"
    CARE = "care"
    LEGAL = "legal"
    PRECAUTIONARY = "precautionary"
    FAIRNESS = "fairness"
    REFUSAL = "refusal_or_policy"
    OTHER = "other"


@dataclass
class FrameworkClassification:
    """Classification result for a single reasoning string."""

    label: FrameworkLabel
    confidence: float
    method: str
    matched_keywords: List[str]

    def to_dict(self) -> Dict:
        """Convert to a serializable dictionary."""
        return {
            "label": self.label.value,
            "confidence": self.confidence,
            "method": self.method,
            "matched_keywords": self.matched_keywords,
        }


class FrameworkClassifier:
    """
    Rule-based classifier for moral frameworks.

    Uses keyword hits to assign a label. For speed and transparency this
    deliberately avoids external dependencies.
    """

    def __init__(self):
        # Priority order resolves ties
        self.priority_order = [
            FrameworkLabel.UTILITARIAN,
            FrameworkLabel.DEONTOLOGICAL,
            FrameworkLabel.FAIRNESS,
            FrameworkLabel.LEGAL,
            FrameworkLabel.PRECAUTIONARY,
            FrameworkLabel.CARE,
            FrameworkLabel.VIRTUE,
            FrameworkLabel.REFUSAL,
            FrameworkLabel.OTHER,
        ]

        self.keyword_map: Dict[FrameworkLabel, List[str]] = {
            FrameworkLabel.UTILITARIAN: [
                "greater good",
                "maximize",
                "minimize harm",
                "overall harm",
                "net benefit",
                "consequence",
                "outcome",
                "more lives",
                "save the most",
                "balance of harms",
            ],
            FrameworkLabel.DEONTOLOGICAL: [
                "duty",
                "obligation",
                "rights",
                "principle",
                "rule",
                "rule-based",
                "intrinsic",
                "wrong regardless",
                "respect autonomy",
                "consent",
            ],
            FrameworkLabel.VIRTUE: [
                "virtue",
                "character",
                "integrity",
                "honesty",
                "compassionate",
                "courage",
                "moral character",
            ],
            FrameworkLabel.CARE: [
                "empathy",
                "compassion",
                "vulnerable",
                "care",
                "relationship",
                "support",
                "harm to vulnerable",
            ],
            FrameworkLabel.LEGAL: [
                "lawful",
                "legal",
                "illegal",
                "policy",
                "regulation",
                "compliance",
                "precedent",
            ],
            FrameworkLabel.PRECAUTIONARY: [
                "precaution",
                "uncertain",
                "risk",
                "safety",
                "potential harm",
                "minimize risk",
                "avoid risk",
            ],
            FrameworkLabel.FAIRNESS: [
                "fair",
                "fairness",
                "equal",
                "equitable",
                "impartial",
                "discrimination",
                "bias",
            ],
            FrameworkLabel.REFUSAL: [
                "cannot comply",
                "refuse",
                "decline",
                "safety policy",
                "inappropriate",
                "ethical guidelines",
            ],
            FrameworkLabel.OTHER: [],
        }

    def classify_reasoning(self, reasoning: str) -> FrameworkClassification:
        """
        Classify a reasoning string.

        Returns:
            FrameworkClassification with label, confidence, method, matched keywords.
        """
        if not reasoning:
            return FrameworkClassification(
                label=FrameworkLabel.OTHER,
                confidence=0.0,
                method="heuristic",
                matched_keywords=[],
            )

        text = reasoning.lower()
        scores: Dict[FrameworkLabel, int] = {label: 0 for label in self.priority_order}
        matched: Dict[FrameworkLabel, List[str]] = {label: [] for label in self.priority_order}

        for label, keywords in self.keyword_map.items():
            for kw in keywords:
                if kw in text:
                    scores[label] += 1
                    matched[label].append(kw)

        # Pick highest score, resolving ties by priority_order
        best_label = FrameworkLabel.OTHER
        best_score = -1
        for label in self.priority_order:
            if scores[label] > best_score:
                best_label = label
                best_score = scores[label]

        hits = best_score if best_score > 0 else 0
        confidence = self._confidence_from_hits(hits)

        return FrameworkClassification(
            label=best_label,
            confidence=confidence,
            method="heuristic",
            matched_keywords=matched[best_label],
        )

    @staticmethod
    def _confidence_from_hits(hits: int) -> float:
        """Map keyword hit count to a coarse confidence score."""
        if hits >= 3:
            return 0.9
        if hits == 2:
            return 0.7
        if hits == 1:
            return 0.5
        return 0.2


class EmbeddingFrameworkClassifier:
    """
    Embedding-based classifier for moral frameworks.

    Uses sentence embeddings to compare the reasoning text to label prototypes.
    Falls back to a low-confidence OTHER label if embeddings are unavailable.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._prototype_embeddings = None
        self.prototype_texts: Dict[FrameworkLabel, List[str]] = {
            FrameworkLabel.UTILITARIAN: [
                "Choose the option that maximizes total good and minimizes overall harm.",
                "Decide based on the consequences and saving the most lives.",
            ],
            FrameworkLabel.DEONTOLOGICAL: [
                "Follow duties, rules, and rights even if outcomes are worse.",
                "Respect obligations and moral principles regardless of consequences.",
            ],
            FrameworkLabel.VIRTUE: [
                "Act according to moral character and virtues like honesty and courage.",
                "Choose the option that reflects good character and integrity.",
            ],
            FrameworkLabel.CARE: [
                "Emphasize empathy, relationships, and protection of the vulnerable.",
                "Prioritize care and compassion in interpersonal context.",
            ],
            FrameworkLabel.LEGAL: [
                "Follow law, regulation, or institutional policy.",
                "Comply with legal requirements and established rules.",
            ],
            FrameworkLabel.PRECAUTIONARY: [
                "Avoid uncertain risks and potential harms; choose the safer option.",
                "Be cautious under uncertainty and minimize risk.",
            ],
            FrameworkLabel.FAIRNESS: [
                "Ensure fairness, equality, and impartial treatment; avoid bias.",
                "Distribute outcomes fairly and respect equal claims.",
            ],
            FrameworkLabel.REFUSAL: [
                "Decline to answer due to safety or ethical policy constraints.",
                "Refuse to comply because of ethical guidelines.",
            ],
            FrameworkLabel.OTHER: [
                "Reasoning that does not match a known moral framework.",
            ],
        }

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _ensure_prototype_embeddings(self):
        if self._prototype_embeddings is not None:
            return self._prototype_embeddings

        model = self._load_model()
        if model is None:
            return None

        embeddings = {}
        for label, texts in self.prototype_texts.items():
            vecs = model.encode(texts)
            # Average multiple prototypes per label
            embeddings[label] = sum(vecs) / len(vecs)
        self._prototype_embeddings = embeddings
        return embeddings

    def classify_reasoning(self, reasoning: str) -> FrameworkClassification:
        if not reasoning:
            return FrameworkClassification(
                label=FrameworkLabel.OTHER,
                confidence=0.0,
                method="embedding_unavailable",
                matched_keywords=[],
            )

        model = self._load_model()
        proto = self._ensure_prototype_embeddings()
        if model is None or proto is None:
            raise RuntimeError("Embedding model not available.")

        import numpy as np

        reasoning_vec = model.encode([reasoning])[0]

        # Normalize
        def _norm(v):
            n = np.linalg.norm(v)
            return v / n if n > 0 else v

        reasoning_vec = _norm(reasoning_vec)
        best_label = FrameworkLabel.OTHER
        best_score = -1.0

        for label, vec in proto.items():
            score = float(np.dot(reasoning_vec, _norm(vec)))
            if score > best_score:
                best_score = score
                best_label = label

        confidence = self._confidence_from_score(best_score)

        return FrameworkClassification(
            label=best_label,
            confidence=confidence,
            method="embedding",
            matched_keywords=[],
        )

    @staticmethod
    def _confidence_from_score(score: float) -> float:
        """
        Map cosine similarity to a coarse confidence.
        Typical sentence-transformer sims: 0.3-0.8 for related text.
        """
        if score >= 0.65:
            return 0.9
        if score >= 0.55:
            return 0.75
        if score >= 0.45:
            return 0.6
        if score >= 0.35:
            return 0.45
        return 0.3


class LLMFrameworkClassifier:
    """
    LLM-based classifier stub.

    Expects a callable `llm_fn(reasoning: str) -> str` that returns a label
    string matching FrameworkLabel values. Left extensible for environments
    where an LLM judge is available.
    """

    def __init__(self, llm_fn):
        if llm_fn is None:
            raise ValueError("llm_fn is required for LLMFrameworkClassifier.")
        self.llm_fn = llm_fn

    def classify_reasoning(self, reasoning: str) -> FrameworkClassification:
        try:
            raw = self.llm_fn(reasoning)
        except Exception:
            return FrameworkClassification(
                label=FrameworkLabel.OTHER,
                confidence=0.0,
                method="llm_error",
                matched_keywords=[],
            )

        label = self._normalize_label(raw)
        confidence = 0.8 if label != FrameworkLabel.OTHER else 0.4

        return FrameworkClassification(
            label=label,
            confidence=confidence,
            method="llm",
            matched_keywords=[],
        )

    @staticmethod
    def _normalize_label(raw: str) -> FrameworkLabel:
        text = (raw or "").strip().lower()
        for lbl in FrameworkLabel:
            if lbl.value in text:
                return lbl
        return FrameworkLabel.OTHER
