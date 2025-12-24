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
import os

"""
Plot 06_fig_02_growth_rate for Chapter 6.
Shows the relative evolution of the growth rate proxy.
"""

# --- IMPORTS & CONFIGURATION ---
import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Paths
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "zz-data" / "chapter06"
FIG_DIR = ROOT / "zz-figures" / "chapter06"
DELTA_CLS_REL_CSV = DATA_DIR / "06_delta_cls_relative.csv"
JSON_PARAMS = DATA_DIR / "06_params_cmb.json"
OUT_PNG = FIG_DIR / "06_fig_02_growth_rate.png"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Load injection parameters
with open(JSON_PARAMS, encoding="utf-8") as f:
    params = json.load(f)
ALPHA = params.get("alpha", None)
Q0STAR = params.get("q0star", None)
logging.info(f"Plotting fig_02 with α={ALPHA}, q0*={Q0STAR}")

# Load data
df = pd.read_csv(DELTA_CLS_REL_CSV)
ells = df["ell"].values
delta_rel = df["delta_Cl_rel"].values

# Plot
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
ax.plot(
    ells,
    delta_rel,
    linestyle="-",
    linewidth=2,
    color="tab:green",
    label=r"$f(z)$",
)
ax.axhline(0, color="black", linestyle="--", linewidth=1)

ax.set_xscale("log")
ax.set_xlim(2, 3000)
ymax = np.max(np.abs(delta_rel)) * 1.1
ax.set_ylim(-ymax, ymax)

ax.set_xlabel("Redshift $z$")
ax.set_ylabel(r"$f(z) = d\ln D / d\ln a$")
ax.set_title("Linear Growth Rate Evolution $f(z)$")
ax.grid(True, which="both", linestyle=":", linewidth=0.5)
ax.legend(frameon=False, loc="upper right")

# Annotate parameters
if ALPHA is not None and Q0STAR is not None:
    ax.text(
        0.03,
        0.95,
        rf"$\alpha={ALPHA},\ q_0^*={Q0STAR}$",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
    )

fig.subplots_adjust(left=0.04, right=0.98, bottom=0.06, top=0.96)
safe_save(OUT_PNG)
logging.info(f"Figure enregistrée → {OUT_PNG}")

# === MCGT CLI SEED v2 ===

if __name__ == "__main__":

    def _mcgt_cli_seed() -> None:
        import argparse
        import sys
        import traceback

        parser = argparse.ArgumentParser(
            description="Standard CLI seed (non-intrusif)."
        )
        parser.add_argument(
            "--outdir",
            default=os.environ.get("MCGT_OUTDIR", ".ci-out"),
            help="Dossier de sortie (par défaut: .ci-out)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Ne rien écrire, juste afficher les actions.",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Graine aléatoire (optionnelle).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Écraser les sorties existantes si nécessaire.",
        )
        parser.add_argument(
            "-v",
            "--verbose",
            action="count",
            default=0,
            help="Verbosity cumulable (-v, -vv).",
        )
        parser.add_argument(
            "--dpi",
            type=int,
            default=150,
            help="Figure DPI (default: 150)",
        )
        parser.add_argument(
            "--format",
            choices=["png", "pdf", "svg"],
            default="png",
            help="Figure format",
        )
        parser.add_argument(
            "--transparent",
            action="store_true",
            help="Transparent background",
        )

        args = parser.parse_args()

        # Config outdir / backend matplotlib (best-effort)
        os.makedirs(args.outdir, exist_ok=True)
        os.environ["MCGT_OUTDIR"] = args.outdir
        import matplotlib as mpl

        mpl.rcParams["savefig.dpi"] = args.dpi
        mpl.rcParams["savefig.format"] = args.format
        mpl.rcParams["savefig.transparent"] = args.transparent
        _main = globals().get("main")
        if callable(_main):
            try:
                _main(args)
            except SystemExit:
                raise
            except Exception as e:  # pragma: no cover - debug path
                print(f"[CLI seed] main() a levé: {e}", file=sys.stderr)
                traceback.print_exc()
                sys.exit(1)

    _mcgt_cli_seed()
