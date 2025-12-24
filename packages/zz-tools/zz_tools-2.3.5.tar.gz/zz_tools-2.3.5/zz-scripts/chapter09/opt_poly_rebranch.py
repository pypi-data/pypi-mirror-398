#!/usr/bin/env python3
"""opt_poly_rebranch.py
Recherche automatique : polynôme (sur unwrap diff) + rebranch entier k optimisé.
Applique la meilleure correction au CSV (backup) et met à jour le JSON métriques.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def p95(a):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    return float(np.percentile(a, 95.0)) if a.size else float("nan")


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--csv",
        type=Path,
        required=True,
        help="Input CSV (use prepoly backup as start)",
    )
    ap.add_argument("--meta", type=Path, required=True, help="JSON meta to update")
    ap.add_argument("--fit-window", nargs=2, type=float, default=[30.0, 250.0])
    ap.add_argument("--metrics-window", nargs=2, type=float, default=[20.0, 300.0])
    ap.add_argument("--degrees", nargs="+", type=int, default=[3, 4, 5])
    ap.add_argument(
        "--bases", nargs="+", choices=["log10", "hz"], default=["log10", "hz"]
    )
    ap.add_argument(
        "--k-range",
        nargs=2,
        type=int,
        default=[-100, 100],
        help="Integer k search range (inclusive)",
    )
    ap.add_argument(
        "--out-csv",
        type=Path,
        default=None,
        help="Output CSV (if omitted, overwrite --csv after backup)",
    )
    ap.add_argument(
        "--out-poly-json",
        type=Path,
        default=None,
        help="Write detailed poly candidate JSON",
    )
    ap.add_argument(
        "--backup", action="store_true", help="Write .backup before overwriting CSV"
    )
    return ap.parse_args()


def basis_x(f: np.ndarray, basis: str) -> np.ndarray:
    if basis == "log10":
        return np.log10(f)
    return f.copy()


def eval_candidate(
    phi_cal: np.ndarray,
    phi_ref: np.ndarray,
    trend: np.ndarray,
    k: int,
    f: np.ndarray,
    m_eval: np.ndarray,
) -> tuple[float, float, float]:
    # apply: candidate = phi_cal - trend - k*2pi
    cand = phi_cal - trend - (k * 2.0 * np.pi)
    # robust diff = unwrap(cand - ref)
    d = np.abs(np.unwrap((cand - phi_ref).astype(float)))
    d_eval = d[m_eval]
    return (
        float(np.nanpercentile(d_eval, 95)) if d_eval.size else float("nan"),
        float(np.nanmean(d_eval)) if d_eval.size else float("nan"),
        float(np.nanmax(d_eval)) if d_eval.size else float("nan"),
    )


def main():
    args = parse_args()
    CSV = args.csv
    META = args.meta
    if not CSV.exists():
        raise SystemExit(f"CSV introuvable: {CSV}")

    df0 = pd.read_csv(CSV)
    if "phi_mcgt_cal" not in df0.columns or "phi_ref" not in df0.columns:
        raise SystemExit("CSV doit contenir au moins 'phi_mcgt_cal' et 'phi_ref'.")

    # output path
    out_csv = args.out_csv if args.out_csv is not None else CSV
    if args.backup:
        bak = out_csv.with_suffix(out_csv.suffix + ".backup")
        df0.to_csv(bak, index=False)

    # arrays
    f_all = df0["f_Hz"].to_numpy(float)
    phi_ref_all = df0["phi_ref"].to_numpy(float)
    phi_cal_all = df0["phi_mcgt_cal"].to_numpy(float)

    f_lo_fit, f_hi_fit = sorted(map(float, args.fit_window))
    f_lo_eval, f_hi_eval = sorted(map(float, args.metrics_window))
    m_fit = (
        (f_all >= f_lo_fit)
        & (f_all <= f_hi_fit)
        & np.isfinite(f_all)
        & np.isfinite(phi_cal_all)
        & np.isfinite(phi_ref_all)
    )
    m_eval = (
        (f_all >= f_lo_eval)
        & (f_all <= f_hi_eval)
        & np.isfinite(f_all)
        & np.isfinite(phi_cal_all)
        & np.isfinite(phi_ref_all)
    )

    if not m_fit.any():
        raise SystemExit("Aucun point pour le fit dans la fenêtre demandée.")

    # unwrap residual used for fitting
    r_raw = (phi_cal_all - phi_ref_all).astype(float)
    r_unwrap = np.unwrap(r_raw)  # unwrap global before fit

    best = None
    candidates = []
    kmin, kmax = args.k_range

    for basis in args.bases:
        x = basis_x(f_all, basis)
        # need finite x in fit
        mask_x = np.isfinite(x) & m_fit
        if not mask_x.any():
            continue
        x_fit = x[mask_x]
        r_fit = r_unwrap[mask_x]
        for deg in args.degrees:
            try:
                c_desc = np.polyfit(x_fit, r_fit, deg)  # coeffs descending
            except Exception as e:
                print("polyfit failed:", e)
                continue
            trend = np.polyval(c_desc, x)
            # scan k
            best_k_for_this = None
            for k in range(kmin, kmax + 1):
                p95_val, mean_val, max_val = eval_candidate(
                    phi_cal_all, phi_ref_all, trend, k, f_all, m_eval
                )
                cand = dict(
                    basis=basis,
                    degree=deg,
                    coeff_desc=[float(x) for x in c_desc.tolist()],
                    k=k,
                    p95=p95_val,
                    mean=mean_val,
                    max=max_val,
                )
                candidates.append(cand)
                if best_k_for_this is None or (
                    p95_val < best_k_for_this[0]
                    or (p95_val == best_k_for_this[0] and mean_val < best_k_for_this[1])
                ):
                    best_k_for_this = (p95_val, mean_val, max_val, k)
            # update global best
            bk = best_k_for_this
            if bk is not None:
                p95_val, mean_val, max_val, kopt = bk
                if best is None or (
                    p95_val < best["p95"]
                    or (p95_val == best["p95"] and mean_val < best["mean"])
                ):
                    best = {
                        "basis": basis,
                        "degree": deg,
                        "coeff_desc": [float(x) for x in c_desc.tolist()],
                        "k": int(kopt),
                        "p95": float(p95_val),
                        "mean": float(mean_val),
                        "max": float(max_val),
                    }

    if best is None:
        raise SystemExit("Aucune solution candidate trouvée.")

    # apply best to data and save
    basis = best["basis"]
    deg = best["degree"]
    c_desc = np.asarray(best["coeff_desc"], float)
    k = int(best["k"])
    x_all = basis_x(f_all, basis)
    trend_all = np.polyval(c_desc, x_all)
    phi_new = phi_cal_all - trend_all - (k * 2.0 * np.pi)

    df_out = df0.copy()
    # write phi_mcgt (we keep phi_mcgt_cal untouched)
    df_out["phi_mcgt"] = phi_new
    out_csv_parent = out_csv.parent
    out_csv_parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(out_csv, index=False)

    # compute final metrics (robust unwrap diff) on eval window
    d = np.abs(np.unwrap((phi_new - phi_ref_all).astype(float)))[m_eval]
    metrics_active = {
        "mean_abs_20_300": float(np.nanmean(d)),
        "p95_abs_20_300": float(np.nanpercentile(d, 95)),
        "max_abs_20_300": float(np.nanmax(d)),
        "variant": f"calibrated+poly_deg{deg}_{basis}_fit{int(f_lo_fit)}-{int(f_hi_fit)}_k{k}",
    }

    # update meta JSON
    meta = json.load(open(META)) if META.exists() else {}
    meta["metrics_active"] = metrics_active
    meta.setdefault("poly_correction", {})  # store details
    meta["poly_correction"].update(
        {
            "applied": True,
            "from_column": "phi_mcgt_cal",
            "basis": basis,
            "degree": deg,
            "fit_window_Hz": [float(f_lo_fit), float(f_hi_fit)],
            "metrics_window_Hz": [float(f_lo_eval), float(f_hi_eval)],
            "coeff_desc": [float(x) for x in c_desc.tolist()],
            "k_cycles": k,
        }
    )
    open(META, "w").write(json.dumps(meta, indent=2))

    if args.out_poly_json:
        json.dump(
            {"candidates": candidates, "best": best},
            open(args.out_poly_json, "w"),
            indent=2,
        )

    print("=== BEST SOLUTION ===")
    print(best)
    print("Metrics_active (written to JSON):", metrics_active)
    print("Updated CSV written to:", str(out_csv))
    if args.backup:
        print("Backup kept at:", str(bak))


if __name__ == "__main__":
    main()
