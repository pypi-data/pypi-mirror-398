#!/usr/bin/env python3
"""
generate_phase_mcgtraw.py

Génère la phase brute MCGT sur une grille log–lin de fréquences,
exporte les résultats en CSV et crée un fichier meta-JSON compagnon.
"""

import argparse
import configparser
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np


# --- Dataclass de paramètres ------------------------------------------------
@dataclass
class PhaseParams:
    m1: float
    m2: float
    q0star: float
    alpha: float
    phi0: float = 0.0
    tc: float = 0.0
    tol: float = 1e-8


# --- Fonctions utilitaires ---------------------------------------------------
def build_loglin_grid(fmin: float, fmax: float, dlog: float) -> np.ndarray:
    logf_min = np.log10(fmin)
    logf_max = np.log10(fmax)
    N = int(np.floor((logf_max - logf_min) / dlog)) + 1
    return 10 ** (logf_min + np.arange(N) * dlog)


def check_log_spacing(grid: np.ndarray, atol: float = 1e-12) -> bool:
    logg = np.log10(grid)
    diffs = np.diff(logg)
    return np.allclose(diffs, diffs[0], atol=atol, rtol=0.0)


# --- Coefficients PN jusqu’à 3.5PN (simplifiés) --------------------------------
_CPN = {
    0: 1,
    2: (3715 / 756 + 55 / 9),
    3: -16 * np.pi,
    4: (15293365 / 508032 + 27145 / 504 + 3085 / 72),
    5: np.pi * (38645 / 756 - 65 / 9) * (1 + 3 * np.log(np.pi)),
    6: (
        11583231236531 / 4694215680 - 640 / 3 * np.pi**2 - 6848 / 21 * np.log(4 * np.pi)
    ),
    7: np.pi * (77096675 / 254016 + 378515 / 1512),
}


def _symmetric_eta(m1: float, m2: float) -> float:
    return (m1 * m2) / (m1 + m2) ** 2


# --- Phase GR (SPA) ----------------------------------------------------------
def phi_gr(freqs: np.ndarray, p: PhaseParams) -> np.ndarray:
    """Phase fréquentielle GR via SPA jusqu’à 3.5PN."""
    M_s = (p.m1 + p.m2) * 4.925490947e-6  # conversion M☉ → s
    eta = _symmetric_eta(p.m1, p.m2)
    v = (np.pi * M_s * freqs) ** (1 / 3)
    series = np.zeros_like(freqs)
    for k, c_k in _CPN.items():
        series += c_k * v**k
    prefac = 3 / (128 * eta) * v ** (-5)
    return 2 * np.pi * freqs * p.tc - p.phi0 - np.pi / 4 + prefac * series


# --- Correcteur analytique ---------------------------------------------------
def corr_phase(
    freqs: np.ndarray, fmin: float, q0star: float, alpha: float
) -> np.ndarray:
    """Correction analytique pour δt = q0star * f^(−alpha)."""
    if np.isclose(alpha, 1.0):
        return 2 * np.pi * q0star * np.log(freqs / fmin)
    return (2 * np.pi * q0star / (1 - alpha)) * (
        freqs ** (1 - alpha) - fmin ** (1 - alpha)
    )


# --- Solveur MCGT ------------------------------------------------------------
def solve_mcgt(freqs: np.ndarray, p: PhaseParams, fmin: float = None) -> np.ndarray:
    """Calcule φ_MCGT(f) = φ_GR(f) − δφ(f) sur la grille `freqs`."""
    freqs = np.asarray(freqs, dtype=float)
    f0 = freqs[0] if fmin is None else fmin
    if not np.all(freqs[1:] > freqs[:-1]):
        raise ValueError("La grille de fréquences doit être strictement croissante.")
    phi_gr_vals = phi_gr(freqs, p)
    delta_phi = corr_phase(freqs, f0, p.q0star, p.alpha)
    return phi_gr_vals - delta_phi


