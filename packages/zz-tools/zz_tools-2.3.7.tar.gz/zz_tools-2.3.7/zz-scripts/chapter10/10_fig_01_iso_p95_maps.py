#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_fig01_iso_p95_maps.py

Trace une carte iso (contour filled) de la métrique p95 dans l'espace (m1,m2).
Affiche les points d'échantillons superposés.
Produit un PNG.

Usage example (lancé depuis la racine du dépôt MCGT) :
python zz-scripts/chapter10/plot_fig01_iso_p95_maps.py \
  --results zz-data/chapter10/10_results_global_scan.csv \
  --p95-col p95_20_300_recalc \
  --m1-col m1 --m2-col m2 \
  --out zz-figures/chapter10/10_fig_01_iso_p95_maps.png \
  --levels 16 --cmap viridis --dpi 300

Options notables:
  --no-clip    : désactive le clipping en percentiles (montre toute la plage)
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.tri as tri
import numpy as np
import pandas as pd
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


# ---------- utilities ----------


def detect_p95_column(df: pd.DataFrame, hint: str | None) -> str:
    """Essaye de trouver la colonne p95 en utilisant un hint ou des noms usuels."""
    if hint and hint in df.columns:
        return hint

    candidates = [
        "p95_20_300_recalc",
        "p95_20_300_circ",
        "p95_20_300",
        "p95_circ",
        "p95_recalc",
        "p95",
    ]
    for c in candidates:
        if c in df.columns:
            return c

    for c in df.columns:
        if "p95" in c.lower():
            return c

    raise KeyError("Aucune colonne 'p95' détectée dans le fichier results.")


def read_and_validate(
    path: Path, m1_col: str, m2_col: str, p95_col: str
) -> pd.DataFrame:
    """Lit le CSV et valide la présence des colonnes requises. Retourne un DataFrame épuré."""
    try:
        df = pd.read_csv(path)
    except Exception as e:  # pragma: no cover - message utilisateur
        raise SystemExit(f"Erreur lecture CSV '{path}': {e}")

    for col in (m1_col, m2_col, p95_col):
        if col not in df.columns:
            raise KeyError(f"Colonne attendue absente: {col}")

    # on garde uniquement les colonnes utiles, sans NaN, en float
    df = df[[m1_col, m2_col, p95_col]].dropna().astype(float)
    if df.shape[0] == 0:
        raise ValueError("Aucune donnée valide après suppression des NaN.")
    return df


def make_triangulation_and_mask(
    x: np.ndarray, y: np.ndarray
) -> tri.Triangulation | None:
    """
    Construit une triangulation pour des points (x,y) dispersés.
    Si les points ne permettent pas une triangulation robuste, retourne None
    (le code appelant basculera alors en mode scatter-only).
    """
    # Vérifie le nombre de points (m1,m2) réellement uniques
    try:
        pts = np.column_stack([x, y])
        unique = np.unique(pts, axis=0)
        if unique.shape[0] < 3:
            warnings.warn(
                "Pas assez de points (m1,m2) uniques pour une triangulation – "
                "fallback en scatter coloré.",
                RuntimeWarning,
            )
            return None
    except Exception:
        # si même ça foire, on laissera le code appelant gérer le fallback
        return None

    try:
        triang = tri.Triangulation(x, y)
        # masque les triangles dégénérés
        tris = triang.triangles
        if tris.size == 0:
            warnings.warn(
                "Triangulation vide ou dégénérée – fallback en scatter coloré.",
                RuntimeWarning,
            )
            return None
        x1 = x[tris[:, 0]]
        x2 = x[tris[:, 1]]
        x3 = x[tris[:, 2]]
        y1 = y[tris[:, 0]]
        y2 = y[tris[:, 1]]
        y3 = y[tris[:, 2]]
        areas = 0.5 * np.abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1))
        mask = areas <= 0.0
        triang.set_mask(mask)
    except Exception:
        warnings.warn(
            "Erreur lors de la triangulation – fallback en scatter coloré.",
            RuntimeWarning,
        )
        return None

    return triang


# ---------- main ----------


