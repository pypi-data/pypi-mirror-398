"""
MCGT common figure styles (opt-in).
Usage:
    import zz-scripts._common.style  # via postparse loader
    style.apply(theme="paper")       # or "talk", "mono"
"""

from __future__ import annotations
import matplotlib

_THEMES = {
    "paper": dict(
        figure_dpi=150,
        font_size=9,
        font_family="DejaVu Sans",
        axes_linewidth=0.8,
        grid=True,
    ),
    "talk": dict(
        figure_dpi=150,
        font_size=12,
        font_family="DejaVu Sans",
        axes_linewidth=1.0,
        grid=True,
    ),
    "mono": dict(
        figure_dpi=150,
        font_size=9,
        font_family="DejaVu Sans Mono",
        axes_linewidth=0.8,
        grid=True,
    ),
}


def apply(theme: str | None) -> None:
    if not theme or theme == "none":
        return
    t = _THEMES.get(theme, _THEMES["paper"])
    rc = matplotlib.rcParams
    # taille police
    rc["font.size"] = t["font_size"]
    rc["font.family"] = [t["font_family"]]
    # traits axes
    rc["axes.linewidth"] = t["axes_linewidth"]
    rc["xtick.major.width"] = t["axes_linewidth"]
    rc["ytick.major.width"] = t["axes_linewidth"]
    # DPI figure par défaut (ne force pas savefig.*)
    rc["figure.dpi"] = t["figure_dpi"]
    # grille légère
    rc["axes.grid"] = bool(t["grid"])
    rc["grid.linestyle"] = ":"
    rc["grid.linewidth"] = 0.6
