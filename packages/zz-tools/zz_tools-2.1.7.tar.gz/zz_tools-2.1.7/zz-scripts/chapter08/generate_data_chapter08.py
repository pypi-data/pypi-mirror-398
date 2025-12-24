#!/usr/bin/env python3
# ruff: noqa: E402
# ---------------------------------------------------------------
# zz-scripts/chapter08/generate_chapter08_data.py
# Pipeline de génération des données – Chapitre 8 (Dark coupling)
# Scan 1D et 2D χ² (axe param2 « phantom » pour la heatmap)
# ---------------------------------------------------------------

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

# --- Permet d’importer cosmo.py depuis utils ---
ROOT = Path(__file__).resolve().parents[2]
UTILS = ROOT / "zz-scripts" / "chapter08" / "utils"
sys.path.insert(0, str(UTILS))
from cosmo import (
    DV,
    Omega_lambda0,
    Omega_m0,
    distance_modulus,
)  # noqa: E402  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(
        description="Génère les données du Chapitre 8 (Dark coupling)"
    )
    p.add_argument(
        "--q0star_min", type=float, required=True, help="Minimum value of q0⋆"
    )
    p.add_argument(
        "--q0star_max", type=float, required=True, help="Maximum value of q0⋆"
    )
    p.add_argument(
        "--n_points", type=int, required=True, help="Number of points in the q0⋆ grid"
    )
    p.add_argument(
        "--export_derivative",
        "--export-derivative",
        dest="export_derivative",
        action="store_true",
        help="Export the smoothed derivative dχ²/dq0⋆",
    )
    p.add_argument(
        "--export_heatmap",
        "--export-heatmap",
        dest="export_heatmap",
        action="store_true",
        help="Export the 2D χ² scan",
    )
    p.add_argument(
        "--param2_min",
        type=float,
        help="Minimum value for the 2nd parameter (with --export-heatmap)",
    )
    p.add_argument(
        "--param2_max",
        type=float,
        help="Maximum value for the 2nd parameter (with --export-heatmap)",
    )
    p.add_argument(
        "--n_param2",
        type=int,
        default=50,
        help="Number of points for the 2nd parameter",
    )
    return p.parse_args()


def load_or_init_params(path: Path, args):
    if path.exists():
        params = json.loads(path.read_text(encoding="utf-8"))
    else:
        params = {
            "thresholds": {"primary": 0.01, "order2": 0.10},
            "max_epsilon_primary": None,
            "max_epsilon_order2": None,
        }
    params.update(
        {
            "q0star_min": args.q0star_min,
            "q0star_max": args.q0star_max,
            "n_points": args.n_points,
        }
    )
    if args.export_heatmap:
        if args.param2_min is None or args.param2_max is None:
            sys.exit("❌ --param2_min & --param2_max required with --export-heatmap")
        params.update(
            {
                "param2_min": args.param2_min,
                "param2_max": args.param2_max,
                "n_param2": args.n_param2,
            }
        )
    return params


def save_params(path: Path, params: dict):
    out = {
        "thresholds": params["thresholds"],
        "max_epsilon_primary": params["max_epsilon_primary"],
        "max_epsilon_order2": params["max_epsilon_order2"],
    }
    if "param2_min" in params:
        out.update(
            {
                "param2_min": params["param2_min"],
                "param2_max": params["param2_max"],
                "n_param2": params["n_param2"],
            }
        )
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")


def build_grid(xmin, xmax, n):
    return np.linspace(xmin, xmax, num=n)


