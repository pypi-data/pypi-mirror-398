#!/usr/bin/env python3
"""
apply_poly_unwrap_rebranch.py
Correction polynomiale du résidu de phase via fit sur unwrap(Δφ) et rebranchage 2π.

But
----
À partir d'un CSV phases (avec 'phi_mcgt_cal' et 'phi_ref'), on:
  1) repart de la variante calibrée: phi_mcgt := phi_mcgt_cal (pour éviter l'empilement d'anciennes corrections),
  2) calcule le résidu Δφ = phi_mcgt - phi_ref, l'unwrap,
  3) fit un polynôme de degré D en fonction de x = log10(f) dans une fenêtre de fit [Ffit_lo, Ffit_hi],
  4) rebranche la tendance sur la même branche 2π que le résidu brut dans la fenêtre de fit,
  5) soustrait la tendance rebranchée à phi_mcgt,
  6) recalcule les métriques @20–300 Hz (ou fenètre demandée) sur unwrap(Δφ),
  7) met à jour le JSON méta (metrics_active + bloc poly_correction), en préservant les autres champs (calibration incl.).

Entrées
-------
--csv        : CSV phases (attend colonnes: f_Hz, phi_ref, phi_mcgt_cal ; phi_mcgt sera écrite/écrasée)
--meta       : JSON méta (facultatif; sera créé/mergé si absent)
--degree     : degré du polynôme (défaut: 4)
--fit-window : fenêtre [Hz] de fit (défaut: 30 250)
--metrics-window : fenêtre [Hz] d’évaluation des métriques (défaut: 20 300)
--basis      : base pour x (log10 | hz). Recommandé: log10 (défaut)
--from-column: colonne source pour repartir (défaut: phi_mcgt_cal)
--backup     : si fourni, copie le CSV original vers <CSV>.backup avant écriture
--dry-run    : ne modifie pas le CSV, imprime seulement résultats/métriques

Sorties
-------
- Écrase/écrit 'phi_mcgt' dans le CSV (sauf --dry-run).
- Met à jour <meta>.metrics_active et ajoute/actualise <meta>.poly_correction.

Exemple
-------
python zz-scripts/chapter09/apply_poly_unwrap_rebranch.py \\
  --csv zz-data/chapter09/09_phases_mcgt.csv \\
  --meta zz-data/chapter09/09_metrics_phase.json \\
  --degree 4 --basis log10 --fit-window 30 250 --metrics-window 20 300 --backup

"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
from pathlib import Path

import numpy as np
import pandas as pd


def setup_logger(level: str = "INFO") -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("apply_poly_unwrap_rebranch")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Correction polynomiale unwrap+rebranch de Δφ."
    )
    ap.add_argument("--csv", type=Path, required=True, help="CSV phases (écrit/écrasé)")
    ap.add_argument(
        "--meta",
        type=Path,
        default=Path("zz-data/chapter09/09_metrics_phase.json"),
        help="JSON méta (mis à jour ou créé)",
    )
    ap.add_argument(
        "--degree", type=int, default=4, help="Degré du polynôme (défaut: 4)"
    )
    ap.add_argument(
        "--fit-window",
        nargs=2,
        type=float,
        default=[30.0, 250.0],
        metavar=("F_LO", "F_HI"),
    )
    ap.add_argument(
        "--metrics-window",
        nargs=2,
        type=float,
        default=[20.0, 300.0],
        metavar=("M_LO", "M_HI"),
    )
    ap.add_argument(
        "--basis",
        choices=["log10", "hz"],
        default="log10",
        help="Variable de fit: log10(f) ou f.",
    )
    ap.add_argument(
        "--from-column",
        default="phi_mcgt_cal",
        help="Colonne source pour repartir (défaut: phi_mcgt_cal)",
    )
    ap.add_argument(
        "--backup",
        action="store_true",
        help="Sauvegarde <csv> -> <csv>.backup avant écriture",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="N’écrit pas, affiche seulement métriques",
    )
    ap.add_argument(
        "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
    )
    return ap.parse_args()


def compute_metrics(
    f: np.ndarray, phi_mcgt: np.ndarray, phi_ref: np.ndarray, lo: float, hi: float
) -> tuple[float, float, float, int]:
    mask = (f >= lo) & (f <= hi) & np.isfinite(phi_mcgt) & np.isfinite(phi_ref)
    if not np.any(mask):
        return float("nan"), float("nan"), float("nan"), 0
    d = np.abs(np.unwrap(phi_mcgt[mask] - phi_ref[mask]))
    return (
        float(np.nanmean(d)),
        float(np.nanpercentile(d, 95)),
        float(np.nanmax(d)),
        int(np.sum(mask)),
    )


def main():
    args = parse_args()
    log = setup_logger(args.log_level)

    if not args.csv.exists():
        raise SystemExit(f"CSV introuvable: {args.csv}")

    df = pd.read_csv(args.csv)
    need = {"f_Hz", "phi_ref", args.from_column}
    if not need.issubset(df.columns):
        raise SystemExit(
            f"Colonnes manquantes dans {args.csv} (requis: {sorted(need)})"
        )

    # Repartir d’une base saine (pas d’empilement)
    df["phi_mcgt"] = df[args.from_column].to_numpy(float)

    f = df["f_Hz"].to_numpy(float)
    x = np.log10(f) if args.basis == "log10" else f
    r0 = (df["phi_mcgt"] - df["phi_ref"]).to_numpy(float)
    ru = np.unwrap(r0)

    flo, fhi = map(float, args.fit_window)
    mfit = (f >= flo) & (f <= fhi) & np.isfinite(x) & np.isfinite(ru)
    nfit = int(np.sum(mfit))
    if nfit < max(8, args.degree + 2):
        raise SystemExit(
            f"Trop peu de points valides dans la fenêtre de fit {flo}-{fhi} Hz (n={nfit})."
        )

    # Fit polynôme sur ru(x) dans la fenêtre
    c_desc = np.polyfit(x[mfit], ru[mfit], args.degree)
    trend = np.polyval(c_desc, x)

    # Rebranchage sur la branche du résidu brut r0 dans la fenêtre de fit
    two_pi = 2 * np.pi
    k = int(np.round(np.median((trend[mfit] - r0[mfit]) / two_pi)))
    trend_adj = trend - k * two_pi

    # Appliquer la correction (soustraction)
    phi_corr = df["phi_mcgt"].to_numpy(float) - trend_adj

    # Métriques @ metrics-window sur unwrap(Δφ)
    mlo, mhi = map(float, args.metrics_window)
    mean_abs, p95_abs, max_abs, n = compute_metrics(
        f, phi_corr, df["phi_ref"].to_numpy(float), mlo, mhi
    )

    log.info(
        "Fit: basis=%s, degree=%d, window=[%.1f, %.1f] Hz, points=%d",
        args.basis,
        args.degree,
        flo,
        fhi,
        nfit,
    )
    log.info(
        "Rebranch: k=%d cycles (soustraction de %.6f rad à la tendance).", k, k * two_pi
    )
    log.info(
        "Metrics %g–%g Hz: mean=%.3f  p95=%.3f  max=%.3f  (n=%d)",
        mlo,
        mhi,
        mean_abs,
        p95_abs,
        max_abs,
        n,
    )

    if args.dry_run:
        return

    # Sauvegarde si demandé
    if args.backup:
        bck = args.csv.with_suffix(args.csv.suffix + ".backup")
        try:
            shutil.copyfile(args.csv, bck)
            log.info("Backup écrit → %s", bck)
        except Exception as e:
            log.warning("Backup impossible (%s) — on continue sans.", e)

    # Écrire CSV (phi_mcgt corrigée)
    df["phi_mcgt"] = phi_corr
    df.to_csv(args.csv, index=False)
    log.info("CSV mis à jour → %s", args.csv)

    # Mettre à jour JSON méta (préserver tout le reste)
    meta = {}
    if args.meta and args.meta.exists():
        try:
            meta = json.loads(args.meta.read_text())
        except Exception:
            meta = {}

    meta["metrics_active"] = {
        "mean_abs_20_300": (
            mean_abs
            if (mlo, mhi) == (20.0, 300.0)
            else meta.get("metrics_active", {}).get("mean_abs_20_300", mean_abs)
        ),
        "p95_abs_20_300": (
            p95_abs
            if (mlo, mhi) == (20.0, 300.0)
            else meta.get("metrics_active", {}).get("p95_abs_20_300", p95_abs)
        ),
        "max_abs_20_300": (
            max_abs
            if (mlo, mhi) == (20.0, 300.0)
            else meta.get("metrics_active", {}).get("max_abs_20_300", max_abs)
        ),
        "variant": f"calibrated+poly_deg{args.degree}_{args.basis}_fit{int(flo)}-{int(fhi)}_unwrap_rebranch",
    }

    meta["poly_correction"] = {
        "applied": True,
        "from_column": args.from_column,
        "basis": args.basis,
        "degree": int(args.degree),
        "fit_window_Hz": [flo, fhi],
        "metrics_window_Hz": [mlo, mhi],
        "coeff_desc": [float(x) for x in c_desc],
        "k_cycles": int(k),
    }

    args.meta.write_text(json.dumps(meta, indent=2))
    log.info("JSON méta mis à jour → %s", args.meta)


if __name__ == "__main__":
    main()
