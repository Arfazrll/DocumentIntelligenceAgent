"""
DocIntel AI — Confidence Scoring.

Composite confidence score using weighted geometric mean.
"""

import math
import logging
from typing import Literal

from app.config import settings
from app.schemas.query import ConfidenceScore

logger = logging.getLogger(__name__)

def compute_confidence(
    retrieval_score: float,
    groundedness_score: float,
    llm_confidence: float = 0.8,
    citation_coverage: float = 1.0,
) -> ConfidenceScore:
    """
    Compute composite confidence score.

    Formula: Weighted geometric mean (penalizes low value in any dimension)
    Weights: retrieval(0.25) × groundedness(0.35) × llm_confidence(0.15) × citation_coverage(0.25)
    """
    weights = [0.25, 0.35, 0.15, 0.25]
    scores = [
        max(retrieval_score, 0.01),
        max(groundedness_score, 0.01),
        max(llm_confidence, 0.01),
        max(citation_coverage, 0.01),
    ]

    log_sum = sum(w * math.log(s) for w, s in zip(weights, scores))
    composite = math.exp(log_sum)

    # Clamp to [0, 1]
    composite = max(0.0, min(1.0, composite))

    # Determine level
    level: Literal["high", "medium", "low"]
    if composite > 0.85:
        level = "high"
    elif composite >= 0.65:
        level = "medium"
    else:
        level = "low"

    return ConfidenceScore(
        score=round(composite, 4),
        level=level,
        retrieval_score=round(retrieval_score, 4),
        groundedness_score=round(groundedness_score, 4),
        llm_confidence=round(llm_confidence, 4),
        citation_coverage=round(citation_coverage, 4),
    )

def should_refuse(confidence: ConfidenceScore) -> bool:
    """Determine if the system should refuse to answer based on confidence."""
    return confidence.score < settings.CONFIDENCE_THRESHOLD
