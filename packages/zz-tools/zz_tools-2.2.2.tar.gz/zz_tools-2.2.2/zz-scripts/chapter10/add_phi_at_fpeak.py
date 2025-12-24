#!/usr/bin/env python3
# zz-scripts/chapter10/add_phi_at_fpeak.py
"""
Ajoute/garantit les colonnes phi_ref_fpeak et phi_mcgt_fpeak dans un CSV results.
- Retente le calcul sur la grille complète si la version "locale" échoue.
- Wrappe les phases en [-pi, pi).
- Filtre valeurs aberrantes et logge erreurs.

Usage:
python zz-scripts/chapter10/add_phi_at_fpeak.py \
  --results zz-data/chapter10/10_mc_results.circ.csv \
  --ref-grid zz-data/chapter09/09_phases_imrphenom.csv \
  --out zz-data/chapter10/10_mc_results.circ.with_fpeak.csv \
  --thresh 1e3 --backup
"""

from __future__ import annotations

import argparse
import logging
import math
import os
import shutil
from datetime import datetime

import numpy as np
import pandas as pd

from zz_tools import common_io as ci

# imports from your package
from mcgt.backends.ref_phase import compute_phi_ref
from mcgt.phase import phi_mcgt


def wrap_phase(phi):
    """Reduce phi to [-pi, pi). Accepts scalars or numpy arrays."""
    a = np.asarray(phi, dtype=float)
    return (a + np.pi) % (2 * np.pi) - np.pi


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return np.nan


