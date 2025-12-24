#!/usr/bin/env python3
"""
Flag milestones de comparaison (chapitre 9).
Usage:
  python zz-scripts/chapter09/flag_milestones.py \
    --csv zz-data/chapter09/09_comparison_milestones.csv \
    --meta zz-data/chapter09/09_comparison_milestones.meta.json \
    --out zz-data/chapter09/09_comparison_milestones.flagged.csv
"""

import argparse
import datetime
import json
from pathlib import Path

import numpy as np
import pandas as pd


def principal_wrap(d):
    # ramène en (-pi, pi]
    return ((d + np.pi) % (2 * np.pi)) - np.pi


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return np.nan


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True, help="CSV milestones input")
    p.add_argument("--meta", required=True, help="Meta JSON to update")
    p.add_argument(
        "--out",
        help="Output flagged CSV (defaults to input with .flagged.csv)",
        default=None,
    )
    p.add_argument(
        "--metrics-window",
        nargs=2,
        type=float,
        default=[20.0, 300.0],
        help="metrics window (Hz)",
    )
    p.add_argument("--sigma-warn", type=float, default=3.0, help="z-score for WARN")
    p.add_argument("--sigma-fail", type=float, default=5.0, help="z-score for FAIL")
    args = p.parse_args()

    csv_path = Path(args.csv)
    meta_path = Path(args.meta)
    out_path = Path(args.out) if args.out else csv_path.with_suffix(".flagged.csv")

    df = pd.read_csv(csv_path)
    # Accept also phi_mcgt_at_fpeak_cal or phi_mcgt_at_fpeak_raw if main absent
    alt_phi_cols = [
        "phi_mcgt_at_fpeak",
        "phi_mcgt_at_fpeak_cal",
        "phi_mcgt_at_fpeak_raw",
    ]

    # find usable phi_mcgt column
    phi_col = None
    for c in alt_phi_cols:
        if c in df.columns:
            phi_col = c
            break
    if phi_col is None:
        raise SystemExit("Aucune colonne phi_mcgt_at_fpeak trouvée (ni .cal/.raw).")

    # ensure columns exist (add missing as NaN)
    for c in ["event", "f_Hz", "obs_phase", "sigma_phase", "classe"]:
        if c not in df.columns:
            df[c] = np.nan

    # compute metrics
    abs_diffs = []
    z_scores = []
    flags = []
    reasons = []
    fmin, fmax = args.metrics_window

    for idx, row in df.iterrows():
        row.get("event", "")
        f = safe_float(row.get("f_Hz", np.nan))
        phi_mcgt = safe_float(row.get(phi_col, np.nan))
        obs = safe_float(row.get("obs_phase", np.nan))
        sigma = safe_float(row.get("sigma_phase", np.nan))
        reason_list = []

        # basic checks
        if not np.isfinite(f) or f <= 0:
            flags.append("FAIL")
            reason_list.append("f_Hz missing/invalid")
            abs_diffs.append(np.nan)
            z_scores.append(np.nan)
            reasons.append("; ".join(reason_list))
            continue

        if not np.isfinite(phi_mcgt):
            flags.append("FAIL")
            reason_list.append(f"{phi_col} missing/invalid")
            abs_diffs.append(np.nan)
            z_scores.append(np.nan)
            reasons.append("; ".join(reason_list))
            continue

        if not np.isfinite(obs):
            # if obs missing: warn
            reason_list.append("obs_phase missing")
            # we'll compute abs diff vs phi_ref if present? For now mark warn.
            flags.append("WARN")
            abs_diffs.append(np.nan)
            z_scores.append(np.nan)
            reasons.append("; ".join(reason_list))
            continue

        # compute abs diff (wrapped)
        d = principal_wrap(phi_mcgt - obs)
        ad = float(np.abs(d))
        abs_diffs.append(ad)

        # sigma logic
        if not np.isfinite(sigma):
            z_scores.append(np.nan)
            # warn: no sigma
            if f < fmin or f > fmax:
                flags.append("WARN")
                reason_list.append("sigma missing; f_peak hors fenêtre metrics")
            else:
                flags.append("WARN")
                reason_list.append("sigma missing")
            z_scores.append(np.nan)
            reasons.append("; ".join(reason_list))
            continue

        if sigma == 0:
            flags.append("FAIL")
            reason_list.append("sigma_phase == 0")
            z_scores.append(np.nan)
            reasons.append("; ".join(reason_list))
            continue

        z = ad / sigma
        z_scores.append(float(z))

        # thresholds
        if z > args.sigma_fail:
            flags.append("FAIL")
            reason_list.append(f"z={z:.2f}>{args.sigma_fail}")
        elif z > args.sigma_warn:
            flags.append("WARN")
            reason_list.append(f"z={z:.2f}>{args.sigma_warn}")
        else:
            flags.append("OK")

        # f window warning
        if f < fmin or f > fmax:
            reason_list.append("f_peak hors fenêtre metrics")
            if flags[-1] == "OK":
                flags[-1] = "WARN"

        reasons.append("; ".join(reason_list) if reason_list else "")

    # attach new columns
    df["_abs_phase_diff_rad"] = abs_diffs
    df["_z_score"] = z_scores
    df["flag"] = flags
    df["flag_reason"] = reasons

    # write flagged csv
    df.to_csv(out_path, index=False)

    # summary
    n_ok = int((df["flag"] == "OK").sum())
    n_warn = int((df["flag"] == "WARN").sum())
    n_fail = int((df["flag"] == "FAIL").sum())
    totals = int(len(df))

    summary = {
        "generated_at": datetime.datetime.now(datetime.UTC)
        .replace(microsecond=0)
        .isoformat()
        + "Z",
        "n_rows_checked": totals,
        "n_ok": n_ok,
        "n_warn": n_warn,
        "n_fail": n_fail,
        "examples_fail": [],
        "examples_warn": [],
    }

    # collect up to 5 examples each
    for label, key in [("FAIL", "examples_fail"), ("WARN", "examples_warn")]:
        sub = df[df["flag"] == label].head(5)
        for _, r in sub.iterrows():
            summary[key].append(
                {
                    "event": r.get("event", ""),
                    "f_Hz": r.get("f_Hz", None),
                    "flag_reason": r.get("flag_reason", ""),
                    "abs_phase_diff": r.get("_abs_phase_diff_rad", None),
                    "sigma_phase": r.get("sigma_phase", None),
                    "z_score": r.get("_z_score", None),
                }
            )

    # update meta json
    try:
        meta = json.loads(Path(meta_path).read_text())
    except Exception:
        meta = {}

    meta.setdefault("flagging_summary", {})
    meta["flagging_summary"].update(summary)
    meta["flagging_summary"]["flagged_csv"] = str(out_path)

    Path(meta_path).write_text(json.dumps(meta, indent=2, ensure_ascii=False))

    print("Flagging done. Summary:", summary)
    print("Flagged csv written to:", out_path)
    print("Meta updated at:", meta_path)


if __name__ == "__main__":
    main()
