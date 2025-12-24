#!/usr/bin/env python3
"""
zz-scripts/chapter09/check_metrics_consistency.py

Vérifications QC rapides pour les résultats MC (Chapter 10).
- Vérifie tailles (n_rows) attendues dans le manifeste
- Vérifie n_ok / n_failed
- Recalcule quelques statistiques clés sur p95_20_300 et les compare (si valeurs de référence présentes)
- Vérifie les hashes sha256 listés dans le manifeste (si fournis)
- Sortie: code 0 si tout OK, 2 si divergences détectées.

Usage:
  python zz-scripts/chapter09/check_metrics_consistency.py \
      --results zz-data/chapter10/10_mc_results.agg.csv \
      --manifest zz-data/chapter10/10_mc_run_manifest.json \
      --rtol 1e-6 --atol 1e-12
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import pathlib
import sys

import numpy as np
import pandas as pd

from zz_tools import common_io as ci

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("check_metrics_consistency")


def sha256_of_file(path: pathlib.Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compare_close(a, b, rtol=1e-6, atol=1e-12) -> bool:
    try:
        return bool(np.allclose(a, b, rtol=rtol, atol=atol))
    except Exception:
        return False


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="check_metrics_consistency.py",
        description="QC quick-check des métriques MC",
    )
    p.add_argument("--results", required=True, help="CSV résultats (agrégé) à vérifier")
    p.add_argument("--manifest", required=True, help="Manifest JSON du run")
    p.add_argument("--rtol", type=float, default=1e-6)
    p.add_argument("--atol", type=float, default=1e-12)
    args = p.parse_args(argv)

    results_p = pathlib.Path(args.results)
    manifest_p = pathlib.Path(args.manifest)

    if not results_p.exists():
        logger.error("Fichier results introuvable: %s", results_p)
        return 2
    if not manifest_p.exists():
        logger.error("Manifest introuvable: %s", manifest_p)
        return 2

    logger.info("Chargement results: %s", results_p)
    df = pd.read_csv(results_p)
    df = ci.ensure_fig02_cols(df)

    # normalisation noms colonnes courants (tolérance)
    _df_cols = {c: c for c in df.columns}
    # required metrics expected
    required_cols = [
        "id",
        "p95_20_300",
        "mean_20_300",
        "max_20_300",
        "n_20_300",
        "status",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(
            "Colonnes essentielles manquantes dans %s : %s", results_p, missing
        )
        # c'est critique : on ne peut pas poursuivre certaines vérifs
        return 2

    n_total = len(df)
    n_ok = int((df["status"] == "ok").sum())
    n_failed = int(n_total - n_ok)
    logger.info("Results : n_total=%d  n_ok=%d  n_failed=%d", n_total, n_ok, n_failed)

    # statistiques p95
    p95_min = float(np.nanmin(df["p95_20_300"]))
    p95_mean = float(np.nanmean(df["p95_20_300"]))
    try:
        p95_p95 = float(np.nanpercentile(df["p95_20_300"], 95, method="linear"))
    except TypeError:
        p95_p95 = float(np.nanpercentile(df["p95_20_300"], 95))
    p95_max = float(np.nanmax(df["p95_20_300"]))

    logger.info(
        "p95_20_300 : min=%.6f mean=%.6f p95=%.6f max=%.6f",
        p95_min,
        p95_mean,
        p95_p95,
        p95_max,
    )

    # lecture manifeste
    logger.info("Chargement manifeste: %s", manifest_p)
    manifest = json.loads(manifest_p.read_text())

    # Checks basiques sur tailles si présentes
    sizes = manifest.get("sizes", {})
    errors = []

    if "n_rows_results" in sizes:
        exp = int(sizes["n_rows_results"])
        if exp != n_total:
            errors.append(
                f"Mismatch n_rows_results: manifest={exp} vs detected={n_total}"
            )
        else:
            logger.info("n_rows_results OK: %d", n_total)

    if "n_rows_ok" in sizes:
        exp_ok = int(sizes["n_rows_ok"])
        if exp_ok != n_ok:
            errors.append(f"Mismatch n_rows_ok: manifest={exp_ok} vs detected={n_ok}")
        else:
            logger.info("n_rows_ok OK: %d", n_ok)

    # Vérification des hashes si fournis
    fh = manifest.get("file_hashes", {})
    if isinstance(fh, dict) and fh:
        for key, info in fh.items():
            path = info.get("path")
            expected = info.get("sha256")
            if not path:
                continue
            pth = pathlib.Path(path)
            actual = sha256_of_file(pth)
            if expected is None:
                logger.warning(
                    "Pas de sha256 attendu pour %s (clé %s) dans manifest", path, key
                )
                continue
            if actual is None:
                errors.append(f"Fichier absent pour hash check: {path}")
            elif actual != expected:
                errors.append(
                    f"Hash mismatch pour {path}: manifest={expected} vs actual={actual}"
                )
            else:
                logger.info("Hash OK: %s", path)

    # Optionnel : si le manifeste contient des métriques de référence, les comparer
    ref_metrics = (
        manifest.get("metrics_reference") or manifest.get("metrics_active") or {}
    )
    # exemple : p95_abs_20_300 dans anciens manifests
    if "p95_abs_20_300" in ref_metrics:
        ref_p95 = float(ref_metrics["p95_abs_20_300"])
        if not compare_close(ref_p95, p95_p95, rtol=args.rtol, atol=args.atol):
            errors.append(
                f"p95_abs_20_300 mismatch: manifest={ref_p95} vs recomputed_p95={p95_p95}"
            )

    # verdict
    if errors:
        logger.error("QC échoué — problèmes détectés:")
        for e in errors:
            logger.error(" - %s", e)
        return 2

    logger.info("QC passé — aucune divergence critique détectée.")
    return 0


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
