"""Tiny shared SVG pieces so every generated card looks like one family."""
from xml.sax.saxutils import escape

BG = "#0b1020"
BAR = "#111833"
VIOLET = "#a78bfa"
CYAN = "#22d3ee"
PINK = "#f472b6"
TEXT = "#c9d1e6"
MUTED = "#64748b"
GREEN = "#22c55e"

MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "ui-sans-serif, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def esc(s) -> str:
    return escape(str(s))


def terminal_frame(w: int, h: int, title: str, gid: str = "frameStroke") -> str:
    """Rounded window with traffic-light dots and a title bar (same style as terminal.svg)."""
    return f"""<defs><linearGradient id="{gid}" x1="0" x2="1"><stop offset="0" stop-color="{VIOLET}"/><stop offset=".5" stop-color="{CYAN}"/><stop offset="1" stop-color="{PINK}"/></linearGradient></defs>
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="18" fill="{BG}" stroke="url(#{gid})" stroke-opacity=".6" stroke-width="1.5"/>
<rect x="1" y="1" width="{w-2}" height="44" rx="18" fill="{BAR}"/><rect x="1" y="28" width="{w-2}" height="17" fill="{BAR}"/>
<circle cx="28" cy="23" r="7" fill="#ff5f57"/><circle cx="52" cy="23" r="7" fill="#febc2e"/><circle cx="76" cy="23" r="7" fill="#28c840"/>
<text x="{w/2:g}" y="28" text-anchor="middle" font-family="{MONO}" font-size="14" fill="{MUTED}">{esc(title)}</text>"""