def nearest_index(arr, val):
    arr = np.asarray(arr)
    if arr.size == 0:
        return None
    return int(np.abs(arr - val).argmin())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--results", required=True, help="CSV results input")
    p.add_argument(
        "--ref-grid", required=True, help="CSV reference grid (first col frequencies)"
    )
    p.add_argument(
        "--out", default=None, help="output CSV (if omitted add .with_fpeak.csv)"
    )
    p.add_argument(
        "--thresh",
        type=float,
        default=1e3,
        help="threshold to consider phi aberrant (abs)",
    )
    p.add_argument(
        "--backup", action="store_true", help="write .bak of original results"
    )
    args = p.parse_args()

    # prepare logging
    log_path = "zz-data/chapter10/add_phi_at_fpeak_errors.log"
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    logging.getLogger().addHandler(logging.StreamHandler())

    # read files
    df = pd.read_csv(args.results)
    df = ci.ensure_fig02_cols(df)

    if args.backup:
        bak = args.results + ".bak"
        if not os.path.exists(bak):
            shutil.copy2(args.results, bak)
            logging.info(f"Backup written: {bak}")

    # read reference grid
    try:
        f_ref = np.loadtxt(args.ref_grid, delimiter=",", skiprows=1, usecols=[0])
    except Exception as e:
        logging.error(f"Failed to load ref-grid '{args.ref_grid}': {e}")
        raise

    # sanitize f_ref
    f_ref = np.asarray(f_ref)
    f_ref = f_ref[np.isfinite(f_ref)]
    if f_ref.size < 2:
        raise SystemExit(
            "Critical: ref-grid contains <2 valid frequencies after cleaning."
        )

    # ensure sorted
    if not np.all(np.diff(f_ref) > 0):
        f_ref = np.sort(f_ref)
        logging.info("ref-grid was not strictly increasing: sorted automatically.")

    # prepare output columns (in case already present keep as-is unless overwrite)
    out_phi_ref_col = "phi_ref_fpeak"
    out_phi_mcgt_col = "phi_mcgt_fpeak"

    # create output arrays initialized from existing columns if present
    phi_ref_out = (
        df[out_phi_ref_col].copy()
        if out_phi_ref_col in df.columns
        else pd.Series([np.nan] * len(df), index=df.index)
    )
    phi_mcgt_out = (
        df[out_phi_mcgt_col].copy()
        if out_phi_mcgt_col in df.columns
        else pd.Series([np.nan] * len(df), index=df.index)
    )

    n_problem = 0
    n_fixed = 0

    for i, row in df.iterrows():
        idx = int(row.get("id", i))
        try:
            # if already present and finite and within thresh, skip calc
            existing_ok = False
            if not pd.isna(phi_ref_out.iloc[i]) and not pd.isna(phi_mcgt_out.iloc[i]):
                try:
                    if (
                        abs(float(phi_mcgt_out.iloc[i])) < args.thresh
                        and abs(float(phi_ref_out.iloc[i])) < args.thresh
                    ):
                        existing_ok = True
                except Exception:
                    existing_ok = False
            if existing_ok:
                continue

            m1 = safe_float(row.get("m1"))
            m2 = safe_float(row.get("m2"))
            if math.isnan(m1) or math.isnan(m2):
                raise ValueError("m1/m2 non-numeric")

            # attempt compute phi_ref on full ref grid (robust default)
            try:
                phi_ref_full = compute_phi_ref(f_ref, m1, m2)
                # ensure length matches
                phi_ref_full = np.asarray(phi_ref_full, dtype=float)
                if phi_ref_full.size != f_ref.size:
                    # if compute_phi_ref returned fewer points, still ok; we will pick nearest index via np.abs
                    logging.debug(
                        f"phi_ref length {phi_ref_full.size} != f_ref length {f_ref.size} for id={idx}"
                    )
            except Exception as e:
                logging.warning(
                    f"compute_phi_ref error for id={idx} (m1={m1},m2={m2}): {e}"
                )
                raise

            # choose f_peak: prefer existing 'f_peak' or 'fpeak' column if present and finite
            f_peak = None
            for cand in ("f_peak", "fpeak", "f_peak_Hz", "fpeak_Hz"):
                if cand in df.columns:
                    ft = row.get(cand)
                    if not (pd.isna(ft) or not np.isfinite(safe_float(ft))):
                        f_peak = float(ft)
                        break
            if f_peak is None:
                # fallback: choose a frequency in the band [20,300] if available, else median of f_ref
                f_min, f_max = np.min(f_ref), np.max(f_ref)
                if (
                    (f_min <= 20)
                    and (f_max >= 20)
                    and (f_min <= 300)
                    and (f_max >= 300)
                ):
                    f_peak = 100.0  # generic fallback inside band; we could refine if you have a better rule
                else:
                    f_peak = float(np.median(f_ref))

            # find nearest index in f_ref
            idx_f = nearest_index(f_ref, f_peak)
            if idx_f is None:
                raise RuntimeError("No index found for f_peak in ref-grid")

            # phi_ref at f_peak (pick nearest)
            try:
                phi_ref_at_fpeak = float(phi_ref_full[idx_f])
            except Exception:
                # fallback: try linear interpolation if shapes differ
                try:
                    phi_ref_at_fpeak = float(np.interp(f_peak, f_ref, phi_ref_full))
                except Exception:
                    phi_ref_at_fpeak = float(phi_ref_full.flat[0])

            # compute phi_mcgt (may raise)
            theta = {}
            for key in ("m1", "m2", "q0star", "alpha", "phi0", "tc", "dist", "incl"):
                if key in row:
                    theta[key] = safe_float(row[key])
            try:
                phi_mcgt_full = phi_mcgt(f_ref, theta)
                phi_mcgt_full = np.asarray(phi_mcgt_full, dtype=float)
                # pick nearest
                try:
                    phi_mcgt_at_fpeak = float(phi_mcgt_full[idx_f])
                except Exception:
                    phi_mcgt_at_fpeak = float(np.interp(f_peak, f_ref, phi_mcgt_full))
            except Exception as e:
                logging.warning(f"phi_mcgt error for id={idx}: {e}")
                raise

            # wrap both phases
            phi_ref_wr = wrap_phase(phi_ref_at_fpeak)
            phi_mcgt_wr = wrap_phase(phi_mcgt_at_fpeak)

            # check thresholds
            if (
                abs(phi_ref_wr) > args.thresh
                or abs(phi_mcgt_wr) > args.thresh
                or not np.isfinite(phi_ref_wr)
                or not np.isfinite(phi_mcgt_wr)
            ):
                logging.info(
                    f"Abnormal phi for id={idx}: phi_ref={phi_ref_wr}, phi_mcgt={phi_mcgt_wr} -> set NaN"
                )
                phi_ref_out.iloc[i] = np.nan
                phi_mcgt_out.iloc[i] = np.nan
                n_problem += 1
                continue

            # write outputs
            phi_ref_out.iloc[i] = phi_ref_wr
            phi_mcgt_out.iloc[i] = phi_mcgt_wr
            n_fixed += 1

        except Exception as e:
            n_problem += 1
            logging.info(f"Row id={idx} index={i} -> failed recompute: {e}")
            phi_ref_out.iloc[i] = np.nan
            phi_mcgt_out.iloc[i] = np.nan
            continue

    # attach columns and write output CSV
    df[out_phi_ref_col] = phi_ref_out
    df[out_phi_mcgt_col] = phi_mcgt_out

    out_path = args.out if args.out else args.results + ".with_fpeak.csv"
    # backup if requested already done; write out
    df.to_csv(out_path, index=False)
    # also write a small manifest
    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "input": os.path.abspath(args.results),
        "ref_grid": os.path.abspath(args.ref_grid),
        "n_rows": int(len(df)),
        "n_fixed": int(n_fixed),
        "n_problem": int(n_problem),
        "out": os.path.abspath(out_path),
    }
    manifest_path = out_path + ".manifest.json"
    import json

    with open(manifest_path, "w") as fh:
        json.dump(manifest, fh, indent=2)
    logging.info(f"Wrote: {out_path}  (fixed={n_fixed}, problems={n_problem})")
    logging.info(f"Manifest: {manifest_path}")
    logging.info(f"Error log: {log_path}")


if __name__ == "__main__":
    main()
