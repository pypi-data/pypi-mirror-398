#!/usr/bin/env python3
"""
launch_scalar_perturbations_solver.py

Génération du scan brut c_s²(k,a) et δφ/φ(k,a) pour le Chapter 7 — Perturbations scalaires MCGT.

Ce script :
 - lit une configuration INI (grilles, knobs, tolérances, lissage),
 - construit les grilles en k (log) et a (lin),
 - appelle les fonctions compute_cs2(...) et compute_delta_phi(...) du module mcgt,
 - écrit un CSV "raw" unifié (colonnes k,a,cs2_raw,delta_phi_raw),
 - (optionnel) écrit des matrices 2D CS2 / delta_phi,
 - journalise et contrôle les erreurs.
"""

from __future__ import annotations

import argparse
import configparser
import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

# rendre mcgt importable depuis la racine du projet
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# fonctions fournies par le package mcgt (doit être disponible dans PYTHONPATH)
try:
    from mcgt.scalar_perturbations import compute_cs2, compute_delta_phi
except Exception as e:
    raise ImportError(
        "Impossible d'importer compute_cs2 / compute_delta_phi depuis mcgt. "
        "Vérifiez l'installation du package mcgt."
    ) from e


# ---------------------------------------------------------------------------
# Dataclass configuration (structure attendue dans l'INI)
# ---------------------------------------------------------------------------
@dataclass
class PhaseParams:
    # cosmologie (utilisées éventuellement par le solveur)
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

    # découpe / split
    x_split: float
    k_split: float

    # lissage
    derivative_window: int
    derivative_polyorder: int

    # scan knobs
    k0: float
    decay: float
    cs2_param: float
    delta_phi_param: float

    # tolérances
    tolerance_primary: float
    tolerance_order2: float

    # dynamique φ (optionnel)
    phi0_init: float
    phi_inf: float
    a_char: float
    m_phi: float
    m_eff_const: float

    # avancés
    a_eq: float
    freeze_scale: float
    Phi0: float


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------
def safe_git_hash(root: Path) -> str | None:
    """Retourne le hash git HEAD si disponible, sinon None."""
    try:
        if not (root / ".git").exists():
            return None
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True)
        return out.strip()
    except Exception:
        return None


def build_log_grid(
    xmin: float | None,
    xmax: float | None,
    n_points: int | None = None,
    dlog: float | None = None,
) -> np.ndarray:
    """Construit une grille log-uniforme robuste.

    Si xmin/xmax sont None, on applique des valeurs par défaut raisonnables
    pour les cas de fallback (p.ex. smoke tests).
    """
    if xmin is None:
        xmin = 1e-4
    if xmax is None:
        xmax = 1.0

    if xmin <= 0 or xmax <= xmin:
        raise ValueError("xmin doit être > 0 et xmax > xmin.")

    # Cas standard : n_points fourni
    if n_points is not None and n_points > 0:
        return np.logspace(np.log10(xmin), np.log10(xmax), n_points)

    # Alternative : dlog fourni
    if dlog is not None:
        n = int(np.floor((np.log10(xmax) - np.log10(xmin)) / dlog)) + 1
        if n <= 0:
            raise ValueError("Nombre de points nul ou négatif avec ce dlog.")
        return 10 ** (np.log10(xmin) + np.arange(n) * dlog)

    # Fallback pour les configs incomplètes (p.ex. smoke sans n_k explicite)
    n_points = 32
    return np.logspace(np.log10(xmin), np.log10(xmax), n_points)


