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
plot_fig01_invariants_schematic.py

Script corrigé de tracé du schéma conceptuel des invariants adimensionnels
– Lit 04_dimensionless_invariants.csv
– Trace I1, I2, I3 vs log10(T) avec symlog pour I3
– Marque les phases et les repères pour I2 et I3
– Sauvegarde la figure 800x500 px DPI 300
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
    # ----------------------------------------------------------------------
    # 1. Chargement des données
    # ----------------------------------------------------------------------
    data_file = "zz-data/chapter04/04_dimensionless_invariants.csv"
    df = pd.read_csv(data_file)
    T = df["T_Gyr"].values
    I1 = df["I1"].values
    I2 = df["I2"].values
    I3 = df["I3"].values

    # Valeurs clés
    Tp = 0.087  # Gyr
    I2_ref = 1e-35
    I3_ref = 1e-6

    # ----------------------------------------------------------------------
    # 2. Création de la figure
    # ----------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)

    # Axe X en log
    ax.set_xscale("log")

    # Axe Y en symlog pour gérer I3 autour de zéro
    ax.set_yscale("symlog", linthresh=1e-7, linscale=1)

    # Tracés des invariants
    ax.plot(T, I1, label=r"$I_1 = P/T$", color="C0", linewidth=1.5)
    ax.plot(T, I2, label=r"$I_2 = \kappa\,T^2$", color="C1", linewidth=1.5)
    ax.plot(T, I3, label=r"$I_3 = f_R - 1$", color="C2", linewidth=1.5)

    # ----------------------------------------------------------------------
    # 3. Repères horizontaux
    # ----------------------------------------------------------------------
    ax.axhline(I2_ref, color="C1", linestyle="--", label=r"$I_2 \approx 10^{-35}$")
    ax.axhline(I3_ref, color="C2", linestyle="--", label=r"$I_3 \approx 10^{-6}$")

    # ----------------------------------------------------------------------
    # 4. Repère vertical de transition T_p
    # ----------------------------------------------------------------------
    ax.axvline(Tp, color="orange", linestyle=":", label=r"$T_p=0.087\ \mathrm{Gyr}$")

    # ----------------------------------------------------------------------
    # 5. Légendes, labels et grille
    # ----------------------------------------------------------------------
    ax.set_xlabel(r"$\phi$ [dimensionless]")
    ax.set_ylabel(r"$V(\phi)$ [arbitrary units]")
    ax.set_title(r"Scalar Field Potential $V(\phi)$")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, which="both", linestyle=":", linewidth=0.5)

    # ----------------------------------------------------------------------
    # 6. Sauvegarde de la figure
    # ----------------------------------------------------------------------
    output_fig = "zz-figures/chapter04/04_fig_01_potential.png"
    fig.subplots_adjust(left=0.04, right=0.98, bottom=0.06, top=0.96)
    safe_save(output_fig)
    print(f"Fig. sauvegardée : {output_fig}")


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
