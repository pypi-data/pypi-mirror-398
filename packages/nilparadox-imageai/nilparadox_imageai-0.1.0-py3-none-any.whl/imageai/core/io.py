from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from PIL import Image, ExifTags


# Optional HEIC/HEIF support (iPhone). We do NOT fail hard if unavailable.
# Instead we keep behavior explicit: HEIC loads only if pillow-heif is installed.
try:
    import pillow_heif  # type: ignore

    pillow_heif.register_heif_opener()
    _HEIF_ENABLED = True
except Exception:
    _HEIF_ENABLED = False


def _extract_exif(im: Image.Image) -> Optional[Dict[str, Any]]:
    try:
        raw_exif = im.getexif()
        if not raw_exif:
            return None
        return {ExifTags.TAGS.get(k, k): v for k, v in raw_exif.items()}
    except Exception:
        return None


def load_image(path: str | Path) -> Dict[str, Any]:
    """
    Load an image in a controlled, auditable way.

    Returns:
      - array: float32 image array in [0, 1], shape (H,W) or (H,W,3)
      - mode: original PIL mode
      - size: (width, height)
      - format: image format (JPEG, PNG, HEIF, WEBP, ...)
      - has_exif: bool
      - exif: dict|None (tag->value)
      - heif_enabled: bool (whether pillow-heif is available)
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {p}")

    # Pillow will open HEIC/HEIF only if pillow-heif is installed and registered.
    try:
        with Image.open(p) as im:
            mode = im.mode
            fmt = im.format
            size = im.size
            exif = _extract_exif(im)

            # Convert to a deterministic working space:
            # - keep grayscale as L
            # - everything else becomes RGB
            if im.mode == "L":
                arr = np.asarray(im)
            else:
                arr = np.asarray(im.convert("RGB"))
    except OSError as e:
        # Provide a clear error message for missing decoders (HEIC) or corrupt images.
        hint = ""
        suffix = p.suffix.lower()
        if suffix in (".heic", ".heif") and not _HEIF_ENABLED:
            hint = " (HEIC/HEIF decoder not installed: run `pip install pillow-heif`)"
        raise OSError(f"Failed to open image: {p}{hint}. Original error: {e}") from e

    # Normalize to float32 [0,1]
    if arr.dtype == np.uint8:
        arr_f = arr.astype(np.float32) / 255.0
    elif arr.dtype == np.uint16:
        arr_f = arr.astype(np.float32) / 65535.0
    else:
        # Rare modes can produce int32/float64 arrays; normalize safely
        arr_f = arr.astype(np.float32)
        # If values appear to be 0..255-ish, normalize; otherwise leave as-is
        vmax = float(np.max(arr_f)) if arr_f.size else 0.0
        if vmax > 1.5 and vmax <= 255.5:
            arr_f = arr_f / 255.0
        elif vmax > 255.5 and vmax <= 65535.5:
            arr_f = arr_f / 65535.0

    # Clip to be safe against decoder quirks
    arr_f = np.clip(arr_f, 0.0, 1.0)

    return {
        "array": arr_f,
        "mode": mode,
        "size": size,
        "format": fmt,
        "has_exif": exif is not None,
        "exif": exif,
        "heif_enabled": _HEIF_ENABLED,
    }
