"""Render streak.svg: total contributions, current + longest streak, last 26 weeks.

Usage:  python scripts/streak_card.py [--user Siddharth1254] [--out build/streak.svg]
Needs GITHUB_TOKEN for the GraphQL API. Locally it falls back to public HTML without
one; in CI a missing token or failed API call exits non-zero (see contrib.py).
Animation is SMIL only (count-up via stepped <set>, rings drawing in, bars growing),
so it plays inside GitHub's <img> sandbox.
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
import pathlib

from contrib import fetch_calendar, streaks
from svgkit import CYAN, MONO, MUTED, PINK, SANS, TEXT, VIOLET, esc, terminal_frame, updated_stamp

W, H = 840, 880


def fmt_date(d: dt.date | None) -> str:
    return f"{d:%b} {d.day}, {d.year}" if d else "—"


def short(d: dt.date | None) -> str:
    return f"{d:%b} {d.day}" if d else "—"


def count_up(x, y, value: int, size: int, fill: str, begin: float = 0.3, dur: float = 1.4,
             anchor: str = "middle", weight: int = 800, steps: int = 18) -> str:
    """Stepped count-up: N stacked <text> frames, each shown for one tick, last one frozen."""
    out = []
    tick = dur / steps
    for k in range(1, steps + 1):
        t = k / steps
        v = round(value * (1 - (1 - t) ** 3))  # ease-out cubic
        start = begin + (k - 1) * tick
        if k < steps:
            anim = f'<set attributeName="opacity" to="1" begin="{start:.3f}s" dur="{tick:.3f}s"/>'
        else:
            anim = f'<set attributeName="opacity" to="1" begin="{start:.3f}s" fill="freeze"/>'
        out.append(
            f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{SANS}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" opacity="0">{v:,}{anim}</text>'
        )
    return "\n".join(out)


def ring(cx, cy, r, frac, color, begin):
    circ = 2 * math.pi * r
    on = circ * max(0.04, min(frac, 1.0))
    return f"""<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#1e2747" stroke-width="10"/>
<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round"
  stroke-dasharray="{on:.1f} {circ:.1f}" stroke-dashoffset="{on:.1f}" transform="rotate(-90 {cx} {cy})">
  <animate attributeName="stroke-dashoffset" from="{on:.1f}" to="0" begin="{begin}s" dur="1.2s" fill="freeze"
    calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .2 1"/>
</circle>"""


def fade(begin: float, dur: float = .6) -> str:
    return f'<animate attributeName="opacity" from="0" to="1" begin="{begin}s" dur="{dur}s" fill="freeze"/>'


def render(days, user: str) -> str:
    s = streaks(days)
    total = s["total"]
    cur, cur_a, cur_b = s["current"]
    lng, lng_a, lng_b = s["longest"]
    since = s["first_day"]

    # weekly totals for the last 26 weeks (Mon-aligned buckets ending today)
    today = days[-1][0] if days else dt.date.today()
    lookup = dict(days)
    weeks = []
    for i in range(25, -1, -1):
        end = today - dt.timedelta(days=7 * i)
        weeks.append(sum(lookup.get(end - dt.timedelta(days=j), 0) for j in range(7)))
    peak = max(weeks) or 1

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="{esc(user)}: {total:,} contributions, current streak {cur} days, longest streak {lng} days">',
         terminal_frame(W, H, "contribution streak"),
         f"""<defs><linearGradient id="num" x1="0" x2="1"><stop offset="0" stop-color="{VIOLET}"/><stop offset=".55" stop-color="{CYAN}"/><stop offset="1" stop-color="{PINK}"/></linearGradient>
<linearGradient id="bar" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{VIOLET}"/><stop offset="1" stop-color="{PINK}"/></linearGradient></defs>""",
         ]

    # --- total ---------------------------------------------------------------
    p.append(f'<g opacity="0">{fade(.1)}<text x="{W/2:g}" y="170" text-anchor="middle" font-family="{MONO}" '
             f'font-size="15" letter-spacing="4" fill="{CYAN}">TOTAL CONTRIBUTIONS</text></g>')
    p.append(count_up(W / 2, 272, total, 104, "url(#num)", begin=.3))
    p.append(f'<g opacity="0">{fade(1.5)}<text x="{W/2:g}" y="318" text-anchor="middle" font-family="{MONO}" '
             f'font-size="16" fill="{MUTED}">{esc(fmt_date(since))} → today</text></g>')
    p.append(f'<rect x="40" y="354" width="{W-80}" height="1" fill="#1e2747"/>')

    # --- streak rings ----------------------------------------------------------
    best = max(lng, 1)
    for cx, label, val, a, b, color, beg, sub in (
        (230, "CURRENT STREAK", cur, cur_a, cur_b, PINK, .6, "days in a row"),
        (610, "LONGEST STREAK", lng, lng_a, lng_b, VIOLET, .9, "personal best"),
    ):
        frac = val / best
        p.append(ring(cx, 490, 84, frac, color, beg))
        p.append(count_up(cx, 510, val, 58, "#ffffff", begin=beg + .2, dur=1.0, steps=12))
        p.append(f'<g opacity="0">{fade(beg + .8)}'
                 f'<text x="{cx}" y="540" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{MUTED}">{sub}</text>'
                 f'<text x="{cx}" y="616" text-anchor="middle" font-family="{MONO}" font-size="15" letter-spacing="3" fill="{color}">{label}</text>'
                 f'<text x="{cx}" y="644" text-anchor="middle" font-family="{MONO}" font-size="15" fill="{TEXT}">'
                 f'{esc(short(a)) + " – " + esc(short(b)) if val else "start one today"}</text></g>')
    p.append(f'<rect x="40" y="678" width="{W-80}" height="1" fill="#1e2747"/>')

    # --- last 26 weeks -----------------------------------------------------------
    p.append(f'<g opacity="0">{fade(1.2)}<text x="40" y="714" font-family="{MONO}" font-size="14" letter-spacing="3" fill="{CYAN}">LAST 26 WEEKS</text>'
             f'<text x="{W-40}" y="714" text-anchor="end" font-family="{MONO}" font-size="14" fill="{MUTED}">peak {peak:,}/wk</text></g>')
    base, maxh, x0, bw, gap = 838, 100, 40, 24, (W - 80 - 26 * 24) / 25
    for i, v in enumerate(weeks):
        h = max(3, v / peak * maxh)
        x = x0 + i * (bw + gap)
        b = 1.3 + i * .04
        p.append(f'<rect x="{x:.1f}" y="{base}" width="{bw}" height="0" rx="4" fill="url(#bar)" opacity="{.35 + .65 * (v / peak):.2f}">'
                 f'<animate attributeName="height" from="0" to="{h:.1f}" begin="{b:.2f}s" dur=".6s" fill="freeze"/>'
                 f'<animate attributeName="y" from="{base}" to="{base - h:.1f}" begin="{b:.2f}s" dur=".6s" fill="freeze"/></rect>')
    p.append(updated_stamp(W - 24, H - 14))
    p.append("</svg>")
    return "\n".join(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="Siddharth1254")
    ap.add_argument("--out", default="build/streak.svg")
    a = ap.parse_args()
    days = fetch_calendar(a.user, all_time=True)
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(days, a.user), encoding="utf-8")
    s = streaks(days)
    print(f"wrote {out}: total={s['total']} current={s['current'][0]} longest={s['longest'][0]}")


if __name__ == "__main__":
    main()
