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
"""Fig. 04 – χ²(T) + dérivée dχ²/dT – Chapitre 5"""

import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from scipy.signal import savgol_filter
from mpl_toolkits.axes_grid1 import make_axes_locatable

# --- Répertoires et constantes ---
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "zz-data" / "chapter05"
FIG_DIR = ROOT / "zz-figures" / "chapter05"
FIG_STEM = "05_fig_04_cost_surface"


def main(args=None) -> None:
    """Construit la figure χ²(T) + dχ²/dT/1e4 et la sauvegarde sur disque."""

    # ---- Gestion des options CLI / défauts homogènes ----
    if args is not None and getattr(args, "outdir", None):
        outdir = Path(args.outdir).expanduser()
    else:
        env_outdir = os.environ.get("MCGT_OUTDIR")
        if env_outdir:
            outdir = Path(env_outdir).expanduser()
        else:
            outdir = FIG_DIR

    dry_run = bool(args is not None and getattr(args, "dry_run", False))
    verbose = int(getattr(args, "verbose", 0) if args is not None else 0) > 0
    fmt = getattr(args, "format", "png") if args is not None else "png"
    dpi = getattr(args, "dpi", 300) if args is not None else 300
    transparent = bool(
        getattr(args, "transparent", False) if args is not None else False
    )

    if not dry_run:
        outdir.mkdir(parents=True, exist_ok=True)

    os.environ["MCGT_OUTDIR"] = str(outdir)

    out_path = outdir / f"{FIG_STEM}.{fmt}"

    chi2_file = DATA_DIR / "05_chi2_bbn_vs_T.csv"
    dchi_file = DATA_DIR / "05_dchi2_vs_T.csv"

    if verbose:
        print(f"[plot_fig04_chi2_vs_T] lecture CHI2={chi2_file}")
        print(f"[plot_fig04_chi2_vs_T] lecture DCHI={dchi_file}")
        print(f"[plot_fig04_chi2_vs_T] sortie -> {out_path}")

    # --- 1) Chargement de χ²(T) ---
    chi2_df = pd.read_csv(chi2_file)

    # auto-détection de la colonne χ² (contient "chi2" mais pas "d"/"deriv")
    chi2_col = next(
        c
        for c in chi2_df.columns
        if "chi2" in c.lower() and not any(k in c.lower() for k in ("d", "deriv"))
    )

    # conversion et nettoyage
    chi2_df["T_Gyr"] = pd.to_numeric(chi2_df["T_Gyr"], errors="coerce")
    chi2_df[chi2_col] = pd.to_numeric(chi2_df[chi2_col], errors="coerce")
    chi2_df = chi2_df.dropna(subset=["T_Gyr", chi2_col])
    T = chi2_df["T_Gyr"].to_numpy()
    chi2 = chi2_df[chi2_col].to_numpy()

    # incertitude : colonne 'chi2_err' si présente, sinon ±10 %
    if "chi2_err" in chi2_df.columns:
        sigma = pd.to_numeric(chi2_df["chi2_err"], errors="coerce").to_numpy()
    else:
        sigma = 0.10 * chi2

    # --- 2) Chargement de dχ²/dT ---
    dchi_df = pd.read_csv(dchi_file)

    # auto-détection de la colonne dérivée (contient "chi2" et "d"/"deriv"/"smooth")
    dchi_col = next(
        c
        for c in dchi_df.columns
        if "chi2" in c.lower() and any(k in c.lower() for k in ("d", "deriv", "smooth"))
    )

    dchi_df["T_Gyr"] = pd.to_numeric(dchi_df["T_Gyr"], errors="coerce")
    dchi_df[dchi_col] = pd.to_numeric(dchi_df[dchi_col], errors="coerce")
    dchi_df = dchi_df.dropna(subset=["T_Gyr", dchi_col])
    Td = dchi_df["T_Gyr"].to_numpy()
    dchi_raw = dchi_df[dchi_col].to_numpy()

    # --- 3) Alignement + lissage Savitzky–Golay ---
    if dchi_raw.size == 0:
        # pas de dérivée dispo : on met un vecteur nul
        dchi = np.zeros_like(chi2)
    else:
        # interpolation sur la même grille T (en log)
        if not np.allclose(Td, T):
            dchi = np.interp(
                np.log10(T),
                np.log10(Td),
                dchi_raw,
                left=np.nan,
                right=np.nan,
            )
        else:
            dchi = dchi_raw.copy()

        # lissage Savitzky–Golay (fenêtre impaire ≤ 7)
        if len(dchi) >= 5:
            win = min(7, (len(dchi) // 2) * 2 + 1)
            dchi = savgol_filter(dchi, window_length=win, polyorder=3, mode="interp")

    # échelle réduite pour lisibilité
    dchi_scaled = dchi / 1e4

    # --- 4) Minimum de χ² ---
    imin = int(np.nanargmin(chi2))
    Tmin = T[imin]
    chi2_min = chi2[imin]

    # --- 5) Tracé ---
    plt.rcParams.update({"font.size": 11})
    fig, ax1 = plt.subplots(figsize=(6.5, 4.5))

    ax1.set_xscale("log")
    ax1.set_xlabel(r"$T\,[\mathrm{Gyr}]$")
    ax1.set_ylabel(r"$\chi^2$", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")
    ax1.grid(which="both", ls=":", lw=0.5, alpha=0.5)
    ax1.set_title("2D Cost Function Surface", pad=20)

    # bande ±1σ
    ax1.fill_between(
        T,
        chi2 - sigma,
        chi2 + sigma,
        color="tab:blue",
        alpha=0.12,
        label=r"$\pm1\sigma$",
    )

    # courbe χ²
    (l1,) = ax1.plot(T, chi2, lw=2, color="tab:blue", label=r"$\chi^2$")

    # axe secondaire pour la dérivée
    ax2 = ax1.twinx()
    ax2.set_ylabel(
        r"$\mathrm{d}\chi^2/\mathrm{d}T$ (×$10^{-4}$)", color="tab:orange", fontsize=10
    )
    ax2.tick_params(axis="y", labelcolor="tab:orange")
    (l2,) = ax2.plot(
        T,
        dchi_scaled,
        lw=2,
        color="tab:orange",
        label=r"$\mathrm{d}\chi^2/\mathrm{d}T/10^{4}$",
    )

    # point de minimum + annotation textuelle
    ax1.scatter(Tmin, chi2_min, s=60, color="k", zorder=4)
    ax1.text(
        0.5,
        0.38,
        rf"Min $\chi^2 = {chi2_min:.2f}$ at $T = {Tmin:.2f}$ Gyr",
        transform=ax1.transAxes,
        ha="center",
        va="top",
        fontsize="small",
        color="k",
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
    )

    # légende combinée
    ax1.legend(
        handles=[l1, l2],
        labels=[r"$\chi^2$", r"$\mathrm{d}\chi^2/\mathrm{d}T/10^4$"],
        loc="center",
        fontsize="small",
        framealpha=0.9,
    )

    sm = ScalarMappable(
        norm=Normalize(vmin=float(np.nanmin(chi2)), vmax=float(np.nanmax(chi2))),
        cmap="viridis",
    )
    sm.set_array([])
    divider = make_axes_locatable(ax2)
    cax = divider.append_axes("right", size="5%", pad=0.8)
    cbar = plt.colorbar(sm, cax=cax)
    cbar.set_label(r"$J(\theta)$ [dimensionless]")

    fig.subplots_adjust(left=0.04, right=0.75, bottom=0.06, top=0.96)

    if verbose:
        print(f"[plot_fig04_chi2_vs_T] sauvegarde -> {out_path}")

    if dry_run:
        return

    safe_save(out_path, dpi=dpi, transparent=transparent)
    if verbose:
        try:
            rel = out_path.relative_to(ROOT)
        except ValueError:
            rel = out_path
        print(f"✓ {rel} généré.")


# === MCGT CLI SEED v2 homogène ===
if __name__ == "__main__":
    import argparse
    import sys
    import traceback
    import matplotlib as mpl

    parser = argparse.ArgumentParser(
        description=(
            "Standard CLI seed (non-intrusif) pour Fig. 04 – "
            "χ²(T) et dérivée (chapter 5)."
        )
    )
    parser.add_argument(
        "--outdir",
        default=None,
        help=("Dossier de sortie (par défaut: zz-figures/chapter05 ou $MCGT_OUTDIR)."),
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
        help="Graine aléatoire (optionnelle, non utilisée ici).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forcer l'écrasement des sorties (placeholder pour homogénéité).",
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
        help="Format de sortie (par défaut: png).",
    )
    parser.add_argument(
        "--transparent",
        action="store_true",
        help="Fond transparent pour la figure.",
    )

    cli_args = parser.parse_args()

    # Config globale Matplotlib, pour rester cohérent avec les autres scripts
    mpl.rcParams["savefig.dpi"] = cli_args.dpi
    mpl.rcParams["savefig.format"] = cli_args.format
    mpl.rcParams["savefig.transparent"] = cli_args.transparent

    try:
        main(cli_args)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"[CLI seed] main() a levé: {exc}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
