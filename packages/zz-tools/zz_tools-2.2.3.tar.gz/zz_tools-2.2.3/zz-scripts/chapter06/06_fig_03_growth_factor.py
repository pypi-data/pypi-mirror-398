#!/usr/bin/env python3
"""
Plot 06_fig_03_growth_factor for Chapter 6.
Displays the growth factor normalized to ΛCDM as a function of redshift.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

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

# ---------------------------------------------------------------------
# Paths & constantes
# ---------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "zz-data" / "chapter06"
FIG_DIR = ROOT / "zz-figures" / "chapter06"
FIG_DIR.mkdir(parents=True, exist_ok=True)

DATA_CSV = DATA_DIR / "06_delta_rs_scan.csv"
JSON_PARAMS = DATA_DIR / "06_params_cmb.json"
OUT_PNG = FIG_DIR / "06_fig_03_growth_factor.png"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_save(filepath, fig=None, **savefig_kwargs):
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with tempfile.NamedTemporaryFile(delete=False, suffix=path.suffix) as tmp:
            tmp_path = Path(tmp.name)
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


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main(args=None) -> None:
    # Logging (éventuellement piloté par args.verbose)
    level = logging.INFO
    if args is not None and getattr(args, "verbose", 0):
        v = int(args.verbose)
        if v >= 2:
            level = logging.DEBUG
        elif v == 1:
            level = logging.INFO
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")

    # Données de scan
    df = pd.read_csv(DATA_CSV)
    x = df["q0star"].to_numpy()
    y = df["delta_rs_rel"].to_numpy()

    # Paramètres d'injection pour annotation
    with JSON_PARAMS.open(encoding="utf-8") as f:
        params = json.load(f)
    alpha = params.get("alpha", None)
    q0star = params.get("q0star", None)
    logging.info("Plotting fig_03 with α=%s, q0*=%s", alpha, q0star)

    # Figure
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    ax.scatter(
        x, y, marker="o", s=20, alpha=0.8, label=r"$D(z) / D_{\Lambda\mathrm{CDM}}$"
    )

    ax.set_xlabel("Redshift $z$", fontsize=11)
    ax.set_ylabel(r"$D(z) / D_{\Lambda\mathrm{CDM}}$", fontsize=11)
    ax.set_title(r"Growth Factor $D(z)$ Normalized to $\Lambda\text{CDM}$")
    ax.grid(which="both", linestyle=":", linewidth=0.5)
    ax.legend(frameon=False, fontsize=9)

    # Annotation des paramètres
    if alpha is not None and q0star is not None:
        ax.text(
            0.15,
            0.95,
            rf"$\alpha={alpha},\ q_0^*={q0star}$",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9,
        )

    fig.subplots_adjust(left=0.04, right=0.98, bottom=0.06, top=0.96)
    safe_save(OUT_PNG)
    logging.info("Figure enregistrée → %s", OUT_PNG)


# === MCGT CLI SEED v2 ===
if __name__ == "__main__":

    def _mcgt_cli_seed() -> None:
        import argparse
        import os
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
        try:
            os.makedirs(args.outdir, exist_ok=True)
            os.environ["MCGT_OUTDIR"] = args.outdir
            import matplotlib as mpl

            mpl.rcParams["savefig.dpi"] = args.dpi
            mpl.rcParams["savefig.format"] = args.format
            mpl.rcParams["savefig.transparent"] = args.transparent
        except Exception:
            pass

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
