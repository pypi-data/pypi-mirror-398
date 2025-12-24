from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Union

from imageai.core.io import load_image
from imageai.core.decision import fuse_evidence

from imageai.forensics.noise_law import estimate_noise_law, noise_law_evidence
from imageai.forensics.resampling import resampling_evidence
from imageai.forensics.screenshot import screenshot_evidence
from imageai.forensics.spectral import spectral_evidence
from imageai.forensics.cfa import cfa_consistency_evidence


PathLike = Union[str, Path]


def detect_image(path: PathLike) -> Dict[str, Any]:
    """
    Programmatic API: returns the same structured JSON object as the CLI.

    Input: image path (str | Path)
    Output: dict with verdict, secondary_flags, audit
    """
    p = Path(path)
    info = load_image(p)
    img = info["array"]

    evidences = [
        noise_law_evidence(estimate_noise_law(img)),
        spectral_evidence(img),
        resampling_evidence(img),
        screenshot_evidence(img),
        cfa_consistency_evidence(img),
    ]

    decision = fuse_evidence(evidences)

    return {
        "verdict": decision,
        "secondary_flags": {
            "camera_computational": decision["primary"] == "camera_computational",
            "externally_generated": decision["primary"] == "externally_generated",
            "screenshot": decision["primary"] == "screenshot",
            "resampled": decision["primary"] == "resampled",
        },
        "audit": {
            "confidence": decision["confidence"],
            "modules": [
                "noise_law",
                "spectral",
                "resampling",
                "screenshot",
                "cfa",
            ],
        },
    }
