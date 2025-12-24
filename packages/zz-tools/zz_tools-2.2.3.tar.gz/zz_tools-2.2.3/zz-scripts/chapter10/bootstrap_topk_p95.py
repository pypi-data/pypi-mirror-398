#!/usr/bin/env python3
"""
bootstrap_topk_p95.py
---------------------

Bootstrap des p95 pour le top-K en utilisant les fichiers de résidus
par-identifiant produits par `inspect_topk_residuals.py`.

Usage (exemple)
---------------
python zz-scripts/chapter10/bootstrap_topk_p95.py \
  --best zz-data/chapter10/10_mc_best.json \
  --results zz-data/chapter10/10_mc_results.csv \
  --B 1000 --seed 12345 \
  --out zz-data/chapter10/10_mc_best_bootstrap.json \
  --log-level INFO

Notes
-----
- Cherche par défaut les fichiers de résidus dans:
    zz-data/chapter10/topk_residuals/10_topresiduals_id{ID}.csv
  Le CSV attendu contient au moins une colonne d'absolu des résidus
  (ex: "absdphi", "abs_dphi", "abs_d_phi", "|Δφ|", "abs(Δφ)").
- Si un fichier de résidus manque pour un ID, le script conserve
  la valeur p95 issue de results.csv (si fournie) et marque p95_ci=null.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


# -----------------------
# Helpers
# -----------------------
_logger = logging.getLogger("mcgt.bootstrap_topk_p95")


def find_resid_file(resid_dir: Path, id_: int) -> Path | None:
    """Retourne le Path du fichier de résidus correspondant à `id_` s'il existe."""
    _candidates = [
        resid_dir / f"10_topresiduals_id{id_}.csv",
        resid_dir / f"topresiduals_id{id_}.csv",
        resid_dir / f"topresiduals_{id_}.csv",
        resid_dir / f"{id_}_topresiduals.csv",
    ]
    for p in _candidates:
        if p.exists():
            return p
    # fallback: glob any file containing the id
    for p in resid_dir.glob(f"*{id_}*.csv"):
        return p
    return None


def detect_abscol(df: pd.DataFrame) -> str | None:
    """Tente détecter la colonne contenant les valeurs |Δφ|."""
    _candidates = [c.lower() for c in df.columns]
    mapping = {
        "absdphi": [
            "absdphi",
            "abs_dphi",
            "abs_d_phi",
            "abs(phi_diff)",
            "|Δφ|",
            "abs(delta_phi)",
        ],
        "absdeltaphi": ["absdeltaphi", "abs_delta_phi", "abs(delta_phi)"],
        "absd": ["absd"],
    }
    # direct exact match
    for col in df.columns:
        key = col.strip().lower()
        if key in sum(mapping.values(), []):
            return col
    # look for substrings
    for col in df.columns:
        key = col.strip().lower()
        if "abs" in key and ("phi" in key or "dphi" in key or "delta" in key):
            return col
        if "dphi" in key or "delta" in key:
            return col
    # if nothing, try numeric-only second column
    if df.shape[1] >= 2:
        return df.columns[1]
    return None


def bootstrap_p95_from_array(
    arr: np.ndarray, B: int, rng: np.random.Generator
) -> np.ndarray:
    """
    Retourne les B valeurs bootstrapées du p95 calculées à partir d'`arr`.
    - arr : 1D array des valeurs |Δφ|(f) sur la fenêtre d'intérêt
    - B : nombre de rééchantillonnages
    - rng : np.random.Generator
    """
    arr = np.asarray(arr, dtype=float)
    L = arr.size
    if L == 0:
        return np.array([], dtype=float)
    # indices shape (B, L)
    idx = rng.integers(0, L, size=(B, L))
    samples = arr[idx]  # shape (B, L)
    # np.nanpercentile with axis=1
    try:
        p95s = np.nanpercentile(samples, 95, axis=1, method="linear")
    except TypeError:
        # fallback older numpy without 'method' kwarg
        p95s = np.nanpercentile(samples, 95, axis=1)
    return p95s


