#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_fig06_residual_map.py  —  Figure 6 (pipeline minimal CH10)

- Carte hexbin des résidus sur (m1,m2).
- Mode "dp95" (par défaut) :
    * si colonnes "orig" + "recalc" dispo -> Δp95 = p95_recalc - p95_orig
    * sinon : résidu centré = p95_metric - median(p95_metric)
- Mode "dphi" (optionnel, manuel) :
    * Δφ = wrap(φ_MCGT - φ_ref) dans (-π, π].

- Échelle colorbar en ×10^exp rad (defaut exp=-7).
- Inserts à droite : Counts (par cellule) + histogramme global (avec stats).
- Deux lignes de footer : échelle / stats globales & N_active.

Compatible avec :
  * ancien CSV : zz-data/chapitre10/10_mc_results.circ.csv
  * nouveau CSV minimal : zz-data/chapter10/10_results_global_scan.csv

Usage typique (ancien jeu de données) :
  python zz-scripts/chapter10/plot_fig06_residual_map.py \
    --results zz-data/chapter10/10_mc_results.circ.csv \
    --metric dp95 --abs \
    --m1-col m1 --m2-col m2 \
    --orig-col p95_20_300 --recalc-col p95_20_300_recalc \
    --out zz-figures/chapter10/10_fig_06_residual_map.png

Dans le pipeline minimal, le script est appelé sans arguments et
utilise par défaut :
    results = zz-data/chapter10/10_results_global_scan.csv
    metric  = dp95 (absolu)
"""

from __future__ import annotations


import argparse
import hashlib
import json
import os
import shutil
import tempfile
from typing import Tuple
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib import colors

plt.rcParams.update(
    {
        "figure.figsize": (10, 6),
        "axes.titlepad": 20,
        "axes.labelpad": 12,
        "savefig.bbox": "tight",
        "font.family": "serif",
    }
)


# ----------------------------------------------------------------------
# utilitaires
# ----------------------------------------------------------------------
def wrap_pi(x: np.ndarray) -> np.ndarray:
    """Ramène les angles en radians dans (-π, π]."""
    return (x + np.pi) % (2 * np.pi) - np.pi


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_save(filepath: Path | str, fig, **savefig_kwargs) -> bool:
    """
    Sauvegarde fig en conservant le mtime si le PNG généré est identique.
    Retourne True si le fichier a été mis à jour, False sinon.
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


def detect_column(df: pd.DataFrame, candidates) -> str:
    """
    Trouve une colonne par nom exact ou par inclusion insensible à la casse.

    candidates peut être une liste de strings ou une string unique.
    """
    if isinstance(candidates, str):
        candidates = [candidates]
    # exact match d'abord
    for cand in candidates:
        if cand and cand in df.columns:
            return cand
    # substring match ensuite
    lowcols = [c.lower() for c in df.columns]
    for cand in candidates:
        if not cand:
            continue
        lc = cand.lower()
        for i, col in enumerate(lowcols):
            if lc == col or lc in col:
                return df.columns[i]
    raise KeyError(
        f"Impossible de trouver l'une des colonnes : {candidates} (colonnes présentes : {list(df.columns)})"
    )


