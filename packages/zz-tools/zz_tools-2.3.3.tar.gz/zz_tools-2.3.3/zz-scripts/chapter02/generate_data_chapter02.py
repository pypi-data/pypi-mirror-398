#!/usr/bin/env python3
"""
Pipeline d'intégration chronologique corrigé pour Chapitre 2 (MCGT)
Avec option --spectre pour générer 02_primordial_spectrum_spec.json et fig_00_spectre.png

Génère :
- zz-data/chapter02/02_P_vs_T_grid_data.dat
- zz-data/chapter02/02_P_derivative_data.dat
- zz-data/chapter02/02_timeline_milestones.csv
- zz-data/chapter02/02_relative_error_timeline.csv
- zz-data/chapter02/02_optimal_parameters.json
Et, si --spectre :
- zz-data/chapter02/02_primordial_spectrum_spec.json
- zz-figures/chapter02/02_fig_00_spectrum.png
"""

# --- Section 1 : Imports et configuration ---
import argparse
import json
import logging
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from scipy.optimize import minimize
from scipy.signal import savgol_filter

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

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Paramètres logistiques pré-calibrés depuis 02_optimal_parameters.json
with open("zz-data/chapter02/02_optimal_parameters.json") as f:
    _params = json.load(f)

_segments = _params["segments"]
_low = _segments["low"]

# Pour le pipeline minimal, on utilise le segment "low"
a0 = _low["alpha0"]
ainf = _low["alpha_inf"]
Tc = _low["Tc"]
Delta = _low["Delta"]
Tp = _low["Tp"]

# Grille temporelle T extraite du fichier P(T)
_grid_PT = np.loadtxt("zz-data/chapter02/02_P_vs_T_grid_data.dat")
T = _grid_PT[:, 0]


# --- Section 2 : Fonctions utilitaires ---
def dotP(T, a0, ainf, Tc, Delta, Tp):
    a_log = a0 + (ainf - a0) / (1 + np.exp(-(T - Tc) / Delta))
    a = a_log * (1 - np.exp(-((T / Tp) ** 2)))
    da_log = (
        ((ainf - a0) / Delta)
        * np.exp(-(T - Tc) / Delta)
        / (1 + np.exp(-(T - Tc) / Delta)) ** 2
    )
    da = da_log * (1 - np.exp(-((T / Tp) ** 2))) + a_log * (2 * T / Tp**2) * np.exp(
        -((T / Tp) ** 2)
    )
    return a * T ** (a - 1) + T**a * np.log(T) * da


def integrate(grid, pars, P0):
    dP = dotP(grid, *pars)
    window = 21 if (len(dP) > 21 and 21 % 2 == 1) else (len(dP) - 1)
    dP_s = savgol_filter(dP, window, 3, mode="interp")
    P = np.empty_like(grid)
    P[0] = P0
    for i in range(1, len(grid)):
        P[i] = P[i - 1] + 0.5 * (dP_s[i] + dP_s[i - 1]) * (grid[i] - grid[i - 1])
    return P


def fit_segment(T, P_ref, mask, grid, P0, weights, prim_mask, thresh_primary):
    def objective(theta):
        P = integrate(grid, theta, P0)
        interp = PchipInterpolator(np.log10(grid), np.log10(P), extrapolate=True)
        P_opt = 10 ** interp(np.log10(T[mask]))
        eps = (P_opt - P_ref[mask]) / P_ref[mask]
        penalty = 0.0
        if prim_mask[mask].any():
            excess = np.max(np.abs(eps[prim_mask[mask]])) - thresh_primary
            penalty = 1e8 * max(0, excess) ** 2
        return np.sum((weights[mask] * eps) ** 2) + penalty

    bounds = [(0.1, 1.0), (0.5, 2.0), (0.01, 0.5), (0.005, 0.1), (0.02, 0.5)]
    res = minimize(
        objective,
        x0=[0.3, 1.0, 0.2, 0.02, 0.15],
        bounds=bounds,
        method="L-BFGS-B",
        options={"maxiter": 400},
    )
    return res.x


def parse_args():
    parser = argparse.ArgumentParser(
        description="Pipeline Chapitre 2 (+ option spectre primordial)"
    )
    parser.add_argument(
        "--spectre",
        action="store_true",
        help="Après calibrage, génère 02_primordial_spectrum_spec.json & fig_00_spectre.png",
    )
    return parser.parse_args()