def main() -> None:
    # Racine du dépôt (MCGT/)
    root = Path(__file__).resolve().parents[2]
    default_results = root / "zz-data" / "chapter10" / "10_results_global_scan.csv"
    default_out = root / "zz-figures" / "chapter10" / "10_fig_01_iso_p95_maps.png"

    ap = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Figure 01 – Carte iso de p95 (m1 vs m2) pour l'exploration globale (Chapitre 10).",
    )
    ap.add_argument(
        "--results",
        default=None,
        help="Fichier CSV de résultats (doit contenir m1, m2 et p95). "
        "Par défaut : zz-data/chapter10/10_results_global_scan.csv",
    )
    ap.add_argument(
        "--p95-col",
        default=None,
        help="Nom de la colonne p95 (auto-détection si omis).",
    )
    ap.add_argument(
        "--m1-col",
        default="m1",
        help="Nom de la colonne pour m1.",
    )
    ap.add_argument(
        "--m2-col",
        default="m2",
        help="Nom de la colonne pour m2.",
    )
    ap.add_argument(
        "--out",
        default=None,
        help="Fichier PNG de sortie. "
        "Par défaut : zz-figures/chapter10/10_fig_01_iso_p95_maps.png",
    )
    ap.add_argument(
        "--levels",
        type=int,
        default=16,
        help="Nombre de niveaux de contours.",
    )
    ap.add_argument(
        "--cmap",
        default="viridis",
        help="Colormap matplotlib.",
    )
    ap.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="DPI du PNG.",
    )
    ap.add_argument(
        "--title",
        default="p95 contour map (m1 vs m2)",
        help="Titre de la figure.",
    )
    ap.add_argument(
        "--no-clip",
        action="store_true",
        help="Ne pas clipper l'échelle de couleurs aux percentiles (affiche toute la plage).",
    )
    args = ap.parse_args()

    # Résolution des chemins (avec valeurs par défaut compatibles pipeline minimal)
    if args.results is None:
        results_path = default_results
    else:
        results_path = Path(args.results)
        if not results_path.is_absolute():
            candidate = root / results_path
            if candidate.exists():
                results_path = candidate

    if args.out is None:
        out_path = default_out
    else:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = root / out_path

    # Lecture brute pour la détection de colonne p95
    try:
        df_all = pd.read_csv(results_path)
    except Exception as e:
        print(f"[ERROR] Cannot read results CSV '{results_path}': {e}", file=sys.stderr)
        sys.exit(2)

    try:
        p95_col = detect_p95_column(df_all, args.p95_col)
    except KeyError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(2)

    # Lecture + validation stricte
    try:
        df = read_and_validate(results_path, args.m1_col, args.m2_col, p95_col)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(2)

    x = df[args.m1_col].values
    y = df[args.m2_col].values
    z = df[p95_col].values

    # Jitter minimal pour forcer un étalement visuel si les données sont quasi constantes
    rng = np.random.default_rng(0)
    if np.std(x) < 1e-4:
        x = x + rng.normal(0, 0.01, size=len(x))
    if np.std(y) < 1e-4:
        y = y + rng.normal(0, 0.01, size=len(y))

    # Triangulation (optionnelle) pour contours
    triang = make_triangulation_and_mask(x, y)

    # Échelle des niveaux et clipping
    zmin, zmax = float(np.nanmin(z)), float(np.nanmax(z))
    if zmax - zmin < 1e-8:
        zmax = zmin + 1e-6
    levels = np.linspace(zmin, zmax, args.levels)

    vmin = zmin
    vmax = zmax
    clipped = False
    if not args.no_clip:
        try:
            p_lo, p_hi = np.percentile(z, [0.1, 99.9])
        except Exception:
            p_lo, p_hi = zmin, zmax
        if p_hi - p_lo > 1e-8 and (p_lo > zmin or p_hi < zmax):
            vmin, vmax = float(p_lo), float(p_hi)
            clipped = True
            warnings.warn(
                (
                    "Detected extreme p95 values: display clipped to "
                    f"[{vmin:.4g}, {vmax:.4g}] (0.1% - 99.9% percentiles) "
                    "to avoid burning the colormap."
                ),
                RuntimeWarning,
            )

    norm = colors.Normalize(vmin=vmin, vmax=vmax, clip=True)

    # Tracé
    plt.style.use("classic")
    fig, ax = plt.subplots(figsize=(10, 8))

    if triang is not None:
        # Mode "plein luxe" : contours lissés
        cf = ax.tricontourf(
            triang,
            z,
            levels=levels,
            cmap=args.cmap,
            alpha=0.95,
            norm=norm,
        )
        ax.tricontour(
            triang,
            z,
            levels=levels,
            colors="k",
            linewidths=0.45,
            alpha=0.5,
        )
        # points en overlay noir (taille augmentée pour visibilité)
        ax.plot(
            x,
            y,
            "o",
            ms=8,
            mfc="none",
            mec="k",
            alpha=0.6,
            label="samples",
            zorder=5,
        )
        cbar = fig.colorbar(cf, ax=ax, shrink=0.8)
        cbar.set_label(f"{p95_col} [rad]")
    else:
        # Fallback robuste : scatter coloré uniquement
        print(
            "[WARNING] Triangulation impossible – figure tracée en mode scatter coloré uniquement.",
            file=sys.stderr,
        )
        sc = ax.scatter(
            x,
            y,
            c=z,
            s=64,
            cmap=args.cmap,
            norm=norm,
            edgecolors="k",
            linewidths=0.3,
            alpha=0.9,
            label="samples (p95)",
            zorder=5,
        )
        cbar = fig.colorbar(sc, ax=ax, shrink=0.8)
        cbar.set_label(f"{p95_col} [rad]")

    ax.set_xlabel(args.m1_col)
    ax.set_ylabel(args.m2_col)
    ax.set_title(args.title, fontsize=15)

    # Forcer un cadrage serré sans aspect contraint, centré sur la médiane
    ax.set_aspect("auto", adjustable="datalim")
    x_med, y_med = np.nanmedian(x), np.nanmedian(y)
    x_lo, x_hi = x_med - 0.5, x_med + 0.5
    y_lo, y_hi = y_med - 0.5, y_med + 0.5
    mask = (x > np.nanpercentile(x, 5)) & (x < np.nanpercentile(x, 95))
    if mask.any():
        x_lo, x_hi = np.nanmin(x[mask]), np.nanmax(x[mask])
        y_lo, y_hi = np.nanmin(y[mask]), np.nanmax(y[mask])
    if x_lo == x_hi:
        x_lo, x_hi = x_lo - 0.1, x_hi + 0.1
    if y_lo == y_hi:
        y_lo, y_hi = y_lo - 0.1, y_hi + 0.1
    ax.set_xlim(x_lo, x_hi)
    ax.set_ylim(y_lo, y_hi)
    print(f"[DEBUG] fig01 x_lim=({x_lo:.4g},{x_hi:.4g}), y_lim=({y_lo:.4g},{y_hi:.4g})")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.tight_layout()

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=args.dpi)
        print(f"[INFO] Wrote: {out_path}")
        if clipped:
            print(
                "Note: color scaling was clipped to percentiles (0.1%/99.9%). "
                "Use --no-clip to disable clipping."
            )
    except Exception as e:
        print(f"[ERROR] cannot write output file '{out_path}': {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
