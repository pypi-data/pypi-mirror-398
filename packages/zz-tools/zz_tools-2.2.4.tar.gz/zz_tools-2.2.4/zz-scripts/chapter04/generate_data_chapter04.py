#!/usr/bin/env python3
# === [PASS5-AUTOFIX-SHIM] ===
if __name__ == "__main__":
    try:
        import sys
        import os
        import atexit

        _argv = sys.argv[1:]
        # 1) Shim --help universel
        if any(a in ("-h", "--help") for a in _argv):
            import argparse

            _p = argparse.ArgumentParser(
                description="MCGT (shim auto-injecté Pass5)",
                add_help=True,
                allow_abbrev=False,
            )
            _p.add_argument(
                "--out", help="Chemin de sortie pour fig.savefig (optionnel)"
            )
            _p.add_argument(
                "--dpi", type=int, default=120, help="DPI (par défaut: 120)"
            )
            _p.add_argument(
                "--show",
                action="store_true",
                help="Force plt.show() en fin d'exécution",
            )
            # parse_known_args() affiche l'aide et gère les options de base
            _p.parse_known_args()
            sys.exit(0)
        # 2) Shim sauvegarde figure si --out présent (sans bloquer)
        _out = None
        if "--out" in _argv:
            try:
                i = _argv.index("--out")
                _out = _argv[i + 1] if i + 1 < len(_argv) else None
            except Exception:
                _out = None
        if _out:
            os.environ.setdefault("MPLBACKEND", "Agg")
            try:
                import matplotlib.pyplot as plt

                # Neutralise show() pour éviter le blocage en headless
                def _shim_show(*a, **k):
                    pass

                plt.show = _shim_show
                # Récupère le dpi si fourni
                _dpi = 120
                if "--dpi" in _argv:
                    try:
                        _dpi = int(_argv[_argv.index("--dpi") + 1])
                    except Exception:
                        _dpi = 120

                @atexit.register
                def _pass5_save_last_figure():
                    try:
                        fig = plt.gcf()
                        fig.savefig(_out, dpi=_dpi)
                        print(f"[PASS5] Wrote: {_out}")
                    except Exception as _e:
                        print(f"[PASS5] savefig failed: {_e}")
            except Exception:
                # matplotlib indisponible: ignorer silencieusement
                pass
    except Exception:
        # N'empêche jamais le script original d'exécuter
        pass
# === [/PASS5-AUTOFIX-SHIM] ===
"""
generate_data_chapter04.py

Pipeline d’intégration complet et corrigé pour le Chapitre 4 — Invariants adimensionnels
"""

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
from scipy.signal import savgol_filter


