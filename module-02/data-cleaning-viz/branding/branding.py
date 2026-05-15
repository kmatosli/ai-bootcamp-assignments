"""Caduceus brand system — slim subset for this deliverable.

Single source of truth for colors, fonts, and matplotlib styling. The full
brand module is in the main Caduceus repo at data-foundation/branding/.
This is a stripped-down copy bundled with the submission so the script runs
standalone without the parent repo.
"""
from __future__ import annotations
import matplotlib.pyplot as plt


# ──────────────────────────────────────────────────────────────────────────────
# Colors
# ──────────────────────────────────────────────────────────────────────────────

COLORS: dict[str, str] = {
    "ink_slate":      "#2C333E",
    "classic_blue":   "#0F4C81",
    "provence":       "#6889C0",
    "baby_blue":      "#B3CDE0",
    "monument":       "#7C8488",
    "stucco":         "#A5968C",
    "off_white":      "#F7F8FA",
    "light_grey":     "#E5E7EB",
    "peach_quartz":   "#F5B9A0",
    "cornhusk":       "#F2E0B2",
    "signal_teal":    "#0D9488",
    "signal_amber":   "#F59E0B",
}


# Ticker → brand color (Phase 1 universe assignments)
TICKER_COLORS: dict[str, str] = {
    "LLY":  COLORS["classic_blue"],
    "JNJ":  COLORS["ink_slate"],
    "ABBV": COLORS["provence"],
    "MRK":  COLORS["signal_teal"],
    "PFE":  COLORS["monument"],
    "BMY":  COLORS["stucco"],
    "AMGN": COLORS["signal_amber"],
    "GILD": COLORS["peach_quartz"],
}


# ──────────────────────────────────────────────────────────────────────────────
# Fonts
# ──────────────────────────────────────────────────────────────────────────────

#: Brand fonts. If Inter / IBM Plex Serif aren't installed, matplotlib falls
#: back to system defaults — chart still renders, just without the brand
#: typography.
FONTS: dict[str, str] = {
    "sans":  "Inter",
    "serif": "IBM Plex Serif",
}

FONT_WEIGHTS: dict[str, str] = {
    "title":    "semibold",
    "emphasis": "semibold",
    "body":     "regular",
}


# ──────────────────────────────────────────────────────────────────────────────
# Style application
# ──────────────────────────────────────────────────────────────────────────────

def apply_matplotlib_style() -> None:
    """Apply brand defaults to matplotlib. Call once at top of any chart script."""
    plt.rcParams.update({
        "figure.facecolor":   COLORS["off_white"],
        "axes.facecolor":     COLORS["off_white"],
        "axes.edgecolor":     COLORS["monument"],
        "axes.labelcolor":    COLORS["ink_slate"],
        "axes.titlesize":     12,
        "axes.titleweight":   FONT_WEIGHTS["title"],
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "axes.grid":          False,
        "xtick.color":        COLORS["ink_slate"],
        "ytick.color":        COLORS["ink_slate"],
        "text.color":         COLORS["ink_slate"],
        "font.family":        ["Inter", "DejaVu Sans", "sans-serif"],
        "font.size":          9.5,
        "legend.frameon":     False,
    })


def annotation_box_style() -> dict:
    """Style dict for inline analysis annotations on chart panels."""
    return dict(
        boxstyle="round,pad=0.4",
        facecolor=COLORS["off_white"],
        edgecolor=COLORS["light_grey"],
        linewidth=0.8,
        alpha=0.95,
    )
