"""
Confidence computation for Senpai.

Host-controlled EWMA-based confidence scoring.
"""

from __future__ import annotations

from typing import Literal


def compute_ewma(scores: list[float], decay: float = 0.9) -> float:
    """Compute exponentially weighted moving average.

    Args:
        scores: List of scores (newest first), each 0.0-1.0
        decay: Decay factor (default 0.9)

    Returns:
        EWMA score 0.0-1.0, or 0.5 if no scores
    """
    if not scores:
        return 0.5

    weighted_sum = 0.0
    weight_sum = 0.0

    for i, score in enumerate(scores):
        weight = decay**i
        weighted_sum += weight * score
        weight_sum += weight

    return weighted_sum / weight_sum if weight_sum > 0 else 0.5


def status_to_score(status: str) -> float | None:
    """Convert attempt status to numeric score.

    Args:
        status: One of "passed", "failed", "partial", "aborted"

    Returns:
        Score (0.0-1.0) or None if status should be ignored
    """
    mapping = {
        "passed": 1.0,
        "partial": 0.5,
        "failed": 0.0,
        "aborted": None,  # Ignored
    }
    return mapping.get(status)


def compute_confidence(
    maturity: Literal["nudge", "approach", "skill"],
    attempt_statuses: list[str],
    decay: float = 0.9,
) -> float:
    """Compute confidence score for a procedure.

    Uses EWMA of attempt outcomes, mapped to maturity-specific ranges:
    - Nudge: 0.30 + 0.20 * ewma (range 0.30-0.50)
    - Approach: 0.50 + 0.30 * ewma (range 0.50-0.80)
    - Skill: 0.80 + 0.15 * ewma (range 0.80-0.95)

    Args:
        maturity: Procedure maturity level
        attempt_statuses: List of status strings (newest first)
        decay: EWMA decay factor (default 0.9)

    Returns:
        Confidence score 0.0-1.0
    """
    # Convert statuses to scores (filter out aborted)
    scores = [
        s for status in attempt_statuses if (s := status_to_score(status)) is not None
    ]

    ewma = compute_ewma(scores, decay)

    # Map to maturity-specific range
    ranges = {
        "nudge": (0.30, 0.20),  # 0.30 + 0.20 * ewma
        "approach": (0.50, 0.30),  # 0.50 + 0.30 * ewma
        "skill": (0.80, 0.15),  # 0.80 + 0.15 * ewma
    }

    base, scale = ranges[maturity]
    return base + scale * ewma
