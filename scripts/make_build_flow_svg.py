"""Regenerate assets/build-flow.svg: six stages that light up as glowing packets pass.

python scripts/make_build_flow_svg.py
"""
import pathlib
from xml.sax.saxutils import escape

MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "ui-sans-serif, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
STAGES = [
    ("🎯", "Frame the problem", "goal · users · metric", "#a78bfa"),
    ("📊", "Data", "collect · clean · explore", "#8b5cf6"),
    ("🧠", "Model", "ML · LLMs · RAG", "#22d3ee"),
    ("🤖", "Agents & automation", "tools · MCP · workflows", "#06b6d4"),
    ("📏", "Evaluate", "metrics · tracing", "#f472b6"),
    ("🚀", "Ship & monitor", "deploy · observe · iterate", "#22c55e"),
]
W, H = 1200, 212
BOX_W, BOX_H, X0, Y0 = 170, 118, 24, 62
GAP = (W - 2 * X0 - len(STAGES) * BOX_W) / (len(STAGES) - 1)
DUR = 6.0
MID_Y = Y0 + BOX_H / 2 + 0  # packet line


def main():
    cx = [X0 + i * (BOX_W + GAP) + BOX_W / 2 for i in range(len(STAGES))]
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        f'aria-label="How I build: {escape(" → ".join(s[1] for s in STAGES))}">',
        '<defs><filter id="g" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="3" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
        f'<rect width="{W}" height="{H}" rx="20" fill="#070a14"/>',
        f'<text x="24" y="38" font-family="{MONO}" font-size="14" fill="#64748b">'
        f'// how I build — from a fuzzy question to a system people can rely on</text>',
    ]
    # dashed connectors + arrowheads
    for i in range(len(STAGES) - 1):
        a = X0 + i * (BOX_W + GAP) + BOX_W + 4
        b = a + GAP - 8
        p.append(f'<path d="M{a:.1f} {MID_Y} H{b:.1f}" stroke="#334155" stroke-width="2" stroke-dasharray="4 5">'
                 f'<animate attributeName="stroke-dashoffset" values="18;0" dur="1s" repeatCount="indefinite"/></path>'
                 f'<path d="M{b - 6:.1f} {MID_Y - 5} l6 5 -6 5" fill="none" stroke="#475569" stroke-width="2"/>')
    # boxes: light up when the packet reaches them (packet travels 0 → .92 of DUR)
    n = len(STAGES)
    for i, (emoji, title, sub, col) in enumerate(STAGES):
        x = X0 + i * (BOX_W + GAP)
        hit = .92 * i / (n - 1)
        k = f"0;{max(hit - .04, 0):.3f};{hit:.3f};{min(hit + .08, 1):.3f};1"
        p.append(f'''<g>
<rect x="{x:.1f}" y="{Y0}" width="{BOX_W}" height="{BOX_H}" rx="16" fill="#0f1530" stroke="{col}" stroke-opacity=".35" stroke-width="1.5">
<animate attributeName="stroke-opacity" values=".35;.35;1;.35;.35" keyTimes="{k}" dur="{DUR}s" repeatCount="indefinite"/></rect>
<rect x="{x:.1f}" y="{Y0}" width="{BOX_W}" height="{BOX_H}" rx="16" fill="{col}" opacity="0">
<animate attributeName="opacity" values="0;0;.16;0;0" keyTimes="{k}" dur="{DUR}s" repeatCount="indefinite"/></rect>
<text x="{cx[i]:.1f}" y="104" text-anchor="middle" font-size="26">{emoji}</text>
<text x="{cx[i]:.1f}" y="138" text-anchor="middle" font-family="{SANS}" font-size="15" font-weight="700" fill="#e2e8f0">{escape(title)}</text>
<text x="{cx[i]:.1f}" y="160" text-anchor="middle" font-family="{MONO}" font-size="10.5" fill="{col}">{escape(sub)}</text>
<text x="{x + 12:.1f}" y="82" font-family="{MONO}" font-size="11" fill="#475569">{i + 1:02d}</text></g>''')
    # glowing packets
    for col, begin in (("#22d3ee", 0), ("#f472b6", 2), ("#a78bfa", 4)):
        p.append(f'<circle r="6" fill="{col}" filter="url(#g)">'
                 f'<animateMotion path="M{cx[0]:.1f} {MID_Y} H{cx[-1]:.1f}" dur="{DUR}s" begin="{begin}s" repeatCount="indefinite" '
                 f'keyPoints="0;1;1" keyTimes="0;.92;1" calcMode="linear"/>'
                 f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.05;.9;1" dur="{DUR}s" begin="{begin}s" repeatCount="indefinite"/></circle>')
    p.append(f'<text x="1176" y="200" text-anchor="end" font-family="{MONO}" font-size="12" fill="#475569">'
             f'↺ every shipped system feeds the next problem · measured at every hop</text>')
    p.append("</svg>")
    path = pathlib.Path(__file__).resolve().parent.parent / "assets" / "build-flow.svg"
    path.write_text("\n".join(p) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
