#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Pipeline Chapitre 1 - génération des données
# - Lecture robuste des jalons
# - Interpolation PCHIP log-log
# - Lissage Savitzky–Golay pour les dérivées
# - Export des tables normalisées CH01

import argparse
from pathlib import Path
from math import log10

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator, interp1d
from scipy.signal import savgol_filter

plt.rcParams.update(
    {
        "figure.autolayout": True,
        "figure.figsize": (10, 6),
        "axes.titlesize": 14,
        "axes.titlepad": 20,
        "axes.labelsize": 12,
        "axes.labelpad": 12,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.2,
        "font.family": "serif",
    }
)


def read_jalons(path: Path):
    """
    Lecture robuste du fichier de jalons temporels CH01.

    Accepte plusieurs variantes d'en-têtes :
    - T_i / Pref
    - T / P_ref
    - fichier sans header (2 colonnes)
    """
    df = pd.read_csv(path)

    # Harmonisation des noms de colonnes
    if "T_i" in df.columns and "T" not in df.columns:
        df = df.rename(columns={"T_i": "T"})
    if "Pref" in df.columns and "P_ref" not in df.columns:
        df = df.rename(columns={"Pref": "P_ref"})

    # Si toujours pas les bonnes colonnes, on force un header standard
    if not {"T", "P_ref"}.issubset(df.columns):
        df = pd.read_csv(path, header=None, names=["T", "P_ref"])

    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["P_ref"] = pd.to_numeric(df["P_ref"], errors="coerce")
    df = df.dropna().sort_values("T")

    return df["T"].values, df["P_ref"].values


def build_grid(tmin: float, tmax: float, step: float, spacing: str):
    """
    Construit une grille en T sur [tmin, tmax].

    - spacing="log" : pas constant en log10(T)
    - spacing="lin" : pas constant en T
    """
    if spacing == "log":
        n = int((log10(tmax) - log10(tmin)) / step) + 1
        return np.logspace(log10(tmin), log10(tmax), n)
    else:
        n = int((tmax - tmin) / step) + 1
        return np.linspace(tmin, tmax, n)


def compute_p(T_j, P_j, T_grid):
    """
    Interpolation PCHIP en log-log des jalons (T_j, P_j)
    vers la grille T_grid.
    """
    logT = np.log10(T_j)
    logP = np.log10(P_j)
    pchip = PchipInterpolator(logT, logP, extrapolate=True)
    return 10.0 ** pchip(np.log10(T_grid))


def _safe_savgol(y: np.ndarray, window: int, poly: int):
    """
    Savitzky–Golay robuste :
    - force une fenêtre impaire
    - adapte la fenêtre si elle dépasse la taille de y
    - si vraiment trop court, renvoie y tel quel
    """
    n = y.size
    if n == 0:
        return y

    # fenêtre impaire
    if window % 2 == 0:
        window += 1

    if window > n:
        window = n if n % 2 == 1 else n - 1

    if window <= poly + 1:
        # pas assez de points pour un filtrage stable
        return y

    return savgol_filter(y, window_length=window, polyorder=poly)