def load_config(ini_path: Path) -> PhaseParams:
    """Lit un INI flexible et renvoie une PhaseParams."""
    cfg = configparser.ConfigParser(
        interpolation=None, inline_comment_prefixes=("#", ";")
    )
    read = cfg.read(ini_path, encoding="utf-8")
    if not read:
        raise FileNotFoundError(f"INI introuvable ou illisible : {ini_path}")

    # cosmologie (section obligatoire)
    if "cosmologie" not in cfg:
        raise KeyError("Section [cosmologie] manquante dans l'INI.")
    cos = cfg["cosmologie"]
    H0 = cos.getfloat("H0")
    ombh2 = cos.getfloat("ombh2")
    omch2 = cos.getfloat("omch2")
    omk = cos.getfloat("omk")
    tau = cos.getfloat("tau")
    mnu = cos.getfloat("mnu")
    As0 = cos.getfloat("As0")
    ns0 = cos.getfloat("ns0")

    # grille : privilégier [scan] si présent
    if "scan" in cfg and "k_min" in cfg["scan"]:
        s = cfg["scan"]
        k_min = float(s["k_min"])
        k_max = float(s["k_max"])
        dlog = float(s.get("dlog", s.get("dlog_k", 0.01)))
        n_k = int(
            s.get("n_k", max(2, int((np.log10(k_max) - np.log10(k_min)) / dlog) + 1))
        )
        a_min = float(s.get("a_min", 0.0))
        a_max = float(s.get("a_max", 1.0))
        n_a = int(s.get("n_a", 1))
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
        s = cfg["scan"] if "scan" in cfg else {}

        # découpe / split
        seg_cfg = cfg["segmentation"] if cfg.has_section("segmentation") else {}
        x_split = float(s.get("x_split", seg_cfg.get("x_split", 1.0)))
    k_split = x_split

    # lissage
    if "lissage" in cfg:
        cfg_lissage = cfg["lissage"]
        window = int(cfg_lissage.get("derivative_window", cfg_lissage.get("window", 7)))
        polyord = int(
            cfg_lissage.get("derivative_polyorder", cfg_lissage.get("polyorder", 3))
        )
    else:
        window = int(s.get("derivative_window", 7))
        polyord = int(s.get("derivative_polyorder", 3))

    # tolérances
    if "tolerances" in cfg:
        t = cfg["tolerances"]
        tol1 = float(t.get("primary", t.get("tolerance_primary", 0.01)))
        tol2 = float(t.get("order2", t.get("tolerance_order2", 0.10)))
    else:
        tol1 = float(s.get("tolerance_primary", 0.01))
        tol2 = float(s.get("tolerance_order2", 0.10))

    # knobs
    k0 = float(s.get("k0", 1.0))
    decay = float(s.get("decay", 1.0))
    cs2_param = float(s.get("cs2_param", 1.0))
    delta_phi_param = float(s.get("delta_phi_param", 1.0))
    phi0_init = float(s.get("phi0_init", 1.0))
    phi_inf = float(s.get("phi_inf", 1.0))
    a_char = float(s.get("a_char", 1.0))
    m_phi = float(s.get("m_phi", 0.0))
    m_eff_const = float(s.get("m_eff_const", 0.0))

    # dynamique phi optionnelle
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


# ---------------------------------------------------------------------------
# Entrée / sortie et exécution
# ---------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(
        description="Lance le solveur de perturbations scalaires (Chapter 7)."
    )
    p.add_argument(
        "-i", "--ini", required=True, help="Chemin du fichier INI de configuration"
    )
    p.add_argument(
        "--export-raw",
        required=True,
        help="Chemin du CSV raw unifié (k,a,cs2_raw,delta_phi_raw)",
    )
    p.add_argument(
        "--export-2d", action="store_true", help="Exporter matrices 2D (csv)"
    )
    p.add_argument("--n-k", type=int, help="Override du nombre de points en k")
    p.add_argument("--n-a", type=int, help="Override du nombre de points en a")
    p.add_argument(
        "--dry-run", action="store_true", help="Construire les grilles et quitter"
    )
    p.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    p.add_argument("--log-file", help="Fichier de log")
    return p.parse_args()