# -----------------------
# Main
# -----------------------
def main(argv=None):
    p = argparse.ArgumentParser(
        description="Bootstrap p95 pour top-K (fichiers de résidus requis)."
    )
    p.add_argument("--best", required=True, help="JSON top-K (10_mc_best.json)")
    p.add_argument(
        "--results",
        required=False,
        help="CSV results (10_mc_results.csv) — utilisé en fallback",
    )
    p.add_argument(
        "--B",
        type=int,
        default=1000,
        help="Nombre de rééchantillonnages bootstrap (défaut: 1000)",
    )
    p.add_argument(
        "--seed", type=int, default=12345, help="Seed RNG pour reproductibilité"
    )
    p.add_argument(
        "--resid-dir",
        default="zz-data/chapter10/topk_residuals",
        help="Répertoire contenant les fichiers de résidus par id",
    )
    p.add_argument("--out", required=True, help="Fichier JSON de sortie (augmenté)")
    p.add_argument("--log-level", default="INFO", help="Niveau de logs")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    _logger.info("Lancement bootstrap_topk_p95.py")
    best_path = Path(args.best)
    out_path = Path(args.out)
    resid_dir = Path(args.resid_dir)

    if not best_path.exists():
        _logger.error("Fichier top-K introuvable : %s", best_path)
        raise SystemExit(2)

    # load top-K JSON
    with best_path.open("r", encoding="utf-8") as fh:
        topk_obj = json.load(fh)

    top_k = topk_obj.get("top_k") or topk_obj.get("topK") or []
    if not top_k:
        _logger.warning("Aucun top_k trouvé dans %s. Rien à faire.", best_path)
        # write minimal output
        out = {
            "top_k": [],
            "meta": {
                "B": args.B,
                "seed": args.seed,
                "created_at": datetime.utcnow().isoformat() + "Z",
            },
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, sort_keys=True)
        return 0

    # load results csv if present (fallback p95 values)
    results_df = None
    if args.results:
        results_p = Path(args.results)
        if results_p.exists():
            _logger.info("Chargement results CSV pour fallback: %s", results_p)
            results_df = pd.read_csv(results_p)
            if "id" in results_df.columns:
                results_df["id"] = results_df["id"].astype(int)

    rng = np.random.default_rng(args.seed)
    B = int(args.B)

    # itérer sur top_k
    enriched = []
    for entry in top_k:
        # standardize entry as dict
        ent = dict(entry)
        id_ = int(ent.get("id") or ent.get("index") or ent.get("idx"))
        _logger.info("Processing id=%d", id_)

        resid_file = find_resid_file(resid_dir, id_)
        if resid_file is None:
            _logger.warning(
                "Fichier de résidus non trouvé pour id=%d (cherche dans %s). Fallback p95 si dispo.",
                id_,
                resid_dir,
            )
            # fallback : copy p95 from results_df if available
            if results_df is not None:
                row = results_df.loc[results_df["id"] == id_]
                if not row.empty and "p95_20_300" in row.columns:
                    ent["p95_boot_median"] = float(row.iloc[0]["p95_20_300"])
                    ent["p95_ci"] = None
                    ent["n_points_resid"] = None
                else:
                    ent["p95_boot_median"] = None
                    ent["p95_ci"] = None
                    ent["n_points_resid"] = None
            else:
                ent["p95_boot_median"] = None
                ent["p95_ci"] = None
                ent["n_points_resid"] = None
            enriched.append(ent)
            continue

        # charger le CSV de résidus
        try:
            dfr = pd.read_csv(resid_file)
        except Exception as e:
            _logger.exception(
                "Impossible de lire %s pour id=%d : %s", resid_file, id_, e
            )
            ent["p95_boot_median"] = None
            ent["p95_ci"] = None
            ent["n_points_resid"] = None
            enriched.append(ent)
            continue

        col = detect_abscol(dfr)
        if col is None:
            _logger.warning(
                "Impossible de détecter colonne |Δφ| dans %s pour id=%d",
                resid_file,
                id_,
            )
            ent["p95_boot_median"] = None
            ent["p95_ci"] = None
            ent["n_points_resid"] = None
            enriched.append(ent)
            continue

        arr = dfr[col].to_numpy(dtype=float)
        n_points = arr.size
        if n_points == 0:
            _logger.warning("Tableau vide pour id=%d (fichier %s).", id_, resid_file)
            ent["p95_boot_median"] = None
            ent["p95_ci"] = None
            ent["n_points_resid"] = 0
            enriched.append(ent)
            continue

        p95s = bootstrap_p95_from_array(arr, B, rng)
        if p95s.size == 0:
            ent["p95_boot_median"] = None
            ent["p95_ci"] = None
            ent["n_points_resid"] = int(n_points)
            enriched.append(ent)
            continue

        # stats
        try:
            low = float(np.nanpercentile(p95s, 2.5, method="linear"))
            high = float(np.nanpercentile(p95s, 97.5, method="linear"))
            med = float(np.nanmedian(p95s))
        except TypeError:
            # fallback
            low = float(np.nanpercentile(p95s, 2.5))
            high = float(np.nanpercentile(p95s, 97.5))
            med = float(np.nanmedian(p95s))

        ent["p95_boot_median"] = med
        ent["p95_ci"] = [low, high]
        ent["n_points_resid"] = int(n_points)
        ent["resid_file"] = str(resid_file)
        enriched.append(ent)
        _logger.info(
            "id=%d: p95_boot_median=%.6g  p95_ci=[%.6g, %.6g]  n=%d",
            id_,
            med,
            low,
            high,
            n_points,
        )

    # écriture du JSON de sortie
    out_obj = {
        "top_k": enriched,
        "meta": {
            "B": B,
            "seed": int(args.seed),
            "resid_dir": str(resid_dir),
            "created_at": datetime.utcnow().isoformat() + "Z",
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(out_obj, fh, indent=2, sort_keys=True, ensure_ascii=False)

    _logger.info("Écriture terminée -> %s", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
