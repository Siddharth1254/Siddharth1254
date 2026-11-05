"""Step 2 of the ASCII portrait: prepped grayscale PNG -> animated terminal SVG.

python scripts/make_ascii_svg.py [--src build/portrait-prepped.png] [--out assets/ascii-portrait.svg]

Each row "types" in left-to-right through its own <clipPath> wipe, with a block
cursor riding the edge; rows are staggered top to bottom and then freeze.
Monochrome on purpose. Pure SMIL so it animates inside GitHub's <img>.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from svgkit import MONO, esc, terminal_frame  # noqa: E402

W, H = 840, 880            # same box as streak.svg so the two line up side by side
COLS = 140
PAD_X, TOP, BOTTOM = 28, 66, 24
RAMP = " .`:-=+*cs#%@"
FILL = "#cbd5e1"           # one light grey: monochrome reads cleaner than colour
ROW_DUR, ROW_STAGGER, START = .32, .055, .25


def to_rows(img: Image.Image, cols: int, rows: int) -> list[str]:
    small = np.asarray(img.convert("L").resize((cols, rows), Image.LANCZOS), dtype=np.float32) / 255.0
    idx = np.clip(np.round(small ** .9 * (len(RAMP) - 1)), 0, len(RAMP) - 1).astype(int)
    return ["".join(RAMP[i] for i in r) for r in idx]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="build/portrait-prepped.png")
    ap.add_argument("--out", default="assets/ascii-portrait.svg")
    ap.add_argument("--cols", type=int, default=COLS)
    a = ap.parse_args()

    cell_w = (W - 2 * PAD_X) / a.cols
    cell_h = cell_w * 1.875                      # character cell aspect ≈ 1 : 1.875
    font = cell_w / .602
    n_rows = int((H - TOP - BOTTOM) / cell_h)
    img = Image.open(a.src)
    # crop to the grid's aspect (centre/top-biased) so the face isn't squashed
    grid_aspect = (a.cols * cell_w) / (n_rows * cell_h)
    iw, ih = img.size
    if iw / ih > grid_aspect:
        nw = int(ih * grid_aspect); img = img.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
    else:
        nh = int(iw / grid_aspect); img = img.crop((0, 0, iw, nh))
    rows = to_rows(img, a.cols, n_rows)

    line_w = a.cols * cell_w
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="ASCII portrait of Siddharth Taurani">',
         terminal_frame(W, H, "sidd@github: ~$ ./portrait.sh", gid="pfs"),
         f'<g font-family="{MONO}" font-size="{font:.2f}" fill="{FILL}" xml:space="preserve">']
    clips, k = [], 0
    for r, line in enumerate(rows):
        if not line.strip():
            continue
        y = TOP + r * cell_h
        base = y + cell_h * .78
        begin = START + r * ROW_STAGGER
        clips.append(f'<clipPath id="r{k}"><rect x="{PAD_X}" y="{y:.2f}" width="0" height="{cell_h + .5:.2f}">'
                     f'<animate attributeName="width" from="0" to="{line_w:.1f}" begin="{begin:.2f}s" dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>')
        p.append(f'<text x="{PAD_X}" y="{base:.2f}" textLength="{line_w:.1f}" lengthAdjust="spacing" '
                 f'clip-path="url(#r{k})">{esc(line)}</text>')
        p.append(f'<rect x="{PAD_X}" y="{y + .5:.2f}" width="{cell_w:.2f}" height="{cell_h:.2f}" fill="#22d3ee" opacity="0">'
                 f'<animate attributeName="x" from="{PAD_X}" to="{PAD_X + line_w:.1f}" begin="{begin:.2f}s" dur="{ROW_DUR}s" fill="freeze"/>'
                 f'<set attributeName="opacity" to=".9" begin="{begin:.2f}s" dur="{ROW_DUR}s"/></rect>')
        k += 1
    p.append("</g>")
    p.insert(2, "<defs>" + "".join(clips) + "</defs>")
    p.append("</svg>")

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(p) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out}: {a.cols}x{n_rows} chars, {out.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
