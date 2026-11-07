"""Step 2 of the ASCII portrait: prepped grayscale PNG -> animated terminal SVG.

python scripts/make_ascii_svg.py [--src build/portrait-prepped.png] [--out assets/ascii-portrait.svg] [--cols 105] [--cut .22]

Each row "types" in left-to-right through its own <clipPath> wipe, with a block
cursor riding the edge; rows are staggered top to bottom and then freeze.
Monochrome on purpose. Pure SMIL so it animates inside GitHub's <img>.

Browsers collapse runs of spaces inside <text> even under xml:space="preserve", and
textLength then stretches the shortened row, so every space is written as &#160;.
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
COLS = 105                 # shown at 420 px wide, so ~7.5 px cells stay legible
PAD_X, TOP, BOTTOM = 28, 66, 24
RAMP = " .:-=+*#%@"
FILL = "#cbd5e1"           # one light grey: monochrome reads cleaner than colour
ROW_DUR, ROW_STAGGER, START = .32, .055, .25


def to_rows(img: Image.Image, cols: int, rows: int, cut: float) -> list[str]:
    """Cells darker than `cut` become spaces (clean empty hair / clothes); the rest
    spans the full ramp from '.' to '@'. Done per cell so stray specks can't leak in."""
    small = np.asarray(img.convert("L").resize((cols, rows), Image.LANCZOS), dtype=np.float32) / 255.0
    span = (np.clip(small, cut, 1) - cut) / (1 - cut)
    idx = np.where(small < cut, 0, 1 + np.round(span * (len(RAMP) - 2))).astype(int)
    return ["".join(RAMP[i] for i in r) for r in idx]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="build/portrait-prepped.png")
    ap.add_argument("--out", default="assets/ascii-portrait.svg")
    ap.add_argument("--cols", type=int, default=COLS)
    ap.add_argument("--cut", type=float, default=.22, help="cells darker than this render as spaces")
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
    rows = to_rows(img, a.cols, n_rows, a.cut)

    line_w = a.cols * cell_w
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="ASCII portrait of Siddharth Taurani">',
         terminal_frame(W, H, "Siddharth Taurani", gid="pfs"),
         f'<g font-family="{MONO}" font-size="{font:.2f}" fill="{FILL}">']
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
                 f'xml:space="preserve" style="white-space:pre" clip-path="url(#r{k})">'
                 f'{esc(line).replace(" ", "&#160;")}</text>')
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
