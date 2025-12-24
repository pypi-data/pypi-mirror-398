#!/usr/bin/env python3
"""
Chapitre 9 — Pipeline principal : accord homogène 20–300 Hz
-----------------------------------------------------------
- Génère/charge la référence φ_ref (IMRPhenomD via LALSuite si possible, sinon fallback script)
- Calcule la phase MCGT (solveur mcgt.phase)
- Calage global WLS (φ0 / t_c) sur fenêtre configurable (par défaut 20–300 Hz)
- Resserre automatiquement la fenêtre (par défaut 30–250 Hz) si p95(|Δφ|) en 20–300 dépasse un seuil
- Exporte:
  * 09_phases_imrphenom.csv
  * 09_phases_mcgt.csv (variante ACTIVE + raw + cal)
  * 09_phase_diff.csv (Δφ actif + variantes)
  * 09_comparison_milestones.csv (si jalons présents)
  * 09_fisher_scan2D.csv (optionnel)
  * 09_metrics_phase.json (métriques + bloc calibration détaillé)

Conventions:
- Les phases sont en radians, unwrap (continues), sans réduction mod 2π.
- La "variante active" reflète la politique de calage (calibrated si --calibrate≠off, sinon raw).
- Les métriques par défaut sont calculées sur 20–300 Hz.
"""

from __future__ import annotations


# === MCGT Hotfix: robust defaults when cfg has None/"" ===
def _mcgt_safe_float(x, default):
    try:
        if x is None or (isinstance(x, str) and x.strip() == ""):
            return float(default)
        return float(x)
    except Exception:
        return float(default)


import argparse
import configparser
import json
import logging
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

# ----- Project path & MCGT solveur import -----
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# mcgt.phase is expected to provide PhaseParams, build_loglin_grid, solve_mcgt
try:
    from mcgt.phase import PhaseParams, build_loglin_grid, solve_mcgt  # type: ignore
except Exception as e:
    raise ImportError("Impossible d'importer mcgt.phase: %s" % e)

# ----- Paths -----
OUT_DIR = Path("zz-data/chapter09")
FIG_DIR = Path("zz-figures/chapter09")
REF_CSV = OUT_DIR / "09_phases_imrphenom.csv"
REF_META = OUT_DIR / "09_phases_imrphenom.meta.json"
JALONS_CSV = OUT_DIR / "09_comparison_milestones.csv"


# -----------------------
# Utilities
# -----------------------
def setup_logger(level: str = "INFO") -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("chapitre9.pipeline")


def git_hash() -> str | None:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT)
            .decode()
            .strip()
        )
    except Exception:
        return None


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)


def load_ini(path: Path | None) -> dict:
    cfg: dict = {}
    if path and path.exists():
        parser = configparser.ConfigParser(
            inline_comment_prefixes=("#", ";"), interpolation=None
        )
        parser.read(path)
        if "scan" in parser:
            s = parser["scan"]

            def fget(key: str, default: float) -> float:
                try:
                    return s.getfloat(key)
                except Exception:
                    return default

            cfg = {
                "fmin": fget("fmin", 20.0),
                "fmax": fget("fmax", 300.0),
                "dlog": fget("dlog", 0.01),
                "m1": fget("m1", 30.0),
                "m2": fget("m2", 30.0),
                "q0star": fget("q0star", 0.20),
                "alpha": fget("alpha", 1.00),
                "phi0": fget("phi0", 0.0),
                "tc": fget("tc", 0.0),
                "tol": fget("tol", 1e-8),
            }
    return cfg