def main():
    # Prepare directories (translated names)
    DATA_DIR = ROOT / "zz-data" / "chapter08"
    FIG_DIR = ROOT / "zz-figures" / "chapter08"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    args = parse_args()
    params_file = DATA_DIR / "08_params_coupling.json"
    params = load_or_init_params(params_file, args)

    # Load observed data (filenames translated)
    bao = pd.read_csv(DATA_DIR / "08_bao_data.csv", encoding="utf-8")
    pant = pd.read_csv(DATA_DIR / "08_pantheon_data.csv", encoding="utf-8")
    jalons = pd.read_csv(DATA_DIR / "08_coupling_milestones.csv", encoding="utf-8")

    # Cleaning
    bao = bao[bao.z > 0].drop_duplicates("z").sort_values("z")
    pant = pant[pant.z > 0].drop_duplicates("z").sort_values("z")

    # Physical filter on q0⋆
    zs = np.unique(np.concatenate([bao.z.values, pant.z.values]))
    bound = -(Omega_m0 * (1 + zs) ** 3 + Omega_lambda0) / (1 + zs) ** 2
    q_phys_min = bound.max()
    print(f">>> Physical domain : q0⋆ ≥ {q_phys_min:.4f}")

    # q0⋆ grid
    q0 = build_grid(params["q0star_min"], params["q0star_max"], params["n_points"])
    q0 = q0[q0 >= q_phys_min]
    print(f">>> q0_grid filtered : {q0[0]:.3f} → {q0[-1]:.3f} ({len(q0)} pts)")

    # 1D χ² scan
    chi2 = []
    for q in q0:
        dv = np.array([DV(z, q) for z in bao.z])
        mu = np.array([distance_modulus(z, q) for z in pant.z])
        cb = ((dv - bao.DV_obs) / bao.sigma_DV) ** 2
        cs = ((mu - pant.mu_obs) / pant.sigma_mu) ** 2
        chi2.append(cb.sum() + cs.sum())
    chi2 = np.array(chi2)

    # optimal q0⋆
    iopt = np.argmin(chi2)
    qbest = q0[iopt]
    print(f">>> optimal q0⋆ = {qbest:.4f}")

    # Export DV_th(z) (translated filename)
    zbao = bao.z.values
    dvb = np.array([DV(z, qbest) for z in zbao])
    pd.DataFrame({"z": zbao, "DV_calc": dvb}).to_csv(
        DATA_DIR / "08_dv_theory_z.csv", index=False
    )
    print(">>> Exported 08_dv_theory_z.csv")

    # Export mu_th(z) (translated filename)
    zsn = pant.z.values
    mub = np.array([distance_modulus(z, qbest) for z in zsn])
    pd.DataFrame({"z": zsn, "mu_calc": mub}).to_csv(
        DATA_DIR / "08_mu_theory_z.csv", index=False
    )
    print(">>> Exported 08_mu_theory_z.csv")

    # Export 1D scan
    pd.DataFrame({"q0star": q0, "chi2_total": chi2, "chi2_err": 0.10 * chi2}).to_csv(
        DATA_DIR / "08_chi2_total_vs_q0.csv", index=False
    )
    print(">>> Exported 08_chi2_total_vs_q0.csv")

    # Smoothed derivative
    if args.export_derivative:
        d1 = np.gradient(chi2, q0)
        w = min(7, 2 * (len(d1) // 2) + 1)
        ds = savgol_filter(d1, w, polyorder=3, mode="interp")
        pd.DataFrame({"q0star": q0, "dchi2_smooth": ds}).to_csv(
            DATA_DIR / "08_dchi2_dq0.csv", index=False
        )
        print(">>> Exported 08_dchi2_dq0.csv")

    # 2D χ² scan (heatmap)
    if args.export_heatmap:
        p2 = build_grid(params["param2_min"], params["param2_max"], params["n_param2"])
        rows = []
        for q in q0:
            for val in p2:
                # val is not used in DV/μ
                dv = np.array([DV(z, q) for z in bao.z])
                mu = np.array([distance_modulus(z, q) for z in pant.z])
                cb = ((dv - bao.DV_obs) / bao.sigma_DV) ** 2
                cs = ((mu - pant.mu_obs) / pant.sigma_mu) ** 2
                rows.append(
                    {"q0star": q, "param2": val, "chi2": float(cb.sum() + cs.sum())}
                )
        pd.DataFrame(rows).to_csv(DATA_DIR / "08_chi2_scan2D.csv", index=False)
        print(">>> Exported 08_chi2_scan2D.csv")

    # Epsilons ε
    eps = []
    for _, r in jalons.iterrows():
        pred = DV(r.z, 0.0) if r.jalon.startswith("BAO") else distance_modulus(r.z, 0.0)
        eps.append(abs(pred - r.obs) / r.obs)
    jalons["epsilon"] = eps
    params["max_epsilon_primary"] = float(
        jalons.query("classe=='primaire'")["epsilon"].max()
    )
    params["max_epsilon_order2"] = float(
        jalons.query("classe=='ordre2'")["epsilon"].max()
    )
    save_params(params_file, params)

    print("✅ Chapter 8 data generated successfully")


if __name__ == "__main__":
    main()
