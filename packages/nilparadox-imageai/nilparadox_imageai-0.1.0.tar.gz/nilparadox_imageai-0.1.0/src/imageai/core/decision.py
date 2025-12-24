from __future__ import annotations

from collections import defaultdict
from imageai.core.evidence import Evidence


HYPOTHESES = [
    "camera_native",
    "camera_computational",
    "externally_generated",
    "screenshot",
    "resampled",
]


def fuse_evidence(evidences: list[Evidence]) -> dict:
    """
    Proper evidence competition with safeguards:

    - No single module can assert externally_generated
    - External generation requires >=2 independent supports
    - Confidence is normalized by total evidence mass
    """

    capital = defaultdict(float)
    support_counts = defaultdict(int)

    for ev in evidences:
        for h in ev.supports:
            capital[h] += ev.score * ev.reliability
            support_counts[h] += 1

    # Remove weak single-support external accusation
    if support_counts["externally_generated"] < 2:
        capital.pop("externally_generated", None)

    total_capital = sum(capital.values())

    # No strong evidence → camera native by default
    if total_capital <= 1e-6:
        return {
            "primary": "camera_native",
            "confidence": 0.5,
        }

    # Pick max capital
    primary = max(capital, key=capital.get)
    confidence = min(0.95, capital[primary] / total_capital)

    return {
        "primary": primary,
        "confidence": confidence,
    }
