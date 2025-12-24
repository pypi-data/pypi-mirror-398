from __future__ import annotations

import numpy as np
from scipy.fft import fft2, fftshift
from imageai.core.evidence import Evidence


def spectral_evidence(img: np.ndarray) -> Evidence:
    """
    Detect spectral anomalies caused by AI sharpening / super-resolution.
    """

    if img.ndim == 3:
        gray = img.mean(axis=2)
    else:
        gray = img

    # Window to reduce boundary artifacts
    win = np.outer(np.hanning(gray.shape[0]), np.hanning(gray.shape[1]))
    gray_w = gray * win

    spec = np.abs(fftshift(fft2(gray_w)))
    spec /= spec.max() + 1e-12

    h, w = spec.shape
    cy, cx = h // 2, w // 2

    # Radial bands
    low = spec[cy-10:cy+10, cx-10:cx+10].mean()
    mid = spec[cy-60:cy+60, cx-60:cx+60].mean()
    high = np.mean(spec) - mid

    # AI sharpening often boosts mid/high disproportionately
    ratio = float((mid + high) / (low + 1e-6))

    score = max(0.0, min(1.0, (ratio - 2.5) / 3.5))
    reliability = 0.7 if gray.size > 512 * 512 else 0.4

    supports = set()
    if score > 0.35:
        supports.add("camera_enhanced")
    if score > 0.6:
        supports.add("ai_generated")

    return Evidence(
        score=score,
        reliability=reliability,
        supports=supports,
    )
