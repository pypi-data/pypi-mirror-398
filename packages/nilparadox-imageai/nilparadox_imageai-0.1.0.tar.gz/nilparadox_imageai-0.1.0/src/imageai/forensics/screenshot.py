from __future__ import annotations

import numpy as np
from imageai.core.evidence import Evidence


def screenshot_evidence(img: np.ndarray) -> Evidence:
    """
    Detect screenshot-like images using edge physics and color statistics.
    Works for PNG, JPEG, HEIC.
    """

    # Convert to grayscale proxy
    if img.ndim == 3:
        gray = img.mean(axis=2)
        rgb_std = img.std(axis=(0, 1))
        color_ratio = float(rgb_std.max() / (rgb_std.min() + 1e-6))
    else:
        gray = img
        color_ratio = 1.0

    # Edge sharpness (screenshots have extreme step edges)
    gx = np.abs(np.diff(gray, axis=1))
    gy = np.abs(np.diff(gray, axis=0))

    edge_energy = float(np.percentile(gx, 99.5) + np.percentile(gy, 99.5))

    # Noise absence proxy
    noise_floor = float(np.percentile(gray, 5) - np.percentile(gray, 1))
    noise_floor = abs(noise_floor)

    # Score composition (physics-inspired)
    score = 0.0
    score += 0.5 * min(1.0, edge_energy * 10.0)
    score += 0.3 * min(1.0, color_ratio / 3.0)
    score += 0.2 * max(0.0, 1.0 - noise_floor * 200.0)

    score = float(min(1.0, score))
    reliability = 0.6 if img.size > 256 * 256 else 0.3

    supports = {"screenshot"} if score > 0.65 else set()

    return Evidence(
        score=score,
        reliability=reliability,
        supports=supports,
    )
