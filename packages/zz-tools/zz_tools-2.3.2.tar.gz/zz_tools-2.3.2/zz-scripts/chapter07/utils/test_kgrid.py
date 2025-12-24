#!/usr/bin/env python3
"""
zz-scripts/chapter07/utils/test_kgrid.py

Teste et affiche la plage et le nombre de points de la grille k pour le Chapitre 7,
en lisant k_min, k_max et dlog depuis le JSON de méta-paramètres.
"""

# === [PASS5B-SHIM] ===
# Shim minimal pour rendre --help et --out sûrs sans effets de bord.
import os
import sys
import atexit

if any(x in sys.argv for x in ("-h", "--help")):
    try:
        import argparse

        p = argparse.ArgumentParser(add_help=True, allow_abbrev=False)
        p.print_help()
    except Exception:
        print("usage: <script> [options]")
    sys.exit(0)

if any(arg.startswith("--out") for arg in sys.argv):
    os.environ.setdefault("MPLBACKEND", "Agg")
    try:
        import matplotlib.pyplot as plt

        def _no_show(*a, **k):
            pass

        if hasattr(plt, "show"):
            plt.show = _no_show

        # sauvegarde automatique si l'utilisateur a oublié de savefig
        def _auto_save():
            out = None
            for i, a in enumerate(sys.argv):
                if a == "--out" and i + 1 < len(sys.argv):
                    out = sys.argv[i + 1]
                    break
                if a.startswith("--out="):
                    out = a.split("=", 1)[1]
                    break
            if out:
                try:
                    fig = plt.gcf()
                    if fig:
                        # marges raisonnables par défaut
                        try:
                            fig.subplots_adjust(
                                left=0.07, right=0.98, top=0.95, bottom=0.12
                            )
                        except Exception:
                            pass
                        fig.savefig(out, dpi=120)
                except Exception:
                    pass

        atexit.register(_auto_save)
    except Exception:
        pass
# === [/PASS5B-SHIM] ===

import json
from pathlib import Path

import numpy as np


def load_params():
    root = Path(__file__).resolve().parents[3]
    json_path = root / "zz-data" / "chapter07" / "07_params_perturbations.json"
    params = json.loads(json_path.read_text(encoding="utf-8"))
    return params


def main():
    params = load_params()
    kmin = params["k_min"]
    kmax = params["k_max"]
    dlog = params["dlog"]

    # Calcul du nombre de points et création de la grille
    n_k = int((np.log10(kmax) - np.log10(kmin)) / dlog) + 1
    kgrid = np.logspace(np.log10(kmin), np.log10(kmax), n_k)

    # Affichage
    print(f"Grille k : de {kgrid[0]:.1e} à {kgrid[-1]:.1e} h/Mpc")
    print(f"Nombre de points : {len(kgrid)}")


if __name__ == "__main__":
    main()