def main():
    import os

    print("[DBG] Entrée dans main(), cwd=", os.getcwd())

    # ----------------------------------------------------------------------
    # 0. Configuration des constantes et des chemins de fichiers
    # ----------------------------------------------------------------------
    kappa = 1e-35
    data_dir = "zz-data/chapter04"
    chap3_dir = "zz-data/chapter03"
    p_file = f"{data_dir}/04_P_vs_T.dat"
    r_file = f"{chap3_dir}/03_ricci_fR_vs_T.csv"
    fr_file = f"{chap3_dir}/03_fR_stability_data.csv"
    output_file = f"{data_dir}/04_dimensionless_invariants.csv"

    # ----------------------------------------------------------------------
    # 1. Chargement des données P(T) brutes
    # ----------------------------------------------------------------------
    df_p = pd.read_csv(
        p_file, sep=r"\s+", skiprows=1, header=None, names=["T_Gyr", "P_raw"]
    )
    df_p = df_p.astype({"T_Gyr": float, "P_raw": float})
    print("[DEBUG] df_p.columns:", df_p.columns.tolist())
    print("[DEBUG] premiers T_Gyr   :", df_p["T_Gyr"].values[:5])
    print("[DEBUG] premiers P_raw   :", df_p["P_raw"].values[:5])

    # ----------------------------------------------------------------------
    # 2. Construction de la grille log-uniforme (T ∈ [1e-6, 14] Gyr)
    # ----------------------------------------------------------------------
    Tmin, Tmax = 1e-6, 14.0
    log_min = np.log10(Tmin)
    log_max = np.log10(Tmax)
    log_grid = np.arange(log_min, log_max + 1e-12, 0.01)
    T = 10**log_grid

    # ----------------------------------------------------------------------
    # 3. Interpolation P(T) en log–log via PCHIP (extrapolation lisse)
    # ----------------------------------------------------------------------
    logT_data = np.log10(df_p["T_Gyr"])
    logP_data = np.log10(df_p["P_raw"])
    interp_logP = PchipInterpolator(logT_data, logP_data, extrapolate=True)
    logP = interp_logP(log_grid)
    P = 10**logP

    # ----------------------------------------------------------------------
    # 4. Calcul et lissage de la dérivée dP/dT (Savitzky–Golay)
    # ----------------------------------------------------------------------
    dP = np.gradient(P, T)
    savgol_filter(dP, window_length=21, polyorder=3, mode="interp")

    # ----------------------------------------------------------------------
    # 5. Interpolation de R/R0 vs T (extrapolation lisse)
    # ----------------------------------------------------------------------
    df_r = pd.read_csv(r_file)
    # Harmonisation des types + tri et suppression des doublons pour T_Gyr
    df_r = df_r.astype({"T_Gyr": float, "R_over_R0": float})
    df_r = df_r.sort_values("T_Gyr")
    df_r = df_r.drop_duplicates(subset="T_Gyr", keep="first")
    logT_r = np.log10(df_r["T_Gyr"].values)
    logR_data = np.log10(df_r["R_over_R0"].values)
    interp_logR = PchipInterpolator(logT_r, logR_data, extrapolate=True)
    logR = interp_logR(log_grid)
    R_R0 = 10**logR

    # ----------------------------------------------------------------------
    # 6. Interpolation log–log de f_R(R) pour préserver la précision ∼10⁻⁶
    # ----------------------------------------------------------------------
    # Lecture du CSV exact de f_R(R)
    df_fr = pd.read_csv(fr_file, sep=",", header=0, usecols=["R_over_R0", "f_R"])
    R_fr = df_fr["R_over_R0"].values
    fR_fr = df_fr["f_R"].values

    # DEBUG – contrôler les données brutes
    print("[DEBUG] df_fr.columns       :", df_fr.columns.tolist())
    print("[DEBUG] premiers R_over_R0  :", R_fr[:5])
    print("[DEBUG] premiers f_R        :", fR_fr[:5])

    # Construire l’interpolateur log–log
    logR_fr = np.log10(R_fr)
    logf_fr = np.log10(fR_fr)
    interp_logf = PchipInterpolator(logR_fr, logf_fr, extrapolate=True)

    # Appliquer sur la grille calculée R_R0
    logfR = interp_logf(np.log10(R_R0))
    f_R = 10**logfR

    # Calcul de l’invariant I3 = f_R – 1
    I3 = f_R - 1

    # DEBUG – vérifier ordre de grandeur de I3
    print("[DEBUG] I3 (f_R–1) min/max    :", I3.min(), I3.max())

    # ----------------------------------------------------------------------
    # 7. Calcul des invariants adimensionnels I1, I2 et I3
    # ----------------------------------------------------------------------
    I1 = P / T
    I2 = kappa * T**2
    I3 = 1 - f_R

    # DEBUG – vérifier la variation d'I2 et d'I3
    print("[DEBUG] I2 (κ·T²) premières valeurs:", I2[:5])
    print("[DEBUG] I3 (1 - f_R) premières valeurs  :", I3[:5])

    # ----------------------------------------------------------------------
    # 8. Export du CSV final
    # ----------------------------------------------------------------------
    df_out = pd.DataFrame({"T_Gyr": T, "I1": I1, "I2": I2, "I3": I3})
    df_out.to_csv(output_file, index=False)
    print(f"[✔] Fichier exporté : {output_file}")


if __name__ == "__main__":
    main()
