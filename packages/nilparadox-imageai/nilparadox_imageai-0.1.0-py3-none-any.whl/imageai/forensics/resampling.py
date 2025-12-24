from __future__ import annotations
import numpy as np
from scipy.fft import fft2, fftshift
from imageai.core.evidence import Evidence

def resampling_evidence(img: np.ndarray) -> Evidence:
    if img.ndim == 3:
        img = img.mean(axis=2)

    lap = (
        -4 * img
        + np.roll(img, 1, 0)
        + np.roll(img, -1, 0)
        + np.roll(img, 1, 1)
        + np.roll(img, -1, 1)
    )

    spec = np.abs(fftshift(fft2(lap)))
    spec /= spec.max() + 1e-12

    mid = spec.shape[0] // 2
    ring = spec[mid-20:mid+20, mid-20:mid+20]
    peak_ratio = float(np.percentile(ring, 99) / (np.mean(ring) + 1e-12))

    score = max(0.0, min(1.0, (peak_ratio - 6.0) / 6.0))
    reliability = 0.7 if img.size > 512*512 else 0.4

    supports = {"resampled"} if score > 0.35 else set()
    return Evidence(score, reliability, supports)
