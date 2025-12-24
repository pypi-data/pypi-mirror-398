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
plot_fig03_invariants_vs_T.py

Script de tracé des invariants adimensionnels I1, I2 et I3 en fonction de T
– Lit 04_dimensionless_invariants.csv
– Utilise une échelle log pour T, symlog pour gérer I3 négatif
– Ajoute les repères pour I2≈10⁻³⁵, I3≈10⁻⁶ et la transition Tp
– Sauvegarde la figure en PNG 800×500 px, DPI 300
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

import matplotlib.pyplot as plt
import pandas as pd


def main():
    # 1. Chargement des données
    df = pd.read_csv("zz-data/chapter04/04_dimensionless_invariants.csv")
    T = df["T_Gyr"].values
    I1 = df["I1"].values
    I2 = df["I2"].values
    I3 = df["I3"].values

    # Valeurs clés
    Tp = 0.087
    I2_ref = 1e-35
    I3_ref = 1e-6

    # 2. Création de la figure
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.set_xscale("log")
    ax.set_yscale("symlog", linthresh=1e-7)
    ax.plot(T, I1, color="C0", label=r"$I_1 = P/T$", linewidth=1.5)
    ax.plot(T, I2, color="C1", label=r"$I_2 = \kappa T^2$", linewidth=1.5)
    ax.plot(T, I3, color="C2", label=r"$I_3 = f_R - 1$", linewidth=1.5)

    # 3. Repères
    ax.axhline(I2_ref, color="C1", linestyle="--", label=r"$I_2 \approx 10^{-35}$")
    ax.axhline(I3_ref, color="C2", linestyle="--", label=r"$I_3 \approx 10^{-6}$")
    ax.axvline(Tp, color="orange", linestyle=":", label=r"$T_p = 0.087\ \mathrm{Gyr}$")

    # 4. Labels et légende
    ax.set_xlabel(r"$T$ [Gyr]")
    ax.set_ylabel(r"$I_n$ [dimensionless]")
    ax.set_title("Dimensionless Invariants Evolution")
    ax.legend(fontsize="small")
    ax.grid(True, which="both", linestyle=":", linewidth=0.5)

    # 5. Sauvegarde
    out = "zz-figures/chapter04/04_fig_03_invariants.png"
    fig.subplots_adjust(left=0.04, right=0.98, bottom=0.06, top=0.96)
    safe_save(out)
    print(f"Figure enregistrée : {out}")


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
