"""Insight design-system tokens for C4 diagrams.

Values come from the ``insight-diagram-design`` skill, section 4. Nothing here
is a preference: changing a hex value takes the output off brand. The light
skin is the only one C4 output uses, because codemap figures are read on a
white page (GitHub, Word, PDF).
"""

from __future__ import annotations

# --- semantic colour roles (light skin) --------------------------------------

PAPER = "#FFFFFF"
PAPER_2 = "#F5F5F5"
INK = "#3E332D"
MUTED = "#6B625C"
SOFT = "#8F8781"
RULE = "rgba(62,51,45,0.12)"
RULE_SOLID = "#BDBDBD"
ACCENT = "#D40E8C"
ACCENT_TINT = "rgba(212,14,140,0.08)"
LINK = "#5990F0"

# --- node treatments ---------------------------------------------------------
# kind -> (fill, stroke, dash or None, text colour)

TREATMENTS: dict[str, tuple[str, str, str | None, str]] = {
    "focal": (ACCENT_TINT, ACCENT, None, INK),
    "backend": (PAPER, INK, None, INK),
    "store": ("rgba(62,51,45,0.05)", MUTED, None, INK),
    "external": ("rgba(62,51,45,0.03)", "rgba(62,51,45,0.30)", None, INK),
    "input": ("rgba(107,98,92,0.10)", SOFT, None, INK),
    "optional": ("rgba(62,51,45,0.02)", "rgba(62,51,45,0.20)", "4,3", INK),
    "security": ("rgba(212,14,140,0.05)", "rgba(212,14,140,0.50)", "4,4", INK),
    "retired": (PAPER, "rgba(143,135,129,0.60)", "2,3", SOFT),
}

# Tag-box stroke/text use the node stroke at reduced alpha. Solid strokes get an
# rgba() twin so the 0.40 / 0.80 variants are expressible.
STROKE_RGB: dict[str, str] = {
    INK: "62,51,45",
    MUTED: "107,98,92",
    SOFT: "143,135,129",
    ACCENT: "212,14,140",
    LINK: "89,144,240",
}

# --- edge treatments ---------------------------------------------------------

EDGE_COLOURS = {"default": MUTED, "accent": ACCENT, "link": LINK}
EDGE_MARKERS = {"default": "arrow", "accent": "arrow-accent", "link": "arrow-link"}
EDGE_WIDTHS = {"default": 1.0, "accent": 1.2, "link": 1.0}

# --- typography --------------------------------------------------------------

SANS = "'Inter', 'Greycliff CF', Arial, sans-serif"
MONO = "'Geist Mono', ui-monospace, monospace"
SLAB = "'Roboto Slab', 'Klinic Slab', Georgia, serif"

FONTS_HREF = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600"
    "&family=Geist+Mono:wght@400;500;600&family=Roboto+Slab:wght@400&display=swap"
)

# --- type ramps --------------------------------------------------------------
# "standard" for documents, "presentation" for slides.

RAMPS = {
    "standard": {
        "title": 28,
        "node": 12,
        "sublabel": 9,
        "tag": 7,
        "arrow": 8,
        "node_h": 80,
        "icon_node_h": 96,
        "icon": 24,
        "min_gap": 24,
    },
    "presentation": {
        "title": 40,
        "node": 16,
        "sublabel": 12,
        "tag": 8,
        "arrow": 12,
        "node_h": 96,
        "icon_node_h": 112,
        "icon": 32,
        "min_gap": 40,
    },
}

# --- size presets ------------------------------------------------------------
# name -> (width, height, ramp). ``fit`` sizes itself from the content.

PRESETS = {
    "doc-inline": (960, 600, "standard"),
    "doc-wide": (1280, 720, "standard"),
    "slide-16x9": (1280, 720, "presentation"),
    "slide-4x3": (1024, 768, "presentation"),
    "print-a4-landscape": (1120, 792, "standard"),
    "fit": (None, None, "standard"),
}

# --- geometry ----------------------------------------------------------------

MARGIN = 40  # outer margin on every preset
RADIUS_NODE = 6
RADIUS_ZONE = 8
RADIUS_TAG = 2
ELBOW_R = 8  # every bend is a quarter arc at this radius
CHANNEL_STEP = 16  # >= 12px apart, on the 4px grid
CHANNEL_INSET = 24  # first channel's offset from a row edge
LEGEND_H = 60
NODE_W = 160  # default node width
NODE_GAP = 32  # default gap between nodes in a row
ZONE_HEADROOM = 32  # zone top sits this far above the first enclosed node
HOP_R = 8


def rgba(solid: str, alpha: float) -> str:
    """Return ``solid`` at ``alpha``, for the roles that need a faded twin."""
    if solid.startswith("rgba"):
        return solid
    rgb = STROKE_RGB.get(solid)
    if rgb is None:  # unknown solid colour: fall back to the opaque value
        return solid
    return f"rgba({rgb},{alpha:.2f})"


def snap(value: float) -> int:
    """Snap to the 4px grid, rounding up. Every coordinate must sit on it."""
    return int(-(-round(value) // 4) * 4)
