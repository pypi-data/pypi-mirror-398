from __future__ import annotations

import numpy as np
from imageai.core.evidence import Evidence


def cfa_consistency_evidence(img: np.ndarray) -> Evidence:
    """
    CFA / demosaic consistency detector.

    IMPORTANT:
    - Strong CFA evidence supports camera origin.
    - Weak or absent CFA evidence is AMBIGUOUS and supports NOTHING.
    - This module NEVER asserts external generation.
    """

    if img.ndim != 3 or img.shape[2] != 3:
        return Evidence(0.0, 0.0, set())

    R, G, B = img[..., 0], img[..., 1], img[..., 2]

    # Channel difference statistics
    rg = np.abs(R - G)
    gb = np.abs(G - B)

    # Periodic sampling proxy (very weak but real in cameras)
    rg_even = rg[::2, ::2].mean()
    rg_odd = rg[1::2, 1::2].mean()

    periodicity = abs(rg_even - rg_odd)

    # Camera images retain small but non-zero periodicity
    score = float(min(1.0, periodicity * 40.0))
    reliability = 0.7 if img.size > 512 * 512 else 0.4

    supports = set()
    if score > 0.3:
        supports.add("camera_computational")

    return Evidence(
        score=score,
        reliability=reliability,
        supports=supports,
    )
