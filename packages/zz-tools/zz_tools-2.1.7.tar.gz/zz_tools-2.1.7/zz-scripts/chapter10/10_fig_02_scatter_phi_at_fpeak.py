#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_fig02_scatter_phi_at_fpeak.py

Nuage de points comparant phi_ref(f_peak) vs phi_MCGT(f_peak).
- Différence circulaire Δφ = wrap(φ_MCGT - φ_ref) dans [-π, π)
- Couleur = |Δφ|
- Hexbin de fond optionnel (+ scatter alpha)
- Colorbar avec ticks explicites (0, π/4, π/2, 3π/4, π)
- Statistiques incluant IC bootstrap (95%) de la moyenne circulaire de Δφ
- Export PNG (DPI au choix)

Si --results n'est pas fourni, le script essaie automatiquement quelques chemins
standards dans le dépôt :

  1) zz-data/chapter10/10_mc_results.circ.with_fpeak.csv   (prioritaire)
  2) zz-data/chapter10/10_phase_diff_fpeak.csv
  3) zz-data/chapter09/09_phase_diff.csv
  4) zz-data/chapter10/10_results_global_scan.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import hashlib
import shutil
import tempfile

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

# ------------------------- Utils (diff & stats circulaires) -------------------------

TWOPI = 2.0 * np.pi


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_save(filepath: Path | str, fig, **savefig_kwargs) -> bool:
    """
    Sauvegarde fig en évitant de toucher le mtime si le PNG est inchangé.
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


def wrap_pi(x: np.ndarray) -> np.ndarray:
    """Réduit sur l'intervalle [-π, π)."""
    return (x + np.pi) % TWOPI - np.pi