# --- Section 3 : Pipeline principal ---
def main(spectre=False):
    ROOT = Path(__file__).resolve().parents[2]
    DATA_DIR = ROOT / "zz-data" / "chapter02"
    IMG_DIR = ROOT / "zz-figures" / "chapter02"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    # 3.1 Chargement des jalons
    meta = pd.read_csv(DATA_DIR / "02_milestones_meta.csv")
    T = meta["T"].values
    P_ref = meta["P_ref"].values
    cls = meta["classe"].values
    weights = np.where(cls == "primaire", 1.0, 0.1)
    prim_mask = cls == "primaire"
    thresh_primary = 0.01
    thresh_order2 = 0.10

    # 3.2 Définition de la grille et segmentation
    Tmin, Tmax, dlog, T_split = 1e-6, 14.0, 0.01, 0.15

    def make_grid(t0, t1):
        n = int(np.floor((np.log10(t1) - np.log10(t0)) / dlog)) + 1
        return np.logspace(np.log10(t0), np.log10(t1), n)

    grid_low = make_grid(Tmin, T_split)
    mask_low = T_split > T
    P0 = float(P_ref[mask_low][0])
    params_low = fit_segment(
        T, P_ref, mask_low, grid_low, P0, weights, prim_mask, thresh_primary
    )
    P_split = integrate(grid_low, params_low, P0)

    params_high = None
    if mask_low.size and (~mask_low).any():
        grid_high = make_grid(T_split, Tmax)
        params_high = fit_segment(
            T,
            P_ref,
            ~mask_low,
            grid_high,
            P_split[-1],
            weights,
            prim_mask,
            thresh_primary,
        )

    # 3.3 Fusion des segments et export de P(T)
    P_low = integrate(grid_low, params_low, P0)
    if params_high is not None:
        P_high = integrate(grid_high, params_high, P_split[-1])
        T_all = np.hstack([grid_low, grid_high])
        P_all = np.hstack([P_low, P_high])
    else:
        T_all, P_all = grid_low, P_low

    idx = np.argsort(T_all)
    T_all, P_all = T_all[idx], P_all[idx]
    np.savetxt(
        DATA_DIR / "02_P_vs_T_grid_data.dat",
        np.column_stack((T_all, P_all)),
        fmt="%.6e",
        header="T P_calc",
    )

    # 3.4 Export de la dérivée lissée
    if params_high is not None:
        dP_low = dotP(grid_low, *params_low)
        dP_high = dotP(grid_high, *params_high)
        T_der = np.hstack([grid_low, grid_high])
        dP_der = np.hstack([dP_low, dP_high])
        idx2 = np.argsort(T_der)
        T_der, dP_der = T_der[idx2], dP_der[idx2]
    else:
        T_der, dP_der = grid_low, dotP(grid_low, *params_low)

    np.savetxt(
        DATA_DIR / "02_P_derivative_data.dat",
        np.column_stack((T_der, dP_der)),
        fmt="%.6e",
        header="T dotP",
    )

    # 3.5 Recalcul des écarts et export des CSV
    logT = np.log10(T_all)
    logP = np.log10(P_all)
    _, unique_idx = np.unique(logT, return_index=True)
    interp_fn = PchipInterpolator(logT[unique_idx], logP[unique_idx], extrapolate=True)
    P_opt = 10 ** interp_fn(np.log10(T))
    eps = (P_opt - P_ref) / P_ref

    pd.DataFrame(
        {
            "T": T,
            "P_ref": P_ref,
            "P_opt": np.round(P_opt, 6),
            "epsilon_i": np.round(eps, 6),
            "classe": cls,
        }
    ).to_csv(DATA_DIR / "02_timeline_milestones.csv", index=False)

    pd.DataFrame({"T": T, "epsilon_i": np.round(eps, 6)}).to_csv(
        DATA_DIR / "02_relative_error_timeline.csv", index=False
    )

    # Alerte ordre 2
    if (~prim_mask).any():
        eps_o2 = float(np.max(np.abs(eps[~prim_mask])))
        if eps_o2 > thresh_order2:
            logging.warning(f"Max ε_order2 = {eps_o2:.4f} ≥ {thresh_order2 * 100:.0f}%")

    # 3.6 Export des paramètres optimaux
    json_out = {
        "T_split_Gyr": T_split,
        "segments": {
            "low": dict(
                zip(
                    ["alpha0", "alpha_inf", "Tc", "Delta", "Tp"],
                    np.round(params_low, 6).tolist(),
                    strict=False,
                )
            )
        },
        "thresholds": {"primary": thresh_primary, "order2": thresh_order2},
        "max_epsilon_primary": float(np.max(np.abs(eps[prim_mask]))),
        "max_epsilon_order2": float(eps_o2 if (~prim_mask).any() else 0.0),
    }

    if params_high is not None:
        json_out["segments"]["high"] = dict(
            zip(
                ["alpha0", "alpha_inf", "Tc", "Delta", "Tp"],
                np.round(params_high, 6).tolist(),
                strict=False,
            )
        )

    with open(DATA_DIR / "02_optimal_parameters.json", "w", encoding="utf-8") as f:
        json.dump(json_out, f, ensure_ascii=False, indent=2)

    logging.info("Pipeline Chap2 terminé.")

    # --- Section 4 : Génération du spectre primordial (option --spectre) ---
    if spectre:
        # 4.1) Lecture des coefficients F et G
        fg_csv = DATA_DIR / "02_FG_series.csv"
        df_fg = pd.read_csv(fg_csv)

        # extraire c1, c1_2, c2, c2_2 depuis le CSV
        c1 = float(df_fg[(df_fg.fonc == "F") & (df_fg.ordre == 1)].coeff)
        c1_2 = float(df_fg[(df_fg.fonc == "F") & (df_fg.ordre == 2)].coeff)
        c2 = float(df_fg[(df_fg.fonc == "G") & (df_fg.ordre == 1)].coeff)
        c2_2 = float(df_fg[(df_fg.fonc == "G") & (df_fg.ordre == 2)].coeff)

        # 4.2) Construction du JSON de métadonnées du spectre
        spec = {
            "label_eq": "eq:spec_prim",
            "formule": "P_R(k;α)=A_s(α) k^{n_s(α)-1}",
            "description": "Spectre primordial modifié MCGT – Paramètres Planck 2018",
            "constantes": {"A_s0": 2.10e-9, "ns0": 0.9649},
            "coefficients": {"c1": c1, "c1_2": c1_2, "c2": c2, "c2_2": c2_2},
        }
        out_spec = DATA_DIR / "02_primordial_spectrum_spec.json"
        with open(out_spec, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)
        logging.info(f"02_primordial_spectrum_spec.json généré → {out_spec}")

        # 4.3) Tracé de la figure d’exemple
        subprocess.run(
            [
                "python3",
                str(ROOT / "zz-scripts" / "chapter02" / "plot_fig00_spectrum.py"),
            ],
            check=True,
        )
        logging.info("fig_00_spectre.png générée.")


if __name__ == "__main__":
    args = parse_args()
    main(spectre=args.spectre)
    print("✅ Génération Chapitre 2 OK")
