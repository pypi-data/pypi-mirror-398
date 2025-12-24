#!/usr/bin/env python3
# ruff: noqa: E402
"""
generate_data_chapter07.py

Génération du scan brut c_s²(k,a) et δφ/φ(k,a) pour le Chapitre 7 – Perturbations scalaires MCGT.
Version francisée : noms d'arguments et fichiers en français (identique en logique).
"""

import argparse
import configparser
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# rendre mcgt importable
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcgt.scalar_perturbations import (
    compute_cs2,
    compute_delta_phi,
)  # noqa: E402  # noqa: E402


@dataclass
class PhaseParams:
    # cosmologie
    H0: float
    ombh2: float
    omch2: float
    omk: float
    tau: float
    mnu: float
    As0: float
    ns0: float
    # grille
    k_min: float
    k_max: float
    dlog: float
    n_k: int
    a_min: float
    a_max: float
    n_a: int
    # découpe/grille secondaire
    x_split: float
    k_split: float  # alias pour compute_delta_phi
    # lissage
    derivative_window: int
    derivative_polyorder: int
    # scan knobs
    k0: float
    decay: float
    cs2_param: float
    delta_phi_param: float
    tolerance_primary: float
    tolerance_order2: float
    # dynamique φ
    phi0_init: float
    phi_inf: float
    a_char: float
    m_phi: float
    m_eff_const: float
    # paramètres dynamique φ avancés
    a_eq: float
    freeze_scale: float
    Phi0: float


def load_config(ini_path: Path) -> PhaseParams:
    cfg = configparser.ConfigParser(
        interpolation=None, inline_comment_prefixes=("#", ";")
    )
    cfg.read(ini_path, encoding="utf-8")

    # 1) section cosmologie
    cos = cfg["cosmologie"]
    H0 = cos.getfloat("H0")
    ombh2 = cos.getfloat("ombh2")
    omch2 = cos.getfloat("omch2")
    omk = cos.getfloat("omk")
    tau = cos.getfloat("tau")
    mnu = cos.getfloat("mnu")
    As0 = cos.getfloat("As0")
    ns0 = cos.getfloat("ns0")

    # 2) section scan ou fallback grille
    if "scan" in cfg and "k_min" in cfg["scan"]:
        s = cfg["scan"]
        k_min = float(s["k_min"])
        k_max = float(s["k_max"])
        dlog = float(s.get("dlog", s.get("dlog_k")))
        n_k = int(s["n_k"])
        a_min = float(s["a_min"])
        a_max = float(s["a_max"])
        n_a = int(s["n_a"])
    else:
        g1 = cfg["grille1D"]
        g2 = cfg["grille2D"]
        k_min = g1.getfloat("k_min")
        k_max = g1.getfloat("k_max")
        dlog = g1.getfloat("dlog_k")
        n_k = g1.getint("n_k")
        a_min = g2.getfloat("a_min")
        a_max = g2.getfloat("a_max")
        n_a = g2.getint("n_a")
        s = cfg["scan"]

    # 3) x_split depuis scan ou segmentation
    raw_xsplit = s.get("x_split")
    x_split = (
        float(raw_xsplit)
        if raw_xsplit is not None
        else cfg["segmentation"].getfloat("x_split")
    )
    k_split = x_split  # aliased for compute_delta_phi

    # 4) lissage (section [lissage] ou fallback)
    if "lissage" in cfg:
        cfg_lissage = cfg["lissage"]
        window = int(cfg_lissage.get("derivative_window", cfg_lissage.get("window")))
        polyord = int(
            cfg_lissage.get("derivative_polyorder", cfg_lissage.get("polyorder"))
        )
    else:
        window = int(s["derivative_window"])
        polyord = int(s["derivative_polyorder"])

    # 5) tolérances (section [tolerances] ou fallback)
    if "tolerances" in cfg:
        t = cfg["tolerances"]
        tol1 = float(t.get("primary", t.get("tolerance_primary")))
        tol2 = float(t.get("order2", t.get("tolerance_order2")))
    else:
        tol1 = float(s.get("tolerance_primary", s.get("primary")))
        tol2 = float(s.get("tolerance_order2", s.get("order2")))

    # 6) knobs scan
    k0 = float(s["k0"])
    decay = float(s["decay"])
    cs2_param = float(s["cs2_param"])
    delta_phi_param = float(s["delta_phi_param"])
    phi0_init = float(s["phi0_init"])
    phi_inf = float(s["phi_inf"])
    a_char = float(s["a_char"])
    m_phi = float(s.get("m_phi", 1.0))
    m_eff_const = float(s.get("m_eff_const", 1.0))

    # 7) dynamique phi (optionnel)
    if "dynamique_phi" in cfg:
        dyn = cfg["dynamique_phi"]
        a_eq = float(dyn.get("a_eq", phi0_init))
        freeze_scale = float(dyn.get("freeze_scale", 1.0))
        Phi0 = float(dyn.get("Phi0", phi0_init))
    else:
        a_eq = phi0_init
        freeze_scale = 1.0
        Phi0 = phi0_init

    return PhaseParams(
        H0=H0,
        ombh2=ombh2,
        omch2=omch2,
        omk=omk,
        tau=tau,
        mnu=mnu,
        As0=As0,
        ns0=ns0,
        k_min=k_min,
        k_max=k_max,
        dlog=dlog,
        n_k=n_k,
        a_min=a_min,
        a_max=a_max,
        n_a=n_a,
        x_split=x_split,
        k_split=k_split,
        derivative_window=window,
        derivative_polyorder=polyord,
        k0=k0,
        decay=decay,
        cs2_param=cs2_param,
        delta_phi_param=delta_phi_param,
        tolerance_primary=tol1,
        tolerance_order2=tol2,
        phi0_init=phi0_init,
        phi_inf=phi_inf,
        a_char=a_char,
        m_phi=m_phi,
        m_eff_const=m_eff_const,
        a_eq=a_eq,
        freeze_scale=freeze_scale,
        Phi0=Phi0,
    )


