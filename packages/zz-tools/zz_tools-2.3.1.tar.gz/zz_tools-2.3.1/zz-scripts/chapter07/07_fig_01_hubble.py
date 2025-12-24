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
plot_fig01_cs2_heatmap.py

Figure 01 - Carte de chaleur de $c_s^2(k,a)$
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
from matplotlib.colors import LogNorm


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
        # Fallback si __file__ n'est pas défini (exécution interactive)
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

    # Fallback: colonnes candidates (numériques) hors 'k' et 'a'
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


def plot_cs2_heatmap(
    *,
    data_csv: Path,
    meta_json: Path,
    out_png: Path,
    dpi: int = 300,
) -> None:
    """Trace la carte de chaleur de c_s^2(k,a) et enregistre la figure."""

    logging.info("Début du tracé de la figure 01 – Carte de chaleur de c_s²(k,a)")
    logging.info("CSV données  : %s", data_csv)
    logging.info("JSON méta    : %s", meta_json)
    logging.info("Figure sortie: %s", out_png)

    # --- Métadonnées ---
    if not meta_json.exists():
        logging.error("Fichier de méta-paramètres introuvable : %s", meta_json)
        raise FileNotFoundError(meta_json)

    meta = json.loads(meta_json.read_text(encoding="utf-8"))
    k_split = float(meta.get("x_split", meta.get("k_split", 0.0)))
    logging.info("Lecture de k_split = %.3e [h/Mpc]", k_split)

    # --- Chargement des données ---
    if not data_csv.exists():
        logging.error("Fichier de données introuvable : %s", data_csv)
        raise FileNotFoundError(data_csv)

    df = pd.read_csv(data_csv)
    logging.info("Chargement terminé : %d lignes", len(df))
    logging.debug("Colonnes du CSV : %s", list(df.columns))

    value_col = detect_value_column(
        df,
        preferred=["cs2_matrice", "cs2", "cs2_value"],
        context="c_s^2(k,a)",
    )
    logging.info("Colonne utilisée pour c_s^2 : %s", value_col)

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

    # On force en float pour les axes
    k_vals = pivot.index.to_numpy(dtype=float)
    a_vals = pivot.columns.to_numpy(dtype=float)
    mat = pivot.to_numpy(dtype=float)
    logging.info("Matrice brute : %d×%d (k×a)", mat.shape[0], mat.shape[1])

    # Masquage des valeurs non finies ou <= 0
    mask = ~np.isfinite(mat) | (mat <= 0)
    mat_masked = np.ma.array(mat, mask=mask)
    masked_ratio = mask.mean() * 100.0
    logging.info("Fraction de valeurs masquées : %.1f %%", masked_ratio)

    if mat_masked.count() == 0:
        raise ValueError("Aucune valeur c_s² > 0 exploitable pour le tracé.")

    # Détermination de vmin / vmax pour l'échelle log
    raw_min = float(mat_masked.min())
    raw_max = float(mat_masked.max())
    vmin = max(raw_min, raw_max * 1e-6)
    vmax = min(raw_max, 1.0)
    if vmin <= 0 or vmin >= vmax:
        vmin = max(raw_max * 1e-6, 1e-12)
        vmax = raw_max
    logging.info("LogNorm vmin=%.3e, vmax=%.3e", vmin, vmax)

    # Police mathtext standard
    plt.rc("font", family="serif")

    # --- Tracé ---
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5), dpi=dpi)

    cmap = plt.get_cmap("Blues")

    mesh = ax.pcolormesh(
        a_vals,
        k_vals,
        mat_masked,
        norm=LogNorm(vmin=vmin, vmax=vmax),
        cmap=cmap,
        shading="auto",
    )

    ax.set_xscale("linear")
    ax.set_yscale("log")
    ax.set_xlabel(r"Redshift $z$", fontsize="small")
    ax.set_ylabel(r"$H(z)$ [km/s/Mpc]", fontsize="small")
    ax.set_title(r"Hubble Parameter Evolution $H(z)$", fontsize="small")

    # Ticks en petite taille
    for lbl in list(ax.xaxis.get_ticklabels()) + list(ax.yaxis.get_ticklabels()):
        lbl.set_fontsize("small")

    # Colorbar
    cbar = fig.colorbar(mesh, ax=ax)
    cbar.set_label(r"$H(z)$", rotation=270, labelpad=15, fontsize="small")
    cbar.ax.yaxis.set_tick_params(labelsize="small")

    # Ligne horizontale k_split (uniquement si k_split>0 pour éviter les logs invalides)
    if k_split > 0:
        ax.axhline(k_split, color="white", linestyle="--", linewidth=1)
        ax.text(
            float(a_vals.max()),
            k_split * 1.1,
            r"$k_{\rm split}$",
            color="white",
            va="bottom",
            ha="right",
            fontsize="small",
        )
        logging.info("Ajout de la ligne horizontale à k = %.3e", k_split)

    # Sauvegarde
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.08, top=0.96)
    safe_save(out_png, dpi=dpi)
    plt.close(fig)

    logging.info("Figure enregistrée : %s", out_png)
    logging.info("Tracé de la figure 01 terminé ✔")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    racine = detect_project_root()
    default_data = racine / "zz-data" / "chapter07" / "07_cs2_matrix.csv.gz"
    default_meta = racine / "zz-data" / "chapter07" / "07_meta_perturbations.json"
    default_out = racine / "zz-figures" / "chapter07" / "07_fig_01_hubble.png"

    p = argparse.ArgumentParser(
        description=(
            "Figure 01 – Carte de chaleur de c_s^2(k,a) (Chapitre 7).\n"
            "Génère la figure PNG à partir de la matrice cs2 et des méta-paramètres."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--data-csv",
        default=str(default_data),
        help="CSV contenant la matrice c_s^2 (colonnes: k, a, valeur).",
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

    plot_cs2_heatmap(
        data_csv=data_csv,
        meta_json=meta_json,
        out_png=out_png,
        dpi=args.dpi,
    )


if __name__ == "__main__":
    main()
