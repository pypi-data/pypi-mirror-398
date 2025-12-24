#!/usr/bin/env python3
# verify_z_grid.py
# Vérifie que la grille en z (ou q0⋆) correspond aux paramètres minimum, maximum et pas attendus.

import json
import sys
from pathlib import Path

import numpy as np

# 1. Chargement des méta-paramètres
ROOT = Path(__file__).resolve().parents[2]
PARAMS_FILE = ROOT / "zz-data" / "chapter08" / "08_coupling_params.json"

if not PARAMS_FILE.exists():
    print(f"❌ Fichier de paramètres introuvable : {PARAMS_FILE}")
    sys.exit(1)

with open(PARAMS_FILE, encoding="utf-8") as f:
    params = json.load(f)

xmin = params.get("q0star_min")
xmax = params.get("q0star_max")
npts = params.get("n_points")

# 2. Validation des valeurs
if xmin is None or xmax is None or npts is None:
    print("❌ Paramètres manquants dans le JSON :", params)
    sys.exit(1)

if xmax <= xmin or npts < 2:
    print("❌ Paramètres invalides (xmin < xmax, npts ≥ 2) :", xmin, xmax, npts)
    sys.exit(1)

# 3. Calcul du pas et du nombre de points
dlog = (np.log10(xmax) - np.log10(xmin)) / (npts - 1)
ncalc = int(round((np.log10(xmax) - np.log10(xmin)) / dlog)) + 1

# 4. Affichage des résultats
print("→ Grille attendue :")
print(f"   xmin = {xmin}")
print(f"   xmax = {xmax}")
print(f"   n_points = {npts}")
print(f"   Δlog10 = {dlog:.5f}")
print(f"   points recalculés = {ncalc}")

if ncalc != npts:
    print("⚠️  Le nombre de points recalculé diffère de n_points !")
    sys.exit(2)
else:
    print("✅ Grille conforme aux paramètres.")
