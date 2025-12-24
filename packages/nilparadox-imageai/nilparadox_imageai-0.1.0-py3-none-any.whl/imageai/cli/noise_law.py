from __future__ import annotations

import json
from pathlib import Path

import typer
from rich import print

from imageai.core.io import load_image
from imageai.forensics.noise_law import estimate_noise_law


noise_app = typer.Typer()


@noise_app.command("noise-law")
def noise_law(
    image_path: Path,
    patch_size: int = typer.Option(32, help="Patch size in pixels."),
    stride: int = typer.Option(16, help="Patch stride in pixels."),
) -> None:
    """
    Fit the Poisson–Gaussian noise-intensity law using homogeneous patches.
    """
    info = load_image(image_path)
    img = info["array"]

    res = estimate_noise_law(img, patch_size=patch_size, stride=stride)
    payload = {
        "path": str(image_path),
        "format": info["format"],
        "size": info["size"],
        "noise_law": {
            "a": res.a,
            "b": res.b,
            "rmse": res.rmse,
            "r2": res.r2,
            "n_patches": res.n_patches,
            "reliability": res.reliability,
            "evidence": res.evidence,
        },
    }
    print(json.dumps(payload, indent=2))
