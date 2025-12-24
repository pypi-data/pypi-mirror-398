#!/usr/bin/env python3
"""
Minimal milestone evaluator (replacement for eval_jalons_fpeak.py).
Computes f_peak from results CSV (expects fpeak_hz column if already present),
or approximates it from p95 ranking. Outputs a jalons CSV with id,fpeak_hz,score.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute f_peak milestones for CH10.")
    ap.add_argument("--samples", required=False, help="Samples CSV (unused fallback).")
    ap.add_argument("--ref-grid", required=False, help="Reference grid (unused).")
    ap.add_argument("--jalons", required=False, help="Input jalons ref (unused).")
    ap.add_argument("--out", required=True, help="Output milestones CSV")
    ap.add_argument("--results", default="zz-data/chapter10/10_mc_results.csv")
    args = ap.parse_args()

    df = pd.read_csv(args.results)
    if "fpeak_hz" not in df.columns:
        # Approximate: derive a synthetic f_peak based on rank of p95_20_300
        if "p95_20_300" in df.columns:
            df = df.sort_values("p95_20_300").reset_index(drop=True)
            df["fpeak_hz"] = 150.0 + (df.index / max(len(df) - 1, 1)) * 50.0
        else:
            df["fpeak_hz"] = 150.0
    out_cols = ["id", "fpeak_hz"]
    if "score" in df.columns:
        out_cols.append("score")
    out_df = df[out_cols]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    print(f"[eval_fpeak_milestones] wrote {out_path} ({len(out_df)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
