"""guardrails/confidence.py — Retrieval confidence scoring and refusal logic."""
from typing import Tuple
from config import CONFIDENCE_THRESHOLD


def compute_confidence(scores: list) -> Tuple[float, str]:
    """
    Compute confidence from a list of cosine similarity scores.

    Returns (confidence_score, label) where label is one of:
    'high', 'medium', 'low', 'insufficient'
    """
    if not scores:
        return 0.0, "insufficient"

    best_score = max(scores)

    if best_score >= 0.70:
        label = "high"
    elif best_score >= 0.50:
        label = "medium"
    elif best_score >= CONFIDENCE_THRESHOLD:
        label = "low"
    else:
        label = "insufficient"

    return round(best_score, 4), label


def should_refuse(confidence: float) -> bool:
    """Return True if confidence is below the threshold — triggers refusal."""
    return confidence < CONFIDENCE_THRESHOLD