def p95(arr: np.ndarray) -> float:
    a = np.asarray(arr, float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return float("nan")
    return float(np.percentile(a, 95.0))


def finite_ratio(arr: np.ndarray) -> float:
    arr = np.asarray(arr, float)
    if arr.size == 0:
        return 0.0
    return float(np.mean(np.isfinite(arr)))


def clamp_min_frequencies(f: np.ndarray, fmin: float) -> np.ndarray:
    f = np.asarray(f, float).copy()
    f[f < fmin] = fmin
    return f


# -----------------------
# Reference generation via LALSuite or fallback
# -----------------------
def _try_lalsuite_phi_ref(
    freqs: np.ndarray, logger: logging.Logger
) -> np.ndarray | None:
    try:
        import lal  # type: ignore
        import lalsimulation as lalsim  # type: ignore
    except Exception as e:
        logger.debug("LALSuite indisponible (%s).", e)
        return None

    try:
        f = np.asarray(freqs, float)
        if f.size < 2 or not np.all(np.isfinite(f)):
            logger.warning("Grille invalide pour LALSuite.")
            return None

        # build a frequency-domain waveform with sufficient df
        fmin = _mcgt_safe_float(np.nanmin(f), 20.0)
        fmax = _mcgt_safe_float(np.nanmax(f), 300.0)
        df_candidates = np.diff(np.unique(f[np.isfinite(f)]))
        df = (
            float(np.nanmin(df_candidates))
            if df_candidates.size
            else max(1.0, fmin * 1e-3)
        )
        if not np.isfinite(df) or df <= 0:
            df = max(1.0, fmin * 1e-3)

        # dummy physical params (phase shape dominated by masses)
        m1_kg = 30.0 * lal.MSUN_SI
        m2_kg = 30.0 * lal.MSUN_SI
        zero = 0.0
        dist = 1.0e6 * lal.PC_SI  # 1 Mpc arbitrary
        incl = 0.0
        phi0 = 0.0
        f_ref = 0.0
        dct = lal.CreateDict()

        hp, _ = lalsim.SimInspiralChooseFDWaveform(
            m1_kg,
            m2_kg,
            zero,
            zero,
            zero,
            zero,
            zero,
            zero,
            dist,
            incl,
            phi0,
            zero,
            zero,
            zero,
            df,
            fmin,
            fmax,
            f_ref,
            dct,
            lalsim.IMRPhenomD,
        )

        n = int(hp.data.length)
        f_uniform = float(hp.f0) + np.arange(n, dtype=float) * float(hp.deltaF)
        phi_uniform = np.unwrap(np.angle(hp.data.data))
        return np.interp(f, f_uniform, phi_uniform)
    except Exception as e:
        logger.warning("Échec LALSuite IMRPhenomD: %s", e)
        return None


def _try_external_script_for_ref(
    freqs: np.ndarray, logger: logging.Logger
) -> np.ndarray | None:
    script = PROJECT_ROOT / "zz-scripts" / "chapter09" / "extract_phenom_phase.py"
    if not script.exists():
        logger.debug("Fallback script introuvable: %s", script)
        return None
    try:
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if REF_CSV.exists():
            df = pd.read_csv(REF_CSV)
            if {"f_Hz", "phi_ref"}.issubset(df.columns):
                f = np.asarray(freqs, float)
                return np.interp(
                    f, df["f_Hz"].to_numpy(float), df["phi_ref"].to_numpy(float)
                )
        logger.debug(
            "extract_phenom_phase stdout: %s",
            proc.stdout.decode(errors="ignore")[:400],
        )
        logger.debug(
            "extract_phenom_phase stderr: %s",
            proc.stderr.decode(errors="ignore")[:400],
        )
    except Exception as e:
        logger.warning("Fallback script a échoué: %s", e)
    return None


def load_or_build_reference(
    freqs_cfg: np.ndarray, logger: logging.Logger, refresh: bool
) -> tuple[np.ndarray, np.ndarray, str]:
    """
    Charge ou (re)génère la référence. Retourne (f_ref, phi_ref, tag_source).
    """
    if refresh and REF_CSV.exists():
        try:
            REF_CSV.unlink()
        except Exception:
            logger.debug("Impossible de supprimer ancienne référence.")

    # Try existing file first
    if REF_CSV.exists():
        try:
            df = pd.read_csv(REF_CSV)
            if {"f_Hz", "phi_ref"}.issubset(df.columns):
                f_ref = df["f_Hz"].to_numpy(float)
                p_ref = df["phi_ref"].to_numpy(float)
                if finite_ratio(p_ref) >= 0.9 and np.all(np.diff(f_ref) > 0):
                    logger.info("Référence existante utilisée (%d pts).", f_ref.size)
                    return f_ref, p_ref, "file_existing"
            logger.warning("Référence existante invalide → régénération.")
        except Exception as e:
            logger.warning("Lecture référence existante échouée: %s", e)

    # Build from LALSuite (preferred) then fallback
    f = np.asarray(freqs_cfg, float)
    phi_ref = _try_lalsuite_phi_ref(f, logger)
    tag = "lalsuite" if phi_ref is not None else "fallback_script"
    if phi_ref is None:
        phi_ref = _try_external_script_for_ref(f, logger)

    if phi_ref is None:
        raise RuntimeError(
            "Impossible de générer φ_ref : installez LALSuite ou fournissez "
            + str(REF_CSV)
        )

    # Save reference
    try:
        pd.DataFrame({"f_Hz": f, "phi_ref": np.asarray(phi_ref, float)}).to_csv(
            REF_CSV, index=False
        )
        meta = {
            "source": tag,
            "n_points": int(len(f)),
            "grid": {
                "fmin_Hz": _mcgt_safe_float(np.nanmin(f), 20.0),
                "fmax_Hz": _mcgt_safe_float(np.nanmax(f), 300.0),
                "monotone": bool(np.all(np.diff(f) > 0)),
            },
            "repro": {
                "git_hash": git_hash(),
                "numpy": np.__version__,
                "pandas": pd.__version__,
            },
        }
        try:
            import lalsimulation as _ls  # type: ignore

            meta["repro"]["lalsuite"] = getattr(_ls, "__version__", "present")
        except Exception:
            meta["repro"]["lalsuite"] = None

        REF_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        logger.info("Référence écrite → %s (source=%s)", REF_CSV, tag)
    except Exception as e:
        logger.warning("Impossible d'écrire REF CSV/meta: %s", e)

    return f, np.asarray(phi_ref, float), tag


# -----------------------
# Fit alignment WLS
# -----------------------
def fit_alignment_phi0_tc(
    f: np.ndarray,
    phi_ref: np.ndarray,
    phi_mcgt: np.ndarray,
    fmin: float,
    fmax: float,
    model: str,
    weight: str,
    logger: logging.Logger,
) -> tuple[float, float, int]:
    f = np.asarray(f, float)
    y = np.asarray(phi_ref, float) - np.asarray(phi_mcgt, float)
    mask = np.isfinite(f) & np.isfinite(y) & (f >= fmin) & (f <= fmax)
    n = int(np.sum(mask))
    if n < 2:
        logger.warning(
            "Calage: trop peu de points dans [%.1f, %.1f] Hz (n=%d).", fmin, fmax, n
        )
        return 0.0, 0.0, n

    ff = f[mask]
    yy = y[mask]

    X_cols = [np.ones(n, float)]
    if model == "phi0_tc":
        X_cols.append(2.0 * np.pi * ff)
    X = np.vstack(X_cols).T

    if weight == "1/f2":
        w = 1.0 / np.clip(ff, 1e-12, None) ** 2
    elif weight == "1/f":
        w = 1.0 / np.clip(ff, 1e-12, None)
    else:
        w = np.ones_like(ff)
    # normalize weights to avoid overflow
    w = w / float(np.nanmean(w))

    sqrtw = np.sqrt(w)
    Xw = X * sqrtw[:, None]
    yw = yy * sqrtw

    beta, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    phi0_hat = float(beta[0])
    tc_hat = float(beta[1]) if (model == "phi0_tc" and len(beta) > 1) else 0.0

    logger.info(
        "Calage %s (poids=%s): φ0=%.6e rad, t_c=%.6e s (n=%d, window=[%.1f, %.1f])",
        model,
        weight,
        phi0_hat,
        tc_hat,
        n,
        fmin,
        fmax,
    )
    return phi0_hat, tc_hat, n


# -----------------------
# CLI
# -----------------------
def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Chapitre 9 — Pipeline MCGT (accord homogène 20–300 Hz)"
    )
    ap.add_argument(
        "-i",
        "--ini",
        type=Path,
        default=Path("zz-configuration/gw_phase.ini"),
        help="Fichier INI (section [scan]).",
    )
    ap.add_argument(
        "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
    )
    ap.add_argument(
        "--overwrite",
        action="store_true",
        help="Écraser les fichiers de sortie s'ils existent.",
    )
    ap.add_argument(
        "--refresh-ref",
        action="store_true",
        help="Forcer la régénération de φ_ref (IMRPhenom).",
    )

    ap.add_argument(
        "--metrics-window",
        nargs=2,
        type=float,
        default=[20.0, 300.0],
        metavar=("FMIN", "FMAX"),
        help="Fenêtre [Hz] pour les métriques.",
    )
    ap.add_argument(
        "--calibrate",
        choices=["off", "phi0", "phi0,tc"],
        default="phi0,tc",
        help="Modèle de calage global (φ0 / φ0+t_c).",
    )
    ap.add_argument(
        "--calib-window",
        nargs=2,
        type=float,
        default=[20.0, 300.0],
        metavar=("FMIN", "FMAX"),
        help="Fenêtre [Hz] pour le fit φ0(/t_c).",
    )
    ap.add_argument(
        "--calib-weight",
        choices=["flat", "1/f", "1/f2"],
        default="1/f2",
        help="Pondération WLS dans la fenêtre de calage.",
    )

    ap.add_argument(
        "--auto-tighten",
        dest="auto_tighten",
        action="store_true",
        default=True,
        help="Activer le resserrage automatique (par défaut ON).",
    )
    ap.add_argument(
        "--no-auto-tighten",
        dest="auto_tighten",
        action="store_false",
        help="Désactiver le resserrage automatique.",
    )
    ap.add_argument(
        "--tighten-window",
        nargs=2,
        type=float,
        default=[30.0, 250.0],
        metavar=("FMIN", "FMAX"),
        help="Fenêtre [Hz] utilisée si resserrage.",
    )
    ap.add_argument(
        "--tighten-threshold-p95",
        type=float,
        default=5.0,
        help="Seuil p95(|Δφ|) 20–300 (rad) déclenchant le resserrage.",
    )

    ap.add_argument(
        "--export-diff",
        action="store_true",
        help="Écrire zz-data/chapter09/09_phase_diff.csv.",
    )
    ap.add_argument(
        "--export-anomalies",
        action="store_true",
        help="Écrire comparaison jalons si présents.",
    )
    ap.add_argument(
        "--export-heatmap",
        action="store_true",
        help="Écrire 09_fisher_scan2D.csv (approx locale).",
    )

    ap.add_argument("--fmin", type=float, default=None)
    ap.add_argument("--fmax", type=float, default=None)
    ap.add_argument("--dlog", type=float, default=None)
    ap.add_argument("--m1", type=float, default=None)
    ap.add_argument("--m2", type=float, default=None)
    ap.add_argument("--q0star", type=float, default=None)
    ap.add_argument("--alpha", type=float, default=None)
    ap.add_argument("--phi0", type=float, default=None)
    ap.add_argument("--tc", type=float, default=None)
    ap.add_argument("--tol", type=float, default=None)

    return ap.parse_args()


