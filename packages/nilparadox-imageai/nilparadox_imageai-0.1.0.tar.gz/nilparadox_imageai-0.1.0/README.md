# imageai

Explainable, physics-based image forensics for:
- camera computational enhancement (denoise / sharpen / beautify)
- screenshots
- resampling artifacts

No end-to-end deep learning classifier. Outputs structured decisions.

## Install (local)
pip install -e .

## CLI
imageai detect /path/to/image.jpg

## Python API
from imageai.api import detect_image
result = detect_image("/path/to/image.jpg")
print(result)

