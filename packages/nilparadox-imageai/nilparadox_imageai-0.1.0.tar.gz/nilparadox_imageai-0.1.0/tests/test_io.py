import numpy as np
from PIL import Image
from pathlib import Path

from imageai.core.io import load_image


def test_load_image_normalization(tmp_path: Path):
    img = (np.random.rand(32, 32, 3) * 255).astype("uint8")
    p = tmp_path / "test.png"
    Image.fromarray(img).save(p)

    info = load_image(p)

    arr = info["array"]
    assert arr.dtype == np.float32
    assert arr.min() >= 0.0
    assert arr.max() <= 1.0
    assert info["size"] == (32, 32)