def main():
    args = parse_args()

    # logger
    logger = logging.getLogger()
    logger.handlers.clear()
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

    # lire INI
    ini_path = Path(args.ini)
    if not ini_path.exists():
        logger.error("INI non trouvé : %s", ini_path)
        sys.exit(1)
    try:
        params = load_config(ini_path)
    except Exception as e:
        logger.exception("Erreur en lisant l'INI : %s", e)
        sys.exit(1)

    # overrides
    if args.n_k:
        params.n_k = args.n_k
        # ajuster dlog pour rester cohérent
        params.dlog = (np.log10(params.k_max) - np.log10(params.k_min)) / max(
            params.n_k - 1, 1
        )
    if args.n_a:
        params.n_a = args.n_a

    # construire grilles
    k_grid = build_log_grid(params.k_min, params.k_max, n_points=params.n_k)
    # Auto-fix: s'assurer que params.k_min/k_max sont toujours définis pour le logging
    try:
        if hasattr(k_grid, "size") and k_grid.size > 0:
            params.k_min = float(k_grid[0])
            params.k_max = float(k_grid[-1])
    except Exception:
        # En cas de problème, on laisse params.k_min/k_max intacts pour ne pas casser l'exécution
        pass
    a_vals = np.linspace(params.a_min, params.a_max, params.n_a)
    logger.info(
        "Grilles : %d k-points entre [%g, %g], %d a-points entre [%g, %g]",
        len(k_grid),
        params.k_min,
        params.k_max,
        len(a_vals),
        params.a_min,
        params.a_max,
    )

    if args.dry_run:
        logger.info("Dry-run demandé. Fin.")
        return

    # Appel du solveur fourni par mcgt
    logger.info("Appel du solveur : compute_cs2 / compute_delta_phi …")
    try:
        cs2_mat = compute_cs2(
            k_grid, a_vals, params
        )  # attente : shape (len(k), len(a))
        phi_mat = compute_delta_phi(k_grid, a_vals, params)  # même shape
    except Exception as e:
        logger.exception("Erreur lors de l'exécution du solveur : %s", e)
        sys.exit(1)

    # vérifications basiques
    if cs2_mat.shape != (len(k_grid), len(a_vals)):
        logger.warning("Shape de cs2_mat inattendue : %s", cs2_mat.shape)
    if phi_mat.shape != (len(k_grid), len(a_vals)):
        logger.warning("Shape de phi_mat inattendue : %s", phi_mat.shape)

    # export raw unifié
    out_raw = Path(args.export_raw)
    out_raw.parent.mkdir(parents=True, exist_ok=True)
    df_raw = pd.DataFrame(
        {
            "k": k_grid.repeat(len(a_vals)),
            "a": np.tile(a_vals, len(k_grid)),
            "cs2_raw": cs2_mat.ravel(),
            "delta_phi_raw": phi_mat.ravel(),
        }
    )
    df_raw.to_csv(out_raw, index=False)
    logger.info("Raw unifié écrit → %s (%d lignes)", out_raw, len(df_raw))

    # export matrices 2D si demandé (format long k,a,val)
    if args.export_2d:
        mat_dir = out_raw.parent
        df_cs2_mat = pd.DataFrame(
            {
                "k": k_grid.repeat(len(a_vals)),
                "a": np.tile(a_vals, len(k_grid)),
                "cs2_matrix": cs2_mat.ravel(),
            }
        )
        df_phi_mat = pd.DataFrame(
            {
                "k": k_grid.repeat(len(a_vals)),
                "a": np.tile(a_vals, len(k_grid)),
                "delta_phi_matrix": phi_mat.ravel(),
            }
        )
        cs2_path = mat_dir / "07_cs2_matrix.csv"
        phi_path = mat_dir / "07_delta_phi_matrix.csv"
        df_cs2_mat.to_csv(cs2_path, index=False)
        df_phi_mat.to_csv(phi_path, index=False)
        logger.info("Matrices 2D exportées → %s , %s", cs2_path, phi_path)

    # écriture d'un méta JSON avec hash git si disponible
    data_dir = out_raw.parent
    meta = {
        "generated_at": datetime.now(UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "n_k": int(len(k_grid)),
        "n_a": int(len(a_vals)),
        "k_min": float(params.k_min),
        "k_max": float(params.k_max),
        "dlog": float(params.dlog),
        "a_min": float(params.a_min),
        "a_max": float(params.a_max),
        "files": [str(out_raw.name)],
    }
    if args.export_2d:
        meta["files"] += ["07_cs2_matrix.csv", "07_delta_phi_matrix.csv"]
    git_h = safe_git_hash(ROOT)
    meta["git_hash"] = git_h or "unknown"
    meta_path = data_dir / "07_meta_perturbations.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    logger.info("Méta écrit → %s", meta_path)

    logger.info("Terminé avec succès.")


if __name__ == "__main__":
    main()
