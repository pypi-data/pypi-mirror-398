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
Script de tracé fig_05_delta_chi2_heatmap pour Chapitre 6 (Rayonnement CMB)
───────────────────────────────────────────────────────────────
Affiche la carte de chaleur 2D de Δχ² en fonction de α et q0star.
"""

import os
import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# CONFIG GLOBALE
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
LOGGER = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "zz-data" / "chapter06"
DEFAULT_FIG_DIR = ROOT / "zz-figures" / "chapter06"

DATA_CSV = DATA_DIR / "06_cmb_chi2_scan2D.csv"
JSON_PARAMS = DATA_DIR / "06_params_cmb.json"


def _resolve_outdir(args_outdir: str | None) -> Path:
    """
    Résout le dossier de sortie à partir de :
      1) args.outdir si fourni
      2) $MCGT_OUTDIR si défini
      3) zz-figures/chapter06 sinon
    """
    # 1) argument explicite
    if args_outdir:
        out = Path(args_outdir)
        if not out.is_absolute():
            out = ROOT / out
        return out

    # 2) variable d'environnement
    env_out = os.environ.get("MCGT_OUTDIR")
    if env_out:
        out = Path(env_out)
        if not out.is_absolute():
            out = ROOT / out
        return out

    # 3) valeur par défaut
    return DEFAULT_FIG_DIR


def main(args) -> None:
    """
    Logique principale : charge les données, construit la heatmap Δχ² et
    sauvegarde la figure au chemin déterminé par la CLI.
    """

    outdir = _resolve_outdir(getattr(args, "outdir", None))
    outdir.mkdir(parents=True, exist_ok=True)

    fmt = getattr(args, "format", "png")
    dpi = getattr(args, "dpi", 300)
    transparent = bool(getattr(args, "transparent", False))

    # Nom canonique aligné avec le manifest / plan de rebuild
    output_basename = f"06_fig_05_delta_chi2_heatmap.{fmt}"
    out_path = outdir / output_basename

    # ------------------------------------------------------------------ #
    # 1) Paramètres d'injection (JSON) pour l'annotation
    # ------------------------------------------------------------------ #
    with open(JSON_PARAMS, encoding="utf-8") as f:
        params = json.load(f)

    alpha = params.get("alpha", None)
    q0star = params.get("q0star", None)
    LOGGER.info("Tracé fig_05 avec α=%s, q0*=%s", alpha, q0star)

    # ------------------------------------------------------------------ #
    # 2) Chargement de la grille 2D Δχ²(α, q0*)
    # ------------------------------------------------------------------ #
    df = pd.read_csv(DATA_CSV)

    alphas = np.sort(df["alpha"].unique())
    q0s = np.sort(df["q0star"].unique())

    chi2_mat = (
        df.pivot(index="q0star", columns="alpha", values="chi2").loc[q0s, alphas].values
    )

    # Bords des cellules pour pcolormesh
    if len(alphas) < 2 or len(q0s) < 2:
        raise RuntimeError(
            "Grille 2D insuffisante pour construire les bords (alpha/q0*)."
        )

    da = alphas[1] - alphas[0]
    dq = q0s[1] - q0s[0]
    alpha_edges = np.concatenate([alphas - da / 2, [alphas[-1] + da / 2]])
    q0_edges = np.concatenate([q0s - dq / 2, [q0s[-1] + dq / 2]])

    # ------------------------------------------------------------------ #
    # 3) Tracé de la heatmap
    # ------------------------------------------------------------------ #
    fig, ax = plt.subplots(figsize=(10, 6), dpi=dpi)
    pcm = ax.pcolormesh(alpha_edges, q0_edges, chi2_mat, shading="auto", cmap="viridis")
    fig.colorbar(pcm, ax=ax, label=r"$\Delta\chi^2$")

    ax.set_title(r"$\Delta\chi^2$ Heatmap (Chapter 6)", fontsize=14, fontweight="bold")
    ax.set_xlabel(r"$\alpha$")
    ax.set_ylabel(r"$q_0^\star$")
    ax.grid(which="major", linestyle=":", linewidth=0.5)
    ax.grid(which="minor", linestyle=":", linewidth=0.3)
    ax.minorticks_on()

    # Annotation des paramètres
    if alpha is not None and q0star is not None:
        ax.text(
            0.03,
            0.95,
            rf"$\alpha={alpha},\ q_0^*={q0star}$",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9,
        )

    fig.subplots_adjust(left=0.04, right=0.98, bottom=0.06, top=0.96)

    # ------------------------------------------------------------------ #
    # 4) Sauvegarde (ou dry-run)
    # ------------------------------------------------------------------ #
    if getattr(args, "dry_run", False):
        LOGGER.info("[dry-run] Figure NON sauvegardée, chemin prévu : %s", out_path)
        return

    safe_save(out_path, dpi=dpi, transparent=transparent, format=fmt)
    LOGGER.info("Carte de chaleur enregistrée → %s", out_path.relative_to(ROOT))


# === MCGT CLI SEED v2 ===
if __name__ == "__main__":

    def _mcgt_cli_seed():
        import argparse
        import sys
        import traceback

        parser = argparse.ArgumentParser(
            description=(
                "Standard CLI seed (non-intrusif) pour Fig. 05 – "
                "carte de chaleur Δχ² (Chapitre 6, CMB)."
            )
        )
        parser.add_argument(
            "--outdir",
            default=os.environ.get("MCGT_OUTDIR", "zz-figures/chapter06"),
            help="Dossier de sortie (par défaut: zz-figures/chapter06 ou $MCGT_OUTDIR).",
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
            help="Graine aléatoire (optionnelle, non utilisée ici, pour homogénéité).",
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
            default=300,
            help="Figure DPI (default: 300).",
        )
        parser.add_argument(
            "--format",
            choices=["png", "pdf", "svg"],
            default="png",
            help="Figure format (default: png).",
        )
        parser.add_argument(
            "--transparent",
            action="store_true",
            help="Fond transparent pour la figure.",
        )

        args = parser.parse_args()

        try:
            if args.verbose:
                logging.getLogger().setLevel(logging.DEBUG)
            main(args)
        except SystemExit:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"[CLI seed] main() a levé: {e}", file=sys.stderr)
            traceback.print_exc()
            sys.exit(1)

    _mcgt_cli_seed()
