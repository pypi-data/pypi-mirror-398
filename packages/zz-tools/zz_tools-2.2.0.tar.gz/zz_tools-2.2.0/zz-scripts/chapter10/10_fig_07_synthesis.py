#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_fig07_synthesis.py — Figure 7 (synthèse)

Panneaux :
  (1) Coverage vs N (Wilson 95% bars if provided)
  (2) Mean CI width vs N [rad] (log–log slope width ≈ a·N^b)
  (3) Numeric synthesis table (second row)

Correction propre (CH10 fig07) — 3 changements
  1) --manifest-a optionnel : si absent, auto-détection sur
       zz-figures/chapter10/10_fig_03c_bootstrap_coverage_vs_n.manifest.json
  2) --out par défaut écrit dans zz-figures/chapter10 (pas de fuite en ROOT)
  3) Export CSV robuste : --out-csv optionnel ; sinon dérivé de --out en *.table.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec

plt.rcParams.update(
    {
        "figure.autolayout": True,
        "figure.figsize": (10, 6),
        "axes.titlepad": 20,
        "axes.labelpad": 12,
        "savefig.bbox": "tight",
        "font.family": "serif",
    }
)


# ---------- utils ----------
def parse_figsize(s: str) -> Tuple[float, float]:
    try:
        a, b = s.split(",")
        return float(a), float(b)
    except Exception as e:
        raise argparse.ArgumentTypeError(
            "figsize doit être 'largeur,hauteur' (ex: 14,6)"
        ) from e


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_save(filepath: Path | str, fig, **savefig_kwargs) -> bool:
    """
    Sauvegarde fig en préservant le mtime si le contenu PNG est identique.

    Retourne True si le fichier a été mis à jour, False sinon.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        with tempfile.NamedTemporaryFile(delete=False, suffix=path.suffix) as tmp:
            tmp_path = Path(tmp.name)
        try:
            fig.savefig(tmp_path, **savefig_kwargs)
            if _sha256(tmp_path) == _sha256(path):
                tmp_path.unlink()
                return False
            shutil.move(tmp_path, path)
            return True
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    fig.savefig(path, **savefig_kwargs)
    return True


def load_manifest(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _first(d: Dict[str, Any], keys: List[str], default=np.nan):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def _param(params: Dict[str, Any], candidates: List[str], default=np.nan):
    return _first(params, candidates, default)


@dataclass
class Series:
    label: str
    N: np.ndarray
    coverage: np.ndarray
    err_low: np.ndarray
    err_high: np.ndarray
    width_mean: np.ndarray
    alpha: float
    params: Dict[str, Any]


def _sort_by_N(s: Series) -> Series:
    key = np.nan_to_num(s.N.astype(float), nan=np.inf, posinf=np.inf, neginf=np.inf)
    order = np.argsort(key)
    return Series(
        label=s.label,
        N=s.N[order],
        coverage=s.coverage[order],
        err_low=s.err_low[order],
        err_high=s.err_high[order],
        width_mean=s.width_mean[order],
        alpha=s.alpha,
        params=s.params,
    )


def series_from_manifest(
    man: Dict[str, Any], label_override: Optional[str] = None
) -> Series:
    results = man.get("results", [])
    if not results:
        raise ValueError("Manifest ne contient pas de 'results'.")

    N = np.array([_first(r, ["N"], np.nan) for r in results], dtype=float)
    coverage = np.array([_first(r, ["coverage"], np.nan) for r in results], dtype=float)
    err_low = np.array(
        [_first(r, ["coverage_err95_low", "coverage_err_low"], 0.0) for r in results],
        dtype=float,
    )
    err_high = np.array(
        [
            _first(
                r,
                ["coverage_err95_high", "coverage_err95_hi", "coverage_err_high"],
                0.0,
            )
            for r in results
        ],
        dtype=float,
    )
    width_mean = np.array(
        [_first(r, ["width_mean_rad", "width_mean"], np.nan) for r in results],
        dtype=float,
    )

    params = man.get("params", {}) if isinstance(man.get("params", {}), dict) else {}
    alpha = float(_param(params, ["alpha", "conf_alpha"], 0.05))
    label = label_override or man.get("series_label") or man.get("label") or "series"

    s = Series(
        label=str(label),
        N=N,
        coverage=coverage,
        err_low=err_low,
        err_high=err_high,
        width_mean=width_mean,
        alpha=alpha,
        params=params,
    )
    return _sort_by_N(s)


def detect_reps_params(params: Dict[str, Any]) -> Tuple[float, float, float]:
    M = _param(
        params, ["M", "num_trials", "n_trials", "n_repeat", "repeats", "nsimu"], np.nan
    )
    outer_B = _param(
        params, ["outer_B", "outer", "B_outer", "outerB", "Bouter"], np.nan
    )
    inner_B = _param(
        params, ["inner_B", "inner", "B_inner", "innerB", "Binner"], np.nan
    )
    return float(M), float(outer_B), float(inner_B)


# ---------- stats & résumé ----------
def compute_summary_rows(series_list: List[Series]) -> List[List[Any]]:
    rows: List[List[Any]] = []
    for s in series_list:
        mean_cov = (
            float(np.nanmean(s.coverage))
            if np.isfinite(np.nanmean(s.coverage))
            else np.nan
        )
        med_cov = (
            float(np.nanmedian(s.coverage))
            if np.isfinite(np.nanmedian(s.coverage))
            else np.nan
        )
        std_cov = (
            float(np.nanstd(s.coverage))
            if np.isfinite(np.nanstd(s.coverage))
            else np.nan
        )
        p95_cov = (
            float(np.nanpercentile(s.coverage, 95))
            if np.isfinite(np.nanpercentile(s.coverage, 95))
            else np.nan
        )
        med_w = (
            float(np.nanmedian(s.width_mean))
            if np.isfinite(np.nanmedian(s.width_mean))
            else np.nan
        )
        _, outer_B, inner_B = detect_reps_params(s.params)
        rows.append(
            [
                s.label,
                int(outer_B) if np.isfinite(outer_B) else "",
                int(inner_B) if np.isfinite(inner_B) else "",
                mean_cov,
                med_cov,
                std_cov,
                p95_cov,
                med_w,
            ]
        )
    return rows


def powerlaw_slope(N: np.ndarray, W: np.ndarray) -> float:
    m = np.isfinite(N) & np.isfinite(W) & (N > 0) & (W > 0)
    if m.sum() < 2:
        return np.nan
    p = np.polyfit(np.log(N[m]), np.log(W[m]), 1)  # log W = a + b log N
    return float(p[0])  # b


# ---------- CSV ----------
def _default_out_csv_from_out(out_png: Path) -> Path:
    # 10_fig_07_synthesis.png -> 10_fig_07_synthesis.table.csv
    base = out_png.with_suffix("")  # enlève .png
    return Path(str(base) + ".table.csv")


def save_summary_csv(series_list: List[Series], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "series",
        "N",
        "coverage",
        "err95_low",
        "err95_high",
        "width_mean",
        "M",
        "outer_B",
        "inner_B",
        "alpha",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for s in series_list:
            M, outer_B, inner_B = detect_reps_params(s.params)
            for i in range(len(s.N)):
                w.writerow(
                    {
                        "series": s.label,
                        "N": int(s.N[i]) if np.isfinite(s.N[i]) else "",
                        "coverage": float(s.coverage[i])
                        if np.isfinite(s.coverage[i])
                        else "",
                        "err95_low": float(s.err_low[i])
                        if np.isfinite(s.err_low[i])
                        else "",
                        "err95_high": float(s.err_high[i])
                        if np.isfinite(s.err_high[i])
                        else "",
                        "width_mean": float(s.width_mean[i])
                        if np.isfinite(s.width_mean[i])
                        else "",
                        "M": int(M) if np.isfinite(M) else "",
                        "outer_B": int(outer_B) if np.isfinite(outer_B) else "",
                        "inner_B": int(inner_B) if np.isfinite(inner_B) else "",
                        "alpha": float(s.alpha),
                    }
                )


# ---------- tracé ----------
def plot_synthese(
    series_list: List[Series],
    out_png: Path,
    figsize: Tuple[float, float] = (14, 6),
    dpi: int = 300,
    ymin_cov: Optional[float] = None,
    ymax_cov: Optional[float] = None,
) -> None:
    plt.style.use("classic")
    fig = plt.figure(figsize=figsize, constrained_layout=False)

    # 2 rangées : (couverture, largeur) / (tableau)
    gs = GridSpec(2, 2, figure=fig, height_ratios=[0.78, 0.22], width_ratios=[1.0, 1.0])
    ax_cov = fig.add_subplot(gs[0, 0])
    ax_width = fig.add_subplot(gs[0, 1])
    ax_tab = fig.add_subplot(gs[1, :])

    # ----- Coverage vs N -----
    alpha = series_list[0].alpha if series_list else 0.05
    nominal_level = 1.0 - alpha

    handles = []
    for s in series_list:
        yerr = np.vstack([s.err_low, s.err_high])
        h = ax_cov.errorbar(
            s.N,
            s.coverage,
            yerr=yerr,
            fmt="o-",
            lw=1.6,
            ms=6,
            capsize=3,
            zorder=3,
            label=s.label,
        )
        handles.append(h)

    ax_cov.axhline(nominal_level, color="crimson", ls="--", lw=1.5, zorder=1)
    nominal_handle = Line2D(
        [0],
        [0],
        color="crimson",
        lw=1.5,
        ls="--",
        label=f"Nominal level {int(nominal_level * 100)}%",
    )

    if handles:
        ax_cov.legend(
            [nominal_handle] + handles,
            [nominal_handle.get_label()] + [s.label for s in series_list],
            loc="upper left",
            frameon=True,
            fontsize=10,
        )
    else:
        ax_cov.legend(
            [nominal_handle],
            [nominal_handle.get_label()],
            loc="upper left",
            frameon=True,
            fontsize=10,
        )

    ax_cov.set_title("Coverage vs N")
    ax_cov.set_xlabel(r"Sample Size $N$")
    ax_cov.set_ylabel("Coverage (95% CI contains reference)")

    if (ymin_cov is not None) or (ymax_cov is not None):
        ymin = ymin_cov if ymin_cov is not None else ax_cov.get_ylim()[0]
        ymax = ymax_cov if ymax_cov is not None else ax_cov.get_ylim()[1]
        ax_cov.set_ylim(ymin, ymax)

    ax_cov.text(
        0.02,
        0.06,
        "Bars = Wilson 95% (outer B=400,2000); inner CI = percentile (inner B=2000)",
        transform=ax_cov.transAxes,
        fontsize=9,
        va="bottom",
    )
    ax_cov.text(
        0.02,
        0.03,
        "α=0.05. Variability higher for small N.",
        transform=ax_cov.transAxes,
        fontsize=9,
        va="bottom",
    )

    if not series_list:
        ax_cov.text(
            0.5,
            0.5,
            "No series (missing/invalid manifest)",
            transform=ax_cov.transAxes,
            ha="center",
            va="center",
            fontsize=11,
        )

    # ----- Largeur vs N -----
    for s, h in zip(series_list, handles):
        color = None
        try:
            if hasattr(h, "lines") and h.lines and h.lines[0] is not None:
                color = h.lines[0].get_color()
        except Exception:
            color = None
        ax_width.plot(s.N, s.width_mean, "-o", lw=1.8, ms=5, label=s.label, color=color)

    ax_width.set_title("CI width vs N")
    ax_width.set_xlabel(r"Sample Size $N$")
    ax_width.set_ylabel("Mean 95% CI width [rad]")
    if series_list:
        ax_width.legend(fontsize=10, loc="upper right", frameon=True)
    else:
        ax_width.text(
            0.5,
            0.5,
            "No series",
            transform=ax_width.transAxes,
            ha="center",
            va="center",
            fontsize=11,
        )

    # ----- Tableau résumé -----
    ax_tab.set_title("Numeric synthesis (summary)", y=0.88, pad=12, fontsize=12)
    rows = compute_summary_rows(series_list)

    col_labels = [
        "series",
        "outer_B",
        "inner_B",
        "mean_cov",
        "med_cov",
        "std_cov",
        "p95_cov",
        "med_width [rad]",
    ]
    cell_text: List[List[str]] = []
    for r in rows:
        cell_text.append(
            [
                str(r[0]),
                f"{r[1]}" if r[1] != "" else "-",
                f"{r[2]}" if r[2] != "" else "-",
                f"{r[3]:.3f}" if np.isfinite(r[3]) else "-",
                f"{r[4]:.3f}" if np.isfinite(r[4]) else "-",
                f"{r[5]:.3f}" if np.isfinite(r[5]) else "-",
                f"{r[6]:.3f}" if np.isfinite(r[6]) else "-",
                f"{r[7]:.5f}" if np.isfinite(r[7]) else "-",
            ]
        )

    if not cell_text:
        cell_text = [["—", "-", "-", "-", "-", "-", "-", "-"]]

    ax_tab.axis("off")
    table = ax_tab.table(
        cellText=cell_text,
        colLabels=col_labels,
        cellLoc="center",
        colLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.3)

    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor("0.3")
        cell.set_linewidth(0.8)
        if r == 0:
            cell.set_height(cell.get_height() * 1.15)
        if c == 0:
            cell.set_width(cell.get_width() * 1.85)

    # ----- Caption bas avec pentes -----
    if series_list:
        slopes = []
        for s in series_list:
            b = powerlaw_slope(s.N, s.width_mean)
            slopes.append(
                f"{s.label}: b={b:.2f}" if np.isfinite(b) else f"{s.label}: b=NA"
            )

        s0 = series_list[0]
        M0, outer0, inner0 = detect_reps_params(s0.params)
        cap1 = (
            f"Protocol: M={int(M0) if np.isfinite(M0) else '?'} outer runs per N "
            f"(outer_B). Bars = Wilson 95% on M. "
            f"Nested bootstrap outer_B={int(outer0) if np.isfinite(outer0) else '?'} "
            f"(coverage), inner_B={int(inner0) if np.isfinite(inner0) else '?'} (inner CI); "
            f"α={s0.alpha:.2f}."
        )
        cap2 = (
            "Mean 95% CI width [rad]; log–log fit width ≈ a·N^b; "
            + " ; ".join(slopes)
            + "."
        )
        fig.text(0.5, 0.035, cap1, ha="center", fontsize=9)
        fig.text(0.5, 0.017, cap2, ha="center", fontsize=9)

    fig.subplots_adjust(
        left=0.06, right=0.98, top=0.93, bottom=0.09, wspace=0.25, hspace=0.35
    )

    out_png.parent.mkdir(parents=True, exist_ok=True)
    updated = safe_save(out_png, fig, dpi=int(dpi), bbox_inches="tight")
    status = "écrite" if updated else "inchangée (identique)"
    print(f"[OK] Figure {status} : {out_png}")


# ---------- CLI ----------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument(
        "--manifest-a",
        default=None,
        help="Manifest JSON de la série A (coverage/width vs N)",
    )
    ap.add_argument("--label-a", default=None, help="Label override pour la série A")
    ap.add_argument(
        "--manifest-b", default=None, help="Manifest JSON d'une série B optionnelle"
    )
    ap.add_argument("--label-b", default=None, help="Label override pour la série B")
    ap.add_argument(
        "--out",
        default="zz-figures/chapter10/10_fig_07_synthesis.png",
        help="PNG de sortie",
    )
    ap.add_argument(
        "--out-csv", default=None, help="CSV de sortie (sinon dérivé de --out)"
    )
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--figsize", default="14,6")
    ap.add_argument("--ymin-coverage", type=float, default=None)
    ap.add_argument("--ymax-coverage", type=float, default=None)
    args = ap.parse_args(argv)

    fig_w, fig_h = parse_figsize(args.figsize)
    out_png = Path(args.out)

    # -------- série A : manifest principal (fig03/convergence) ----------
    default_manifest_a = Path(
        "zz-figures/chapter10/10_fig_03_convergence.manifest.json"
    )
    series_list: List[Series] = []

    if args.manifest_a:
        try:
            man_a = load_manifest(Path(args.manifest_a))
            series_list.append(series_from_manifest(man_a, args.label_a))
            print(f"[INFO] Manifest A chargé explicitement : {args.manifest_a}")
        except Exception as e:
            print(f"[ERR] Manifest A invalide: {e}", file=sys.stderr)
            return 2
    else:
        if default_manifest_a.exists():
            try:
                man_a = load_manifest(default_manifest_a)
                label_a = args.label_a or "bootstrap (CH10)"
                series_list.append(series_from_manifest(man_a, label_a))
                print(f"[INFO] Manifest A auto-détecté : {default_manifest_a}")
            except Exception as e:
                print(
                    f"[WARN] Auto-detected manifest A invalid ({e}); synthesis figure will be empty.",
                    file=sys.stderr,
                )
        else:
            print(
                "[WARN] No manifest A provided and auto-detect failed; synthesis figure will be empty.",
                file=sys.stderr,
            )

    # -------- série B optionnelle ----------
    if args.manifest_b:
        try:
            man_b = load_manifest(Path(args.manifest_b))
            series_list.append(series_from_manifest(man_b, args.label_b))
            print(f"[INFO] Manifest B chargé : {args.manifest_b}")
        except Exception as e:
            print(f"[WARN] Manifest B ignoré: {e}", file=sys.stderr)

    # -------- CSV ----------
    out_csv = Path(args.out_csv) if args.out_csv else _default_out_csv_from_out(out_png)
    save_summary_csv(series_list, out_csv)
    print(f"[OK] CSV écrit : {out_csv}")

    # -------- figure ----------
    plot_synthese(
        series_list,
        out_png,
        figsize=(fig_w, fig_h),
        dpi=int(args.dpi),
        ymin_cov=args.ymin_coverage,
        ymax_cov=args.ymax_coverage,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

    # --- normalisation sortie : si '--out' est un nom nu -> redirige vers zz-figures/chapter10/ ---
    from pathlib import Path as _Path

    _outp = _Path(args.out)
    if _outp.parent == _Path("."):
        args.out = str(_Path("zz-figures/chapter10") / _outp.name)
