from __future__ import annotations

import json
from pathlib import Path
import typer
from rich import print

from imageai.core.io import load_image
from imageai.core.decision import fuse_evidence

from imageai.forensics.noise_law import estimate_noise_law, noise_law_evidence
from imageai.forensics.resampling import resampling_evidence
from imageai.forensics.screenshot import screenshot_evidence
from imageai.forensics.spectral import spectral_evidence
from imageai.forensics.cfa import cfa_consistency_evidence


detect_app = typer.Typer()


@detect_app.command("detect")
def detect(image_path: Path):
    """
    Run full forensic detection and return a single structured verdict.
    """

    info = load_image(image_path)
    img = info["array"]

    evidences = [
        noise_law_evidence(estimate_noise_law(img)),
        spectral_evidence(img),
        resampling_evidence(img),
        screenshot_evidence(img),
        cfa_consistency_evidence(img),
    ]

    decision = fuse_evidence(evidences)

    output = {
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

    print(json.dumps(output, indent=2))
