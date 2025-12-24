#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_fig04_scatter_p95_recalc_vs_orig.py

Compare p95_orig vs p95_recalc : scatter coloré par |Δp95|, encart histogramme,
optionnel encart zoom (--with-zoom). Title fontsize=15.

Usage example (recommandé) :

python zz-scripts/chapter10/plot_fig04_scatter_p95_recalc_vs_orig.py \
  --results zz-data/chapter10/10_results_global_scan.csv \
  --orig-col p95_20_300 --recalc-col p95_20_300_recalc \
  --out zz-figures/chapter10/10_fig_04_p95_comparison.png \
  --dpi 300 \
  --point-size 10 --alpha 0.7 --cmap viridis \
  --change-eps 1e-6 \
  --hist-x 0.60 --hist-y 0.18 --hist-scale 3.0 --bins 50

Pour le pipeline minimal, le script sait aussi travailler avec un seul
champ p95 (par ex. 'p95_rad') : il utilise alors la même colonne comme
“orig” et “recalc”, ce qui donne Δp95 = 0 mais garde la même esthétique.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import tempfile
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset

plt.rcParams.update(
    {
        "figure.autolayout": True,
        "figure.figsize": (10, 6),
        "axes.titlepad": 20,
        "axes.labelpad": 12,
        "savefig.bbox": "tight",
        "font.family": "serif",
    }
)


# ---------------------------------------------------------------------------
#  Utils
# ---------------------------------------------------------------------------


def detect_column(df: pd.DataFrame, hint: str | None, candidates: list[str]) -> str:
    """
    Détecte une colonne dans df :
    - si hint est fourni et existe, on le prend;
    - sinon on parcourt candidates;
    - sinon on fait une recherche par sous-chaîne (case-insensitive).
    """
    if hint and hint in df.columns:
        return hint

    # candidats exacts
    for c in candidates:
        if c in df.columns:
            return c

    # fallback substring match
    lowcols = [c.lower() for c in df.columns]
    for cand in candidates:
        lc = cand.lower()
        for i, col in enumerate(lowcols):
            if lc in col:
                return df.columns[i]

    raise KeyError(
        f"Aucune colonne trouvée parmi : {candidates} (hint={hint}, "
        f"colonnes présentes = {list(df.columns)})"
    )