def build_dp95_metric(
    df: pd.DataFrame,
    orig_hint: str | None,
    recalc_hint: str | None,
) -> Tuple[np.ndarray, str, str, str]:
    """
    Construit le vecteur de métrique pour 'dp95'.

    Retourne:
      metric_raw  : np.ndarray (en rad)
      desc_mode   : str  ("recalc-orig" ou "centered")
      orig_used   : str ou "" (nom de colonne, éventuellement vide)
      recalc_used : str (nom de colonne utilisée)
    """
    # candidats "origine"
    orig_candidates = [
        orig_hint,
        "p95_20_300",
        "p95",
        "p95_raw",
        "p95_orig",
        "p95_20_300_raw",
    ]
    # candidats "recalc"
    recalc_candidates = [
        recalc_hint,
        "p95_20_300_recalc",
        "p95_recalc",
        "p95_circ",
        "p95_rad",  # format global_scan
        "p95",
    ]

    orig_col = None
    for c in orig_candidates:
        if c and c in df.columns:
            orig_col = c
            break

    recalc_col = None
    for c in recalc_candidates:
        if c and c in df.columns:
            recalc_col = c
            break

    if recalc_col is None:
        raise KeyError(
            "Impossible de trouver une colonne 'p95' recalculée. "
            f"Candidats testés : {recalc_candidates}. Colonnes: {list(df.columns)}"
        )

    if orig_col is not None and orig_col != recalc_col:
        # vrai Δp95 = recalc - orig
        raw = df[recalc_col].astype(float).values - df[orig_col].astype(float).values
        desc = "recalc-orig"
        orig_used = orig_col
    else:
        # on n'a qu'une métrique p95 → on centre par la médiane
        vals = df[recalc_col].astype(float).values
        raw = vals - float(np.median(vals))
        desc = "centered (p95 - median(p95))"
        orig_used = ""

    return raw, desc, orig_used, recalc_col


def build_dphi_metric(
    df: pd.DataFrame,
    phi_ref_hint: str | None,
    phi_mcgt_hint: str | None,
) -> Tuple[np.ndarray, str, str, str]:
    """
    Construit Δφ = wrap(phi_mcgt - phi_ref).

    Si les colonnes manquent, lève une erreur explicite.
    """
    phi_ref_candidates = [
        phi_ref_hint,
        "phi_ref_fpeak",
        "phi_ref",
        "phi_ref_f_peak",
    ]
    phi_mcgt_candidates = [
        phi_mcgt_hint,
        "phi_mcgt_fpeak",
        "phi_mcgt",
        "phi_mcg_at_fpeak",
    ]

    phi_ref_col = detect_column(df, phi_ref_candidates)
    phi_mcgt_col = detect_column(df, phi_mcgt_candidates)

    ref = df[phi_ref_col].astype(float).values
    mcg = df[phi_mcgt_col].astype(float).values
    raw = wrap_pi(mcg - ref)
    desc = "wrap(phi_mcgt - phi_ref)"
    return raw, desc, phi_ref_col, phi_mcgt_col


