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
plot_fig03_invariant_i1.py

Figure 03 – Invariant i1(k)
Chapitre 7 – Perturbations scalaires MCGT.

Ce script reste volontairement générique :
- il lit un CSV avec au moins une colonne 'k' + une colonne de valeurs pour i1
- il détecte automatiquement la colonne i1 parmi quelques noms usuels
  ou, à défaut, parmi les colonnes numériques ≠ 'k'.

Par défaut, il suppose un fichier :
  zz-data/chapter07/07_scalar_invariants.csv
mais tu peux surcharger avec --data-csv et --value-col.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def setup_logging(verbose: int = 0) -> None:
    if verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")


def detect_project_root() -> Path:
    try:
        return Path(__file__).resolve().parents[2]
    except NameError:
        return Path.cwd()


def detect_value_column(
    df: pd.DataFrame,
    preferred: Sequence[str],
    context: str,
) -> str:
    """Détermine la colonne de valeurs à utiliser pour i1(k)."""
    cols = list(df.columns)
    for name in preferred:
        if name in df.columns:
            logging.info("Colonne %s détectée automatiquement pour %s", name, context)
            return name

    numeric_cols = [
        c for c in df.columns if c != "k" and pd.api.types.is_numeric_dtype(df[c])
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
        "Colonnes numériques candidates (hors 'k') : %s",
        context,
        cols,
        numeric_cols,
    )
    raise RuntimeError(
        f"Impossible de déterminer la colonne de valeurs pour {context} "
        f"(colonnes: {cols}, candidates numériques: {numeric_cols})"
    )


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------


def plot_invariant_i1(
    *,
    data_csv: Path,
    meta_json: Path,
    out_png: Path,
    value_col: Optional[str] = None,
    dpi: int = 300,
) -> None:
    """Trace i1(k) en échelle log-log, avec repère k_split."""

    logging.info("Début du tracé de la figure 03 – Invariant i1(k)")
    logging.info("CSV données  : %s", data_csv)
    logging.info("JSON méta    : %s", meta_json)
    logging.info("Figure sortie: %s", out_png)

    if not meta_json.exists():
        logging.error("Fichier de méta-paramètres introuvable : %s", meta_json)
        raise FileNotFoundError(meta_json)
    meta = json.loads(meta_json.read_text(encoding="utf-8"))
    k_split = float(meta.get("x_split", meta.get("k_split", 0.0)))
    logging.info("Lecture de k_split = %.3e [h/Mpc]", k_split)

    if not data_csv.exists():
        logging.error("CSV introuvable : %s", data_csv)
        raise FileNotFoundError(data_csv)

    df = pd.read_csv(data_csv)
    logging.info("Chargement terminé : %d lignes", len(df))
    logging.debug("Colonnes du CSV : %s", list(df.columns))

    if "k" not in df.columns:
        raise KeyError(
            f"Colonne 'k' absente du CSV {data_csv} (colonnes: {list(df.columns)})"
        )

    if value_col is None:
        value_col = detect_value_column(
            df,
            preferred=["i1", "invariant_i1", "I1", "inv1"],
            context="invariant i1(k)",
        )

    k_vals = df["k"].to_numpy(dtype=float)
    i1_vals = df[value_col].to_numpy(dtype=float)

    # Filtrage des points non finis / <=0 pour la log (sur y)
    mask = np.isfinite(k_vals) & np.isfinite(i1_vals) & (k_vals > 0) & (i1_vals > 0)
    k_vals = k_vals[mask]
    i1_vals = i1_vals[mask]
    logging.info("Points retenus après filtrage log-log : %d", k_vals.size)

    if k_vals.size == 0:
        raise ValueError("Aucun point positif/valide pour tracer i1(k) en log-log.")

    plt.rc("font", family="serif")

    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.0, 4.5), dpi=dpi)

    ax.loglog(k_vals, i1_vals, color="C0", lw=2.0, label=r"$i_1(k)$")

    ax.set_xlabel("Redshift $z$", fontsize="small")
    ax.set_ylabel(r"$\Omega_m(z)$", fontsize="small")
    ax.set_title(r"Matter Density Fraction $\Omega_m(z)$", fontsize="small")

    # Repère k_split
    if k_split > 0:
        ax.axvline(k_split, color="k", ls="--", lw=1.0)
        ax.text(
            k_split,
            0.9,
            r"$k_{\rm split}$",
            transform=ax.get_xaxis_transform(),
            rotation=90,
            ha="right",
            va="top",
            fontsize="small",
        )

    ax.grid(which="both", ls=":", lw=0.5, alpha=0.8)
    ax.legend(loc="best", frameon=False, fontsize="small")

    for lbl in list(ax.xaxis.get_ticklabels()) + list(ax.yaxis.get_ticklabels()):
        lbl.set_fontsize("x-small")

    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.13, top=0.90)
    safe_save(out_png, dpi=dpi)
    plt.close(fig)

    logging.info("Figure enregistrée : %s", out_png)
    logging.info("Tracé de la figure 03 terminé ✔")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    root = detect_project_root()
    default_data = root / "zz-data" / "chapter07" / "07_scalar_invariants.csv"
    default_meta = root / "zz-data" / "chapter07" / "07_meta_perturbations.json"
    default_out = root / "zz-figures" / "chapter07" / "07_fig_03_density.png"

    p = argparse.ArgumentParser(
        description=(
            "Figure 03 – Invariant i1(k).\n"
            "Lit un CSV (k + colonne i1) et génère la figure PNG."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--data-csv",
        default=str(default_data),
        help="CSV contenant les colonnes 'k' et la colonne i1.",
    )
    p.add_argument(
        "--meta-json",
        default=str(default_meta),
        help="JSON méta contenant au moins k_split/x_split.",
    )
    p.add_argument(
        "--out",
        default=str(default_out),
        help="Chemin de sortie de la figure PNG.",
    )
    p.add_argument(
        "--value-col",
        default=None,
        help="Nom explicite de la colonne i1 (sinon détection automatique).",
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


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    setup_logging(args.verbose)

    data_csv = Path(args.data_csv)
    meta_json = Path(args.meta_json)
    out_png = Path(args.out)

    plot_invariant_i1(
        data_csv=data_csv,
        meta_json=meta_json,
        out_png=out_png,
        value_col=args.value_col,
        dpi=args.dpi,
    )


if __name__ == "__main__":
    main()
