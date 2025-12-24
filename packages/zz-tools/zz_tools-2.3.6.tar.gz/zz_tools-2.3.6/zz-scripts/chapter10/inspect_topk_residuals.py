#!/usr/bin/env python3
"""
Inspect top-K / best candidates:
- calcule Δφ_principal selon la règle canonique (k@20-300)
- écrit CSV per-sample: f_Hz, phi_ref, phi_mcgt, abs_dphi_principal
- sauvegarde overlays + histogramme des résidus (PNG)
Usage: python zz-scripts/chapter10/inspect_topk_residuals.py --ids 3903,1624,...
"""

import argparse
import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


from mcgt.backends.ref_phase import compute_phi_ref
from mcgt.phase import phi_mcgt


def compute_abs_dphi_principal(phi_m, phi_r, f_Hz, window=(20.0, 300.0)):
    # mask window
    mask = (f_Hz >= window[0]) & (f_Hz <= window[1])
    if not mask.any():
        raise ValueError("Fenêtre vide")
    # calculate k as rounded median((phi_m - phi_r)/(2π)) on window, no unwrap
    cycles = (phi_m[mask] - phi_r[mask]) / (2 * np.pi)
    k = int(np.round(np.nanmedian(cycles)))
    # principal residual on full grid
    dphi = ((phi_m - k * 2 * np.pi) - phi_r + np.pi) % (2 * np.pi) - np.pi
    return np.abs(dphi), k


def main(args):
    # load files
    samples = pd.read_csv(args.samples).set_index("id")
    ref = np.loadtxt(args.ref_grid, delimiter=",", skiprows=1, usecols=[0])
    if args.ids:
        ids = [int(x) for x in args.ids.split(",")]
    else:
        best = json.load(open(args.best_json))["top_k"]
        ids = [int(x["id"]) for x in best[: args.k]]
    os.makedirs(args.out_dir, exist_ok=True)

    for id_ in ids:
        row = samples.loc[int(id_)]
        theta = dict(row[["m1", "m2", "q0star", "alpha", "phi0", "tc", "dist", "incl"]])
        phi_r = compute_phi_ref(ref, float(row.m1), float(row.m2))
        phi_m = phi_mcgt(ref, theta)
        abs_dphi, k = compute_abs_dphi_principal(
            phi_m, phi_r, ref, window=(20.0, 300.0)
        )
        # save CSV
        outcsv = os.path.join(args.out_dir, f"10_topresiduals_id{id_:d}.csv")
        df = pd.DataFrame(
            {
                "f_Hz": ref,
                "phi_ref": phi_r,
                "phi_mcgt": phi_m,
                "abs_dphi_principal": abs_dphi,
            }
        )
        df.to_csv(outcsv, index=False, float_format="%.12f")
        print(f"Wrote {outcsv} (k={k})")
        # overlay PNG
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.semilogx(ref, phi_r, label="phi_ref")
        ax.semilogx(ref, phi_m, label="phi_mcgt")
        ax.set_xlabel("f [Hz]")
        ax.set_ylabel("phase [rad]")
        ax.set_title(f"Overlay id={id_:d} (k={k})")
        ax.legend()
        f_png = os.path.join(args.out_dir, f"overlay_id{id_:d}.png")
        fig.savefig(f_png, dpi=150)
        plt.close(fig)
        # resid histogram
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.hist(
            df.loc[(df.f_Hz >= 20) & (df.f_Hz <= 300), "abs_dphi_principal"], bins=30
        )
        ax.set_xlabel("|Δφ_principal| (20–300 Hz) [rad]")
        ax.set_ylabel("counts")
        fig.savefig(os.path.join(args.out_dir, f"dphi_hist_id{id_:d}.png"), dpi=150)
        plt.close(fig)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--samples", default="zz-data/chapter10/10_mc_samples.csv")
    p.add_argument("--ref-grid", default="zz-data/chapter09/09_phases_imrphenom.csv")
    p.add_argument("--best-json", default="zz-data/chapter10/10_mc_best.json")
    p.add_argument("--ids", default=None, help="liste csv d'ids (ex: 3903,1624)")
    p.add_argument("--k", type=int, default=50, help="K top if --ids not provided")
    p.add_argument("--out-dir", default="zz-data/chapter10/topk_residuals")
    args = p.parse_args()
    main(args)
