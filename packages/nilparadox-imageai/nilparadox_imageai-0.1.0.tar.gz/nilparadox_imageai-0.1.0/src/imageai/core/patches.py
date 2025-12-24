from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


@dataclass(frozen=True)
class Patch:
    x: int
    y: int
    w: int
    h: int
    mean: float
    var: float
    grad_energy: float


def _gradient_energy(gray: np.ndarray) -> float:
    # Finite differences (fast, deterministic)
    gx = gray[:, 1:] - gray[:, :-1]
    gy = gray[1:, :] - gray[:-1, :]
    return float(np.mean(gx * gx) + np.mean(gy * gy))


def extract_homogeneous_patches(
    img: np.ndarray,
    patch_size: int = 32,
    stride: int = 16,
    max_patches: int = 800,
    grad_quantile: float = 0.25,
) -> List[Patch]:
    """
    Extract candidate patches that are likely to be 'flat' (low texture),
    so their variance reflects noise.

    img: float32 array in [0,1], shape (H,W) or (H,W,C)
    """
    if img.ndim == 3:
        # luminance approximation; avoid color artifacts
        gray = 0.299 * img[..., 0] + 0.587 * img[..., 1] + 0.114 * img[..., 2]
    else:
        gray = img

    H, W = gray.shape
    ps = patch_size

    patches: List[Patch] = []
    for y in range(0, H - ps + 1, stride):
        for x in range(0, W - ps + 1, stride):
            patch = gray[y : y + ps, x : x + ps]
            m = float(np.mean(patch))
            v = float(np.var(patch, ddof=0))
            ge = _gradient_energy(patch)
            patches.append(Patch(x=x, y=y, w=ps, h=ps, mean=m, var=v, grad_energy=ge))

    if not patches:
        return []

    # Keep lowest-gradient patches (most homogeneous)
    grad_vals = np.array([p.grad_energy for p in patches], dtype=np.float64)
    thr = float(np.quantile(grad_vals, grad_quantile))
    flat = [p for p in patches if p.grad_energy <= thr]

    # Sort by gradient energy ascending; cap count
    flat.sort(key=lambda p: p.grad_energy)
    return flat[:max_patches]