def circ_diff(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Δφ = wrap( b - a ) dans [-π, π)."""
    return wrap_pi(b - a)


def circ_mean_rad(angles: np.ndarray) -> float:
    """Moyenne circulaire (angle) en radians [-π, π)."""
    z = np.mean(np.exp(1j * angles))
    return float(np.angle(z))


def circ_std_rad(angles: np.ndarray) -> float:
    """Écart-type circulaire (radians). Définition basée sur R = |E[e^{iθ}]|."""
    R = np.abs(np.mean(np.exp(1j * angles)))
    # std circulaire : sqrt(-2 ln R)
    return float(np.sqrt(max(0.0, -2.0 * np.log(max(R, 1e-12)))))


def bootstrap_circ_mean_ci(
    angles: np.ndarray, B: int = 1000, seed: int = 12345
) -> tuple[float, float, float]:
    """
    IC bootstrap (percentile, 95%) pour la moyenne circulaire de `angles`.

    Technique: calcule la moyenne circulaire θ̂. Pour chaque bootstrap, calcule θ_b.
    Étant sur un cercle, on centre puis "wrap" : Δ_b = wrap(θ_b - θ̂).
    On prend les percentiles 2.5% et 97.5% de Δ_b, puis on réapplique autour de θ̂.

    Retourne: (theta_hat, ci_low, ci_high) en radians dans [-π, π).
    """
    n = len(angles)
    if n == 0 or B <= 0:
        th = circ_mean_rad(angles)
        return th, th, th

    rng = np.random.default_rng(seed)
    theta_hat = circ_mean_rad(angles)
    deltas = np.empty(B, dtype=float)

    for _ in range(B):
        idx = rng.integers(0, n, size=n)
        th_b = circ_mean_rad(angles[idx])
        deltas[_] = wrap_pi(th_b - theta_hat)

    lo = np.percentile(deltas, 2.5)
    hi = np.percentile(deltas, 97.5)
    ci_low = wrap_pi(theta_hat + lo)
    ci_high = wrap_pi(theta_hat + hi)
    return theta_hat, ci_low, ci_high


# ------------------------- Parsing & auto-détection -------------------------


def detect_column(df: pd.DataFrame, hint: str | None, candidates: list[str]) -> str:
    """Détecte une colonne en utilisant un hint explicite ou une liste de candidats."""
    if hint and hint in df.columns:
        return hint
    for c in candidates:
        if c in df.columns:
            return c
    # fallback: recherche par sous-chaîne (case-insensitive)
    lowcols = [c.lower() for c in df.columns]
    for cand in candidates:
        if cand.lower() in lowcols:
            return df.columns[lowcols.index(cand.lower())]
    raise KeyError(f"Aucune colonne trouvée parmi : {candidates} (ou hint={hint})")


def auto_find_results_csv(
    args_results: str | None, x_hint: str | None, y_hint: str | None
) -> str:
    """
    Si args_results est fourni, le renvoie tel quel.
    Sinon essaie une liste de chemins standards et vérifie qu'on y trouve bien
    les colonnes phi_ref_fpeak / phi_mcgt_fpeak (ou équivalents).
    """
    if args_results:
        return args_results

    search_paths = [
        "zz-data/chapter10/10_mc_results.circ.with_fpeak.csv",
        "zz-data/chapter10/10_phase_diff_fpeak.csv",
        "zz-data/chapter09/09_phase_diff.csv",
        "zz-data/chapter10/10_results_global_scan.csv",
    ]

    x_candidates = [
        "phi_ref_fpeak",
        "phi_ref",
        "phi_ref_f_peak",
        "phi_ref_at_fpeak",
        "phi_reference",
    ]
    y_candidates = [
        "phi_mcgt_fpeak",
        "phi_mcgt",
        "phi_mcg",
        "phi_mcg_at_fpeak",
        "phi_MCGT",
    ]

    last_err: str | None = None

    for rel in search_paths:
        path = Path(rel)
        if not path.exists():
            last_err = f"Fichier absent: {path}"
            continue
        try:
            df_try = pd.read_csv(path)
        except Exception as e:  # pragma: no cover - robust chemin d'erreur
            last_err = f"Erreur lecture '{path}': {e}"
            continue
        try:
            _ = detect_column(df_try, x_hint, x_candidates)
            _ = detect_column(df_try, y_hint, y_candidates)
        except Exception as e:
            last_err = f"{e}"
            continue

        # Si on arrive ici, ce fichier contient des phases ref/MCGT utilisables.
        return str(path)

    # Rien de concluant
    print(
        "[ERROR] Impossible de trouver un CSV utilisable pour les phases ref/MCGT.",
        file=sys.stderr,
    )
    print("Chemin(s) testé(s) :", file=sys.stderr)
    for rel in search_paths:
        print(f"  {Path(rel)}", file=sys.stderr)
    if last_err is not None:
        print(f"Dernier message d'erreur : {last_err}", file=sys.stderr)
    sys.exit(2)


# ------------------------- Plot principal -------------------------


def main() -> None:
    p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument(
        "--results",
        default=None,
        help=(
            "CSV contenant les colonnes de phases à f_peak. "
            "Si omis, tente une auto-détection dans zz-data/."
        ),
    )
    p.add_argument(
        "--x-col",
        default=None,
        help="Nom colonne phase ref (x). Auto-détect si omis.",
    )
    p.add_argument(
        "--y-col",
        default=None,
        help="Nom colonne phase MCGT (y). Auto-détect si omis.",
    )
    p.add_argument(
        "--group-col",
        default=None,
        help="Colonne de groupe optionnelle (marqueurs)",
    )
    p.add_argument(
        "--out",
        default="zz-figures/chapter10/10_fig_02_scatter_phi_at_fpeak.png",
        help="PNG de sortie",
    )
    p.add_argument("--dpi", type=int, default=300, help="DPI PNG")
    p.add_argument(
        "--title",
        default=r"Pointwise comparison at $f_{\rm peak}$: $\phi_{\rm ref}$ vs $\phi_{\rm MCGT}$",
        help="Figure title (fontsize=15)",
    )
    p.add_argument(
        "--point-size", type=float, default=12.0, help="Taille des points du scatter"
    )
    p.add_argument(
        "--alpha", type=float, default=0.7, help="Alpha des points du scatter"
    )
    p.add_argument("--cmap", default="viridis", help="Colormap pour |Δφ|")

    # options de clipping / échelle
    p.add_argument(
        "--clip_pi",
        action="store_true",
        help="Force axes X/Y dans [-π, π] (utile si phases wrapées).",
    )
    p.add_argument(
        "--p95-ref",
        type=float,
        default=0.7104087123286049,
        help="Seuil de référence pour fraction |Δφ| < réf.",
    )
    p.add_argument(
        "--annotate-top-k",
        type=int,
        default=0,
        help="Annote les K pires |Δφ| (0 = désactivé).",
    )

    # HEXBIN
    p.add_argument(
        "--with-hexbin",
        action="store_true",
        help="Ajoute un hexbin de fond (densité).",
    )
    p.add_argument(
        "--hexbin-gridsize",
        type=int,
        default=120,
        help="Grille hexbin (densité).",
    )
    p.add_argument(
        "--hexbin-alpha",
        type=float,
        default=0.18,
        help="Alpha du hexbin de fond.",
    )

    # Colorbar ticks π/4
    p.add_argument(
        "--pi-ticks",
        action="store_true",
        help="Colorbar avec ticks à 0, π/4, π/2, 3π/4, π.",
    )

    # Bootstrap IC sur la moyenne circulaire
    p.add_argument(
        "--boot-ci",
        type=int,
        default=1000,
        help=(
            "B (réplicats) pour IC bootstrap 95% de la moyenne circulaire "
            "de Δφ. 0 = off."
        ),
    )
    p.add_argument("--seed", type=int, default=12345, help="Seed RNG bootstrap")

    args = p.parse_args()

    # --- normalisation sortie : si '--out' est un nom nu -> redirige vers zz-figures/chapter10/ ---
    from pathlib import Path as _Path

    _outp = _Path(args.out)
    if _outp.parent == _Path("."):
        args.out = str(_Path("zz-figures/chapter10") / _outp.name)
    # ---------- Résolution du CSV à utiliser ----------
    results_path = auto_find_results_csv(args.results, args.x_col, args.y_col)

    # lecture
    df = pd.read_csv(results_path)

    x_candidates = [
        "phi_ref_fpeak",
        "phi_ref",
        "phi_ref_f_peak",
        "phi_ref_at_fpeak",
        "phi_reference",
    ]
    y_candidates = [
        "phi_mcgt_fpeak",
        "phi_mcgt",
        "phi_mcg",
        "phi_mcg_at_fpeak",
        "phi_MCGT",
    ]

    xcol = detect_column(df, args.x_col, x_candidates)
    ycol = detect_column(df, args.y_col, y_candidates)
    groupcol = args.group_col if (args.group_col in df.columns) else None

    cols = [xcol, ycol] + ([groupcol] if groupcol else [])
    sub = df[cols].dropna().copy()
    x = sub[xcol].astype(float).values
    y = sub[ycol].astype(float).values
    groups = sub[groupcol].values if groupcol else None

    # Δφ circulaire
    dphi = circ_diff(x, y)
    abs_d = np.abs(dphi)
    N = len(abs_d)

    # stats scalaires
    mean_abs = float(np.mean(abs_d))
    median_abs = float(np.median(abs_d))
    p95_abs = float(np.percentile(abs_d, 95))
    max_abs = float(np.max(abs_d))
    frac_below = float(np.mean(abs_d < args.p95_ref))

    # stats circulaires
    cmean = circ_mean_rad(dphi)
    cstd = circ_std_rad(dphi)
    if args.boot_ci > 0:
        cmean_hat, ci_lo, ci_hi = bootstrap_circ_mean_ci(
            dphi, B=args.boot_ci, seed=args.seed
        )
    else:
        cmean_hat, ci_lo, ci_hi = cmean, cmean, cmean

    # largeur d'arc la plus courte entre les bornes d'IC, puis demi-largeur
    arc_width = float(np.abs(wrap_pi(ci_hi - ci_lo)))
    half_arc = 0.5 * arc_width

    # Figure
    plt.style.use("classic")
    fig, ax = plt.subplots(figsize=(8, 8))

    # hexbin en fond
    if args.with_hexbin:
        ax.hexbin(
            x,
            y,
            gridsize=args.hexbin_gridsize,
            mincnt=1,
            cmap="Greys",
            alpha=args.hexbin_alpha,
            linewidths=0,
            zorder=0,
        )

    # scatter par-dessus
    sc = ax.scatter(
        x,
        y,
        c=abs_d,
        s=args.point_size,
        alpha=args.alpha,
        cmap=args.cmap,
        edgecolor="none",
        zorder=1,
    )

    # limites
    xmin, xmax = np.min(x), np.max(x)
    ymin, ymax = np.min(y), np.max(y)
    if args.clip_pi:
        ax.set_xlim(-np.pi, np.pi)
        ax.set_ylim(-np.pi, np.pi)
    else:
        pad_x = 0.03 * (xmax - xmin) if xmax > xmin else 0.1
        pad_y = 0.03 * (ymax - ymin) if ymax > ymin else 0.1
        ax.set_xlim(xmin - pad_x, xmax + pad_x)
        ax.set_ylim(ymin - pad_y, ymax + pad_y)

    # même échelle en X et Y pour que y=x soit à 45°
    ax.set_aspect("equal", adjustable="box")

    # y = x
    lo = min(ax.get_xlim()[0], ax.get_ylim()[0])
    hi = max(ax.get_xlim()[1], ax.get_ylim()[1])
    ax.plot([lo, hi], [lo, hi], color="gray", linestyle="--", lw=1.2, zorder=2)

    # axes / titre
    ax.set_xlabel(f"{xcol} [rad]")
    ax.set_ylabel(f"{ycol} [rad]")
    ax.set_title(args.title, fontsize=15)

    # colorbar |Δφ|
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label(r"$|\Delta\phi|$ [rad]")
    if args.pi_ticks:
        ticks = [0.0, np.pi / 4, np.pi / 2, 3 * np.pi / 4, np.pi]
        cbar.set_ticks(ticks)
        cbar.set_ticklabels(["0", r"$\pi/4$", r"$\pi/2$", r"$3\pi/4$", r"$\pi$"])

    # stats box
    stat_lines = [
        f"N = {N}",
        f"|Δφ| mean = {mean_abs:.3f}",
        f"median = {median_abs:.3f}",
        f"p95 = {p95_abs:.3f}",
        f"max = {max_abs:.3f}",
        f"|Δφ| < {args.p95_ref:.4f} : {100 * frac_below:.2f}% (n={int(round(frac_below * N))})",
        f"circ-mean(Δφ) = {cmean_hat:.3f} rad",
        f"  95% CI ≈ {cmean_hat:.3f} ± {half_arc:.3f} rad (arc court)",
        f"circ-std(Δφ) = {cstd:.3f} rad",
    ]
    bbox = dict(boxstyle="round", fc="white", ec="black", lw=1, alpha=0.95)
    ax.text(
        0.02,
        0.98,
        "\n".join(stat_lines),
        transform=ax.transAxes,
        fontsize=9,
        va="top",
        ha="left",
        bbox=bbox,
        zorder=5,
    )

    # annotation top-K pires |Δφ|
    if args.annotate_top_k and args.annotate_top_k > 0:
        k = int(min(args.annotate_top_k, N))
        idx = np.argsort(-abs_d)[:k]
        for i in idx:
            ax.annotate(
                f"{abs_d[i]:.3f}",
                (x[i], y[i]),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=7,
                color="black",
                alpha=0.8,
            )

    # pied de figure
    foot = (
        r"$\Delta\phi$ computed circularly in radians "
        r"(b − a mod $2\pi \rightarrow [-\pi,\pi)$). "
        r"Color = $|\Delta\phi|$. Hexbin = density (if enabled)."
    )
    fig.text(0.5, 0.02, foot, ha="center", fontsize=9)

    plt.tight_layout(rect=[0, 0.04, 1, 0.98])
    updated = safe_save(args.out, fig, dpi=args.dpi)
    status = "Wrote" if updated else "Unchanged (identique)"
    print(f"{status}: {args.out}")


if __name__ == "__main__":
    main()
