#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chapitre 10 — Pipeline complet (génération & agrégation des données)
===================================================================

Ce pipeline orchestre, dans le bon ordre et avec traçabilité :
  1) Préflight (dossiers, dépendances, grille de référence)
  2) Génération Sobol des échantillons 8D (global)
  3) Évaluation des métriques canoniques |Δφ|_principal @ [20,300] Hz
  4) Évaluation des jalons f_peak pour le top-K courant
  5) Agrégation + score multi-objectif (p95 + λ·pénalité jalons)
  6) (Option) Raffinement global autour du top-K puis fusion
  7) Résumé de run & sorties manifestes

Ce qui est volontairement laissé à d’autres scripts (indépendants) :
  - La production des figures 10-01…10-06 (scripts zz-scripts/chapitre10/plot_*).
  - Des explorations très spécifiques (raffinement “boîte par boîte”, CMA-ES, etc.).

Exemples d’exécution
--------------------
# Run global simple (comme validé)
python zz-scripts/chapitre10/generer_donnees_chapitre10.py \
  --n 5000 --batch 256 --n-workers 8 --K 50 --lambda 0.2 \
  --ref-grid zz-data/chapitre9/09_phases_imrphenom.csv \
  --jalons   zz-data/chapitre9/09_jalons_comparaison.csv \
  --log-level INFO

# Même chose + raffinement global autour du top-K (ex. 10k points)
python zz-scripts/chapitre10/generer_donnees_chapitre10.py \
  --n 5000 --batch 256 --n-workers 8 --K 50 --lambda 0.2 \
  --ref-grid zz-data/chapitre9/09_phases_imrphenom.csv \
  --jalons   zz-data/chapitre9/09_jalons_comparaison.csv \
  --refine --refine-n 10000 --refine-shrink 3.0 \
  --log-level INFO

Notes
-----
- Si 10_mc_config.json est absent, le pipeline en **génère un template** minimal et continue.
- Le pipeline appelle ces scripts validés :
    • generer_echantillons_8d.py
    • eval_metrics_principal_20_300.py
    • eval_jalons_fpeak.py
    • aggreger_runs_mc.py
