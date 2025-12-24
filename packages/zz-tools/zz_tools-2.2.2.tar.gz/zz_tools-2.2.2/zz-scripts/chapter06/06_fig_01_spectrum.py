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
Script de tracé fig_02_cls_lcdm_vs_mcgt pour Chapitre 6 (Rayonnement CMB)
"""

import json
import logging
import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

# Paths
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "zz-data" / "chapter06"
FIG_DIR = ROOT / "zz-figures" / "chapter06"
FIG_DIR.mkdir(parents=True, exist_ok=True)

CLS_LCDM_DAT = DATA_DIR / "06_cls_spectrum_lcdm.dat"
CLS_MCGT_DAT = DATA_DIR / "06_cls_spectrum.dat"
JSON_PARAMS = DATA_DIR / "06_params_cmb.json"
OUT_PNG = FIG_DIR / "06_fig_01_spectrum.png"


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main(args=None) -> None:
    # Logging de base (on utilise éventuellement args.verbose si présent)
    level = logging.INFO
    if args is not None and getattr(args, "verbose", 0):
        v = int(args.verbose)
        if v >= 2:
            level = logging.DEBUG
        elif v == 1:
            level = logging.INFO
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")

    # Paramètres d'injection
    with JSON_PARAMS.open(encoding="utf-8") as f:
        params = json.load(f)
    alpha = params.get("alpha", None)
    q0star = params.get("q0star", None)
    logging.info("Plotting fig_01 with α=%s, q0*=%s", alpha, q0star)

    # Spectres C_ell
    cols_l = ["ell", "Cl_LCDM"]
    cols_m = ["ell", "Cl_MCGT"]
    df_lcdm = pd.read_csv(CLS_LCDM_DAT, sep=r"\s+", names=cols_l, comment="#")
    df_mcgt = pd.read_csv(CLS_MCGT_DAT, sep=r"\s+", names=cols_m, comment="#")
    df = pd.merge(df_lcdm, df_mcgt, on="ell")
    df = df[df["ell"] >= 2]

    ells = df["ell"].to_numpy()
    cl0 = df["Cl_LCDM"].to_numpy()
    cl1 = df["Cl_MCGT"].to_numpy()
    delta_rel = (cl1 - cl0) / cl0

    # Figure principale
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300, constrained_layout=True)

    ax.plot(ells, cl0, linestyle="--", linewidth=2, label=r"$\Lambda$CDM", alpha=0.7)
    ax.plot(
        ells,
        cl1,
        linestyle="-",
        linewidth=2,
        label="MCGT",
        alpha=0.7,
        color="tab:orange",
    )

    # Zone où MCGT > ΛCDM
    ax.fill_between(ells, cl0, cl1, where=cl1 > cl0, color="tab:red", alpha=0.15)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(2, 3000)
    ymin = float(min(cl0.min(), cl1.min()) * 0.8)
    ymax = float(max(cl0.max(), cl1.max()) * 1.2)
    ax.set_ylim(ymin, ymax)

    ax.set_xlabel(r"$k$ [$h/\mathrm{Mpc}$]")
    ax.set_ylabel(r"$P(k)$ [$(h^{-1}\mathrm{Mpc})^3$]")
    ax.set_title("Matter Power Spectrum Comparison")
    ax.grid(True, which="both", linestyle=":", linewidth=0.5)
    ax.legend(loc="upper right", frameon=False)

    # Inset 1 : ΔC_ell / C_ell (bas gauche)
    axins1 = inset_axes(
        ax,
        width="85%",
        height="85%",
        bbox_to_anchor=(0.06, 0.06, 0.30, 0.35),
        bbox_transform=ax.transAxes,
        borderpad=0,
    )
    axins1.plot(ells, delta_rel, linestyle="-", color="tab:green")
    axins1.set_xscale("log")
    axins1.set_ylim(-0.02, 0.02)
    axins1.set_xlabel(r"$k$", fontsize=8)
    axins1.set_ylabel(r"$\Delta C_{\ell}/C_{\ell}$", fontsize=8)
    axins1.grid(True, which="both", linestyle=":", linewidth=0.5)
    axins1.tick_params(labelsize=7)

    # Inset 2 : zoom 200 < ell < 300 (droite)
    axins2 = inset_axes(
        ax,
        width="85%",
        height="85%",
        bbox_to_anchor=(0.50, 0.06, 0.30, 0.35),
        bbox_transform=ax.transAxes,
        borderpad=0,
    )
    mask_zoom = (ells > 200) & (ells < 300)
    axins2.plot(ells[mask_zoom], cl0[mask_zoom], "--", linewidth=1, alpha=0.7)
    axins2.plot(
        ells[mask_zoom],
        cl1[mask_zoom],
        "-",
        linewidth=1,
        alpha=0.7,
        color="tab:orange",
    )
    axins2.set_xscale("log")
    axins2.set_yscale("log")
    axins2.set_title(r"Zoom $200<\ell<300$", fontsize=8)
    axins2.grid(True, which="both", linestyle=":", linewidth=0.5)
    axins2.tick_params(labelsize=7)

    # Annotation paramètres
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

    safe_save(OUT_PNG)
    logging.info("Figure enregistrée → %s", OUT_PNG)


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
