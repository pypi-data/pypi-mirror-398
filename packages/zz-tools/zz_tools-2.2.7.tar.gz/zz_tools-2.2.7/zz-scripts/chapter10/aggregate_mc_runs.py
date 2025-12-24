#!/usr/bin/env python3
"""
Aggregate Monte Carlo runs (replacement for aggreger_runs_mc.py).
- Reads a results CSV (production columns).
- Writes an aggregated CSV (here: simple copy) and a best.json (top-K by score or p95).
This is a lightweight stand-in so the pipeline can execute end-to-end.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser(description="Aggregate MC runs for CH10.")
    ap.add_argument("--out-results", required=True, help="Aggregated CSV output")
    ap.add_argument("--out-best", required=True, help="Top-K JSON output")
    ap.add_argument("--results", default="zz-data/chapter10/10_mc_results.csv")
    ap.add_argument("--K", type=int, default=50)
    args = ap.parse_args()

    df = pd.read_csv(args.results)
    # Choose score column
    score_col = "score" if "score" in df.columns else None
    if score_col is None and "p95_20_300" in df.columns:
        score_col = "p95_20_300"
    if score_col:
        df = df.sort_values(score_col, ascending=True).reset_index(drop=True)
    # Write aggregated CSV (simple copy)
    out_csv = Path(args.out_results)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)

    # Best JSON: top-K rows as list of dicts
    topk = df.head(args.K)
    out_best = Path(args.out_best)
    out_best.parent.mkdir(parents=True, exist_ok=True)
    with out_best.open("w", encoding="utf-8") as f:
        json.dump(topk.to_dict(orient="records"), f, indent=2, ensure_ascii=False)
    print(f"[aggregate_mc_runs] wrote {out_csv} and {out_best} (K={len(topk)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
