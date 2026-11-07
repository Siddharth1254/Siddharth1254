"""Step 1 of the ASCII portrait: avatar -> clean, high-contrast grayscale PNG.

python scripts/prep_photo.py [--src URL_OR_PATH] [--out build/portrait-prepped.png]
                             [--model u2net_human_seg] [--edge 0]

Needs:  pip install "rembg[cpu]" onnxruntime opencv-python pillow numpy

* background removal with rembg (required, no fallback), keeping only the largest
  connected blob (head + torso) so props next to the body drop out; the mask edge
  is feathered and everything outside it is pure black, so it renders as blank space
* head + top of the shoulders: forehead -> chin ~70% of the frame height, face
  centred horizontally, at the ASCII grid's aspect ratio
* contrast inside the mask only: 2nd-98th percentile stretch, CLAHE, unsharp mask,
  gamma, and an optional light Sobel edge pass (--edge) for jaw / glasses / hairline
  (the dark cut to spaces happens per character cell in make_ascii_svg.py)
Run by hand only; it is NOT part of the daily workflow. The output lives in build/
(git-ignored) so the photo itself is never committed.
"""
from __future__ import annotations

import argparse
import io
import pathlib
import sys
import urllib.request

import cv2  # type: ignore
import numpy as np
from PIL import Image, ImageFilter

DEFAULT_SRC = "https://github.com/Siddharth1254.png?size=800"
ASPECT = 784 / 790        # ASCII grid width / height in make_ascii_svg.py (840x880 card)
FACE_FRAC = .70           # forehead -> chin, as a fraction of the frame height
HEAD_TOP = .03            # top of the hair sits at least this far below the frame top
OUT_H = 900


def load(src: str) -> Image.Image:
    if src.startswith("http"):
        req = urllib.request.Request(src, headers={"User-Agent": "profile-art-generator"})
        data = urllib.request.urlopen(req, timeout=30).read()
        return Image.open(io.BytesIO(data)).convert("RGB")
    return Image.open(src).convert("RGB")


def subject_mask(img: Image.Image, model: str) -> np.ndarray:
    """Feathered alpha mask in [0,1]: rembg, largest connected blob only."""
    try:
        from rembg import new_session, remove  # type: ignore
    except ImportError:
        sys.exit('error: rembg is required: pip install "rembg[cpu]" onnxruntime')
    alpha = np.asarray(remove(img, session=new_session(model)).split()[-1]) > 127
    n, labels, stats, _ = cv2.connectedComponentsWithStats(alpha.astype(np.uint8), connectivity=8)
    if n < 2:
        sys.exit("error: rembg found no subject in the photo")
    biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    blob = ((labels == biggest) * 255).astype(np.uint8)
    # human_seg leaves the torso patchy: close small gaps, then fill enclosed holes
    k = max(3, round(min(blob.shape) * .03) | 1)
    blob = cv2.morphologyEx(blob, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    outside = np.pad(blob, 1).copy()
    cv2.floodFill(outside, None, (0, 0), 255)
    blob |= cv2.bitwise_not(outside[1:-1, 1:-1])
    keep = Image.fromarray(blob)
    return np.asarray(keep.filter(ImageFilter.GaussianBlur(1.5)), dtype=np.float32) / 255.0


def face_box(gray: np.ndarray) -> tuple[int, int, int, int]:
    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = det.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(60, 60))
    if len(faces) == 0:
        sys.exit("error: no face detected; pass a clearer, front-facing photo with --src")
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return int(x), int(y), int(w), int(h)


def crop_box(mask: np.ndarray, face) -> tuple[int, int, int, int]:
    fx, fy, fw, fh = face
    forehead, chin = fy, fy + fh * 1.08          # Haar boxes stop just above the chin
    frame_h = (chin - forehead) / FACE_FRAC
    head_top = int(np.nonzero(mask > .5)[0].min())
    # put the face block in the middle of the spare height, but never clip the hair
    top = min(forehead - (frame_h - (chin - forehead)) / 2, head_top - HEAD_TOP * frame_h)
    frame_w = frame_h * ASPECT
    left = fx + fw / 2 - frame_w / 2
    return int(round(left)), int(round(top)), int(round(left + frame_w)), int(round(top + frame_h))


def tone(gray: np.ndarray, mask: np.ndarray, edge: float) -> np.ndarray:
    inside = mask > .5
    lo, hi = np.percentile(gray[inside], [2, 98])
    x = np.clip((gray - lo) / max(hi - lo, 1e-3), 0, 1)
    x8 = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply((x * 255).astype(np.uint8))
    x8 = np.asarray(Image.fromarray(x8).filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=0)))
    x = (x8.astype(np.float32) / 255.0) ** 1.1
    if edge > 0:
        g = cv2.GaussianBlur(x * mask, (0, 0), 1.2)
        mag = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3))
        mag = np.clip(mag / max(np.percentile(mag[inside], 99), 1e-3), 0, 1)
        x = (1 - edge) * x + edge * mag
        x = np.clip(x / max(np.percentile(x[inside], 99), 1e-3), 0, 1)   # blending dims the top end
    return x * mask


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEFAULT_SRC)
    ap.add_argument("--out", default="build/portrait-prepped.png")
    ap.add_argument("--model", default="u2net_human_seg", help="rembg model, e.g. u2net or u2net_human_seg")
    ap.add_argument("--edge", type=float, default=0, help="Sobel edge blend weight (try .25), 0 turns it off")
    ap.add_argument("--mask-out", help="also save the cleaned mask here (debugging)")
    a = ap.parse_args()

    img = load(a.src)
    mask = subject_mask(img, a.model)
    gray = np.asarray(img.convert("L"), dtype=np.float32) / 255.0
    face = face_box(np.asarray(img.convert("L")))
    out_img = Image.fromarray((tone(gray, mask, a.edge) * 255).astype(np.uint8))

    box = crop_box(mask, face)
    out_img = out_img.crop(box)        # out-of-bounds areas come back black = blank space
    out_img = out_img.resize((round(OUT_H * ASPECT), OUT_H), Image.LANCZOS)

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out_img.save(out)
    if a.mask_out:
        Image.fromarray((mask * 255).astype(np.uint8)).save(a.mask_out)
    print(f"wrote {out}: model={a.model} edge={a.edge} face={face} crop={box}")


if __name__ == "__main__":
    main()
