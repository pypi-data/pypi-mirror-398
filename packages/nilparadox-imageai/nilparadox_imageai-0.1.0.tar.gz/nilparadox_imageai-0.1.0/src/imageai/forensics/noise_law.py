from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Tuple

import numpy as np

from imageai.core.patches import extract_homogeneous_patches
from imageai.core.evidence import Evidence


@dataclass(frozen=True)
class NoiseLawResult:
    inconsistency: float
    reliability: float


def estimate_noise_law(
    img: np.ndarray,
    patch_size: int = 32,
    stride: int = 16,
) -> NoiseLawResult:

    patches = extract_homogeneous_patches(img, patch_size, stride)

    if len(patches) < 40:
        return NoiseLawResult(0.0, 0.0)

    means = np.array([p.mean for p in patches])
    vars_ = np.array([p.var for p in patches])

    coef = np.polyfit(means, vars_, 1)
    pred = coef[0] * means + coef[1]

    rmse = float(np.sqrt(np.mean((vars_ - pred) ** 2)))
    scale = float(np.mean(vars_) + 1e-12)

    inconsistency = rmse / scale
    reliability = min(1.0, len(patches) / 400.0)

    return NoiseLawResult(inconsistency, reliability)


def noise_law_evidence(res: NoiseLawResult) -> Evidence:
    if res.reliability < 0.3:
        return Evidence(0.0, 0.0, set())

    score = min(1.0, res.inconsistency * 1.6)

    supports = set()
    if score > 0.25:
        supports.add("camera_computational")
    if score > 0.7:
        supports.add("externally_generated")

    return Evidence(score, res.reliability, supports)
