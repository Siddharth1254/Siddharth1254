"""Step 1 of the ASCII portrait: avatar -> clean, high-contrast grayscale PNG.

python scripts/prep_photo.py [--src URL_OR_PATH] [--out build/portrait-prepped.png]

* grayscale
* background removal: `rembg` if installed, otherwise a high-contrast threshold
  that pushes the (flat) background to black so it renders as blank space
* local contrast with CLAHE (OpenCV) or PIL autocontrast as a fallback
Run by hand only; it is NOT part of the daily workflow.
"""
from __future__ import annotations

import argparse
import io
import pathlib
import urllib.request

import numpy as np
from PIL import Image, ImageOps

DEFAULT_SRC = "https://github.com/Siddharth1254.png?size=800"


def load(src: str) -> Image.Image:
    if src.startswith("http"):
        req = urllib.request.Request(src, headers={"User-Agent": "profile-art-generator"})
        data = urllib.request.urlopen(req, timeout=30).read()
        return Image.open(io.BytesIO(data)).convert("RGB")
    return Image.open(src).convert("RGB")


def subject_mask(img: Image.Image) -> np.ndarray | None:
    """Alpha mask in [0,1] from rembg, or None if rembg isn't available."""
    try:
        from rembg import remove  # type: ignore
    except Exception:
        return None
    cut = remove(img)  # RGBA
    return np.asarray(cut.split()[-1], dtype=np.float32) / 255.0


def local_contrast(gray: np.ndarray) -> np.ndarray:
    try:
        import cv2  # type: ignore
        clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
        return clahe.apply(gray)
    except Exception:
        return np.asarray(ImageOps.autocontrast(Image.fromarray(gray), cutoff=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEFAULT_SRC)
    ap.add_argument("--out", default="build/portrait-prepped.png")
    a = ap.parse_args()

    img = load(a.src)
    gray = np.asarray(ImageOps.grayscale(img), dtype=np.uint8)
    gray = local_contrast(gray).astype(np.float32) / 255.0

    mask = subject_mask(img)
    if mask is not None:
        print("background: rembg")
        # stretch the subject's own range, darken mid-tones so the face pops, and keep
        # a faint floor inside the silhouette so dark hair / clothes still show as '.'
        inside = mask > .5
        lo, hi = np.percentile(gray[inside], [2, 99.5])
        gray = np.clip((gray - lo) / max(hi - lo, 1e-3), 0, 1) ** 1.35
        gray = np.where(inside, np.maximum(gray, .09), 0.0) * np.clip(mask * 1.4, 0, 1)
    else:
        print("background: threshold fallback (pip install rembg for a cleaner cut)")
        lo, hi = np.percentile(gray, [35, 99])
        gray = np.clip((gray - lo) / max(hi - lo, 1e-3), 0, 1)

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((gray * 255).astype(np.uint8)).save(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
