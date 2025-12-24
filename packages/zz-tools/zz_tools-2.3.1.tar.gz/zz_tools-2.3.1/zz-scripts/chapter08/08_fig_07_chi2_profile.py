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
zz-scripts/chapter08/plot_fig07_chi2_profile.py

Trace le profil Δχ² en fonction de q₀⋆ autour du minimum,
avec annotations des niveaux 1σ, 2σ, 3σ (1 degré de liberté).
"""
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

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main():
    # Répertoires
    ROOT = Path(__file__).resolve().parents[2]
    DATA_DIR = ROOT / "zz-data" / "chapter08"
    FIG_DIR = ROOT / "zz-figures" / "chapter08"
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # Chargement du scan 1D χ²
    df = pd.read_csv(DATA_DIR / "08_chi2_total_vs_q0.csv")
    q0 = df["q0star"].values
    chi2 = df["chi2_total"].values

    # Calcul Δχ²
    chi2_min = chi2.min()
    delta_chi2 = chi2 - chi2_min
    idx_min = delta_chi2.argmin()
    q0_best = q0[idx_min]

    # Prépare le tracé
    plt.rcParams.update({"font.size": 12})
    fig, ax = plt.subplots(figsize=(6.5, 4.5))

    # Profil Δχ²
    ax.plot(q0, delta_chi2, color="C0", lw=2, label=r"$\Delta\chi^2(q_0^\star)$")

    # Niveaux de confiance (1 dof)
    sigmas = [1.0, 4.0, 9.0]
    styles = ["--", "-.", ":"]
    for lvl, ls in zip(sigmas, styles, strict=False):
        ax.axhline(lvl, color="C1", linestyle=ls, lw=1.5)
        # annotation sur la ligne
        ax.text(
            q0_best + 0.02,
            lvl + 0.2,
            rf"${int(lvl**0.5)}\sigma$",
            color="C1",
            va="bottom",
        )

    # Best-fit point
    ax.plot(
        q0_best,
        0.0,
        "o",
        mfc="white",
        mec="C0",
        mew=2,
        ms=8,
        label=rf"$q_0^* = {q0_best:.3f}$",
    )

    # Zoom autour du minimum
    dx = 0.2
    ax.set_xlim(q0_best - dx, q0_best + dx)
    ax.set_ylim(0, sigmas[-1] * 1.2)

    # Labels et titre
    ax.set_xlabel(r"$q_0^\star$")
    ax.set_ylabel(r"$\Delta\chi^2$")
    ax.set_title("High Redshift Prediction Constraints")

    ax.grid(ls=":", lw=0.5, alpha=0.7)

    # Légende
    ax.legend(loc="upper left", frameon=True)

    fig.subplots_adjust(left=0.04, right=0.98, bottom=0.06, top=0.96)
    out = FIG_DIR / "08_fig_07_chi2_profile.png"
    safe_save(out, dpi=300)
    print(f"✅ {out.name} générée")


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
