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
zz-scripts/chapter08/plot_fig05_residuals.py

Trace les résidus BAO et Pantheon+ :
  (a) ΔD_V = D_V^obs - D_V^th  avec barres d'erreur σ_DV
  (b) Δμ   = μ^obs   - μ^th    avec barres d'erreur σ_μ

Échelles homogènes, ±1σ, annotations, légendes internes.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# --- Répertoires ---
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "zz-data" / "chapter08"
FIG_DIR = ROOT / "zz-figures" / "chapter08"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def main():
    # --- Chargement des données BAO + théorique ---
    bao = pd.read_csv(DATA_DIR / "08_bao_data.csv", encoding="utf-8")
    dv_th = pd.read_csv(DATA_DIR / "08_dv_theory_z.csv", encoding="utf-8")
    df_bao = pd.merge(bao, dv_th, on="z", how="inner")
    df_bao["dv_resid"] = df_bao["DV_obs"] - df_bao["DV_calc"]
    df_bao["dv_err"] = df_bao["sigma_DV"]

    # --- Chargement des données Pantheon+ + théorique ---
    pant = pd.read_csv(DATA_DIR / "08_pantheon_data.csv", encoding="utf-8")
    mu_th = pd.read_csv(DATA_DIR / "08_mu_theory_z.csv", encoding="utf-8")
    df_pant = pd.merge(pant, mu_th, on="z", how="inner")
    df_pant["mu_resid"] = df_pant["mu_obs"] - df_pant["mu_calc"]
    df_pant["mu_err"] = df_pant["sigma_mu"]

    # --- Calcul des dispersions σ ---
    dv_std = df_bao["dv_resid"].std()
    mu_std = df_pant["mu_resid"].std()

    # --- Tracé ---
    plt.rcParams.update({"font.size": 11})
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(7, 6))

    # (a) BAO
    ax1.errorbar(
        df_bao["z"],
        df_bao["dv_resid"],
        yerr=df_bao["dv_err"],
        fmt="o",
        ms=5,
        alpha=0.8,
        capsize=3,
        label=r"$D_V^{\rm obs}-D_V^{\rm th}$",
    )
    ax1.set_xscale("log")
    ax1.set_ylabel(r"$\Delta D_V\ \mathrm{[Mpc]}$")
    ax1.set_ylim(-50, 400)
    ax1.axhline(0, ls="--", color="black", lw=1)
    ax1.axhline(dv_std, ls=":", color="gray", lw=1, label=r"$\pm1\sigma$")
    ax1.axhline(-dv_std, ls=":", color="gray", lw=1)
    ax1.text(0.02, 0.90, "(a) BAO", transform=ax1.transAxes, weight="bold")
    ax1.legend(loc="upper right", framealpha=0.5)
    ax1.grid(which="both", ls=":", lw=0.5, alpha=0.6)

    # (b) Supernovae Pantheon+
    ax2.errorbar(
        df_pant["z"],
        df_pant["mu_resid"],
        yerr=df_pant["mu_err"],
        fmt="o",
        ms=4,
        alpha=0.4,
        capsize=2,
        label=r"$\mu^{\rm obs}-\mu^{\rm th}$",
    )
    ax2.set_xscale("log")
    ax2.set_ylabel(r"$\Delta \mu\ \mathrm{[mag]}$")
    ax2.set_xlabel("Redshift $z$")
    ax2.set_ylim(-1.0, 1.0)
    ax2.axhline(0, ls="--", color="black", lw=1)
    ax2.axhline(mu_std, ls=":", color="gray", lw=1)
    ax2.axhline(-mu_std, ls=":", color="gray", lw=1)
    ax2.text(0.02, 0.90, "(b) Supernovae", transform=ax2.transAxes, weight="bold")
    ax2.legend(loc="upper right", framealpha=0.5)
    ax2.grid(which="both", ls=":", lw=0.5, alpha=0.6)

    # --- Ajustements finaux ---
    fig.suptitle("MCMC Posterior Distributions", y=0.98)
    fig.subplots_adjust(left=0.04, right=0.98, bottom=0.06, top=0.96)

    outpath = FIG_DIR / "08_fig_05_residuals.png"
    safe_save(outpath, dpi=300)
    print(f"✅ {outpath.name} générée")


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
