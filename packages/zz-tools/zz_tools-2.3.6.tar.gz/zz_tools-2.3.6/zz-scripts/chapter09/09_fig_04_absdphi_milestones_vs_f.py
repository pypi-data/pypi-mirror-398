#!/usr/bin/env python3
from __future__ import annotations

"""
Figure 04 — Phase residuals at milestones vs frequency (restored).
"""

import argparse
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import LogLocator, NullFormatter, NullLocator

plt.rcParams.update(
    {
        "figure.autolayout": True,
        "figure.figsize": (10, 6),
        "axes.titlepad": 25,
        "axes.labelpad": 15,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.3,
        "font.family": "serif",
    }
)

DEF_DIFF = Path("zz-data/chapter09/09_phase_diff.csv")
DEF_CSV = Path("zz-data/chapter09/09_phases_mcgt.csv")
DEF_MILESTONES = Path("zz-data/chapter09/09_comparison_milestones.csv")
DEF_OUT = Path("zz-figures/chapter09/09_fig_04_absdphi_milestones_vs_f.png")


def setup_logger(level: str) -> logging.Logger:
    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("fig04_milestones")


def principal_diff(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    two_pi = 2.0 * np.pi
    return (np.asarray(a, float) - np.asarray(b, float) + np.pi) % (two_pi) - np.pi


def safe_pos(y: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    y = np.asarray(y, float)
    return np.where((~np.isfinite(y)) | (y <= 0), eps, y)


def load_background(
    diff_path: Path, csv_path: Path, log: logging.Logger
) -> tuple[np.ndarray, np.ndarray]:
    if diff_path.exists():
        df = pd.read_csv(diff_path)
        if {"f_Hz", "abs_dphi"}.issubset(df.columns):
            log.info("Loaded background from %s", diff_path)
            f = df["f_Hz"].to_numpy(float)
            vals = safe_pos(df["abs_dphi"].to_numpy(float))
            return f, vals
        log.warning(
            "%s missing required columns; falling back to %s", diff_path, csv_path
        )

    if not csv_path.exists():
        raise SystemExit(f"Neither {diff_path} nor {csv_path} is available.")
    mc = pd.read_csv(csv_path)
    need = {"f_Hz", "phi_ref"}
    if not need.issubset(mc.columns):
        raise SystemExit(f"{csv_path} must contain {need}")
    variant = None
    for c in ("phi_mcgt", "phi_mcgt_cal", "phi_mcgt_raw"):
        if c in mc.columns:
            variant = c
            break
    if variant is None:
        raise SystemExit("No phi_mcgt* column found in phases CSV.")

    f = mc["f_Hz"].to_numpy(float)
    ref = mc["phi_ref"].to_numpy(float)
    mcg = mc[variant].to_numpy(float)
    m = np.isfinite(f) & np.isfinite(ref) & np.isfinite(mcg)
    f, ref, mcg = f[m], ref[m], mcg[m]
    vals = safe_pos(np.abs(principal_diff(mcg, ref)))
    log.info("Built background from %s (variant=%s)", csv_path, variant)
    return f, vals


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Milestone |Δφ| vs frequency with log-log axes (Chapter 09)"
    )
    ap.add_argument(
        "--diff", type=Path, default=DEF_DIFF, help="Background CSV (f_Hz, abs_dphi)"
    )
    ap.add_argument("--csv", type=Path, default=DEF_CSV, help="Fallback phases CSV")
    ap.add_argument(
        "--milestones",
        type=Path,
        default=DEF_MILESTONES,
        help="Milestone CSV (required)",
    )
    ap.add_argument("--out", type=Path, default=DEF_OUT, help="Output PNG")
    ap.add_argument(
        "--window", nargs=2, type=float, default=[20.0, 300.0], help="Shaded band [Hz]"
    )
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument(
        "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
    )
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    log = setup_logger(args.log_level)

    if not args.milestones.exists():
        raise SystemExit(f"Milestone file missing: {args.milestones}")

    f_bg, absd_bg = load_background(args.diff, args.csv, log)
    order = np.argsort(f_bg)
    f_bg, absd_bg = f_bg[order], absd_bg[order]

    ms = pd.read_csv(args.milestones)
    need = {"f_Hz", "phi_mcgt_at_fpeak", "obs_phase"}
    if not need.issubset(ms.columns):
        raise SystemExit(f"{args.milestones} must contain {need}")

    f_ms = ms["f_Hz"].to_numpy(float)
    phi_m = ms["phi_mcgt_at_fpeak"].to_numpy(float)
    phi_obs = ms["obs_phase"].to_numpy(float)
    cls = (
        ms["classe"].to_numpy(object)
        if "classe" in ms.columns
        else np.array(["autres"] * len(ms), object)
    )
    sigma = ms["sigma_phase"].to_numpy(float) if "sigma_phase" in ms.columns else None

    resid = np.abs(principal_diff(phi_m, phi_obs))
    resid = safe_pos(resid)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6), dpi=args.dpi)

    ax.plot(f_bg, absd_bg, color="0.6", lw=1.2, alpha=0.8, label="Background |Δφ|")
    fmin, fmax = sorted(map(float, args.window))
    ax.axvspan(
        fmin, fmax, color="0.9", alpha=0.5, label=f"Band {fmin:.0f}-{fmax:.0f} Hz"
    )

    cmap = {"primaire": "C0", "ordre2": "C1", "autres": "C2"}
    for name in ("primaire", "ordre2", "autres"):
        m = np.array([str(c).lower().startswith(name) for c in cls])
        if not np.any(m):
            continue
        yerr = None
        if sigma is not None:
            sg = sigma[m]
            yerr = np.where(np.isfinite(sg) & (sg > 0), sg, np.nan)
        ax.errorbar(
            f_ms[m],
            resid[m],
            yerr=yerr,
            fmt="o",
            ms=5,
            capsize=3,
            elinewidth=0.9,
            color=cmap[name],
            ecolor=cmap[name],
            alpha=0.9,
            label=f"Milestones: {name}",
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel(r"$|\Delta \phi|$  [rad]")
    ax.set_title("Milestone Phase Residuals vs Frequency")
    ax.grid(True, which="both", ls=":", alpha=0.4)
    ax.yaxis.set_major_locator(LogLocator(base=10.0, numticks=5))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_minor_formatter(NullFormatter())

    stats_txt = (
        f"Background N = {absd_bg.size}\n"
        f"Milestones N = {resid.size}\n"
        f"Milestone mean = {float(np.nanmean(resid)):.3f}\n"
        f"Milestone p95 = {float(np.nanpercentile(resid, 95.0)):.3f}"
    )

    handles, labels = ax.get_legend_handles_labels()
    handles.append(plt.Line2D([], [], color="none"))
    labels.append(stats_txt)
    # Compact single legend stacked in lower-right (keeps upper-left clear)
    ax.legend(
        handles,
        labels,
        loc="lower right",
        bbox_to_anchor=(0.98, 0.02),
        framealpha=0.9,
        fontsize=9.5,
        borderaxespad=0.6,
    )
    fig.savefig(args.out, dpi=args.dpi)
    log.info("PNG saved → %s", args.out)


if __name__ == "__main__":
    main()
