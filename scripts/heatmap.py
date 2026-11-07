"""Render heatmap.svg: last year's contribution calendar, cells revealing one by one.

Usage:  python scripts/heatmap.py [--user Siddharth1254] [--out build/heatmap.svg]
Same data source as streak_card.py. Pure SMIL, plays once and freezes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import pathlib

from contrib import fetch_calendar
from svgkit import MONO, MUTED, TEXT, esc, terminal_frame, updated_stamp

# violet -> pink, level 0 is the empty cell
LEVELS = ["#161b2e", "#3b1f6e", "#6d28d9", "#a78bfa", "#f472b6"]
CELL, GAP = 13, 3
STEP = CELL + GAP
LEFT, TOP = 70, 120


def level(c: int, q: list[int]) -> int:
    if c <= 0:
        return 0
    for i, t in enumerate(q, start=1):
        if c <= t:
            return i
    return 4


def render(days, user: str) -> str:
    today = days[-1][0]
    start = today - dt.timedelta(days=364)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)  # back to Sunday, like GitHub
    lookup = dict(days)

    cells = []
    d = start
    while d <= today:
        col = (d - start).days // 7
        row = (d.weekday() + 1) % 7  # Sun=0
        cells.append((d, col, row, lookup.get(d, 0)))
        d += dt.timedelta(days=1)

    nz = sorted(c for *_, c in cells if c > 0)
    q = [nz[int(len(nz) * f) - 1] if nz else 1 for f in (.25, .5, .75)] if nz else [1, 2, 3]
    total = sum(c for *_, c in cells)
    ncols = cells[-1][1] + 1
    W = LEFT + ncols * STEP + 40
    H = TOP + 7 * STEP + 70

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="{esc(user)}: {total:,} contributions in the last year">',
         terminal_frame(W, H, "contribution heatmap"),
         f'<text x="40" y="84" font-family="{MONO}" font-size="16" fill="{TEXT}">'
         f'<tspan fill="#22c55e">❯</tspan> {total:,} contributions in the last year</text>']

    # month labels
    seen = set()
    for d, col, row, _ in cells:
        if d.day <= 7 and row == 0 and (d.year, d.month) not in seen and col < ncols - 1:
            seen.add((d.year, d.month))
            p.append(f'<text x="{LEFT + col * STEP}" y="{TOP - 10}" font-family="{MONO}" font-size="12" fill="{MUTED}">{d:%b}</text>')
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        p.append(f'<text x="{LEFT - 10}" y="{TOP + row * STEP + 10}" text-anchor="end" font-family="{MONO}" font-size="12" fill="{MUTED}">{name}</text>')

    # cells: diagonal sweep, ~2.6 s total
    for d, col, row, c in cells:
        lv = level(c, q)
        b = col * .045 + row * .02
        p.append(f'<rect x="{LEFT + col * STEP}" y="{TOP + row * STEP}" width="{CELL}" height="{CELL}" rx="3" '
                 f'fill="{LEVELS[lv]}" opacity="0"><title>{c} on {d.isoformat()}</title>'
                 f'<animate attributeName="opacity" from="0" to="1" begin="{b:.2f}s" dur=".35s" fill="freeze"/></rect>')

    # legend
    lx = W - 40 - 5 * STEP - 80
    ly = TOP + 7 * STEP + 26
    p.append(f'<text x="{lx}" y="{ly + 11}" font-family="{MONO}" font-size="12" fill="{MUTED}">less</text>')
    for i, col in enumerate(LEVELS):
        p.append(f'<rect x="{lx + 38 + i * STEP}" y="{ly}" width="{CELL}" height="{CELL}" rx="3" fill="{col}"/>')
    p.append(f'<text x="{lx + 42 + 5 * STEP}" y="{ly + 11}" font-family="{MONO}" font-size="12" fill="{MUTED}">more</text>')
    p.append(updated_stamp(40, ly + 11, anchor="start"))
    p.append("</svg>")
    return "\n".join(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="Siddharth1254")
    ap.add_argument("--out", default="build/heatmap.svg")
    a = ap.parse_args()
    days = fetch_calendar(a.user, all_time=False)
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(days, a.user), encoding="utf-8")
    print(f"wrote {out}: {sum(c for _, c in days)} contributions, {len(days)} days")


if __name__ == "__main__":
    main()
