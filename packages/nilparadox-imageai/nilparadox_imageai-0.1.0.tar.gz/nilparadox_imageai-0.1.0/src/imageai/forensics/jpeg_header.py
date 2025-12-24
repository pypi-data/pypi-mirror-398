from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

from PIL import Image


def extract_jpeg_quant_tables(path: str | Path) -> Dict[str, Any]:
    """
    Extract JPEG quantization tables using Pillow's internal parser.

    Returns:
      - is_jpeg: bool
      - quant_tables: list of tables (each 64 ints)
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)

    with Image.open(p) as im:
        if im.format != "JPEG":
            return {
                "is_jpeg": False,
                "quant_tables": [],
            }

        qt = getattr(im, "quantization", None)
        if qt is None:
            return {
                "is_jpeg": True,
                "quant_tables": [],
            }

        tables: List[List[int]] = []
        for _, table in qt.items():
            tables.append(list(table))

    return {
        "is_jpeg": True,
        "quant_tables": tables,
    }