# ----------------------------------------------------------------------
# script principal
# ----------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument(
        "--results",
        default=None,
        help=(
            "CSV d'entrée. "
            "Par défaut (pipeline minimal) : zz-data/chapter10/10_results_global_scan.csv"
        ),
    )
    ap.add_argument(
        "--metric",
        choices=["dp95", "dphi"],
        default="dp95",
        help="Type de métrique à cartographier.",
    )
    ap.add_argument(
        "--abs",
        action="store_true",
        help="Prendre la valeur absolue de la métrique.",
    )
    ap.add_argument("--m1-col", default="m1", help="Nom de colonne pour m1.")
    ap.add_argument("--m2-col", default="m2", help="Nom de colonne pour m2.")
    ap.add_argument(
        "--orig-col",
        default="p95_20_300",
        help="Colonne p95 originale (pour metric=dp95).",
    )
    ap.add_argument(
        "--recalc-col",
        default="p95_20_300_recalc",
        help="Colonne p95 recalculée (pour metric=dp95).",
    )
    ap.add_argument(
        "--phi-ref-col",
        default=None,
        help="Colonne phi_ref (pour metric=dphi).",
    )
    ap.add_argument(
        "--phi-mcgt-col",
        default=None,
        help="Colonne phi_mcgt (pour metric=dphi).",
    )
    ap.add_argument(
        "--gridsize",
        type=int,
        default=20,
        help="Taille de la grille hexbin.",
    )
    ap.add_argument(
        "--mincnt",
        type=int,
        default=3,
        help="Masque les hexagones avec nb < mincnt.",
    )
    ap.add_argument("--cmap", default="viridis", help="Colormap principale.")
    ap.add_argument(
        "--vclip",
        default="1,99",
        help="Percentiles pour vmin,vmax (ex: '1,99').",
    )
    ap.add_argument(
        "--scale-exp",
        type=int,
        default=-7,
        help="Exposant pour l'échelle ×10^exp rad.",
    )
    ap.add_argument(
        "--threshold",
        type=float,
        default=1e-6,
        help="Seuil pour fraction |metric|>threshold [rad].",
    )
    ap.add_argument(
        "--figsize",
        default="15,9",
        help="Largeur,hauteur en pouces (ex: '15,9').",
    )
    ap.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="DPI de sortie.",
    )
    ap.add_argument(
        "--out",
        default="zz-figures/chapter10/10_fig_06_residual_map.png",
        help="PNG de sortie.",
    )
    ap.add_argument(
        "--manifest",
        action="store_true",
        help="Écrit un petit JSON manifest à côté de la figure.",
    )
    args = ap.parse_args()
    # --- normalisation sortie : si '--out' est un nom nu -> redirige vers zz-figures/chapter10/ ---
    outp = Path(args.out)
    if outp.parent == Path("."):
        outp = Path("zz-figures/chapter10") / outp.name
    outp.parent.mkdir(parents=True, exist_ok=True)
    args.out = str(outp)

    # Fichier par défaut si non fourni (cas pipeline minimal)
    if args.results is None:
        args.results = "zz-data/chapter10/10_results_global_scan.csv"
        print(
            f"[INFO] --results non fourni ; utilisation par défaut de '{args.results}'."
        )

    # ------------------------------------------------------------------ data
    df = pd.read_csv(args.results)
    if args.m1_col not in df.columns or args.m2_col not in df.columns:
        raise KeyError(
            f"Colonnes {args.m1_col!r} et {args.m2_col!r} requises dans {args.results} "
            f"(colonnes présentes : {list(df.columns)})"
        )

    df = df.dropna(subset=[args.m1_col, args.m2_col])
    x = df[args.m1_col].astype(float).values
    y = df[args.m2_col].astype(float).values
    N = len(df)
    rng = np.random.default_rng(0)
    if np.std(x) < 1e-4:
        x = x + rng.normal(0, 0.10, size=len(x))
    if np.std(y) < 1e-4:
        y = y + rng.normal(0, 0.10, size=len(y))

    # ---------------------------------------------------------------- metric
    if args.metric == "dp95":
        raw_metric, desc_mode, orig_used, recalc_used = build_dp95_metric(
            df, args.orig_col, args.recalc_col
        )
        metric_name_latex = r"\Delta p_{95}"
    else:  # dphi
        raw_metric, desc_mode, phi_ref_used, phi_mcgt_used = build_dphi_metric(
            df, args.phi_ref_col, args.phi_mcgt_col
        )
        metric_name_latex = r"\Delta \phi"

    # aligner sur x,y (au cas où)
    raw_metric = np.asarray(raw_metric, dtype=float)
    if raw_metric.shape[0] != N:
        raise ValueError(
            f"Taille métrique ({raw_metric.shape[0]}) différente de N={N}."
        )

    if args.abs:
        raw = np.abs(raw_metric)
        metric_label = rf"|{metric_name_latex}|"
    else:
        raw = raw_metric
        metric_label = metric_name_latex

    # Pré-scaling pour l'affichage : valeurs en unités “×10^exp rad”
    scale_factor = 10.0**args.scale_exp
    scaled = raw / scale_factor

    # vmin/vmax via percentiles sur *scaled*
    p_lo, p_hi = [float(t) for t in args.vclip.split(",")]
    vmin = float(np.percentile(scaled, p_lo))
    vmax = float(np.percentile(scaled, p_hi))

    # Stats globales (sur scaled) + fraction > threshold (non-scalé)
    med = float(np.median(scaled))
    mean = float(np.mean(scaled))
    std = float(np.std(scaled, ddof=0))
    p95 = float(np.percentile(scaled, 95.0))
    frac_over = float(np.mean(np.abs(raw_metric) > args.threshold))

    # ------------------------------ figure & axes ---------------------------
    fig_w, fig_h = [float(s) for s in args.figsize.split(",")]
    plt.style.use("classic")
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=args.dpi)

    # Axes : carte principale, colorbar et inserts à droite
    ax_main = fig.add_axes([0.07, 0.145, 0.56, 0.74])  # left, bottom, width, height
    ax_cbar = fig.add_axes([0.645, 0.145, 0.025, 0.74])

    right_left = 0.75
    right_w = 0.23
    ax_cnt = fig.add_axes([right_left, 0.60, right_w, 0.30])
    ax_hist = fig.add_axes([right_left, 0.20, right_w, 0.30])

    # ------------------------------- main hexbin ---------------------------
    hb = ax_main.hexbin(
        x,
        y,
        C=scaled,
        gridsize=args.gridsize,
        reduce_C_function=np.median,
        mincnt=1,
        vmin=vmin,
        vmax=vmax,
        cmap=args.cmap,
    )
    cbar = fig.colorbar(hb, cax=ax_cbar)
    exp_txt = f"× 10^{args.scale_exp}"  # ex: × 10^-7
    cbar.set_label(rf"{metric_label} {exp_txt} [rad]")

    title_extra = " (absolu)" if args.abs else ""
    ax_main.set_title(
        rf"Residual map of ${metric_label}$ over $(m_1,m_2)$" + title_extra,
        fontsize=14,
    )
    ax_main.set_xlabel("m1")
    ax_main.set_ylabel("m2")
    ax_main.set_aspect("auto", adjustable="datalim")
    x_med, y_med = np.nanmedian(x), np.nanmedian(y)
    x_lo, x_hi = x_med - 0.5, x_med + 0.5
    y_lo, y_hi = y_med - 0.5, y_med + 0.5
    if x_lo == x_hi:
        x_lo, x_hi = x_lo - 0.1, x_hi + 0.1
    if y_lo == y_hi:
        y_lo, y_hi = y_lo - 0.1, y_hi + 0.1
    ax_main.set_xlim(x_lo, x_hi)
    ax_main.set_ylim(y_lo, y_hi)
    print(
        f"[DEBUG] fig06 main x_lim=({x_lo:.4g},{x_hi:.4g}), y_lim=({y_lo:.4g},{y_hi:.4g})"
    )

    # annotation mincnt
    ax_main.text(
        0.02,
        0.02,
        f"Empty hexagons = count < {args.mincnt}",
        transform=ax_main.transAxes,
        ha="left",
        va="bottom",
        bbox=dict(boxstyle="round", fc="white", ec="0.5", alpha=0.9),
        fontsize=9,
    )

    # ------------------------------- counts inset --------------------------
    hb_counts = ax_cnt.hexbin(
        x,
        y,
        gridsize=args.gridsize,
        cmap="gray_r",
        mincnt=1,
    )
    counts_arr = hb_counts.get_array()
    if counts_arr.size and np.nanmin(counts_arr[counts_arr > 0]) > 0:
        min_pos = float(np.nanmin(counts_arr[counts_arr > 0]))
        max_val = float(np.nanmax(counts_arr))
        if max_val / max(min_pos, 1e-9) > 50:
            hb_counts.set_norm(colors.LogNorm(vmin=min_pos, vmax=max_val))
    cbar_cnt = fig.colorbar(
        hb_counts,
        ax=ax_cnt,
        orientation="vertical",
        fraction=0.046,
        pad=0.03,
    )
    cbar_cnt.set_label("Counts")
    ax_cnt.set_title("Counts per cell", fontsize=11)
    ax_cnt.set_xlabel("m1")
    ax_cnt.set_ylabel("m2")
    ax_cnt.set_xlim(x_lo, x_hi)
    ax_cnt.set_ylim(y_lo, y_hi)
    ax_cnt.autoscale(enable=True, axis="both", tight=False)
    ax_cnt.xaxis.set_major_locator(MaxNLocator(nbins=5))
    ax_cnt.yaxis.set_major_locator(MaxNLocator(nbins=5))

    # n_active = somme des points contenus dans les cellules ayant count >= mincnt
    counts_arr = hb_counts.get_array()
    n_active = int(np.sum(counts_arr[counts_arr >= args.mincnt]))

    # ------------------------------- histogram inset -----------------------
    ax_hist.hist(
        scaled,
        bins=40,
        color="#1f77b4",
        edgecolor="black",
        linewidth=0.6,
    )
    ax_hist.set_title("Distribution globale", fontsize=11)
    ax_hist.set_xlabel(rf"metric {exp_txt} [rad]")
    ax_hist.set_ylabel("fréquence")

    # Boîte de stats (3 lignes)
    stats_lines = [
        rf"median={med:.2f}, mean={mean:.2f}",
        rf"std={std:.2f}, p95={p95:.2f} {exp_txt} [rad]",
        rf"fraction |metric|>{args.threshold:.0e} rad = {100 * frac_over:.2f}%",
    ]
    ax_hist.text(
        0.98,
        0.98,
        "\n".join(stats_lines),
        transform=ax_hist.transAxes,
        ha="right",
        va="top",
        fontsize=9,
        bbox=dict(boxstyle="round", fc="white", ec="0.5", alpha=0.9),
    )
    ax_hist.set_ylim(0, 8.0)

    # ------------------------------- footers --------------------------------
    foot_scale = (
        f"Réduction par médiane (gridsize={args.gridsize}, mincnt={args.mincnt}). "
        f"Échelle: vmin={vmin:.6g}, vmax={vmax:.6g}  (percentiles {p_lo}–{p_hi})."
    )

    if args.metric == "dp95":
        metric_source = (
            f"mode={desc_mode}, orig='{orig_used or '-'}', recalc='{recalc_used}'."
        )
    else:
        metric_source = f"mode={desc_mode}."

    foot_stats = (
        f"Stats globales: median={med:.2f}, mean={mean:.2f}, std={std:.2f}, "
        f"p95={p95:.2f} {exp_txt} [rad]. N={N}, cellules actives (≥{args.mincnt}) = "
        f"{n_active}. {metric_source}"
    )

    fig.subplots_adjust(
        left=0.07,
        right=0.96,
        top=0.96,
        bottom=0.12,
        wspace=0.34,
        hspace=0.30,
    )
    fig.text(0.5, 0.053, foot_scale, ha="center", fontsize=10)
    fig.text(0.5, 0.032, foot_stats, ha="center", fontsize=10)

    # ------------------------------- sortie ---------------------------------
    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    updated = safe_save(args.out, fig, dpi=args.dpi, bbox_inches="tight")
    status = "écrite" if updated else "inchangée (identique)"
    print(f"[OK] Figure {status}: {args.out}")

    if args.manifest:
        man_path = os.path.splitext(args.out)[0] + ".manifest.json"
        manifest = {
            "script": "plot_fig06_residual_map.py",
            "generated_at": pd.Timestamp.utcnow().isoformat() + "Z",
            "inputs": {
                "csv": args.results,
                "m1_col": args.m1_col,
                "m2_col": args.m2_col,
            },
            "metric": {
                "type": args.metric,
                "absolute": bool(args.abs),
                "orig_col_hint": args.orig_col,
                "recalc_col_hint": args.recalc_col,
                "phi_ref_col_hint": args.phi_ref_col,
                "phi_mcgt_col_hint": args.phi_mcgt_col,
                "mode_desc": desc_mode,
            },
            "plot_params": {
                "gridsize": int(args.gridsize),
                "mincnt": int(args.mincnt),
                "cmap": args.cmap,
                "vclip_percentiles": [p_lo, p_hi],
                "vmin_scaled": float(vmin),
                "vmax_scaled": float(vmax),
                "scale_exp": int(args.scale_exp),
                "threshold_rad": float(args.threshold),
                "figsize": [fig_w, fig_h],
                "dpi": int(args.dpi),
            },
            "dataset": {"N": int(N), "n_active_points": int(n_active)},
            "stats_scaled": {
                "median": med,
                "mean": mean,
                "std": std,
                "p95": p95,
                "fraction_abs_gt_threshold": frac_over,
            },
            "figure_path": args.out,
        }
        with open(man_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"[OK] Manifest écrit: {man_path}")


if __name__ == "__main__":
    main()
