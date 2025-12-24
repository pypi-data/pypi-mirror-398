#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_fig03_convergence.py

Trace la convergence d’estimateurs de p95 (mean, median, trimmed mean) en fonction
de la taille d’échantillon N, avec IC 95% (bootstrap percentile).
Produit un PNG.

Exemple (pipeline minimal, par défaut) :
  python zz-scripts/chapter10/plot_fig03_convergence.py

Exemple (MC complet historique) :
  python zz-scripts/chapter10/plot_fig03_convergence.py \\
    --results zz-data/chapter10/10_mc_results.circ.csv \\
    --p95-col p95_20_300_recalc \\
    --out zz-figures/chapter10/10_fig_03_convergence.png \\
    --B 2000 --seed 12345 --dpi 150
"""

from __future__ import annotations

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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


def detect_p95_column(df: pd.DataFrame, hint: str | None):
    """Détection robuste de la colonne p95 (avec hint optionnel)."""
    if hint and hint in df.columns:
        return hint
    for c in [
        "p95_20_300_recalc",
        "p95_20_300_circ",
        "p95_20_300",
        "p95_circ",
        "p95_recalc",
    ]:
        if c in df.columns:
            return c
    for c in df.columns:
        if "p95" in c.lower():
            return c
    raise KeyError("Aucune colonne 'p95' détectée dans le fichier results.")


def trimmed_mean(arr: np.ndarray, alpha: float) -> float:
    """Moyenne tronquée bilatérale: retire alpha de chaque côté."""
    if alpha <= 0:
        return float(np.mean(arr))
    n = len(arr)
    k = int(np.floor(alpha * n))
    if 2 * k >= n:
        return float(np.mean(arr))
    a = np.sort(arr)
    return float(np.mean(a[k : n - k]))


def compute_bootstrap_convergence(
    p95: np.ndarray,
    N_list: np.ndarray,
    B: int,
    seed: int,
    trim_alpha: float,
):
    """Bootstrap percentile pour mean / median / trimmed mean à différents N."""
    rng = np.random.default_rng(seed)
    npoints = len(N_list)

    mean_est = np.empty(npoints)
    mean_low = np.empty(npoints)
    mean_high = np.empty(npoints)

    median_est = np.empty(npoints)
    median_low = np.empty(npoints)
    median_high = np.empty(npoints)

    tmean_est = np.empty(npoints)
    tmean_low = np.empty(npoints)
    tmean_high = np.empty(npoints)

    for i, N in enumerate(N_list):
        ests_mean = np.empty(B)
        ests_median = np.empty(B)
        ests_tmean = np.empty(B)
        for b in range(B):
            samp = rng.choice(p95, size=N, replace=True)
            ests_mean[b] = np.mean(samp)
            ests_median[b] = np.median(samp)
            ests_tmean[b] = trimmed_mean(samp, trim_alpha)

        # Estimateurs ponctuels = moyenne des estimates bootstrap
        mean_est[i] = ests_mean.mean()
        median_est[i] = ests_median.mean()
        tmean_est[i] = ests_tmean.mean()

        # IC percentile 95%
        mean_low[i], mean_high[i] = np.percentile(ests_mean, [2.5, 97.5])
        median_low[i], median_high[i] = np.percentile(ests_median, [2.5, 97.5])
        tmean_low[i], tmean_high[i] = np.percentile(ests_tmean, [2.5, 97.5])

    return (
        mean_est,
        mean_low,
        mean_high,
        median_est,
        median_low,
        median_high,
        tmean_est,
        tmean_low,
        tmean_high,
    )


def main():
    p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument(
        "--results",
        default="zz-data/chapter10/10_results_global_scan.csv",
        help="CSV results (avec une colonne p95).",
    )
    p.add_argument(
        "--p95-col", default=None, help="Nom de la colonne p95 (auto si omis)"
    )
    p.add_argument(
        "--out",
        default="zz-figures/chapter10/10_fig_03_convergence.png",
        help="PNG de sortie",
    )
    p.add_argument("--B", type=int, default=2000, help="Nombre de réplicats bootstrap")
    p.add_argument("--seed", type=int, default=12345, help="Seed RNG")
    p.add_argument("--dpi", type=int, default=150, help="DPI PNG")
    p.add_argument("--npoints", type=int, default=100, help="Nb de valeurs N évaluées")
    p.add_argument(
        "--trim",
        type=float,
        default=0.05,
        help="Proportion tronquée de chaque côté (trimmed mean)",
    )
    args = p.parse_args()

    # Lecture & détection de la colonne p95
    df = pd.read_csv(args.results)
    p95_col = detect_p95_column(df, args.p95_col)
    p95 = df[p95_col].dropna().astype(float).values
    M = len(p95)
    if M == 0:
        raise SystemExit("Aucun p95 disponible dans le fichier.")

    # Grille N
    minN = max(10, int(max(10, M * 0.01)))
    N_list = np.unique(np.linspace(minN, M, args.npoints, dtype=int))
    if N_list[-1] != M:
        N_list = np.append(N_list, M)

    # Références plein-échantillon
    ref_mean = float(np.mean(p95))
    ref_median = float(np.median(p95))
    ref_tmean = trimmed_mean(p95, args.trim)

    print(
        f"[INFO] Bootstrap convergence: M={M}, B={args.B}, "
        f"points={len(N_list)}, seed={args.seed}, trim={args.trim:.3f}"
    )

    (
        mean_est,
        mean_low,
        mean_high,
        median_est,
        median_low,
        median_high,
        tmean_est,
        tmean_low,
        tmean_high,
    ) = compute_bootstrap_convergence(
        p95,
        N_list,
        args.B,
        args.seed,
        args.trim,
    )

    # Résumés finaux (pour boîte)
    final_i = np.where(N_list == M)[0][0] if (N_list == M).any() else -1
    final_mean, final_mean_ci = (
        mean_est[final_i],
        (mean_low[final_i], mean_high[final_i]),
    )
    final_median, final_median_ci = (
        median_est[final_i],
        (median_low[final_i], median_high[final_i]),
    )
    final_tmean, final_tmean_ci = (
        tmean_est[final_i],
        (tmean_low[final_i], tmean_high[final_i]),
    )

    # --- Plot principal (même style que ton original) ---
    plt.style.use("classic")
    fig, ax = plt.subplots(figsize=(14, 6))

    # IC 95% pour la moyenne (zone bleue)
    ci_handle = ax.fill_between(
        N_list,
        mean_low,
        mean_high,
        color="tab:blue",
        alpha=0.18,
        label="95% CI (bootstrap, mean)",
    )

    # Estimateurs
    (mean_line,) = ax.plot(
        N_list, mean_est, color="tab:blue", lw=2.0, label="Estimator (mean)"
    )
    (median_line,) = ax.plot(
        N_list,
        median_est,
        color="tab:orange",
        lw=1.6,
        ls="--",
        label="Estimator (median)",
    )
    (tmean_line,) = ax.plot(
        N_list,
        tmean_est,
        color="tab:green",
        lw=1.6,
        ls="-.",
        label=f"Estimator (trimmed mean, α={args.trim:.2f})",
    )

    # Ligne de référence (mean plein-échantillon)
    ref_line = ax.axhline(
        ref_mean, color="crimson", lw=2, label=f"Estimate at N={M} (mean ref)"
    )

    ax.set_xlim(0, M)
    ax.set_xlabel(r"Sample Size $N$")
    ax.set_ylabel(f"Estimator of {p95_col} [rad]")
    ax.set_title(f"Convergence of {p95_col} estimation", fontsize=15)

    # Légende unique (statistiques finales)
    stats_lines = [
        f"N = {M}",
        f"mean = {final_mean:.3f} [{final_mean_ci[0]:.3f}, {final_mean_ci[1]:.3f}]",
        f"median = {final_median:.3f} [{final_median_ci[0]:.3f}, {final_median_ci[1]:.3f}]",
        f"trimmed = {final_tmean:.3f} [{final_tmean_ci[0]:.3f}, {final_tmean_ci[1]:.3f}]",
    ]
    stats_handles = [
        plt.Line2D([0], [0], color="none", marker="None", label=txt)
        for txt in stats_lines
    ]
    labels_stats = [h.get_label() for h in stats_handles]
    leg_stats = ax.legend(
        stats_handles,
        labels_stats,
        loc="lower left",
        frameon=True,
        fontsize=10,
    )
    leg_stats.set_zorder(5)

    # Footnote
    fig.text(
        0.5,
        0.02,
        f"Bootstrap (B={args.B}, percentile) sur {M} échantillons. "
        f"Estimateurs tracés = mean (plein), median (pointillé), "
        f"trimmed mean (tiret-point, α={args.trim:.2f}).",
        ha="center",
        fontsize=9,
    )

    plt.tight_layout(rect=[0, 0.05, 1, 0.97])
    fig.savefig(args.out, dpi=args.dpi)
    print(f"Wrote: {args.out}")


if __name__ == "__main__":
    main()