# -----------------------
# Main
# -----------------------
def main() -> None:
    args = parse_args()
    logger = setup_logger(args.log_level)
    ensure_dirs()

    # Defaults + INI + overrides
    cfg = {
        "fmin": 20.0,
        "fmax": 300.0,
        "dlog": 0.01,
        "m1": 30.0,
        "m2": 30.0,
        "q0star": 0.20,
        "alpha": 1.00,
        "phi0": 0.0,
        "tc": 0.0,
        "tol": 1e-8,
    }
    cfg.update(load_ini(args.ini))
    for k in (
        "fmin",
        "fmax",
        "dlog",
        "m1",
        "m2",
        "q0star",
        "alpha",
        "phi0",
        "tc",
        "tol",
    ):
        v = getattr(args, k, None)
        if v is not None:
            cfg[k] = v

    fmin = _mcgt_safe_float(cfg.get("fmin"), 20.0)
    fmax = _mcgt_safe_float(cfg.get("fmax"), 300.0)
    dlog = _mcgt_safe_float(cfg.get("dlog"), 0.01)
    params = PhaseParams(
        m1=_mcgt_safe_float(cfg.get("m1"), 30.0),
        m2=_mcgt_safe_float(cfg.get("m2"), 25.0),
        q0star=_mcgt_safe_float(cfg.get("q0star"), 0.0),
        alpha=_mcgt_safe_float(cfg.get("alpha"), 0.0),
        phi0=_mcgt_safe_float(cfg.get("phi0"), 0.0),
        tc=_mcgt_safe_float(cfg.get("tc"), 0.0),
        tol=_mcgt_safe_float(cfg.get("tol"), 1e-6),
    )
    logger.info("Paramètres MCGT: %s", params)

    # Build grid
    freqs_cfg = build_loglin_grid(fmin, fmax, dlog)

    # Load or build reference
    f_ref, phi_ref, ref_tag = load_or_build_reference(
        freqs_cfg, logger, refresh=args.refresh_ref
    )

    # Solve MCGT on reference grid (clamp f < fmin to fmin)
    f = clamp_min_frequencies(f_ref, fmin)
    phi_mcgt_raw = solve_mcgt(f, params)

    # Filter finite points
    mask_ok = np.isfinite(f) & np.isfinite(phi_ref) & np.isfinite(phi_mcgt_raw)
    if not np.any(mask_ok):
        raise RuntimeError(
            "Aucune donnée finie après génération de la référence et solveur MCGT."
        )
    if np.sum(~mask_ok) > 0:
        logger.warning(
            "Points non finis supprimés: %d / %d",
            int(np.sum(~mask_ok)),
            int(len(f)),
        )

    f = f[mask_ok]
    phi_ref = phi_ref[mask_ok]
    phi_mcgt_raw = phi_mcgt_raw[mask_ok]

    # Calibration WLS
    calib_enabled = args.calibrate != "off"
    calib_model = (
        "phi0_tc"
        if args.calibrate == "phi0,tc"
        else ("phi0" if args.calibrate == "phi0" else None)
    )
    f_cal_lo, f_cal_hi = map(float, args.calib_window)

    phi0_hat = 0.0
    tc_hat = 0.0
    n_cal = 0
    used_window = [float(f_cal_lo), float(f_cal_hi)]
    used_weight = args.calib_weight
    tightened = False
    p95_check_before = float("nan")
    p95_check_after = float("nan")

    if calib_enabled and calib_model is not None:
        phi0_hat, tc_hat, n_cal = fit_alignment_phi0_tc(
            f,
            phi_ref,
            phi_mcgt_raw,
            f_cal_lo,
            f_cal_hi,
            model=calib_model,
            weight=args.calib_weight,
            logger=logger,
        )
        phi_mcgt_cal = phi_mcgt_raw + phi0_hat + (2.0 * np.pi * f * tc_hat)

        # Check p95 in metrics window (20-300 default)
        band_lo, band_hi = map(float, args.metrics_window)
        band_mask = (f >= band_lo) & (f <= band_hi)
        p95_check_before = p95(np.abs(phi_mcgt_cal[band_mask] - phi_ref[band_mask]))
        logger.info(
            "Contrôle p95 avant resserrage: p95(|Δφ|)@[%.1f-%.1f]=%.6f rad (seuil=%.3f)",
            band_lo,
            band_hi,
            p95_check_before,
            float(args.tighten_threshold_p95),
        )

        if args.auto_tighten and (p95_check_before > float(args.tighten_threshold_p95)):
            tlo, thi = map(float, args.tighten_window)
            logger.info(
                "Resserrement automatique: refit sur [%.1f, %.1f] Hz.", tlo, thi
            )
            phi0_hat, tc_hat, n_cal = fit_alignment_phi0_tc(
                f,
                phi_ref,
                phi_mcgt_raw,
                tlo,
                thi,
                model=calib_model,
                weight=args.calib_weight,
                logger=logger,
            )
            phi_mcgt_cal = phi_mcgt_raw + phi0_hat + (2.0 * np.pi * f * tc_hat)
            used_window = [tlo, thi]
            tightened = True
            p95_check_after = p95(np.abs(phi_mcgt_cal[band_mask] - phi_ref[band_mask]))
            logger.info(
                "Après resserrage: p95(|Δφ|)@[%.1f-%.1f]=%.6f rad",
                band_lo,
                band_hi,
                p95_check_after,
            )
        else:
            p95_check_after = p95_check_before

        phi_mcgt_active = phi_mcgt_cal
        active_variant = "calibrated"
    else:
        phi_mcgt_cal = phi_mcgt_raw.copy()
        phi_mcgt_active = phi_mcgt_raw.copy()
        active_variant = "raw"

    # Exports phases (respect overwrite)
    out_mcgt = OUT_DIR / "09_phases_mcgt.csv"
    if out_mcgt.exists() and not args.overwrite:
        logger.info(
            "Conserver fichier existant (utilisez --overwrite pour écraser): %s",
            out_mcgt,
        )
    else:
        pd.DataFrame(
            {
                "f_Hz": f,
                "phi_ref": phi_ref,
                "phi_mcgt": phi_mcgt_active,
                "phi_mcgt_raw": phi_mcgt_raw,
                "phi_mcgt_cal": phi_mcgt_cal,
            }
        ).to_csv(out_mcgt, index=False)
        logger.info("Écrit → %s", out_mcgt)

    # Δφ and metrics (metrics window)
    dphi_raw = phi_mcgt_raw - phi_ref
    dphi_cal = (phi_mcgt_raw + phi0_hat + 2.0 * np.pi * f * tc_hat) - phi_ref
    abs_raw = np.abs(dphi_raw)
    abs_cal = np.abs(dphi_cal)

    mw_lo, mw_hi = map(float, args.metrics_window)
    mask_win = (f >= mw_lo) & (f <= mw_hi)

    def stats(x: np.ndarray) -> tuple[float, float, float]:
        arr = np.asarray(x, float)
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            return float("nan"), float("nan"), float("nan")
        return float(np.nanmean(arr)), float(np.nanmax(arr)), float(p95(arr))

    mean_raw, max_raw, p95_raw = stats(abs_raw[mask_win])
    mean_cal, max_cal, p95_cal = stats(abs_cal[mask_win])

    if calib_enabled:
        dphi = dphi_cal
        abs_dphi = abs_cal
        mean_abs, max_abs, p95_abs = mean_cal, max_cal, p95_cal
    else:
        dphi = dphi_raw
        abs_dphi = abs_raw
        mean_abs, max_abs, p95_abs = mean_raw, max_raw, p95_raw

    # Export diff CSV if requested
    out_diff = OUT_DIR / "09_phase_diff.csv"
    if args.export_diff:
        if out_diff.exists() and not args.overwrite:
            logger.info(
                "Conserver diff existant (use --overwrite to replace): %s", out_diff
            )
        else:
            df_diff = pd.DataFrame(
                {
                    "f_Hz": f,
                    "dphi": dphi,
                    "abs_dphi": abs_dphi,
                    "mean_abs_20_300": np.full_like(f, float(mean_abs), dtype=float),
                    "max_abs_20_300": np.full_like(f, float(max_abs), dtype=float),
                    "p95_abs_20_300": np.full_like(f, float(p95_abs), dtype=float),
                    "dphi_raw": dphi_raw,
                    "abs_dphi_raw": abs_raw,
                    "dphi_cal": dphi_cal,
                    "abs_dphi_cal": abs_cal,
                }
            )
            df_diff.to_csv(out_diff, index=False)
            logger.info("Écrit → %s", out_diff)

    # Jalons comparison
    out_jalons_cmp = None
    if args.export_anomalies:
        if JALONS_CSV.exists():
            jal = pd.read_csv(JALONS_CSV)
            need = {"event", "f_Hz", "obs_phase", "sigma_phase"}
            if not need.issubset(jal.columns):
                logger.warning(
                    "Jalons: colonnes manquantes (attendues: %s).", sorted(need)
                )
            else:
                fpk = np.asarray(jal["f_Hz"].to_numpy(float), float)
                phi_ref_at = np.interp(fpk, f, phi_ref)
                phi_raw_at = np.interp(fpk, f, phi_mcgt_raw)
                phi_cal_at = np.interp(
                    fpk, f, phi_mcgt_raw + phi0_hat + 2.0 * np.pi * f * tc_hat
                )
                phi_active_at = phi_cal_at if calib_enabled else phi_raw_at

                obs = jal["obs_phase"].to_numpy(float)
                denom = np.where(np.abs(obs) > 0, np.abs(obs), np.inf)
                epsilon_rel = (phi_active_at - obs) / denom

                out_jalons_cmp = OUT_DIR / "09_comparison_milestones.csv"
                pd.DataFrame(
                    {
                        "event": jal["event"],
                        "f_Hz": fpk,
                        "phi_ref_at_fpeak": phi_ref_at,
                        "phi_mcgt_at_fpeak": phi_active_at,
                        "phi_mcgt_at_fpeak_raw": phi_raw_at,
                        "phi_mcgt_at_fpeak_cal": phi_cal_at,
                        "obs_phase": jal["obs_phase"],
                        "sigma_phase": jal["sigma_phase"],
                        "epsilon_rel": epsilon_rel,
                        "classe": jal.get("classe", pd.Series([""] * len(jal))),
                        "variant": "calibrated" if calib_enabled else "raw",
                    }
                ).to_csv(out_jalons_cmp, index=False)
                logger.info("Écrit → %s", out_jalons_cmp)
        else:
            logger.warning(
                "Aucun jalon à comparer (fichier introuvable): %s", JALONS_CSV
            )

    # Optional local Fisher-like heatmap (approx)
    out_fisher = None
    if args.export_heatmap:
        try:
            if JALONS_CSV.exists():
                sj = pd.read_csv(JALONS_CSV).get("sigma_phase", pd.Series([0.1]))
                sigma_phase = float(np.median(sj.values)) if len(sj) else 0.1
            else:
                sigma_phase = 0.1

            param2_vals = np.linspace(
                max(0.5, params.alpha - 0.5), min(2.0, params.alpha + 0.5), 51
            )
            eps = 1e-5
            rows = []
            for a in param2_vals:
                p_lo = PhaseParams(
                    m1=params.m1,
                    m2=params.m2,
                    q0star=params.q0star - eps,
                    alpha=a,
                    phi0=params.phi0,
                    tc=params.tc,
                    tol=params.tol,
                )
                p_hi = PhaseParams(
                    m1=params.m1,
                    m2=params.m2,
                    q0star=params.q0star + eps,
                    alpha=a,
                    phi0=params.phi0,
                    tc=params.tc,
                    tol=params.tol,
                )
                phi_lo = solve_mcgt(f, p_lo)
                phi_hi = solve_mcgt(f, p_hi)
                dphi_dq = (phi_hi - phi_lo) / (2 * eps)
                fisher = (
                    (dphi_dq**2) / (sigma_phase**2)
                    if sigma_phase > 0
                    else np.full_like(dphi_dq, np.nan)
                )
                rows.append(
                    pd.DataFrame(
                        {
                            "f_Hz": f,
                            "param2": np.full_like(f, a),
                            "fisher_value": fisher,
                        }
                    )
                )
            fisher_df = pd.concat(rows, ignore_index=True)
            out_fisher = OUT_DIR / "09_fisher_scan2D.csv"
            fisher_df.to_csv(out_fisher, index=False)
            logger.info("Écrit → %s", out_fisher)
        except Exception as e:
            logger.warning("Erreur calcul heatmap fisher: %s", e)

    # Write metrics JSON
    meta = {
        "ini": str(args.ini),
        "params": asdict(params),
        "reference": {
            "csv": str(REF_CSV),
            "meta": str(REF_META),
            "source_tag": ref_tag,
        },
        "grid_used": {
            "fmin_Hz": _mcgt_safe_float(np.nanmin(f), 20.0),
            "fmax_Hz": _mcgt_safe_float(np.nanmax(f), 300.0),
            "dlog10": float(dlog),
            "n_points_used": int(len(f)),
        },
        "metrics_window_Hz": [float(mw_lo), float(mw_hi)],
        "metrics_active": {
            "mean_abs_20_300": float(mean_abs),
            "max_abs_20_300": float(max_abs),
            "p95_abs_20_300": float(p95_abs),
            "variant": active_variant,
        },
        "metrics_raw": {
            "mean_abs_20_300": float(mean_raw),
            "max_abs_20_300": float(max_raw),
            "p95_abs_20_300": float(p95_raw),
        },
        "metrics_cal": {
            "mean_abs_20_300": float(mean_cal),
            "max_abs_20_300": float(max_cal),
            "p95_abs_20_300": float(p95_cal),
        },
        "calibration": {
            "enabled": bool(calib_enabled),
            "mode": args.calibrate,
            "model_used": calib_model,
            "phi0_hat_rad": float(phi0_hat),
            "tc_hat_s": float(tc_hat),
            "initial_window_Hz": [float(f_cal_lo), float(f_cal_hi)],
            "used_window_Hz": [float(used_window[0]), float(used_window[1])],
            "weight": used_weight,
            "auto_tightened": bool(tightened),
            "tighten_threshold_p95_rad": float(args.tighten_threshold_p95),
            "p95_check_before_rad": float(p95_check_before),
            "p95_check_after_rad": float(p95_check_after),
            "n_points": int(n_cal),
        },
        "outputs": {
            "phases_mcgt_csv": str(out_mcgt) if out_mcgt.exists() else None,
            "diff_phase_csv": str(out_diff)
            if args.export_diff and out_diff.exists()
            else None,
            "comparison_milestones_csv": str(out_jalons_cmp)
            if out_jalons_cmp
            else None,
            "fisher_scan2D_csv": str(out_fisher) if out_fisher else None,
        },
        "repro": {
            "git_hash": git_hash(),
            "python": "{}.{}.{}".format(*sys.version_info[:3]),
            "libs": {"numpy": np.__version__, "pandas": pd.__version__},
        },
    }
    (OUT_DIR / "09_metrics_phase.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    logger.info("Écrit → %s", OUT_DIR / "09_metrics_phase.json")

    logger.info(
        "Terminé. Variante ACTIVE: %s | p95(|Δφ|)@%g–%g = %.6f rad",
        active_variant,
        mw_lo,
        mw_hi,
        p95_abs,
    )


if __name__ == "__main__":
    main()
