#!/usr/bin/env python3
# check_p95_methods.py
"""
Compare p95 (et autres stats) pour trois traitements du résidu de phase:
  - raw:    abs(phi_mcgt - phi_ref)
  - unwrap: abs( unwrap(phi_mcgt - phi_ref) )
  - rebranch: alignement par k cycles entières: phi_mcgt - k*2pi

Usage (exemple):
python zz-scripts/chapter09/check_p95_methods.py \
  --csv zz-data/chapter09/09_phases_mcgt.csv \
  --window 20 300 \
  --bins 30 50 80 \
  --plot --out-dir zz-figures/chapter09/p95_methods --xscale log
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def parse_args():
    p = argparse.ArgumentParser(
        description="Compare p95 raw / unwrap / rebranch (k cycles)."
    )
    p.add_argument(
        "--csv", type=Path, required=True, help="CSV phases (09_phases_mcgt.csv)"
    )
    p.add_argument(
        "--window",
        nargs=2,
        type=float,
        default=[20.0, 300.0],
        help="Fenêtre [Fmin Fmax] (Hz)",
    )
    p.add_argument(
        "--bins",
        nargs="+",
        type=int,
        default=[30, 50, 80],
        help="Bins pour histogrammes (optionnel)",
    )
    p.add_argument(
        "--plot",
        action="store_true",
        help="Enregistrer histogrammes pour chaque méthode et bins",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("zz-figures/chapter09/p95_methods"),
        help="Répertoire de sortie si --plot",
    )
    p.add_argument(
        "--xscale",
        choices=["linear", "log"],
        default="log",
        help="Echelle x pour histogrammes",
    )
    p.add_argument("--dpi", type=int, default=150)
    return p.parse_args()


def compute_stats(arr):
    arrf = arr[np.isfinite(arr)]
    if arrf.size == 0:
        return {"n": 0, "mean": np.nan, "median": np.nan, "p95": np.nan, "max": np.nan}
    return {
        "n": int(arrf.size),
        "mean": float(np.nanmean(arrf)),
        "median": float(np.nanmedian(arrf)),
        "p95": float(np.nanpercentile(arrf, 95)),
        "max": float(np.nanmax(arrf)),
    }


def make_log_bins(vals, nbins):
    """Create log-spaced bins for positive vals. If no positive, fallback to linear bins."""
    pos = vals[vals > 0]
    if pos.size == 0:
        return np.linspace(0.0, 1.0, nbins + 1)
    lo = max(pos.min(), 1e-12)
    hi = pos.max()
    if hi <= lo:
        hi = lo * 10.0
    return np.logspace(np.log10(lo), np.log10(hi), nbins + 1)


def plot_hist(vals, bins, outpath, xscale="log", dpi=150, title=None):
    plt.figure(figsize=(8, 4.5))
    if xscale == "log":
        bins_arr = make_log_bins(vals, bins)
        plt.hist(vals, bins=bins_arr, alpha=0.7, edgecolor="k", linewidth=0.3)
        plt.xscale("log")
    else:
        plt.hist(vals, bins=bins, alpha=0.7, edgecolor="k", linewidth=0.3)
    plt.grid(True, linestyle=":", alpha=0.4)
    if title:
        plt.title(title)
    plt.xlabel(r"$|\Delta\phi|$ [rad]")
    plt.ylabel("Comptes")
    outpath.parent.mkdir(parents=True, exist_ok=True)
    fig.subplots_adjust(left=0.04, right=0.98, bottom=0.06, top=0.96)
    plt.savefig(outpath, dpi=dpi)
    plt.close()


def main():
    args = parse_args()
    csv = args.csv
    if not csv.exists():
        raise SystemExit(f"CSV not found: {csv}")
    df = pd.read_csv(csv)
    need = {"f_Hz", "phi_ref", "phi_mcgt"}
    if not need.issubset(df.columns):
        raise SystemExit(f"{csv} must contain columns {need}")

    f = df.f_Hz.to_numpy(float)
    phi_ref = df.phi_ref.to_numpy(float)
    phi_mcgt = df.phi_mcgt.to_numpy(float)

    fmin, fmax = float(args.window[0]), float(args.window[1])
    sel = (f >= fmin) & (f <= fmax)
    nsel = sel.sum()
    if nsel == 0:
        raise SystemExit("No points in the requested frequency window.")

    phi_ref_win = phi_ref[sel]
    phi_mcgt_win = phi_mcgt[sel]

    # method A: raw
    raw = np.abs(phi_mcgt_win - phi_ref_win)

    # method B: unwrap (absolute of unwrapped difference)
    unw = np.abs(np.unwrap((phi_mcgt_win - phi_ref_win).astype(float)))

    # method C: rebranch by median cycles (k cycles)
    two_pi = 2.0 * np.pi
    # compute k per-point then median and round to integer
    k_array = (phi_mcgt_win - phi_ref_win) / two_pi
    # remove NaN/infs
    k_array_f = k_array[np.isfinite(k_array)]
    if k_array_f.size == 0:
        k_med = 0
    else:
        k_med = int(np.round(np.nanmedian(k_array_f)))
    phi_mcgt_rebranch = phi_mcgt_win - (k_med * two_pi)
    reb = np.abs(phi_mcgt_rebranch - phi_ref_win)

    # diagnostics: differences
    max_raw_unw = float(np.nanmax(np.abs(raw - unw))) if raw.size > 0 else np.nan
    max_unw_reb = float(np.nanmax(np.abs(unw - reb))) if unw.size > 0 else np.nan

    print("\n=== Diagnostics ===")
    print(f"CSV: {csv}")
    print(f"Window: {fmin:.1f} - {fmax:.1f} Hz, points in window: {nsel}")
    print(f"K (median cycles) = {k_med}")
    print(f"max |raw - unwrap| = {max_raw_unw:.6g}")
    print(f"max |unwrap - rebranch| = {max_unw_reb:.6g}")
    print("-" * 72)

    methods = [("raw", raw), ("unwrap", unw), ("rebranch_k", reb)]
    # print table header
    print(
        "{:>12s} {:>6s} {:>8s} {:>8s} {:>8s} {:>8s}".format(
            "method", "n", "mean", "median", "p95", "max"
        )
    )
    print("-" * 72)
    for name, arr in methods:
        s = compute_stats(arr)
        print(
            "{:>12s} {:6d} {:8.3f} {:8.3f} {:8.3f} {:8.3f}".format(
                name, s["n"], s["mean"], s["median"], s["p95"], s["max"]
            )
        )
    print("-" * 72)

    # show a few sample numbers for inspection
    sample_idx = np.arange(0, min(10, raw.size))
    print("\nFirst sample (index, f_Hz, raw, unwrap, rebranch):")
    for i in sample_idx:
        fi = np.where(sel)[0][i]  # original index for frequency
        print(
            f" {i:2d}  f={f[fi]:7.3f} Hz  raw={raw[i]:10.6g}  unw={unw[i]:10.6g}  reb={reb[i]:10.6g}"
        )

    # plotting (optional) : one PNG per method and per bin
    if args.plot:
        for bins in args.bins:
            for name, arr in methods:
                out = args.out_dir / f"fig_03_{name}_bins{bins}.png"
                title = f"{name} — bins={bins} — window={int(fmin)}-{int(fmax)} Hz (k={k_med})"
                plot_hist(
                    arr,
                    bins=bins,
                    outpath=out,
                    xscale=args.xscale,
                    dpi=args.dpi,
                    title=title,
                )
        print(f"\nPlots saved in: {args.out_dir}")

    # final recommendation line
    print("\nRecommendation:")
    if np.nanmean(unw) < np.nanmean(raw):
        print(
            " - unwrap reduces large offsets vs raw: use unwrap (or rebranch) for statistics in publication."
        )
    if np.nanmean(reb) < np.nanmean(unw):
        print(
            " - rebranch (k cycles) reduces differences further: consider using rebranch output."
        )
    print(
        " - If raw and unwrap identical => likely every point shifted by same integer*2π (unwrap won't change). Use 'rebranch' to align.\n"
    )


if __name__ == "__main__":
    main()
