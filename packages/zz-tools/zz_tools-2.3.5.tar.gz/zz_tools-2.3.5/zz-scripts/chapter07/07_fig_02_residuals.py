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
r"""
plot_fig02_delta_phi_heatmap.py

Figure 02 – Carte de chaleur de $\delta\phi/\phi(k,a)$
pour le Chapitre 7 (Perturbations scalaires) du projet MCGT.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import PowerNorm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def setup_logging(verbose: int = 0) -> None:
    """Configure le niveau de logging en fonction de -v / -vv."""
    if verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")


def detect_project_root() -> Path:
    """Détecte la racine du dépôt à partir du chemin du script."""
    try:
        return Path(__file__).resolve().parents[2]
    except NameError:
        return Path.cwd()


def detect_value_column(
    df: pd.DataFrame,
    preferred: Sequence[str],
    context: str,
) -> str:
    """
    Détecte la colonne de valeur pour le heatmap.

    - Essaie d'abord les noms préférés dans l'ordre.
    - Sinon, cherche les colonnes numériques ≠ {'k','a'}.
      * Si une seule, on la prend.
      * Sinon, on lève une erreur explicite.
    """
    cols = list(df.columns)
    for name in preferred:
        if name in df.columns:
            logging.info("Colonne %s détectée automatiquement pour %s", name, context)
            return name

    numeric_cols = [
        c
        for c in df.columns
        if c not in {"k", "a"} and pd.api.types.is_numeric_dtype(df[c])
    ]
    if len(numeric_cols) == 1:
        logging.info(
            "Colonne unique numérique '%s' sélectionnée automatiquement pour %s",
            numeric_cols[0],
            context,
        )
        return numeric_cols[0]

    logging.error(
        "Impossible de déterminer la colonne de valeurs pour %s.\n"
        "Colonnes disponibles : %s\n"
        "Colonnes numériques candidates (hors k,a) : %s",
        context,
        cols,
        numeric_cols,
    )
    raise RuntimeError(
        f"Impossible de déterminer la colonne de valeurs pour {context} "
        f"(colonnes: {cols}, candidates numériques: {numeric_cols})"
    )


# ---------------------------------------------------------------------------
# Cœur du tracé
# ---------------------------------------------------------------------------


def plot_delta_phi_heatmap(
    *,
    data_csv: Path,
    meta_json: Path,
    out_png: Path,
    dpi: int = 300,
) -> None:
    """Trace la carte de chaleur de δφ/φ(k,a) et enregistre la figure."""

    logging.info("Début du tracé de la figure 02 – Carte de chaleur de δφ/φ")
    logging.info("CSV matrice : %s", data_csv)
    logging.info("JSON méta   : %s", meta_json)
    logging.info("Figure out  : %s", out_png)

    # --- Métadonnées ---
    if not meta_json.exists():
        logging.error("Fichier de méta-paramètres introuvable : %s", meta_json)
        raise FileNotFoundError(meta_json)

    meta = json.loads(meta_json.read_text(encoding="utf-8"))
    k_split = float(meta.get("x_split", meta.get("k_split", 0.0)))
    logging.info("Lecture de k_split = %.3e [h/Mpc]", k_split)

    # --- Chargement des données ---
    if not data_csv.exists():
        logging.error("CSV introuvable : %s", data_csv)
        raise FileNotFoundError(data_csv)

    df = pd.read_csv(data_csv)
    logging.info("Chargement terminé : %d lignes", len(df))
    logging.debug("Colonnes du CSV : %s", list(df.columns))

    value_col = detect_value_column(
        df,
        preferred=["delta_phi_matrice", "delta_phi_over_phi", "delta_phi_phi"],
        context="delta_phi/phi(k,a)",
    )
    logging.info("Colonne utilisée pour δφ/φ : %s", value_col)

    try:
        pivot = df.pivot(index="k", columns="a", values=value_col)
    except KeyError:
        logging.error(
            "Colonnes 'k','a',%r manquantes dans %s (colonnes présentes: %s)",
            value_col,
            data_csv,
            list(df.columns),
        )
        raise

    k_vals = pivot.index.to_numpy(dtype=float)
    a_vals = pivot.columns.to_numpy(dtype=float)
    mat_raw = pivot.to_numpy(dtype=float)
    logging.info("Matrice brute : %d×%d (k×a)", mat_raw.shape[0], mat_raw.shape[1])

    # Masquage des non-finis et <= 0
    mask = ~np.isfinite(mat_raw) | (mat_raw <= 0)
    mat = np.ma.array(mat_raw, mask=mask)
    logging.info("Fraction de valeurs masquées : %.1f %%", 100.0 * mask.mean())

    # --- Échelle couleur ---
    # Bornes choisies pour mettre en évidence la transition
    vmin, vmax = 1e-6, 1e-5
    logging.info("Colorbar fixed range: [%.1e, %.1e]", vmin, vmax)

    norm = PowerNorm(gamma=0.5, vmin=vmin, vmax=vmax)
    cmap = plt.get_cmap("Oranges").copy()
    cmap.set_bad(color="lightgrey", alpha=0.8)

    plt.rc("font", family="serif")

    # --- Tracé ---
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5), dpi=dpi)

    mesh = ax.pcolormesh(
        a_vals,
        k_vals,
        mat,
        cmap=cmap,
        norm=norm,
        shading="auto",
    )

    ax.set_xscale("linear")
    ax.set_yscale("log")
    ax.set_xlabel("Redshift $z$", fontsize="small")
    ax.set_ylabel(r"$\Delta \mu$ [mag]", fontsize="small")
    ax.set_title("Distance Modulus Residuals (MCGT vs $\\Lambda$CDM)", fontsize="small")

    # Ticks en petite taille
    for lbl in list(ax.xaxis.get_ticklabels()) + list(ax.yaxis.get_ticklabels()):
        lbl.set_fontsize("small")

    # Contours guides (en blanc, semi-opaques)
    levels = np.logspace(np.log10(vmin), np.log10(vmax), 5)
    mat_for_contour = np.where(mask, np.nan, mat_raw)
    ax.contour(
        a_vals,
        k_vals,
        mat_for_contour,
        levels=levels,
        colors="white",
        linewidths=0.5,
        alpha=0.7,
    )

    # Repère k_split
    if k_split > 0:
        ax.axhline(k_split, color="black", linestyle="--", linewidth=1)
        ax.text(
            float(a_vals.max()),
            k_split * 1.1,
            r"$k_{\rm split}$",
            va="bottom",
            ha="right",
            fontsize="small",
            color="black",
        )

    # --- Barre de couleur ---
    cbar = fig.colorbar(mesh, ax=ax, pad=0.02, extend="both")
    cbar.set_label(r"$\Delta \mu$", rotation=270, labelpad=15, fontsize="small")
    ticks = np.logspace(np.log10(vmin), np.log10(vmax), 5)
    cbar.set_ticks(ticks)
    cbar.set_ticklabels([f"$10^{{{int(np.round(np.log10(t)))}}}$" for t in ticks])
    cbar.ax.yaxis.set_tick_params(labelsize="small")

    # Sauvegarde
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.08, top=0.96)
    safe_save(out_png, dpi=dpi)
    plt.close(fig)

    logging.info("Figure sauvegardée : %s", out_png)
    logging.info("Tracé de la figure 02 terminé ✔")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    racine = detect_project_root()
    default_data = racine / "zz-data" / "chapter07" / "07_delta_phi_matrix.csv.gz"
    default_meta = racine / "zz-data" / "chapter07" / "07_meta_perturbations.json"
    default_out = racine / "zz-figures" / "chapter07" / "07_fig_02_residuals.png"

    p = argparse.ArgumentParser(
        description=(
            "Figure 02 – Carte de chaleur de δφ/φ(k,a) (Chapitre 7).\n"
            "Génère la figure PNG à partir de la matrice delta_phi_matrice."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--data-csv",
        default=str(default_data),
        help="CSV contenant la matrice δφ/φ (colonnes: k, a, valeur).",
    )
    p.add_argument(
        "--meta-json",
        default=str(default_meta),
        help="JSON des méta-paramètres (contient notamment k_split).",
    )
    p.add_argument(
        "--out",
        default=str(default_out),
        help="Chemin de sortie pour la figure PNG.",
    )
    p.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Résolution de la figure.",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Verbosity cumulable (-v, -vv).",
    )
    return p


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    setup_logging(args.verbose)

    data_csv = Path(args.data_csv)
    meta_json = Path(args.meta_json)
    out_png = Path(args.out)

    plot_delta_phi_heatmap(
        data_csv=data_csv,
        meta_json=meta_json,
        out_png=out_png,
        dpi=args.dpi,
    )


if __name__ == "__main__":
    main()