# --- CLI & logging -----------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Génère les phases brutes MCGT (09_phase_run_*.dat)"
    )
    parser.add_argument(
        "-i", "--ini", type=Path, required=True, help="Chemin vers gw_phase.ini"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche un aperçu et n'écrit pas les fichiers",
    )
    parser.add_argument(
        "--export-raw", action="store_true", help="Exporter le CSV et le meta-JSON"
    )
    parser.add_argument(
        "--npts", type=int, help="Override du nombre de points de la grille"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Niveau de verbosité",
    )
    parser.add_argument("--log-file", type=Path, help="Chemin vers un fichier de log")
    return parser.parse_args()


def setup_logger(level: str, logfile: Path = None):
    handlers = [logging.StreamHandler()]
    if logfile:
        handlers.append(logging.FileHandler(logfile, encoding="utf-8"))
    logging.basicConfig(
        level=getattr(logging, level),
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )
    return logging.getLogger(__name__)


# --- Script principal --------------------------------------------------------
def main():
    args = parse_args()
    logger = setup_logger(args.log_level, args.log_file)

    # Lecture de la config
    config = configparser.ConfigParser(
        inline_comment_prefixes=("#", ";"), interpolation=None
    )
    config.read(args.ini)
    scan = config["scan"]

    # Extraction des paramètres
    fmin = scan.getfloat("fmin")
    fmax = scan.getfloat("fmax")
    dlog = scan.getfloat("dlog")
    q0star = scan.getfloat("q0star")
    alpha = scan.getfloat("alpha")
    m1 = scan.getfloat("m1")
    m2 = scan.getfloat("m2")
    phi0 = scan.getfloat("phi0")
    tc = scan.getfloat("tc")
    tol = scan.getfloat("tol")

    # Instanciation des paramètres
    params = PhaseParams(m1, m2, q0star, alpha, phi0, tc, tol)
    logger.info("PhaseParams : %r", params)

    # Construction de la grille
    if args.npts:
        freqs = np.logspace(np.log10(fmin), np.log10(fmax), args.npts)
    else:
        freqs = build_loglin_grid(fmin, fmax, dlog)
    if not check_log_spacing(freqs, atol=tol):
        raise RuntimeError("Espacement log non constant !")
    logger.info("Grille : %d points de %g à %g Hz", len(freqs), freqs[0], freqs[-1])

    # Calcul de la phase MCGT
    phi_mcgt = solve_mcgt(freqs, params, fmin)

    # Préparation des chemins de sortie
    out_dir = Path("zz-data/chapter09")
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"q0star{q0star:.2f}_alpha{alpha:.2f}"
    output_csv = out_dir / f"09_phase_run_{tag}.dat"
    meta_json = output_csv.with_suffix(".meta.json")

    # Dry-run : aperçu
    if args.dry_run:
        print("# sep=,")
        print("# q0star, alpha, f_Hz, phi_mcgt")
        for f, phi in zip(freqs[:5], phi_mcgt[:5], strict=False):
            print(f"{q0star:.2f}, {alpha:.2f}, {f:.6e}, {phi:.6e}")
        return

    # Export du CSV
    if args.export_raw:
        with open(output_csv, "w", encoding="utf-8") as f:
            f.write("# sep=,\n")
            f.write("# q0star, alpha, f_Hz, phi_mcgt\n")
            for f_val, phi_val in zip(freqs, phi_mcgt, strict=False):
                f.write(f"{q0star:.2f}, {alpha:.2f}, {f_val:.6e}, {phi_val:.6e}\n")
        logger.info("CSV exporté → %s", output_csv)

        # Écriture du meta-JSON
        meta_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "q0star": q0star,
            "alpha": alpha,
            "m1": m1,
            "m2": m2,
            "phi0": phi0,
            "tc": tc,
            "tol": tol,
            "fmin_Hz": float(freqs[0]),
            "fmax_Hz": float(freqs[-1]),
            "dlog": dlog,
            "n_points": len(freqs),
            "log_level": args.log_level,
        }
        with open(meta_json, "w", encoding="utf-8") as f_meta:
            json.dump(meta_data, f_meta, indent=2)
        logger.info("Meta-JSON exporté → %s", meta_json)

    # Message de fin
    logger.info("Génération terminée avec succès.")


if __name__ == "__main__":
    main()
