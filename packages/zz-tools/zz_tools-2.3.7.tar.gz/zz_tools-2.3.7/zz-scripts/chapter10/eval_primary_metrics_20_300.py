#!/usr/bin/env python3
"""
eval_metrics_principal_20_300.py
================================

Évalue les métriques canoniques |Δφ|_principal sur la fenêtre 20-300 Hz
pour un catalogue d'échantillons 8D.

Usage (exemple) :
python zz-scripts/chapter10/eval_metrics_principal_20_300.py \
  --samples zz-data/chapter10/10_mc_samples.csv \
  --ref-grid zz-data/chapter09/09_phases_imrphenom.csv \
  --out-results zz-data/chapter10/10_mc_results.csv \
  --out-best    zz-data/chapter10/10_mc_best.json \
  --batch 256 --n-workers 8 --K 50 --overwrite --log-level INFO

Sorties :
 - CSV résultats : id,θ,k,mean_20_300,p95_20_300,max_20_300,n_20_300,status,error_code,wall_time_s,worker_id,model,score
 - JSON top-K : top-K trié par 'score' (ici = p95 par défaut)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from typing import Any

import numpy as np
import pandas as pd

from joblib import Parallel, delayed

# Importer les backends locaux (doivent exister dans le dépôt)
try:
    from mcgt.backends.ref_phase import compute_phi_ref, ref_cache_info
except Exception:
    compute_phi_ref = None
    ref_cache_info = None

try:
    from mcgt.phase import phi_mcgt
except Exception:
    phi_mcgt = None

# ---------------------------------------------------------------------
# Constantes (cohérentes avec le GUIDE Chap.9/10)
# ---------------------------------------------------------------------
WINDOW_DEFAULT = (20.0, 300.0)
PCTL_METHOD = "linear"  # np.nanpercentile method
EPS_PLOT = 1e-12

# Codes d'erreur uniformes
ERR_CODES = {
    "FORWARD_MISSING": "PHI_MCGT_IMPORT_FAIL",
    "REF_MISSING": "REF_BACKEND_MISSING",
    "GRID_MISMATCH": "GRID_MISMATCH",
    "MODEL_DIVERGED": "MODEL_DIVERGED",
    "NAN_IN_OUTPUT": "NAN_IN_OUTPUT",
    "NAN_IN_WINDOW": "NAN_IN_WINDOW",
    "OUT_OF_DOMAIN": "OUT_OF_DOMAIN",
    "TIMEOUT": "TIMEOUT",
    "UNKNOWN": "UNKNOWN",
}


# ---------------------------------------------------------------------
# Utils IO safe (atomique)
# ---------------------------------------------------------------------
def safe_write_csv(
    df: pd.DataFrame, path: str, overwrite: bool = False, **kwargs
) -> None:
    if os.path.exists(path) and not overwrite:
        raise SystemExit(
            f"Refuse d'écraser {path} — relancer avec --overwrite ou supprimer le fichier."
        )
    tmp = path + ".part"
    df.to_csv(tmp, index=False, float_format="%.6f", **kwargs)
    os.replace(tmp, path)


def safe_write_json(obj: Any, path: str, overwrite: bool = False) -> None:
    if os.path.exists(path) and not overwrite:
        raise SystemExit(
            f"Refuse d'écraser {path} — relancer avec --overwrite ou supprimer le fichier."
        )
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


# ---------------------------------------------------------------------
# Calculs principaux
# ---------------------------------------------------------------------
def compute_rebranch_k(
    phi_mcgt: np.ndarray,
    phi_ref: np.ndarray,
    f_hz: np.ndarray,
    window: tuple[float, float] = WINDOW_DEFAULT,
) -> int:
    """Calcul de k via median((φ_mcgt − φ_ref)/2π) sur la fenêtre window."""
    fmin, fmax = window
    mask = (
        (f_hz >= fmin) & (f_hz <= fmax) & np.isfinite(phi_mcgt) & np.isfinite(phi_ref)
    )
    if not np.any(mask):
        raise ValueError("NAN_IN_WINDOW")
    cycles = (phi_mcgt[mask] - phi_ref[mask]) / (2.0 * np.pi)
    med = float(np.nanmedian(cycles))
    k = int(np.round(med))  # ties-to-even (numpy default)
    return k


def delta_phi_principal(
    phi_mcgt: np.ndarray, phi_ref: np.ndarray, k: int
) -> np.ndarray:
    """Retourne Δφ_principal = ((φ_mcgt - k·2π) - φ_ref + π) mod 2π - π."""
    raw = (phi_mcgt - k * 2.0 * np.pi) - phi_ref
    # opération modulo sur floats
    wrapped = (raw + np.pi) % (2.0 * np.pi) - np.pi
    return wrapped


def metrics_from_absdphi(absdphi: np.ndarray) -> dict[str, Any]:
    """Calcule mean, p95, max, n_points"""
    arr = np.asarray(absdphi, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return {"mean": np.nan, "p95": np.nan, "max": np.nan, "n": 0}
    mean = float(np.nanmean(finite))
    p95 = float(np.nanpercentile(finite, 95, method=PCTL_METHOD))
    mx = float(np.nanmax(finite))
    n = int(finite.size)
    return {"mean": mean, "p95": p95, "max": mx, "n": n}


# ---------------------------------------------------------------------
# Évaluation d'un sample (unité de travail)
# ---------------------------------------------------------------------
def evaluate_sample(
    row: pd.Series, f_hz: np.ndarray, window: tuple[float, float]
) -> dict[str, Any]:
    """Évalue les métriques pour un sample (pandas Series). Retourne dict de sortie."""
    t0 = time.time()
    result = {}
    sid = int(row["id"])
    result.update(
        {
            "id": sid,
            "m1": float(row["m1"]),
            "m2": float(row["m2"]),
            "q0star": float(row["q0star"]),
            "alpha": float(row["alpha"]),
            "phi0": float(row.get("phi0", 0.0)),
            "tc": float(row.get("tc", 0.0)),
            "dist": float(row.get("dist", 1000.0)),
            "incl": float(row.get("incl", 0.0)),
            "seed": int(row.get("seed", 0)),
        }
    )
    try:
        # 1) calculer phi_ref via backend (peut lever)
        if compute_phi_ref is None:
            raise RuntimeError(ERR_CODES["REF_MISSING"])
        phi_ref = compute_phi_ref(f_hz, float(row["m1"]), float(row["m2"]))
        if phi_ref.shape != f_hz.shape:
            raise RuntimeError(ERR_CODES["GRID_MISMATCH"])

        # 2) construire theta et appeler forward
        if phi_mcgt is None:
            raise RuntimeError(ERR_CODES["FORWARD_MISSING"])
        theta = {
            "m1": float(row["m1"]),
            "m2": float(row["m2"]),
            "q0star": float(row["q0star"]),
            "alpha": float(row["alpha"]),
            "phi0": float(row.get("phi0", 0.0)),
            "tc": float(row.get("tc", 0.0)),
            "dist": float(row.get("dist", 1000.0)),
            "incl": float(row.get("incl", 0.0)),
        }
        phi_m = phi_mcgt(f_hz, theta, model=row.get("model", "default"))
        if phi_m.shape != f_hz.shape:
            raise RuntimeError(ERR_CODES["GRID_MISMATCH"])

        # 3) compute k on WINDOW
        k = compute_rebranch_k(phi_m, phi_ref, f_hz, window=window)

        # 4) delta principal, abs and metrics
        dphi = delta_phi_principal(phi_m, phi_ref, k)
        absd = np.abs(dphi)

        # metrics on window
        mask = (f_hz >= window[0]) & (f_hz <= window[1]) & np.isfinite(absd)
        absd_win = absd[mask]
        if absd_win.size == 0:
            raise ValueError("NAN_IN_WINDOW")
        met = metrics_from_absdphi(absd_win)

        # fill result
        result.update(
            {
                "k": int(k),
                "mean_20_300": met["mean"],
                "p95_20_300": met["p95"],
                "max_20_300": met["max"],
                "n_20_300": int(met["n"]),
                "status": "ok",
                "error_code": "",
                "wall_time_s": float(time.time() - t0),
                "model": row.get("model", "default"),
                # score = p95 par défaut (réécrit après si jalons pénalisés)
                "score": float(met["p95"]),
            }
        )
        return result

    except ValueError as ve:
        msg = str(ve)
        code = ERR_CODES.get(msg, ERR_CODES["UNKNOWN"])
        result.update(
            {
                "status": "failed",
                "error_code": code,
                "wall_time_s": float(time.time() - t0),
                "score": float("nan"),
            }
        )
        logging.debug("Sample %s failed ValueError: %s", sid, msg)
        return result
    except RuntimeError as re:
        msg = str(re)
        # si runtime vient d'un code interne string comme "REF_BACKEND_MISSING"
        code = msg if msg in ERR_CODES.values() else ERR_CODES["UNKNOWN"]
        result.update(
            {
                "status": "failed",
                "error_code": code,
                "wall_time_s": float(time.time() - t0),
                "score": float("nan"),
            }
        )
        logging.debug("Sample %s failed RuntimeError: %s", sid, msg)
        return result
    except Exception:
        logging.exception("Erreur inattendue pour sample %s", sid)
        result.update(
            {
                "status": "failed",
                "error_code": ERR_CODES["UNKNOWN"],
                "wall_time_s": float(time.time() - t0),
                "score": float("nan"),
            }
        )
        return result


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Évaluer métriques |Δφ|_principal (20-300 Hz) pour un catalogue d'échantillons."
    )
    p.add_argument(
        "--samples", required=True, help="CSV samples (id,m1,m2,q0star,alpha,...)"
    )
    p.add_argument(
        "--ref-grid",
        required=True,
        help="CSV grille de référence (f_Hz [, phi_ref]) — nous utilisons f_Hz pour calculer phi_ref via backend",
    )
    p.add_argument(
        "--out-results",
        default="zz-data/chapter10/10_mc_results.csv",
        help="CSV résultats (sortie)",
    )
    p.add_argument(
        "--out-best",
        default="zz-data/chapter10/10_mc_best.json",
        help="JSON top-K (sortie)",
    )
    p.add_argument(
        "--batch", type=int, default=256, help="taille de batch pour logging"
    )
    p.add_argument("--n-workers", type=int, default=8, help="n_workers joblib")
    p.add_argument("--K", type=int, default=50, help="Top-K à sauver dans out-best")
    p.add_argument(
        "--n-test",
        type=int,
        default=None,
        help="mode test: n premiers échantillons seulement",
    )
    p.add_argument(
        "--jalons",
        default=None,
        help="(optionnel) fichier jalons — non utilisé ici, penalty via aggregate",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Autorise l'écrasement des fichiers de sortie",
    )
    p.add_argument("--log-level", default="INFO", help="Niveau de log")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logging.info("Lancement eval_metrics_principal_20_300.py")

    # checks imports
    if compute_phi_ref is None:
        logging.error(
            "Backend compute_phi_ref introuvable. Assurez-vous que mcgt.backends.ref_phase module est disponible."
        )
    if phi_mcgt is None:
        logging.error(
            "Forward phi_mcgt introuvable. Assurez-vous que mcgt.phase.phi_mcgt est importable."
        )

    # charger grille f_Hz
    df_ref = pd.read_csv(args.ref_grid)
    if "f_Hz" not in df_ref.columns:
        raise SystemExit(
            f"Fichier ref-grid {args.ref_grid} doit contenir une colonne 'f_Hz'."
        )
    f_hz = np.asarray(df_ref["f_Hz"].values, dtype=float)
    logging.info(
        "Grille de référence : %d pts (%.3f..%.3f Hz)",
        f_hz.size,
        float(f_hz.min()),
        float(f_hz.max()),
    )

    # charger samples
    samples = pd.read_csv(args.samples)
    if args.n_test:
        samples = samples.head(args.n_test)
    n_samples = len(samples)
    logging.info("Nombre d'échantillons à évaluer : %d", n_samples)

    # prepare parallel evaluation
    window = WINDOW_DEFAULT
    _work = []
    # joblib Parallel with chunksize automatic
    logging.info(
        "Démarrage évaluation en parallèle : batch=%d n_workers=%d",
        args.batch,
        args.n_workers,
    )
    try:
        results = Parallel(n_jobs=args.n_workers, backend="loky")(
            delayed(evaluate_sample)(row, f_hz, window) for _, row in samples.iterrows()
        )
    except KeyboardInterrupt:
        logging.error("Interruption clavier reçue ; arrêt.")
        raise

    # construire DataFrame résultats
    df_out = pd.DataFrame(results)
    # colonne ordering
    cols = [
        "id",
        "m1",
        "m2",
        "q0star",
        "alpha",
        "phi0",
        "tc",
        "dist",
        "incl",
        "k",
        "mean_20_300",
        "p95_20_300",
        "max_20_300",
        "n_20_300",
        "status",
        "error_code",
        "wall_time_s",
        "model",
        "score",
    ]
    # some fields may be missing if many failed; ensure they exist
    for c in cols:
        if c not in df_out.columns:
            df_out[c] = np.nan
    df_out = df_out[cols]

    # safe write CSV
    safe_write_csv(df_out, args.out_results, overwrite=args.overwrite)
    logging.info(
        "Écriture des résultats (%d lignes) -> %s", len(df_out), args.out_results
    )

    # top-K (tri par score ascendant : petite p95 = meilleur)
    df_ok = df_out[df_out["status"] == "ok"].copy()
    if df_ok.shape[0] == 0:
        topk = []
        logging.warning("Aucun sample valide (status==ok). Pas de top-K.")
    else:
        df_ok = df_ok.sort_values(
            ["score", "p95_20_300", "mean_20_300", "max_20_300", "id"]
        )
        top = df_ok.head(args.K)
        topk = top.to_dict(orient="records")

    meta = {
        "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "n_total": int(n_samples),
        "n_ok": int((df_out["status"] == "ok").sum()),
        "n_failed": int((df_out["status"] != "ok").sum()),
        "pctl_method": PCTL_METHOD,
        "window": list(window),
        "forward_backend": "phi_mcgt (direct)" if phi_mcgt is not None else None,
        "ref_backend": "compute_phi_ref" if compute_phi_ref is not None else None,
    }
    out_best = {"meta": meta, "top_k": topk}
    safe_write_json(out_best, args.out_best, overwrite=args.overwrite)
    logging.info("Écriture top-K (%d) -> %s", len(topk), args.out_best)

    logging.info("Terminé.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
