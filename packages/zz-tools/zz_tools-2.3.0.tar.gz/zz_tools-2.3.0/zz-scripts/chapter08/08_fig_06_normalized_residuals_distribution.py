#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path as _SafePath

import matplotlib.pyplot as plt

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


def _sha256(path: _SafePath) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_save(filepath, fig=None, **savefig_kwargs):
    path = _SafePath(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with tempfile.NamedTemporaryFile(delete=False, suffix=path.suffix) as tmp:
            tmp_path = _SafePath(tmp.name)
        try:
            if fig is not None:
                fig.savefig(tmp_path, **savefig_kwargs)
            else:
                plt.savefig(tmp_path, **savefig_kwargs)
            if _sha256(tmp_path) == _sha256(path):
                tmp_path.unlink()
                return False
            shutil.move(tmp_path, path)
            return True
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
    if fig is not None:
        fig.savefig(path, **savefig_kwargs)
    else:
        plt.savefig(path, **savefig_kwargs)
    return True


#!/usr/bin/env python3
"""
zz-scripts/chapter08/plot_fig06_normalized_residuals_distribution.py

Distribution des pulls (résidus normalisés) pour BAO et Supernovae.
Rug‐plot + KDE pour BAO, histogramme pour Supernovae
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde, norm

# --- pour importer cosmo.py depuis utils ---
ROOT = Path(__file__).resolve().parents[2]
UTILS = ROOT / "zz-scripts" / "chapter08" / "utils"
sys.path.insert(0, str(UTILS))
from cosmo import DV, distance_modulus  # noqa: E402  # noqa: E402


def main():
    # Répertoires
    DATA_DIR = ROOT / "zz-data" / "chapter08"
    FIG_DIR = ROOT / "zz-figures" / "chapter08"
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # Lecture des données
    bao = pd.read_csv(DATA_DIR / "08_bao_data.csv", encoding="utf-8")
    pant = pd.read_csv(DATA_DIR / "08_pantheon_data.csv", encoding="utf-8")
    df1d = pd.read_csv(DATA_DIR / "08_chi2_total_vs_q0.csv", encoding="utf-8")

    # q0* optimal
    q0_star = df1d.loc[df1d["chi2_total"].idxmin(), "q0star"]

    # Calcul des pulls BAO
    z_bao = bao["z"].values
    dv_obs = bao["DV_obs"].values
    dv_sig = bao["sigma_DV"].values
    dv_th = np.array([DV(z, q0_star) for z in z_bao])
    pulls_bao = (dv_obs - dv_th) / dv_sig

    # Calcul des pulls Supernovae
    z_sn = pant["z"].values
    mu_obs = pant["mu_obs"].values
    mu_sig = pant["sigma_mu"].values
    mu_th = np.array([distance_modulus(z, q0_star) for z in z_sn])
    pulls_sn = (mu_obs - mu_th) / mu_sig

    # Statistiques
    mu_bao, sigma_bao, N_bao = pulls_bao.mean(), pulls_bao.std(ddof=1), len(pulls_bao)
    mu_sn, sigma_sn, N_sn = pulls_sn.mean(), pulls_sn.std(ddof=1), len(pulls_sn)

    # Plot
    plt.rcParams.update({"font.size": 11})
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    # (a) BAO – rug + KDE
    ax = axes[0]
    ax.plot(pulls_bao, np.zeros_like(pulls_bao), "|", ms=20, mew=2, label="BAO pulls")
    kde = gaussian_kde(pulls_bao)
    xk = np.linspace(pulls_bao.min() - 1, pulls_bao.max() + 1, 300)
    ax.plot(xk, kde(xk), "-", lw=2, label="KDE")
    # Annotation μ,σ,N en haut-gauche
    txt_bao = rf"$\mu={mu_bao:.2f},\ \sigma={sigma_bao:.2f},\ N={N_bao}$"
    ax.text(
        0.02,
        0.95,
        txt_bao,
        transform=ax.transAxes,
        va="top",
        ha="left",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.5"),
    )
    ax.set_title("(a) BAO")
    ax.set_xlabel("Pull")
    ax.set_ylabel("Densité")
    ax.set_ylim(0, 0.1)
    ax.legend(loc="upper right", frameon=False)
    ax.grid(ls=":", lw=0.5, alpha=0.6)

    # (b) Supernovae – histogramme
    ax = axes[1]
    bins = np.linspace(-5, 5, 50)
    ax.hist(
        pulls_sn,
        bins=bins,
        density=True,
        histtype="stepfilled",
        alpha=0.8,
        color="#FF8C00",
        label="SNe pulls",
    )
    x = np.linspace(-5, 5, 400)
    ax.plot(x, norm.pdf(x, 0, 1), "k--", lw=2, label=r"$\mathcal{N}(0,1)$")
    txt_sn = rf"$\mu={mu_sn:.2f},\ \sigma={sigma_sn:.2f},\ N={N_sn}$"
    ax.text(
        0.02,
        0.95,
        txt_sn,
        transform=ax.transAxes,
        va="top",
        ha="left",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.5"),
    )
    ax.set_title("(b) Supernovae")
    ax.set_xlabel("Pull")
    ax.set_ylim(0, 1.0)
    ax.legend(loc="upper right", frameon=False)
    ax.grid(ls=":", lw=0.5, alpha=0.6)

    fig.suptitle("Parameter Correlation Matrix", y=1.02, fontsize=14)
    fig.subplots_adjust(left=0.04, right=0.98, bottom=0.06, top=0.96)

    out_path = FIG_DIR / "08_fig_06_pulls.png"
    safe_save(out_path, dpi=300, bbox_inches="tight")
    print(f"✅ {out_path.name} générée")


if __name__ == "__main__":
    main()

# [MCGT POSTPARSE EPILOGUE v2]
# (compact) delegate to common helper; best-effort wrapper
try:
    import os
    import sys

    _here = os.path.abspath(os.path.dirname(__file__))
    _zz = os.path.abspath(os.path.join(_here, ".."))
    if _zz not in sys.path:
        sys.path.insert(0, _zz)
    from _common.postparse import apply as _mcgt_postparse_apply
except Exception:

    def _mcgt_postparse_apply(*_a, **_k):
        pass


try:
    if "args" in globals():
        _mcgt_postparse_apply(args, caller_file=__file__)
except Exception:
    pass
# === [PASS5B-SHIM] ===
# Shim minimal pour rendre --help et --out sûrs sans effets de bord.
import os
import sys
import atexit

if any(x in sys.argv for x in ("-h", "--help")):
    try:
        import argparse

        p = argparse.ArgumentParser(add_help=True, allow_abbrev=False)
        p.print_help()
    except Exception:
        print("usage: <script> [options]")
    sys.exit(0)

if any(arg.startswith("--out") for arg in sys.argv):
    os.environ.setdefault("MPLBACKEND", "Agg")
    try:
        import matplotlib.pyplot as plt

        def _no_show(*a, **k):
            pass

        if hasattr(plt, "show"):
            plt.show = _no_show

        # sauvegarde automatique si l'utilisateur a oublié de savefig
        def _auto_save():
            out = None
            for i, a in enumerate(sys.argv):
                if a == "--out" and i + 1 < len(sys.argv):
                    out = sys.argv[i + 1]
                    break
                if a.startswith("--out="):
                    out = a.split("=", 1)[1]
                    break
            if out:
                try:
                    fig = plt.gcf()
                    if fig:
                        # marges raisonnables par défaut
                        try:
                            fig.subplots_adjust(
                                left=0.07, right=0.98, top=0.95, bottom=0.12
                            )
                        except Exception:
                            pass
                        safe_save(out, dpi=120)
                except Exception:
                    pass

        atexit.register(_auto_save)
    except Exception:
        pass
# === [/PASS5B-SHIM] ===