def main():
    repo_root = Path(__file__).resolve().parents[2]

    parser = argparse.ArgumentParser(
        description="Chapitre 01 – génération des données (pipeline minimal)."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=repo_root / "zz-data" / "chapter01" / "01_timeline_milestones.csv",
        help="Fichier de jalons temporels (T, P_ref).",
    )
    parser.add_argument("--tmin", type=float, default=1e-6, help="T_min (Gyr)")
    parser.add_argument("--tmax", type=float, default=14.0, help="T_max (Gyr)")
    parser.add_argument(
        "--step",
        type=float,
        default=0.01,
        help="Pas en log10(T) si --grid=log, ou en T si --grid=lin.",
    )
    parser.add_argument(
        "--grid",
        choices=["log", "lin"],
        default="log",
        help="Type de grille temporelle (log ou lin).",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=21,
        help="Longueur de fenêtre Savitzky–Golay (impair, ajusté si besoin).",
    )
    parser.add_argument(
        "--poly",
        type=int,
        default=3,
        help="Ordre du polynôme Savitzky–Golay.",
    )

    args = parser.parse_args()

    base = args.csv.parent

    print(f"[CH01] Lecture des jalons depuis: {args.csv}")
    T_j, P_ref = read_jalons(args.csv)

    # ------------------------------------------------------------------
    # 1) Dérivée initiale (optionnelle) à partir de 01_initial_grid_data.dat
    # ------------------------------------------------------------------
    init_path = base / "01_initial_grid_data.dat"
    if init_path.exists():
        print(f"[CH01] Lecture de la grille initiale: {init_path}")
        init_dat = np.loadtxt(init_path)
        T_init, P_init = init_dat[:, 0], init_dat[:, 1]

        dP_raw = np.gradient(P_init, T_init)
        dP_init = _safe_savgol(dP_raw, window=args.window, poly=args.poly)

        df_dinit = pd.DataFrame({"T": T_init, "dP_dT": dP_init})
        df_dinit.to_csv(base / "01_P_derivative_initial.csv", index=False)
    else:
        print(
            f"[CH01] Avertissement: {init_path} introuvable, "
            "01_P_derivative_initial.csv ne sera pas produit."
        )

    # ------------------------------------------------------------------
    # 2) Grille optimisée et interpolation de P(T)
    # ------------------------------------------------------------------
    print("[CH01] Construction de la grille temporelle optimisée…")
    T_grid = build_grid(args.tmin, args.tmax, args.step, args.grid)

    print("[CH01] Interpolation PCHIP log-log sur la grille…")
    P_opt = compute_p(T_j, P_ref, T_grid)

    print("[CH01] Calcul de la dérivée optimisée…")
    dP_opt_raw = np.gradient(P_opt, T_grid)
    dP_opt = _safe_savgol(dP_opt_raw, window=args.window, poly=args.poly)

    # ------------------------------------------------------------------
    # 3) Exports principaux (CSV + DAT)
    # ------------------------------------------------------------------
    print("[CH01] Export des tables principales…")

    df_opt = pd.DataFrame({"T": T_grid, "P_calc": P_opt})
    df_opt.to_csv(base / "01_optimized_data.csv", index=False)

    # Version DAT (grille optimisée)
    np.savetxt(
        base / "01_optimized_grid_data.dat",
        np.column_stack([T_grid, P_opt]),
    )

    # Dérivée optimisée seule
    pd.DataFrame({"T": T_grid, "dP_dT": dP_opt}).to_csv(
        base / "01_P_derivative_optimized.csv", index=False
    )

    # Données + dérivée
    pd.DataFrame({"T": T_grid, "P_calc": P_opt, "dP_dT": dP_opt}).to_csv(
        base / "01_optimized_data_and_derivatives.csv", index=False
    )

    # ------------------------------------------------------------------
    # 4) Écarts relatifs sur les jalons
    # ------------------------------------------------------------------
    print("[CH01] Calcul des écarts relatifs sur les jalons…")
    interp_P = interp1d(T_grid, P_opt, kind="linear", fill_value="extrapolate")
    eps = (interp_P(T_j) - P_ref) / P_ref

    pd.DataFrame({"T": T_j, "epsilon": eps}).to_csv(
        base / "01_relative_error_timeline.csv", index=False
    )

    # ------------------------------------------------------------------
    # 5) Invariant I1 = P / T
    # ------------------------------------------------------------------
    print("[CH01] Calcul des invariants adimensionnels…")
    I1 = P_opt / T_grid
    pd.DataFrame({"T": T_grid, "I1": I1}).to_csv(
        base / "01_dimensionless_invariants.csv", index=False
    )

    print("[CH01] Données du chapitre 1 régénérées avec succès.")


if __name__ == "__main__":
    main()
