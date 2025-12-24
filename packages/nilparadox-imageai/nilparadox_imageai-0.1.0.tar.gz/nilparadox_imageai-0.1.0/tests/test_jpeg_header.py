from pathlib import Path
import numpy as np
from PIL import Image

from imageai.forensics.jpeg_header import extract_jpeg_quant_tables


def test_jpeg_quant_tables(tmp_path: Path):
    img = (np.random.rand(64, 64, 3) * 255).astype("uint8")
    p = tmp_path / "test.jpg"
    Image.fromarray(img).save(p, quality=90)

    info = extract_jpeg_quant_tables(p)
    assert info["is_jpeg"] is True
    assert len(info["quant_tables"]) >= 1
    assert len(info["quant_tables"][0]) == 64
