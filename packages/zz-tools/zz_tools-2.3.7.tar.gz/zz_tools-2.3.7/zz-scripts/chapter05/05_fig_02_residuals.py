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
Fig. 02 – Diagramme D/H : modèle vs observations (Chapitre 5)

- Compare D/H calculé (DH_calc) et D/H observé (DH_obs) aux jalons BBN.
- DH_calc est interpolé (PCHIP) aux temps des jalons à partir de 05_bbn_data.csv.
- Affiche :
    * les points de calibration avec barres d’erreur (sigma_DH),
    * la droite d’identité y = x,
    * un encadré résumant les métriques de calibration (max epsilon).

Entrées (par défaut) :
- zz-data/chapter05/05_bbn_milestones.csv
- zz-data/chapter05/05_bbn_data.csv
- zz-data/chapter05/05_bbn_params.json  (optionnel)

Sortie :
- zz-figures/chapter05/05_fig_02_dh_model_vs_obs.png
"""

import os
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

# Répertoires
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "zz-data" / "chapter05"
FIG_DIR = ROOT / "zz-figures" / "chapter05"
FIG_DIR.mkdir(parents=True, exist_ok=True)

OUT_FIG = FIG_DIR / "05_fig_02_residuals.png"


def main(args=None) -> None:
    # ------------------------------------------------------------------
    # Chargement des données
    # ------------------------------------------------------------------
    jalons = pd.read_csv(DATA_DIR / "05_bbn_milestones.csv")
    donnees = pd.read_csv(DATA_DIR / "05_bbn_data.csv")

    # Chargement des métriques (optionnelles)
    params_path = DATA_DIR / "05_bbn_params.json"
    max_ep_primary = None
    max_ep_order2 = None
    if params_path.exists():
        with params_path.open("r", encoding="utf-8") as f:
            params = json.load(f)
        max_ep_primary = params.get("max_epsilon_primary", None)
        max_ep_order2 = params.get("max_epsilon_order2", None)

    # ------------------------------------------------------------------
    # Interpolation PCHIP pour DH_calc aux temps des jalons
    # ------------------------------------------------------------------
    interp = PchipInterpolator(
        np.log10(donnees["T_Gyr"].values),
        np.log10(donnees["DH_calc"].values),
        extrapolate=False,
    )
    jalons["DH_calc"] = 10.0 ** interp(np.log10(jalons["T_Gyr"].values))

    # ------------------------------------------------------------------
    # Préparation du tracé
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))

    # Barres d'erreur et points de calibration
    ax.errorbar(
        jalons.index,
        jalons["DH_calc"] - jalons["DH_obs"],
        yerr=jalons["sigma_DH"],
        fmt="o",
        label=r"Residuals $\sigma$",
    )

    # Droite d'identité y = x
    ax.axhline(0.0, ls="--", color="black", label="Noise threshold")

    # Annotation des métriques de calibration (si présentes)
    txt_lines = []
    if max_ep_primary is not None:
        txt_lines.append(f"max ε_primary = {max_ep_primary:.2e}")
    if max_ep_order2 is not None:
        txt_lines.append(f"max ε_order2 = {max_ep_order2:.2e}")
    if txt_lines:
        ax.text(
            0.05,
            0.05,
            "\n".join(txt_lines),
            transform=ax.transAxes,
            va="bottom",
            ha="left",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.5),
        )

    # Légendes et annotations
    ax.set_xlabel("Sample index")
    ax.set_ylabel("Residual value")
    ax.set_title("Distribution of Residuals")
    ax.legend(framealpha=0.3, loc="upper left")

    # ------------------------------------------------------------------
    # Enregistrement
    # ------------------------------------------------------------------
    fig.subplots_adjust(left=0.04, right=0.98, bottom=0.06, top=0.96)
    safe_save(OUT_FIG, dpi=300)
    plt.close(fig)
    print(f"Figure enregistrée → {OUT_FIG}")


# === MCGT CLI SEED v2 ===
if __name__ == "__main__":

    def _mcgt_cli_seed():
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

        # Configuration non-intrusive de l'environnement matplotlib
        try:
            os.makedirs(args.outdir, exist_ok=True)
            os.environ["MCGT_OUTDIR"] = args.outdir
            import matplotlib as mpl

            mpl.rcParams["savefig.dpi"] = args.dpi
            mpl.rcParams["savefig.format"] = args.format
            mpl.rcParams["savefig.transparent"] = args.transparent
        except Exception:
            # Le seed ne doit jamais casser le script principal
            pass

        _main = globals().get("main")
        if callable(_main):
            try:
                _main(args)
            except SystemExit:
                raise
            except Exception as e:
                print(f"[CLI seed] main() a levé: {e}", file=sys.stderr)
                traceback.print_exc()
                sys.exit(1)

    _mcgt_cli_seed()
