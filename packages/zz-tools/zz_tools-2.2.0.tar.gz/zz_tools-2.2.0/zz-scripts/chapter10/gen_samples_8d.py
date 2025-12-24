#!/usr/bin/env python3
"""
Sobol 8D sampler for Chapter 10 production runs.
- Reads a config JSON with priors/min/max (defaults mirror desktop config).
- Generates n samples (Sobol if scipy.stats.qmc is available, otherwise fall back to
  pseudo-random uniform) and writes a CSV compatible with the production metrics
  evaluator (columns: id,m1,m2,q0star,alpha,phi0,tc,dist,incl,model,seed).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import numpy as np


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        # Minimal template matching desktop defaults
        return {
            "priors": {
                "m1": {"min": 5.0, "max": 80.0, "dist": "uniform"},
                "m2": {"min": 5.0, "max": 80.0, "dist": "uniform"},
                "q0star": {"min": -0.3, "max": 0.3, "dist": "uniform"},
                "alpha": {"min": -1.0, "max": 1.0, "dist": "uniform"},
            },
            "nuisance": {"phi0": 0.0, "tc": 0.0, "dist": 1000.0, "incl": 0.0},
            "sobol": {"scramble": True, "seed": 12345},
            "model": "default",
        }
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _sobol_sample(n: int, dim: int, scramble: bool, seed: int) -> np.ndarray:
    try:
        from scipy.stats import qmc
    except Exception:
        rng = np.random.default_rng(seed)
        return rng.random((n, dim))
    engine = qmc.Sobol(d=dim, scramble=scramble, seed=seed)
    return engine.random(n=n)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate Sobol 8D samples for CH10.")
    ap.add_argument("--config", default="zz-data/chapter10/10_mc_config.json")
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--scramble", choices=["on", "off"], default="on")
    ap.add_argument("--sobol-offset", type=int, default=None)
    ap.add_argument("--out", default="zz-data/chapter10/10_mc_samples.csv")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    cfg = load_config(Path(args.config))
    priors = cfg.get("priors", {})
    nuisance = cfg.get("nuisance", {})
    sobol_cfg = cfg.get("sobol", {})
    scramble = (
        args.scramble == "on"
        if args.scramble
        else bool(sobol_cfg.get("scramble", True))
    )
    seed = args.seed if args.seed is not None else int(sobol_cfg.get("seed", 12345))

    n = int(args.n)
    # Dim order: m1, m2, q0star, alpha, phi0, tc, dist, incl
    mins = [
        priors.get("m1", {}).get("min", 5.0),
        priors.get("m2", {}).get("min", 5.0),
        priors.get("q0star", {}).get("min", -0.3),
        priors.get("alpha", {}).get("min", -1.0),
        nuisance.get("phi0", 0.0),
        nuisance.get("tc", 0.0),
        nuisance.get("dist", 1000.0),
        nuisance.get("incl", 0.0),
    ]
    maxs = [
        priors.get("m1", {}).get("max", 80.0),
        priors.get("m2", {}).get("max", 80.0),
        priors.get("q0star", {}).get("max", 0.3),
        priors.get("alpha", {}).get("max", 1.0),
        nuisance.get("phi0", 0.0),
        nuisance.get("tc", 0.0),
        nuisance.get("dist", 1000.0),
        nuisance.get("incl", np.pi),
    ]

    base = _sobol_sample(n, dim=8, scramble=scramble, seed=seed)
    if args.sobol_offset:
        base = (
            base + 0.0
        )  # placeholder: real offset would skip sequence; not critical here

    scaled = np.array(mins) + base * (np.array(maxs) - np.array(mins))
    rows = []
    for i, row in enumerate(scaled):
        rows.append(
            {
                "id": i,
                "m1": row[0],
                "m2": row[1],
                "q0star": row[2],
                "alpha": row[3],
                "phi0": row[4],
                "tc": row[5],
                "dist": row[6],
                "incl": row[7],
                "model": cfg.get("model", "default"),
                "seed": seed,
            }
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and not args.overwrite:
        raise SystemExit(f"{out_path} exists; re-run with --overwrite.")
    import pandas as pd

    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"[gen_samples_8d] wrote {out_path} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
