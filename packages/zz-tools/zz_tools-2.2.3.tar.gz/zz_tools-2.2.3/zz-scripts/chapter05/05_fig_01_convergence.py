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
# zz-scripts/chapter05/tracer_fig01_schema_reactions_bbn.py
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def draw_bbn_schema(
    save_path="zz-figures/chapter05/05_fig_01_convergence.png",
):
    fig, ax = plt.subplots(figsize=(8, 4.2), facecolor="white")

    # Centres des boîtes (x, y)
    P = {
        "n": np.array((0.07, 0.58)),
        "p": np.array((0.07, 0.38)),
        "D": np.array((0.34, 0.48)),
        "T": np.array((0.56, 0.74)),
        "He3": np.array((0.56, 0.22)),
        "He4": np.array((0.90, 0.48)),
    }

    dx = 0.04  # décalage horizontal flèches ←→ boîtes (légèrement augmenté)
    pad_box = 0.65  # padding interne des boîtes (boîtes « n », « p » plus larges)

    # Dessin des boîtes
    for lab, pos in P.items():
        ax.text(
            *pos,
            lab,
            fontsize=14,
            ha="center",
            va="center",
            bbox=dict(boxstyle=f"round,pad={pad_box}", fc="lightgray", ec="gray"),
        )

    # Fonction utilitaire pour tracer une flèche décalée
    def arrow(src, dst):
        x0, y0 = P[src]
        x1, y1 = P[dst]
        start = (x0 + dx, y0) if x1 > x0 else (x0 - dx, y0)
        end = (x1 - dx, y1) if x1 > x0 else (x1 + dx, y1)
        ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", lw=2))

    # Flèches du réseau BBN
    arrow("n", "D")
    arrow("p", "D")
    arrow("D", "T")
    arrow("D", "He3")
    arrow("T", "He4")
    arrow("He3", "He4")

    # Titre rapproché
    ax.set_title("Algorithm Convergence History", fontsize=14, pad=6)

    ax.axis("off")
    fig.subplots_adjust(left=0.04, right=0.98, bottom=0.06, top=0.96)
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    safe_save(save_path, dpi=300)
    plt.close()


if __name__ == "__main__":
    draw_bbn_schema()

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
