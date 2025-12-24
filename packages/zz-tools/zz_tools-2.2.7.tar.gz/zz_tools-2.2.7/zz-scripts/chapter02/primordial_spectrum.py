#!/usr/bin/env python3
"""
Module `primordial_spectrum.py`

Définit une petite API pour le spectre primordial MCGT et permet de générer
un fichier JSON de métadonnées (commande CLI).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

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

# --- constantes Planck 2018 (valeurs par défaut) ---
A_S0 = 2.10e-9
NS0 = 0.9649

# --- coefficients MCGT (linéaires) ---
C1 = 1.0
C2 = -0.04

# --- chemins (projet supposé racine 2 niveaux au-dessus) ---
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "zz-data" / "chapter02"
SPEC_FILE = DATA_DIR / "02_primordial_spectrum_spec.json"


def P_R(k: np.ndarray | float, alpha: float) -> np.ndarray:
    """
    Spectre primordial MCGT:
        P_R(k; alpha) = A_s(alpha) * k**(n_s(alpha) - 1)

    où :
        A_s(alpha) = A_S0 * (1 + C1 * alpha)
        n_s(alpha) = NS0 + C2 * alpha

    Args:
        k: scalaire ou tableau de nombres d'onde comobile (h·Mpc^-1)
        alpha: paramètre MCGT (float), attendu dans [-0.1, 0.1]

    Returns:
        np.ndarray: valeurs de P_R(k)
    """
    alpha = float(alpha)
    if not -0.1 <= alpha <= 0.1:
        raise ValueError(f"alpha={alpha} hors du domaine [-0.1, 0.1]")

    k_arr = np.asarray(k, dtype=float)
    As = A_S0 * (1 + C1 * alpha)
    ns = NS0 + C2 * alpha
    return As * (k_arr ** (ns - 1))


def generate_spec() -> None:
    """Génère un petit JSON descriptif du spectre primordial (méta)."""
    spec = {
        "label_eq": "eq:spec_prim",
        "formula": "P_R(k; α) = A_s(α) k^{n_s(α)-1}",
        "description": "Spectre primordial modifié MCGT — paramètres de référence (Planck 2018).",
        "constants": {"A_s0": A_S0, "ns0": NS0},
        "coefficients": {"c1": C1, "c2": C2, "c1_2": 0.0, "c2_2": 0.0},
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SPEC_FILE, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    print(f"Fichier méta généré → {SPEC_FILE}")


if __name__ == "__main__":
    generate_spec()