def fmt_sci_power(v: float) -> tuple[float, int]:
    """
    Retourne (scaled_value, exp) avec v ≈ scaled_value * 10**exp.
    Utile pour mettre l'axe en "×10^exp".
    """
    if v == 0 or not np.isfinite(v):
        return 0.0, 0
    exp = int(np.floor(np.log10(abs(v))))
    scale = 10.0**exp
    return v / scale, exp


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_save(filepath: Path | str, fig, **savefig_kwargs) -> bool:
    """
    Sauvegarde fig en conservant le mtime si le PNG est identique.
    Retourne True si le fichier a changé, False sinon.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        with tempfile.NamedTemporaryFile(delete=False, suffix=path.suffix) as tmp:
            tmp_path = Path(tmp.name)
        try:
            fig.savefig(tmp_path, **savefig_kwargs)
            if _sha256(tmp_path) == _sha256(path):
                tmp_path.unlink()
                return False
            shutil.move(tmp_path, path)
            return True
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    fig.savefig(path, **savefig_kwargs)
    return True


# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument(
        "--results",
        default=None,
        help="CSV results (doit contenir les colonnes p95 orig/recalc ou au moins une colonne p95).",
    )
    p.add_argument(
        "--orig-col",
        default="p95_20_300",
        help="Nom de la colonne p95 'originale'. Auto-détection si absente.",
    )
    p.add_argument(
        "--recalc-col",
        default="p95_20_300_recalc",
        help="Nom de la colonne p95 'recalculée'. Auto-détection si absente.",
    )
    p.add_argument(
        "--out",
        default="zz-figures/chapter10/10_fig_04_p95_comparison.png",
        help="PNG de sortie",
    )
    p.add_argument("--dpi", type=int, default=300, help="DPI PNG")
    p.add_argument(
        "--point-size",
        type=float,
        default=10.0,
        help="Taille des marqueurs du scatter",
    )
    p.add_argument(
        "--alpha",
        type=float,
        default=0.7,
        help="Alpha des points du scatter",
    )
    p.add_argument(
        "--cmap",
        default="viridis",
        help="Colormap pour |Δp95|",
    )
    p.add_argument(
        "--change-eps",
        type=float,
        default=1e-6,
        help="Seuil pour considérer qu'un point a 'changé' (|Δ| > eps).",
    )

    # Inset zoom (optionnel)
    p.add_argument(
        "--with-zoom",
        action="store_true",
        help="Active l'encart zoom (sinon désactivé).",
    )
    p.add_argument(
        "--zoom-center-x",
        type=float,
        default=None,
        help="Centre X du zoom (unités data).",
    )
    p.add_argument(
        "--zoom-center-y",
        type=float,
        default=None,
        help="Centre Y du zoom (unités data).",
    )
    p.add_argument(
        "--zoom-w",
        type=float,
        default=0.45,
        help="Largeur de l'encart zoom (fraction fig).",
    )
    p.add_argument(
        "--zoom-h",
        type=float,
        default=0.10,
        help="Hauteur de l'encart zoom (fraction fig).",
    )

    # Histogramme (position identique à ta version originale)
    p.add_argument(
        "--hist-x",
        type=float,
        default=0.60,
        help="X (coords figure) de l'histogramme (plus petit = plus à gauche).",
    )
    p.add_argument(
        "--hist-y",
        type=float,
        default=0.18,
        help="Y (coords figure) de l'histogramme (plus grand = plus haut).",
    )
    p.add_argument(
        "--hist-scale",
        type=float,
        default=3.0,
        help="Facteur d'échelle de la taille de l'histogramme (1.0 = base).",
    )
    p.add_argument("--bins", type=int, default=50, help="Nombre de bins histogramme")

    p.add_argument(
        "--title",
        default="p95_20_300 comparison: original vs. recalculated (linear metric)",
        help="Figure title (fontsize=15).",
    )

    args = p.parse_args()

    # --- normalisation sortie : si '--out' est un nom nu -> redirige vers zz-figures/chapter10/ ---
    from pathlib import Path as _Path

    _outp = _Path(args.out)
    if _outp.parent == _Path("."):
        args.out = str(_Path("zz-figures/chapter10") / _outp.name)

    # Si --results non fourni (cas pipeline minimal), on prend le CSV standard
    if not args.results:
        args.results = "zz-data/chapter10/10_results_global_scan.csv"
        print(
            f"[INFO] --results non fourni ; utilisation par défaut de '{args.results}'."
        )

    # ------------------------------------------------------------------
    # Lecture + détection des colonnes
    # ------------------------------------------------------------------
    df = pd.read_csv(args.results)

    # Candidats pour l'original et le recalculé.
    # On inclut p95_rad pour le pipeline minimal (10_results_global_scan.csv).
    orig_candidates: list[str] = []
    if args.orig_col:
        orig_candidates.append(args.orig_col)
    orig_candidates += [
        "p95_20_300",
        "p95_20_300_circ",
        "p95",
        "p95_rad",
    ]

    recalc_candidates: list[str] = []
    if args.recalc_col:
        recalc_candidates.append(args.recalc_col)
    recalc_candidates += [
        "p95_20_300_recalc",
        "p95_20_300_circ",
        "p95_20_300",
        "p95",
        "p95_rad",
    ]

    orig_col = detect_column(df, args.orig_col, orig_candidates)
    recalc_col = detect_column(df, args.recalc_col, recalc_candidates)

    # ------------------------------------------------------------------
    # Extraction en évitant les problèmes si orig_col == recalc_col
    # ------------------------------------------------------------------
    s_orig = df[orig_col].astype(float)
    s_recalc = df[recalc_col].astype(float)

    mask = s_orig.notna() & s_recalc.notna()
    x = s_orig[mask].to_numpy()  # original
    y = s_recalc[mask].to_numpy()  # recalculé

    if x.size == 0:
        raise SystemExit("Aucun point non-NA trouvé dans les colonnes p95.")

    # ------------------------------------------------------------------
    # Δp95 et stats
    # ------------------------------------------------------------------
    delta = y - x
    abs_delta = np.abs(delta)

    N = len(x)
    mean_x = float(np.mean(x))
    mean_y = float(np.mean(y))
    mean_delta = float(np.mean(delta))
    med_delta = float(np.median(delta))
    std_delta = float(np.std(delta, ddof=0))
    p95_abs = float(np.percentile(abs_delta, 95))
    max_abs = float(np.max(abs_delta))

    n_changed = int(np.sum(abs_delta > args.change_eps))
    frac_changed = 100.0 * n_changed / float(N)

    # ------------------------------------------------------------------
    # Figure principale
    # ------------------------------------------------------------------
    plt.style.use("classic")
    fig, ax = plt.subplots(figsize=(10, 10))

    # Échelle pour la couleur : clip haut pour éviter de brûler la colormap
    if abs_delta.size == 0:
        vmax = 1.0
    else:
        vmax = float(np.percentile(abs_delta, 99.9))
        if vmax <= 0.0:
            vmax = float(np.max(abs_delta))
    if vmax <= 0.0 or not np.isfinite(vmax):
        vmax = 1.0

    sc = ax.scatter(
        x,
        y,
        c=abs_delta,
        s=args.point_size,
        alpha=args.alpha,
        cmap=args.cmap,
        edgecolor="none",
        vmin=0.0,
        vmax=vmax,
        zorder=2,
    )

    # diagonale y = x
    lo = float(min(np.min(x), np.min(y)))
    hi = float(max(np.max(x), np.max(y)))
    ax.plot([lo, hi], [lo, hi], color="gray", linestyle="--", linewidth=1.0, zorder=1)

    ax.set_xlabel(f"{orig_col} [rad]")
    ax.set_ylabel(f"{recalc_col} [rad]")
    ax.set_title(args.title, fontsize=15)

    extend = "max" if np.max(abs_delta) > vmax else "neither"
    cbar = fig.colorbar(sc, ax=ax, extend=extend, pad=0.02)
    cbar.set_label(r"$|\Delta p95|$ [rad]")

    # ------------------------------------------------------------------
    # Boîte de stats (en haut à gauche)
    # ------------------------------------------------------------------
    stats_lines = [
        f"N = {N}",
        f"mean(orig)   = {mean_x:.3f} rad",
        f"mean(recalc) = {mean_y:.3f} rad",
        "Δ = recalc - orig :",
        f"  mean   = {mean_delta:.3e}",
        f"  median = {med_delta:.3e}",
        f"  std    = {std_delta:.3e}",
        f"p95(|Δ|) = {p95_abs:.3e} rad",
        f"max |Δ|  = {max_abs:.3e} rad",
        f"N_changed (|Δ| > {args.change_eps:g}) = {n_changed} ({frac_changed:.2f}%)",
    ]
    stats_text = "\n".join(stats_lines)
    bbox = dict(boxstyle="round", fc="white", ec="black", lw=1, alpha=0.95)
    ax.text(
        0.02,
        0.98,
        stats_text,
        transform=ax.transAxes,
        fontsize=9,
        va="top",
        ha="left",
        bbox=bbox,
        zorder=10,
    )

    # ------------------------------------------------------------------
    # Histogramme de |Δp95|
    # ------------------------------------------------------------------
    hist_base_w = 0.18
    hist_base_h = 0.14
    hist_w = hist_base_w * args.hist_scale
    hist_h = hist_base_h * args.hist_scale

    hist_ax = inset_axes(
        ax,
        width=f"{hist_w * 100}%",
        height=f"{hist_h * 100}%",
        bbox_to_anchor=(args.hist_x - 0.1, args.hist_y, hist_w, hist_h),
        bbox_transform=fig.transFigure,
        loc="lower left",
        borderpad=1.0,
    )

    max_abs = float(np.max(abs_delta)) if abs_delta.size else 0.0
    _, exp = fmt_sci_power(max_abs if max_abs > 0 else 1.0)
    scale = 10.0**exp if max_abs > 0 else 1.0

    hist_vals = abs_delta / scale
    hist_ax.hist(hist_vals, bins=args.bins, color="tab:blue", edgecolor="black")
    hist_ax.axvline(0.0, color="red", linewidth=2.0)

    hist_ax.set_title("|Δp95|", fontsize=9)
    hist_ax.set_xlabel(f"× 10^{{{exp}}}", fontsize=8)
    hist_ax.tick_params(axis="both", which="major", labelsize=8)

    # ------------------------------------------------------------------
    # Zoom optionnel
    # ------------------------------------------------------------------
    if args.with_zoom:
        if args.zoom_center_x is None:
            zx_center = 0.5 * (lo + hi)
        else:
            zx_center = args.zoom_center_x
        if args.zoom_center_y is None:
            zy_center = zx_center
        else:
            zy_center = args.zoom_center_y

        dx = 0.06 * (hi - lo) if (hi - lo) > 0 else 0.1
        dy = dx
        zx0, zx1 = zx_center - dx / 2.0, zx_center + dx / 2.0
        zy0, zy1 = zy_center - dy / 2.0, zy_center + dy / 2.0

        inset_w = args.zoom_w
        inset_h = args.zoom_h
        inz = inset_axes(
            ax,
            width=f"{inset_w * 100}%",
            height=f"{inset_h * 100}%",
            bbox_to_anchor=(0.42, 0.62, inset_w, inset_h),
            bbox_transform=fig.transFigure,
            loc="lower left",
            borderpad=1.0,
        )

        inz.scatter(
            x,
            y,
            c=abs_delta,
            s=max(1.0, args.point_size / 2.0),
            alpha=min(1.0, args.alpha + 0.1),
            cmap=args.cmap,
            edgecolor="none",
            vmin=0.0,
            vmax=vmax,
        )
        inz.plot([zx0, zx1], [zx0, zx1], color="gray", linestyle="--", linewidth=0.8)
        inz.set_xlim(zx0, zx1)
        inz.set_ylim(zy0, zy1)
        inz.set_title("zoom", fontsize=8)
        mark_inset(ax, inz, loc1=2, loc2=4, fc="none", ec="0.5", lw=0.8)

    # ------------------------------------------------------------------
    # Pied de figure
    # ------------------------------------------------------------------
    foot = textwrap.dedent(
        r"""
        $\Delta p95 = p95_{\mathrm{recalc}} - p95_{\mathrm{orig}}$.
        Couleur = $|\Delta p95|$. Histogramme en encart (position et taille configurables).
        """
    ).strip()
    fig.text(0.5, 0.02, foot, ha="center", fontsize=9)

    plt.tight_layout(rect=[0, 0.04, 1, 0.98])
    updated = safe_save(args.out, fig, dpi=args.dpi)
    status = "Wrote" if updated else "Unchanged (identique)"
    print(f"{status}: {args.out}")


if __name__ == "__main__":
    main()
