import argparse
import logging
from pathlib import Path

import numpy as np

from mcgt.constants import H0_KM_S_PER_MPC as H0  # unified

# --- Configuration logging ---
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# --- Chemins ---
ROOT = Path(__file__).resolve().parents[2]
# English folder name for configuration
CONF_DIR = ROOT / "zz-configuration"
OUT_FILE = CONF_DIR / "pdot_plateau_z.dat"
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# --- Paramètres cosmologiques par défaut ---
# H0 unifié → import
ombh2 = 0.0224
omch2 = 0.12
tau = 0.06

# --- CLI ---
parser = argparse.ArgumentParser(description="Génère pdot_plateau_z.dat")
parser.add_argument("--zmin", type=float, default=1e-4, help="Redshift minimal")
parser.add_argument("--zmax", type=float, default=1e5, help="Redshift maximal")
parser.add_argument("--npoints", type=int, default=1000, help="Nombre de points")
args = parser.parse_args()

# --- Grille de redshift log-uniforme ---
log_z = np.linspace(np.log10(args.zmin), np.log10(args.zmax), args.npoints)
z_grid = 10**log_z

# --- Calcul de H(z)/H0 pour univers plat ---
h = H0 / 100.0
Omega_m = (ombh2 + omch2) / (h**2)
Omega_L = 1.0 - Omega_m
Hz_over_H0 = np.sqrt(Omega_m * (1 + z_grid) ** 3 + Omega_L)

# --- Export ---
header = "# z    H_over_H0"
np.savetxt(
    OUT_FILE,
    np.column_stack([z_grid, Hz_over_H0]),
    header=header,
    comments="",
    fmt="%.6e  %.6e",
)
logging.info(f"Fichier généré → {OUT_FILE}")

# === MCGT CLI SEED v2 ===
