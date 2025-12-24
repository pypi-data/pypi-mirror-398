from __future__ import annotations

import json
from pathlib import Path

import typer
from rich import print

from imageai.core.io import load_image
from imageai.forensics.jpeg_header import extract_jpeg_quant_tables


analyze_app = typer.Typer()


@analyze_app.command("analyze")
def analyze(image_path: Path) -> None:
    """
    Analyze an image and print a forensic header report.
    """
    info = load_image(image_path)
    jpeg_info = extract_jpeg_quant_tables(image_path)

    report = {
        "path": str(image_path),
        "format": info["format"],
        "mode": info["mode"],
        "size": info["size"],
        "has_exif": info["has_exif"],
        "jpeg": jpeg_info,
    }

    print(json.dumps(report, indent=2))
