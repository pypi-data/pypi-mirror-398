#!/usr/bin/env python3
"""
regen_fig05_using_circp95.py

Figure 05 : Histogramme + CDF des p95 recalculés en métrique circulaire.

"""

from __future__ import annotations

import argparse
import textwrap

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from zz_tools import common_io as ci

from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset


# ---------- utils ----------
def detect_p95_column(df: pd.DataFrame) -> str:
    candidates = [
        "p95_20_300_recalc",
        "p95_20_300_circ",
        "p95_20_300_recalced",
        "p95_20_300",
        "p95_circ",
        "p95_recalc",
    ]
    for c in candidates:
        if c in df.columns:
            return c
    for c in df.columns:
        if "p95" in c.lower():
            return c
    raise KeyError("Aucune colonne 'p95' détectée dans le CSV results.")


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--results", required=True, help="CSV avec p95 circulaire recalculé"
    )
    ap.add_argument(
        "--out", default="fig_05_hist_cdf_metrics.png", help="PNG de sortie"
    )
    ap.add_argument(
        "--ref-p95",
        type=float,
        default=0.7104087123286049,
        help="p95 de référence [rad]",
    )
    ap.add_argument("--bins", type=int, default=50, help="Nb de bacs histogramme")
    ap.add_argument("--dpi", type=int, default=150, help="DPI du PNG")
    # position et fenêtre du zoom (centre + demi-étendues)
    ap.add_argument("--zoom-x", type=float, default=3.0, help="centre X du zoom (rad)")
    ap.add_argument(
        "--zoom-y", type=float, default=35.0, help="centre Y du zoom (counts)"
    )
    ap.add_argument(
        "--zoom-dx", type=float, default=0.30, help="demi-largeur X du zoom (rad)"
    )
    ap.add_argument(
        "--zoom-dy", type=float, default=30.0, help="demi-hauteur Y du zoom (counts)"
    )
    # taille du panneau de zoom (fraction de l’axe)
    ap.add_argument(
        "--zoom-w", type=float, default=0.35, help="largeur du zoom (fraction)"
    )
    ap.add_argument(
        "--zoom-h", type=float, default=0.25, help="hauteur du zoom (fraction)"
    )
    args = ap.parse_args()

    # --- lecture & colonne p95 ---
    df = pd.read_csv(args.results)
    df = ci.ensure_fig02_cols(df)

    p95_col = detect_p95_column(df)
    p95 = df[p95_col].dropna().astype(float).values

    # Heuristique : si colonne "originale" dispo, compter les corrections unwrap
    wrapped_corrected = None
    for cand in ("p95_20_300", "p95_raw", "p95_orig", "p95_20_300_raw"):
        if cand in df.columns and cand != p95_col:
            diff = df[[cand, p95_col]].dropna().astype(float)
            wrapped_corrected = int((np.abs(diff[cand] - diff[p95_col]) > 1e-6).sum())
            break

    # --- stats ---
    N = p95.size
    mean, median, std = (
        float(np.mean(p95)),
        float(np.median(p95)),
        float(np.std(p95, ddof=0)),
    )
    n_below = int((p95 < args.ref_p95).sum())
    frac_below = n_below / max(1, N)

    # --- figure ---
    plt.style.use("classic")
    fig, ax = plt.subplots(figsize=(14, 6))

    # Histogramme (counts)
    counts, bins, patches = ax.hist(p95, bins=args.bins, alpha=0.7, edgecolor="k")
    ax.set_ylabel("Effectifs")
    ax.set_xlabel("p95_20_300_recalc [rad]")

    # CDF empirique (axe droit)
    ax2 = ax.twinx()
    sorted_p = np.sort(p95)
    ecdf = np.arange(1, N + 1) / N
    (cdf_line,) = ax2.plot(sorted_p, ecdf, lw=2)
    ax2.set_ylabel("CDF empirique")
    ax2.set_ylim(0.0, 1.02)

    # Ligne verticale de référence
    ax.axvline(args.ref_p95, color="crimson", linestyle="--", lw=2)
    ax.text(
        args.ref_p95,
        ax.get_ylim()[1] * 0.45,
        f"ref = {args.ref_p95:.4f} rad",
        color="crimson",
        rotation=90,
        va="center",
        ha="right",
        fontsize=10,
    )

    # Boîte de stats (haut-gauche)
    stat_lines = [
        f"N = {N}",
        f"mean = {mean:.3f}",
        f"median = {median:.3f}",
        f"std = {std:.3f}",
    ]
    if wrapped_corrected is not None:
        stat_lines.append(f"wrapped_corrected = {wrapped_corrected}")
    stat_lines.append(f"p(P95 < ref) = {frac_below:.3f} (n={n_below})")
    stat_text = "\n".join(stat_lines)
    ax.text(
        0.02,
        0.98,
        stat_text,
        transform=ax.transAxes,
        fontsize=10,
        va="top",
        ha="left",
        bbox=dict(boxstyle="round", fc="white", ec="black", lw=1, alpha=0.95),
    )

    # Petite légende (sous la boîte de stats)
    handles = []
    if len(patches) > 0:
        handles.append(patches[0])
    else:
        from matplotlib.patches import Rectangle

        handles.append(
            Rectangle((0, 0), 1, 1, facecolor="C0", edgecolor="k", alpha=0.7)
        )
    proxy_cdf = mlines.Line2D([], [], color=cdf_line.get_color(), lw=2)
    proxy_ref = mlines.Line2D([], [], color="crimson", linestyle="--", lw=2)
    handles += [proxy_cdf, proxy_ref]
    labels = ["Histogramme (effectifs)", "CDF empirique", "p95 réf"]
    ax.legend(
        handles,
        labels,
        loc="upper left",
        bbox_to_anchor=(0.02, 0.72),
        frameon=True,
        fontsize=10,
    )

    # Inset zoom
    inset_ax = inset_axes(
        ax,
        width=f"{args.zoom_w * 100:.0f}%",
        height=f"{args.zoom_h * 100:.0f}%",
        loc="center",
        borderpad=1.0,
    )
    x0, x1 = args.zoom_x - args.zoom_dx, args.zoom_x + args.zoom_dx
    _y0_user, _y1_user = max(0, args.zoom_y - args.zoom_dy), args.zoom_y + args.zoom_dy
    mask_x = (p95 >= x0) & (p95 <= x1)
    data_inset = p95[mask_x] if mask_x.sum() >= 5 else p95
    inset_counts, inset_bins, _ = inset_ax.hist(
        data_inset, bins=min(args.bins, 30), alpha=0.9, edgecolor="k"
    )
    ymax_auto = (np.max(inset_counts) if inset_counts.size else 1.0) * 1.10
    y0 = 0.0
    y1 = max(float(args.zoom_y + args.zoom_dy), ymax_auto)
    inset_ax.set_xlim(x0, x1)
    inset_ax.set_ylim(y0, y1)
    inset_ax.set_title("zoom", fontsize=10)
    inset_ax.tick_params(axis="both", which="major", labelsize=8)
    try:
        mark_inset(ax, inset_ax, loc1=2, loc2=4, fc="none", ec="0.5", lw=0.8)
    except Exception:
        pass

    ax.set_title("Distribution de p95_20_300 (MC global)", fontsize=15)
    foot = textwrap.fill(
        (
            r"Métrique : distance circulaire (mod $2\pi$). "
            r"Définition : p95 = $95^{\mathrm{e}}$ centile de $|\Delta\phi(f)|$ pour $f\in[20,300]\ \mathrm{Hz}$. "
            r"Corrections : sauts de branchement corrigés, "
            rf"$N_{{\mathrm{{wrapped\_corrected}}}} = {wrapped_corrected if wrapped_corrected is not None else 0}$. "
            r"Comparaison : "
            rf"$p(\mathrm{{p95}}<\mathrm{{p95_{{ref}}}}) = {frac_below:.3f}$ "
            rf"(n = {n_below})."
        ),
        width=180,
    )
    fig.subplots_adjust(left=0.04, right=0.98, bottom=0.06, top=0.96)
    fig.text(0.5, 0.04, foot, ha="center", va="bottom", fontsize=9)

    fig.savefig(args.out, dpi=args.dpi)
    print(f"Wrote : {args.out}")


if __name__ == "__main__":
    main()
