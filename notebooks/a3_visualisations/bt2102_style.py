"""
bt2102_style.py - chart conventions from BT2102 (Data Visualisation, DV Methods, Storytelling lectures).

Rules this module enforces:
  * Title = the takeaway message (not a description). Subtitle = metric + unit only.
  * One highlight colour for the story; grey for context. Red only for negative/bad.
  * Quantities by lightness of one hue (sequential), never by rainbow hues.
  * Sans-serif, consistent fonts. Minimal ink: no top/right spines, light y-grid only.
  * Bars/areas start at zero. Lines and dot plots may not.
  * Label data directly (no legend if possible); labels must not collide (see spread_labels).
  * Small source line bottom-left.

Usage:
    import bt2102_style as bs
    bs.setup()
    fig, ax = bs.new_chart("Fringe districts grew fastest", "Annual price growth, 2012-2017 (%)")
    ...
    bs.finish(fig, "charts/x.png", source="Lianjia, 2012-2017")
"""
import glob
import os

import matplotlib.pyplot as plt
from matplotlib import font_manager

# Tableau-10-style palette (familiar to the class, colour-blind friendly)
HIGHLIGHT = "#4E79A7"   # the story
HIGHLIGHT_2 = "#F28E2B"  # second story element, use sparingly
NEGATIVE = "#E15759"    # bad / negative only
CONTEXT = "#BAB0AC"     # everything else
FADE = "#E6E6E6"        # de-emphasised marks in a "spotlight" variant
FADE_TEXT = "#C4C4C4"   # de-emphasised labels
INK = "#333333"
MUTED = "#7A7A7A"
GRID = "#E6E6E6"
SEQ_BLUES = ["#DCE6F0", "#A9C1DB", "#6F97C2", "#4E79A7", "#2B4F7A"]  # lightness ramp

FIGSIZE = (10, 6)   # 1500x900 px at 150 dpi; fits a slide's chart panel
DPI = 150

_here = os.path.dirname(os.path.abspath(__file__))
_FONT_DIR = next((p for p in [os.path.join(_here, "..", "assets", "fonts"), os.path.join(_here, "fonts")] if os.path.isdir(p)), _here)


def setup():
    """Register Inter (bundled) and set clean rcParams. Falls back to DejaVu Sans."""
    for f in glob.glob(os.path.join(_FONT_DIR, "*.ttf")):
        font_manager.fontManager.addfont(f)
    has_inter = any(f.name == "Inter" for f in font_manager.fontManager.ttflist)
    plt.rcParams.update({
        "font.family": "Inter" if has_inter else "DejaVu Sans",
        "font.size": 13,
        "text.color": INK, "axes.labelcolor": INK,
        "axes.edgecolor": "#BBBBBB", "axes.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.labelsize": 12, "ytick.labelsize": 12,
        "axes.labelsize": 13,
        "axes.grid": False,
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "legend.frameon": False,
    })


def new_chart(title, subtitle=None, figsize=FIGSIZE, rect=(0.09, 0.15, 0.86, 0.66)):
    """Figure with a takeaway title + short subtitle. Returns (fig, ax)."""
    fig = plt.figure(figsize=figsize, dpi=DPI)
    fig.text(0.04, 0.955, title, fontsize=21, fontweight="bold", va="top", color=INK)
    if subtitle:
        fig.text(0.04, 0.885, subtitle, fontsize=13.5, va="top", color=MUTED)
    ax = fig.add_axes(rect)
    return fig, ax


def ygrid(ax):
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def xgrid(ax):
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def spread_labels(values, min_gap):
    """Return y-positions for end-of-line labels so no two are closer than min_gap.
    Keeps order, pushes apart symmetrically."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    pos = [values[i] for i in order]
    for _ in range(200):
        moved = False
        for k in range(1, len(pos)):
            gap = pos[k] - pos[k - 1]
            if gap < min_gap:
                shift = (min_gap - gap) / 2
                pos[k - 1] -= shift
                pos[k] += shift
                moved = True
        if not moved:
            break
    out = [0] * len(values)
    for k, i in enumerate(order):
        out[i] = pos[k]
    return out


def finish(fig, path, source=None):
    if source:
        fig.text(0.04, 0.025, f"Source: {source}", fontsize=10, color=MUTED, va="bottom")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path