- Les fichiers sont produits dans zz-data/chapitre10/ ; les journaux (logs) sont sur stdout/err.
"""

from __future__ import annotations
import argparse
import sys
import os
import json
import time
import logging
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------
# 0) Emplacements et scripts appelés
# ---------------------------------------------------------------------
HERE = Path(__file__).resolve().parent  # .../zz-scripts/chapter10
ROOT = HERE.parent.parent  # racine du dépôt
DDIR = ROOT / "zz-data" / "chapter10"
FDIR = ROOT / "zz-figures" / "chapter10"
REF_CH9 = ROOT / "zz-data" / "chapter09"
CACHE_REF = DDIR / ".cache_ref"

SCRIPTS = {
    "samples": HERE / "gen_samples_8d.py",
    "metrics": HERE / "eval_metrics_20_300.py",
    "jalons": HERE / "eval_fpeak_milestones.py",
    "agg": HERE / "aggregate_mc_runs.py",
}

DEFAULTS = {
    "config": DDIR / "10_mc_config.json",
    "samples_csv": DDIR / "10_mc_samples.csv",
    "results_csv": DDIR / "10_mc_results.csv",
    "results_agg_csv": DDIR / "10_mc_results.agg.csv",
    "best_json": DDIR / "10_mc_best.json",
    "jalons_csv": DDIR / "10_mc_jalons_eval.csv",
    "manifest": DDIR / "10_mc_run_manifest.json",
    "summary": DDIR / "10_pipeline_summary.json",
    "ref_grid": REF_CH9 / "09_phases_imrphenom.csv",
    "jalons_ref": REF_CH9 / "09_jalons_comparaison.csv",
}


# ---------------------------------------------------------------------
# 1) Utilitaires génériques
# ---------------------------------------------------------------------
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def save_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, sort_keys=True)


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_cmd(cmd: list[str], log: logging.Logger, check=True):
    log.debug("CMD: %s", " ".join(str(c) for c in cmd))
    cp = subprocess.run([str(c) for c in cmd], stdout=sys.stdout, stderr=sys.stderr)
    if check and cp.returncode != 0:
        raise SystemExit(cp.returncode)
    return cp.returncode


def ensure_dirs(log: logging.Logger):
    for p in [DDIR, FDIR, CACHE_REF]:
        p.mkdir(parents=True, exist_ok=True)
        log.debug("ok dossier: %s", p)


def write_default_config_if_missing(cfg_path: Path, log: logging.Logger):
    if cfg_path.exists():
        log.debug("Config déjà présente : %s", cfg_path)
        return
    # Template conforme aux décisions figées (bornes & constantes)
    template = {
        "model": "default",
        "priors": {
            "m1": {"min": 5.0, "max": 80.0, "dist": "uniform"},
            "m2": {"min": 5.0, "max": 80.0, "dist": "uniform"},
            "q0star": {"min": -0.3, "max": 0.3, "dist": "uniform"},
            "alpha": {"min": -1.0, "max": 1.0, "dist": "uniform"},
        },
        "nuisance": {"phi0": 0.0, "tc": 0.0, "dist": 1000.0, "incl": 0.0},
        "sobol": {"scramble": True, "seed": 12345},
    }
    save_json(template, cfg_path)
    log.info("Config absente → TEMPLATE créé : %s", cfg_path)


def bref(path: Path) -> str:
    """Chemin abrégé pour affichage log."""
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


# ---------------------------------------------------------------------
# 2) Étapes du pipeline (fonctions)
# ---------------------------------------------------------------------
def etape_1_preflight(args, log: logging.Logger):
    log.info("1) Préflight & initialisation")
    ensure_dirs(log)
    # Grille de référence
    ref_grid = Path(args.ref_grid or DEFAULTS["ref_grid"])
    if not ref_grid.exists():
        raise FileNotFoundError(f"Grille de référence introuvable : {ref_grid}")
    # Jalons (si non désactivé)
    if not args.skip_jalons:
        jal = Path(args.jalons or DEFAULTS["jalons_ref"])
        if not jal.exists():
            raise FileNotFoundError(f"Fichier jalons introuvable : {jal}")
    # Config
    cfg = Path(args.config or DEFAULTS["config"])
    write_default_config_if_missing(cfg, log)
    # Sanity minimal : scripts présents
    for k, sp in SCRIPTS.items():
        if not sp.exists():
            raise FileNotFoundError(f"Script manquant ({k}) : {sp}")
    log.info(
        "   ✓ Dossiers/entrées OK | grille=%s | jalons=%s | config=%s",
        bref(ref_grid),
        bref(Path(args.jalons or DEFAULTS["jalons_ref"])),
        bref(cfg),
    )


def etape_2_samples_global(args, log: logging.Logger):
    if args.skip_samples:
        log.info("2) Échantillons (global) — SKIP demandé")
        return Path(args.samples_csv or DEFAULTS["samples_csv"])
    log.info("2) Génération des échantillons (global Sobol)")
    cmd = [
        sys.executable,
        str(SCRIPTS["samples"]),
        "--config",
        str(args.config or DEFAULTS["config"]),
        "--n",
        str(args.n),
        "--scheme",
        "sobol",
        "--scramble",
        "on" if args.scramble else "off",
        "--seed",
        str(args.seed),
        "--out",
        str(args.samples_csv or DEFAULTS["samples_csv"]),
    ]
    if args.overwrite:
        cmd.append("--overwrite")
    if args.sobol_offset is not None:
        cmd += ["--sobol-offset", str(args.sobol_offset)]
    run_cmd(cmd, log)
    out = Path(args.samples_csv or DEFAULTS["samples_csv"])
    log.info("   ✓ Échantillons écrits : %s", bref(out))
    return out


def etape_3_metrics(args, log: logging.Logger, samples_csv: Path):
    if args.skip_metrics:
        log.info("3) Métriques canoniques — SKIP demandé")
        return (
            Path(args.results_csv or DEFAULTS["results_csv"]),
            Path(args.best_json or DEFAULTS["best_json"]),
        )
    log.info("3) Évaluation des métriques canoniques |Δφ|_principal @ [20,300] Hz")
    cmd = [
        sys.executable,
        str(SCRIPTS["metrics"]),
        "--samples",
        str(samples_csv),
        "--ref-grid",
        str(args.ref_grid or DEFAULTS["ref_grid"]),
        "--out-results",
        str(args.results_csv or DEFAULTS["results_csv"]),
        "--out-best",
        str(args.best_json or DEFAULTS["best_json"]),
        "--batch",
        str(args.batch),
        "--n-workers",
        str(args.n_workers),
        "--K",
        str(args.K),
        "--log-level",
        args.log_level,
    ]
    if args.overwrite:
        cmd.append("--overwrite")
    run_cmd(cmd, log)
    res = Path(args.results_csv or DEFAULTS["results_csv"])
    best = Path(args.best_json or DEFAULTS["best_json"])
    log.info("   ✓ Résultats : %s | Top-K provisoire : %s", bref(res), bref(best))
    return (res, best)


def etape_4_jalons(args, log: logging.Logger, best_json: Path):
    if args.skip_jalons:
        log.info("4) Jalons f_peak — SKIP demandé")
        return None
    log.info("4) Évaluation jalons f_peak pour le top-K")
    cmd = [
        sys.executable,
        str(SCRIPTS["jalons"]),
        "--jalons",
        str(args.jalons or DEFAULTS["jalons_ref"]),
        "--ref-grid",
        str(args.ref_grid or DEFAULTS["ref_grid"]),
        "--samples",
        str(args.samples_csv or DEFAULTS["samples_csv"]),
        "--best-json",
        str(best_json),
        "--out",
        str(args.jalons_out or DEFAULTS["jalons_csv"]),
        "--log-level",
        args.log_level,
    ]
    run_cmd(cmd, log)
    out = Path(args.jalons_out or DEFAULTS["jalons_csv"])
    log.info("   ✓ Évaluation jalons écrite : %s", bref(out))
    return out


def etape_5_agregat(
    args, log: logging.Logger, jalons_csv: Path | None, results_csv: Path
):
    if args.skip_aggregate:
        log.info("5) Agrégation & score — SKIP demandé")
        return (
            Path(args.results_agg_csv or DEFAULTS["results_agg_csv"]),
            Path(args.best_json or DEFAULTS["best_json"]),
        )
    log.info("5) Agrégation, scoring multi-objectif & top-K final")
    cmd = [
        sys.executable,
        str(SCRIPTS["agg"]),
        "--results",
        str(results_csv),
        "--out-results",
        str(args.results_agg_csv or DEFAULTS["results_agg_csv"]),
        "--out-best",
        str(args.best_json or DEFAULTS["best_json"]),
        "--K",
        str(args.K),
        "--lambda",
        str(args.lmbda),
        "--log-level",
        args.log_level,
    ]
    if (not args.skip_jalons) and jalons_csv is not None and jalons_csv.exists():
        cmd += ["--jalons", str(jalons_csv)]
    if args.overwrite:
        cmd.append("--overwrite")
    run_cmd(cmd, log)
    out_agg = Path(args.results_agg_csv or DEFAULTS["results_agg_csv"])
    best = Path(args.best_json or DEFAULTS["best_json"])
    log.info(
        "   ✓ Résultats agrégés : %s | Top-K final : %s", bref(out_agg), bref(best)
    )
    return (out_agg, best)


# ----------------------- Raffinement (option) ------------------------
def _charger_topk(best_json: Path) -> list[dict]:
    bj = load_json(best_json)
    return bj.get("top_k") or bj.get("topK") or []


def _calcul_boite_topk(topk: list[dict], shrink: float) -> dict:
    """
    Boîte englobante du top-K sur {m1,m2,q0star,alpha}, resserrée par facteur 'shrink'.
    Stratégie : on prend [min,max] sur le top-K, on recentre à la médiane, et
    on réduit la demi-largeur -> demi_largeur/shrink.
    """
    import numpy as np

    keys = ["m1", "m2", "q0star", "alpha"]
    out = {}
    for k in keys:
        vals = np.array([float(t[k]) for t in topk if k in t], dtype=float)
        vmin, vmax = float(vals.min()), float(vals.max())
        vmed = float(np.median(vals))
        half = (vmax - vmin) / 2.0
        half = half / max(shrink, 1.0)
        out[k] = {"min": vmed - half, "max": vmed + half}
    return out


def _ecrire_config_raffine(
    cfg_base: Path, cfg_out: Path, boite: dict, log: logging.Logger
):
    base = load_json(cfg_base)
    # Adapter les bornes uniquement sur les 4 paramètres libres
    for key in ["m1", "m2", "q0star", "alpha"]:
        if key in base.get("priors", {}):
            base["priors"][key]["min"] = float(boite[key]["min"])
            base["priors"][key]["max"] = float(boite[key]["max"])
    save_json(base, cfg_out)
    log.info("   ↪ Config de raffinement écrite : %s", bref(cfg_out))


def _assurer_ids_uniques(samples_path: Path, id_offset: int, log: logging.Logger):
    """
    Re-numérotation simple : id := id + id_offset (garantit unicité lors de fusions).
    """
    import pandas as pd

    df = pd.read_csv(samples_path)
    if "id" not in df.columns:
        raise RuntimeError("Le fichier d'échantillons n'a pas de colonne 'id'.")
    df["id"] = df["id"].astype(int) + int(id_offset)
    tmp = samples_path.with_suffix(".tmp.csv")
    df.to_csv(tmp, index=False, float_format="%.6f")
    os.replace(tmp, samples_path)
    log.info("   ↪ IDs décalés de +%d dans %s", id_offset, bref(samples_path))


def etape_6_raffinement(
    args,
    log: logging.Logger,
    best_json_final: Path,
    samples_global: Path,
    results_global: Path,
):
    if not args.refine:
        log.info("6) Raffinement global — SKIP (désactivé)")
        return None

    log.info("6) Raffinement global autour du top-K (boîte restreinte)")
    topk = _charger_topk(best_json_final)
    if not topk:
        log.warning("   ! Top-K vide : raffinement annulé.")
        return None

    # 6.1 Boîte englobante restreinte
    boite = _calcul_boite_topk(topk, args.refine_shrink)
    cfg_refine = DDIR / "10_mc_config.refine.json"
    _ecrire_config_raffine(
        Path(args.config or DEFAULTS["config"]), cfg_refine, boite, log
    )

    # 6.2 Génération des échantillons (raffiné)
    samples_ref = DDIR / "10_mc_samples.refine.csv"
    cmdS = [
        sys.executable,
        str(SCRIPTS["samples"]),
        "--config",
        str(cfg_refine),
        "--n",
        str(args.refine_n),
        "--scheme",
        "sobol",
        "--scramble",
        "on" if args.scramble else "off",
        "--seed",
        str(args.seed),
        "--out",
        str(samples_ref),
        "--overwrite",
    ]
    run_cmd(cmdS, log)

    # Décaler les ids pour unicité (à partir du max de l'existant)
    import pandas as pd

    dfG = pd.read_csv(samples_global, usecols=["id"])
    max_id = int(dfG["id"].max())
    _assurer_ids_uniques(samples_ref, id_offset=max_id, log=log)

    # 6.3 Évaluation des métriques (raffiné)
    results_ref = DDIR / "10_mc_results.refine.csv"
    best_ref = DDIR / "10_mc_best.refine.json"  # provisoire
    cmdM = [
        sys.executable,
        str(SCRIPTS["metrics"]),
        "--samples",
        str(samples_ref),
        "--ref-grid",
        str(args.ref_grid or DEFAULTS["ref_grid"]),
        "--out-results",
        str(results_ref),
        "--out-best",
        str(best_ref),
        "--batch",
        str(args.batch),
        "--n-workers",
        str(args.n_workers),
        "--K",
        str(args.K),
        "--log-level",
        args.log_level,
        "--overwrite",
    ]
    run_cmd(cmdM, log)

    # 6.4 Fusion des résultats global + raffiné (concat)
    dfR = pd.read_csv(results_global)
    dfR2 = pd.read_csv(results_ref)
    merged = DDIR / "10_mc_results.merge.csv"
    dfAll = pd.concat([dfR, dfR2], ignore_index=True)
    dfAll.to_csv(merged, index=False, float_format="%.6f")
    log.info("   ✓ Fusion résultats : %s (rows=%d)", bref(merged), len(dfAll))

    # 6.5 Jalons (top-K du merged, via agrégateur plus bas)
    # On laisse l'agrégateur recalc le top-K final et réutiliser le même fichier jalons.
    return merged


def etape_7_resume(
    args, log: logging.Logger, results_final_csv: Path, best_json_final: Path
):
    import pandas as pd
    import numpy as np

    log.info("7) Résumé & manifeste pipeline")
    df = pd.read_csv(results_final_csv)
    n_total = int(len(df))
    n_ok = int((df["status"] == "ok").sum()) if "status" in df.columns else n_total
    n_failed = n_total - n_ok
    p95 = df["p95_20_300"].dropna().values if "p95_20_300" in df.columns else []
    resume = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "inputs": {
            "ref_grid": bref(Path(args.ref_grid or DEFAULTS["ref_grid"])),
            "jalons": bref(Path(args.jalons or DEFAULTS["jalons_ref"]))
            if not args.skip_jalons
            else None,
            "config": bref(Path(args.config or DEFAULTS["config"])),
        },
        "results": {
            "csv_final": bref(results_final_csv),
            "best_json": bref(best_json_final),
            "n_total": n_total,
            "n_ok": n_ok,
            "n_failed": n_failed,
            "p95_min": float(np.min(p95)) if len(p95) else None,
            "p95_median": float(np.median(p95)) if len(p95) else None,
            "p95_max": float(np.max(p95)) if len(p95) else None,
        },
    }
    save_json(resume, Path(args.summary or DEFAULTS["summary"]))
    log.info("   ✓ Résumé écrit : %s", bref(Path(args.summary or DEFAULTS["summary"])))


# ---------------------------------------------------------------------
# 3) Argumentaire CLI
# ---------------------------------------------------------------------
def build_parser():
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="Chapitre 10 — Pipeline complet de génération/agrégation des données.",
    )
    # Fichiers d’E/S principaux
    p.add_argument("--config", default=str(DEFAULTS["config"]))
    p.add_argument("--ref-grid", default=str(DEFAULTS["ref_grid"]))
    p.add_argument("--jalons", default=str(DEFAULTS["jalons_ref"]))
    p.add_argument("--samples-csv", default=str(DEFAULTS["samples_csv"]))
    p.add_argument("--results-csv", default=str(DEFAULTS["results_csv"]))
    p.add_argument("--results-agg-csv", default=str(DEFAULTS["results_agg_csv"]))
    p.add_argument("--best-json", default=str(DEFAULTS["best_json"]))
    p.add_argument("--jalons-out", default=str(DEFAULTS["jalons_csv"]))
    p.add_argument("--summary", default=str(DEFAULTS["summary"]))

    # Contrôles généraux
    p.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    p.add_argument(
        "--overwrite", action="store_true", help="autoriser l'écrasement des sorties"
    )
    p.add_argument("--skip-samples", action="store_true")
    p.add_argument("--skip-metrics", action="store_true")
    p.add_argument("--skip-jalons", action="store_true")
    p.add_argument("--skip-aggregate", action="store_true")

    # Paramètres échantillons (global)
    p.add_argument("--n", type=int, default=5000)
    p.add_argument("--scramble", default=True, action=argparse.BooleanOptionalAction)
    p.add_argument("--seed", type=int, default=12345)
    p.add_argument(
        "--sobol-offset",
        type=int,
        default=None,
        help="reprise/append de la séquence sobol",
    )

    # Paramètres métriques / agrégation
    p.add_argument("--batch", type=int, default=256)
    p.add_argument("--n-workers", type=int, default=8)
    p.add_argument("--K", type=int, default=50)
    p.add_argument("--lambda", dest="lmbda", type=float, default=0.2)

    # Raffinement global (option)
    p.add_argument(
        "--refine",
        action="store_true",
        help="activer un second lot raffiné (global bbox du top-K)",
    )
    p.add_argument("--refine-n", type=int, default=10000)
    p.add_argument(
        "--refine-shrink",
        type=float,
        default=3.0,
        help="facteur de rétrécissement par dimension (>1)",
    )

    return p


# ---------------------------------------------------------------------
# 4) Main
# ---------------------------------------------------------------------
def main(argv=None):
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    log = logging.getLogger("mcgt.pipeline10")

    t0 = time.time()
    try:
        # 1) Préflight
        etape_1_preflight(args, log)

        # 2) Samples (global)
        samples_csv = etape_2_samples_global(args, log)

        # 3) Metrics (global)
        results_csv, best_json = etape_3_metrics(args, log, samples_csv)

        # 4) Jalons (top-K courant)
        jalons_csv = etape_4_jalons(args, log, best_json)

        # 5) Agrégation (global)
        results_agg_csv, best_json_final = etape_5_agregat(
            args, log, jalons_csv, results_csv
        )

        # 6) Raffinement (option) puis re-agrégation sur la fusion
        merged_csv = etape_6_raffinement(
            args, log, best_json_final, samples_csv, results_csv
        )
        if merged_csv is not None:
            # On relance une agrégation sur la fusion (avec les mêmes jalons)
            results_agg_csv, best_json_final = etape_5_agregat(
                args, log, jalons_csv, merged_csv
            )

        # 7) Résumé
        etape_7_resume(args, log, results_agg_csv, best_json_final)

        dt = time.time() - t0
        log.info("✓ Pipeline terminé en %.2f s", dt)
        return 0

    except SystemExit as e:
        # sous-processus a retourné une erreur -> propager code
        return e.code
    except Exception as e:
        log.exception("Échec pipeline: %s", e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