def parse_args():
    p = argparse.ArgumentParser(
        description="Génère le scan brut c_s²(k,a) et δφ/φ(k,a) pour le Chapitre 7."
    )
    p.add_argument("-i", "--ini", required=True, help="INI de config")
    p.add_argument("--export-raw", required=True, help="CSV brut unifié (sortie)")
    p.add_argument("--export-2d", action="store_true", help="Exporter matrices 2D")
    p.add_argument("--n-k", type=int, metavar="NK", help="Override # points k")
    p.add_argument("--n-a", type=int, metavar="NA", help="Override # points a")
    p.add_argument("--dry-run", action="store_true", help="Valide config et grille")
    p.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Niveau log",
    )
    p.add_argument("--log-file", metavar="FILE", help="Fichier log")
    return p.parse_args()


def main():
    args = parse_args()

    # Logging
    logger = logging.getLogger()
    fmt = logging.Formatter("[%(levelname)s] %(message)s")
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    logger.setLevel(args.log_level.upper())
    if args.log_file:
        lf = Path(args.log_file)
        lf.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(lf)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    # Charger config
    ini_path = Path(args.ini)
    if not ini_path.exists():
        logger.error("INI non trouvé : %s", ini_path)
        sys.exit(1)
    p = load_config(ini_path)

    # Overrides grille
    if args.n_k:
        p.n_k = args.n_k
        if p.k_min is None:
            p.k_min = 1.0e-4
        if p.k_max is None:
            p.k_max = 1.0
        if p.n_k is None or p.n_k < 2:
            logger.warning("n_k absent ou invalide (n_k=%s); fallback n_k=32", p.n_k)
            p.n_k = 32
        p.dlog = (np.log10(p.k_max) - np.log10(p.k_min)) / (p.n_k - 1)
    if args.n_a:
        p.n_a = args.n_a

    # Construire grilles
    k_min = p.k_min if p.k_min is not None else 1e-4
    k_max = p.k_max if p.k_max is not None else 1.0
    if k_min <= 0 or k_max <= k_min:
        raise ValueError(f"Invalid grid bounds: k_min={k_min}, k_max={k_max}")
    k_grid = np.logspace(np.log10(k_min), np.log10(k_max), p.n_k)
    a_vals = np.linspace(p.a_min, p.a_max, p.n_a)
    logger.info("Grilles : %d k-points × %d a-points", len(k_grid), len(a_vals))

    if args.dry_run:
        logger.info("Dry-run uniquement : pas de calcul.")
        return

    # Exécution solveur
    logger.info("Exécution du solveur MCGT…")
    cs2_mat = compute_cs2(k_grid, a_vals, p)
    phi_mat = compute_delta_phi(k_grid, a_vals, p)

    # Export brut unifié
    brut_path = Path(args.export_raw)
    brut_path.parent.mkdir(parents=True, exist_ok=True)
    df_brut = pd.DataFrame(
        {
            "k": k_grid.repeat(len(a_vals)),
            "a": np.tile(a_vals, len(k_grid)),
            "cs2_brut": cs2_mat.ravel(),
            "delta_phi_brut": phi_mat.ravel(),
        }
    )
    df_brut.to_csv(brut_path, index=False)
    logger.info("Brut unifié écrit → %s", brut_path)

    # Export matrices 2D
    if args.export_2d:
        mat_dir = brut_path.parent
        pd.DataFrame(
            {
                "k": k_grid.repeat(len(a_vals)),
                "a": np.tile(a_vals, len(k_grid)),
                "cs2_matrice": cs2_mat.ravel(),
            }
        ).to_csv(mat_dir / "07_cs2_matrix.csv", index=False)
        pd.DataFrame(
            {
                "k": k_grid.repeat(len(a_vals)),
                "a": np.tile(a_vals, len(k_grid)),
                "delta_phi_matrice": phi_mat.ravel(),
            }
        ).to_csv(mat_dir / "07_delta_phi_matrix.csv", index=False)
        logger.info("Matrices 2D exportées → %s", mat_dir)


if __name__ == "__main__":
    main()
