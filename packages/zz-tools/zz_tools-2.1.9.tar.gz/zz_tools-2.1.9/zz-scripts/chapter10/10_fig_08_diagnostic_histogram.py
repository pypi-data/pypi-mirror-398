#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

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


def wrap_phase(x: np.ndarray) -> np.ndarray:
    """Ramène un angle en radians dans l'intervalle [-pi, pi)."""
    return (x + np.pi) % (2.0 * np.pi) - np.pi


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Diagnostics sur les phases à f_peak : "
            "Δphi(f_peak) = wrap(phi_mcgt_fpeak - phi_ref_fpeak)."
        )
    )
    parser.add_argument(
        "--results",
        required=True,
        help="CSV de résultats (ex. zz-data/chapter10/10_mc_results.circ.with_fpeak.csv)",
    )
    parser.add_argument(
        "--ref-grid",
        required=False,
        help=(
            "Grille de référence des phases IMRPhenom (ex. zz-data/chapter09/09_phases_imrphenom.csv). "
            "Actuellement utilisé uniquement à titre informatif."
        ),
    )
    parser.add_argument(
        "--outdir",
        default="zz-figures/chapter10",
        help="Répertoire de sortie pour les figures / fichiers diag (défaut: zz-figures/chapter10).",
    )
    parser.add_argument(
        "--prefix",
        default="10_fig_08_diagnostic_histogram",
        help="Préfixe des fichiers de sortie (défaut: 10_fig_08_diagnostic_histogram).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    results_path = Path(args.results)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if not results_path.is_file():
        raise SystemExit(f"[ERREUR] Fichier results introuvable: {results_path}")

    print(f"[INFO] Lecture des résultats : {results_path}")
    df = pd.read_csv(results_path)

    required_cols = ["phi_ref_fpeak", "phi_mcgt_fpeak"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing and "phi_at_fpeak_rad" in df.columns:
        print(
            "[WARN] Missing phi_ref_fpeak/phi_mcgt_fpeak, using phi_at_fpeak_rad as fallback."
        )
        df["phi_ref_fpeak"] = df["phi_at_fpeak_rad"]
        df["phi_mcgt_fpeak"] = df["phi_at_fpeak_rad"]
        missing = []
    if missing:
        raise SystemExit(
            f"[ERREUR] Colonnes manquantes dans {results_path} : {missing} "
            f"(colonnes disponibles: {df.columns.tolist()})"
        )

    # Δphi(f_peak) avec wrap dans [-pi, pi)
    dphi = df["phi_mcgt_fpeak"].to_numpy() - df["phi_ref_fpeak"].to_numpy()
    dphi_wrapped = wrap_phase(dphi)
    df["delta_phi_fpeak"] = dphi_wrapped

    # Statistiques simples
    n = len(dphi_wrapped)
    abs_dphi = np.abs(dphi_wrapped)

    stats = {
        "n": int(n),
        "mean_delta_phi": float(np.mean(dphi_wrapped)),
        "std_delta_phi": float(np.std(dphi_wrapped, ddof=1)) if n > 1 else float("nan"),
        "min_delta_phi": float(np.min(dphi_wrapped)),
        "max_delta_phi": float(np.max(dphi_wrapped)),
    }

    quantiles = [0.5, 0.9, 0.95, 0.99]
    q_vals = np.quantile(abs_dphi, quantiles)
    for q, v in zip(quantiles, q_vals):
        stats[f"abs_delta_phi_q{int(q * 100):02d}"] = float(v)

    # Si une grille ref est fournie, on la lit juste pour info
    if args.ref_grid:
        ref_path = Path(args.ref_grid)
        if ref_path.is_file():
            try:
                print(f"[INFO] Lecture de la grille de référence : {ref_path}")
                f_ref = np.loadtxt(ref_path, delimiter=",", skiprows=1, usecols=[0])
                stats["f_ref_min_Hz"] = float(np.min(f_ref))
                stats["f_ref_max_Hz"] = float(np.max(f_ref))
                stats["f_ref_n"] = int(len(f_ref))
            except Exception as exc:  # noqa: BLE001
                print(
                    f"[WARN] Impossible de lire la grille de référence {ref_path}: {exc}"
                )
        else:
            print(f"[WARN] Fichier ref-grid introuvable: {ref_path}")

    # Impression console
    print("\n=== Diagnostics Δphi(f_peak) ===")
    for k in sorted(stats.keys()):
        print(f"{k:>24} : {stats[k]}")

    # Sauvegarde stats JSON
    stats_path = outdir / f"{args.prefix}_stats.json"
    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, sort_keys=True)
    print(f"[INFO] Stats écrites dans : {stats_path}")

    # Sauvegarde CSV enrichi (optionnel mais pratique)
    csv_diag_path = outdir / f"{args.prefix}_samples.csv"
    df.to_csv(csv_diag_path, index=False)
    print(f"[INFO] Echantillons enrichis écrits dans : {csv_diag_path}")

    # Histogramme de Δphi(f_peak)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(
        dphi_wrapped,
        bins=50,
        density=True,
        alpha=0.8,
    )
    xmin, xmax = float(np.min(dphi_wrapped)), float(np.max(dphi_wrapped))
    if abs(xmax - xmin) < 1e-9:
        xmin, xmax = -0.1, 0.1
    ax.set_xlim(xmin, xmax)
    ax.set_xlabel(r"$\Delta\phi(f_\mathrm{peak})$ [rad]")
    ax.set_ylabel("Counts")
    ax.set_title(r"Distribution of $\Delta\phi(f_\mathrm{peak})$ (wrap[-$\pi$,$\pi$))")
    ax.axvline(0.0, color="k", linestyle="--", linewidth=1)

    fig.tight_layout()
    fig_path = outdir / f"{args.prefix}_hist.png"
    fig.savefig(fig_path, dpi=150)
    plt.close(fig)
    print(f"[INFO] Figure écrite dans : {fig_path}")


if __name__ == "__main__":
    main()
