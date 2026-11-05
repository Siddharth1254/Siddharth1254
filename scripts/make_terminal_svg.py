"""Regenerate assets/terminal.svg (the typing terminal at the top of the README).

Edit WHOAMI / PHRASES below, then:  python scripts/make_terminal_svg.py
Each phrase is revealed by its own <clipPath> wipe. The clip width is
len(text) * FONT_SIZE * 0.602 (monospace advance ≈ 0.602 em) so lines never get cut.
"""
import pathlib
from xml.sax.saxutils import escape

WHOAMI = "Siddharth Taurani · AI & Data Science engineer-in-training · Paris"
PHRASES = [
    "turning messy data into decisions",
    "building AI agents, assistants and automations",
    "making LLM systems reliable and measurable",
    "open to an AI / Data alternance · 3 wks company / 1 wk school",
]
FONT = 20
ADV = FONT * 0.602
X0 = 122
SLOT = 4.5                      # seconds per phrase
CYCLE = SLOT * len(PHRASES)
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"


def kt(*secs):
    return ";".join(f"{s / CYCLE:.4f}".rstrip("0").rstrip(".") if s else "0" for s in secs)


def main():
    type_t, hold_t, erase_t = 1.7, 3.9, 4.2   # within a slot
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 220" width="1000" height="220" role="img" '
        f'aria-label="Terminal: {escape(WHOAMI)}">',
        '<defs><linearGradient id="bd" x1="0" x2="1"><stop offset="0" stop-color="#a78bfa"/><stop offset=".5" stop-color="#22d3ee"/><stop offset="1" stop-color="#f472b6"/></linearGradient></defs>',
        '<rect x="1" y="1" width="998" height="218" rx="16" fill="#0b1020" stroke="url(#bd)" stroke-opacity=".6" stroke-width="1.5"/>',
        '<rect x="1" y="1" width="998" height="40" rx="16" fill="#111833"/><rect x="1" y="26" width="998" height="15" fill="#111833"/>',
        '<circle cx="28" cy="21" r="7" fill="#ff5f57"/><circle cx="52" cy="21" r="7" fill="#febc2e"/><circle cx="76" cy="21" r="7" fill="#28c840"/>',
        f'<text x="500" y="26" text-anchor="middle" font-family="{MONO}" font-size="13" fill="#64748b">sidd@paris — zsh — 80×24</text>',
        f'<g font-family="{MONO}" font-size="{FONT}">',
        '<text x="32" y="82"><tspan fill="#22c55e">❯</tspan><tspan fill="#a78bfa"> whoami</tspan></text>',
        f'<text x="32" y="114" fill="#94a3b8">{escape(WHOAMI)}</text>',
        '<text x="32" y="172"><tspan fill="#22c55e">❯</tspan><tspan fill="#f472b6"> now</tspan></text>',
    ]
    keys = kt(0, type_t, hold_t, erase_t, CYCLE)
    vis = kt(0, 0.002, hold_t + 0.1, erase_t - 0.01, erase_t, CYCLE)
    for i, text in enumerate(PHRASES):
        w = round(len(text) * ADV, 1)
        begin = f"{i * SLOT:.1f}s"
        out.append(
            f'<clipPath id="c{i}"><rect x="{X0}" y="150" height="34" width="0">'
            f'<animate attributeName="width" values="0;{w};{w};0;0" keyTimes="{keys}" dur="{CYCLE}s" begin="{begin}" repeatCount="indefinite"/>'
            f'</rect></clipPath>'
        )
        out.append(f'<text x="{X0}" y="172" clip-path="url(#c{i})" fill="#e2e8f0">{escape(text)}</text>')
        out.append(
            f'<rect x="{X0}" y="155" width="11" height="22" fill="#22d3ee" opacity="0">'
            f'<animate attributeName="x" values="{X0};{X0 + w};{X0 + w};{X0};{X0}" keyTimes="{keys}" dur="{CYCLE}s" begin="{begin}" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;1;1;1;0;0" keyTimes="{vis}" dur="{CYCLE}s" begin="{begin}" repeatCount="indefinite"/>'
            f'</rect>'
        )
        assert X0 + w + 11 < 990, f"phrase too long for the window: {text!r}"
    out.append("</g></svg>")
    path = pathlib.Path(__file__).resolve().parent.parent / "assets" / "terminal.svg"
    path.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
