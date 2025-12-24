#!/usr/bin/env python3
# toy_model_couplage.py
# Génère un toy-model pour tester l’interpolation PCHIP en log-log

import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import PchipInterpolator

# 1. Points de référence (coarse grid)
z_ref = np.logspace(-2, 0, 6)  # de 0.01 à 1.0
y_ref = z_ref**1.5  # toy-fonction y = z^1.5

# 2. Grille fine pour interpolation
z_fine = np.logspace(np.log10(z_ref.min()), np.log10(z_ref.max()), 200)

# 3. Constructeur PCHIP log-log
interp = PchipInterpolator(np.log10(z_ref), np.log10(y_ref), extrapolate=True)
y_interp = 10 ** interp(np.log10(z_fine))

# 4. Préparation du dossier de sortie
ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = ROOT / "zz-figures" / "chapter08"
os.makedirs(FIG_DIR, exist_ok=True)
out_png = FIG_DIR / "fig_00_toy_model_coupling.png"

# 5. Tracé
plt.figure(figsize=(6.5, 4.5))
plt.loglog(z_ref, y_ref, "o", label="Points de référence")
plt.loglog(z_fine, y_interp, "-", label="Interpolation PCHIP")
plt.xlabel("z")
plt.ylabel("y = z^1.5")
plt.title("Toy-model : test interpolation log–log")
plt.grid(True, which="both", ls=":", lw=0.5, alpha=0.7)
plt.legend()
fig.subplots_adjust(left=0.04, right=0.98, bottom=0.06, top=0.96)
plt.savefig(out_png, dpi=300)
print(f"✅ Toy-model enregistré sous : {out_png}")
