#!/usr/bin/env python3
# ---IMPORTS & CONFIGURATION---

import argparse
import json
import logging
from pathlib import Path

import camb
import numpy as np
import pandas as pd

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Parser CLI
parser = argparse.ArgumentParser(
    description="Chapter 6 pipeline: generate CMB spectra for MCGT"
)
parser.add_argument("--alpha", type=float, default=0.0, help="Modulation amplitude α")
parser.add_argument(
    "--q0star",
    type=float,
    default=0.0,
    help="Effective curvature parameter q0star (Ω_k)",
)
parser.add_argument(
    "--export-derivative", action="store_true", help="Export derivative Δχ²/Δℓ"
)
args = parser.parse_args()

ALPHA = args.alpha
Q0STAR = args.q0star

# Project root directory
ROOT = Path(__file__).resolve().parents[2]

# Config and data directories (English names)
CONF_DIR = ROOT / "zz-configuration"
DATA_DIR = ROOT / "zz-data" / "chapter06"
INI_DIR = ROOT / "06-cmb"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---LOAD CHAPTER-2 SPECTRUM COEFFICIENTS---

# Note: chapter02 path uses English folder name 'chapter02' and spec file
SPEC2_FILE = ROOT / "zz-data" / "chapter02" / "02_primordial_spectrum_spec.json"
with open(SPEC2_FILE, encoding="utf-8") as f:
    spec2 = json.load(f)

A_S0 = (
    spec2["constantes"]["A_s0"]
    if "constantes" in spec2
    else spec2.get("constants", {}).get("A_s0")
)
NS0 = (
    spec2["constantes"]["ns0"]
    if "constantes" in spec2
    else spec2.get("constants", {}).get("ns0")
)
C1 = spec2.get("coefficients", {}).get("c1")
C2 = spec2.get("coefficients", {}).get("c2")

logging.info(f"Chapter02 spectrum loaded: A_s0={A_S0}, ns0={NS0}, c1={C1}, c2={C2}")
logging.info(f"MCGT parameters: alpha={ALPHA}, q0star={Q0STAR}")

# ---OPTIONAL EXPORT: A_s(α) and n_s(α) over alpha grid---

alpha_vals = np.arange(-0.1, 0.1001, 0.01)
df_alpha = pd.DataFrame(
    {
        "alpha": alpha_vals,
        "A_s": A_S0 * (1 + C1 * alpha_vals),
        "n_s": NS0 + C2 * alpha_vals,
    }
)
OUT_ALPHA = DATA_DIR / "06_alpha_evolution.csv"
df_alpha.to_csv(OUT_ALPHA, index=False)
logging.info(f"06_alpha_evolution.csv generated → {OUT_ALPHA}")

# ---CMB CONSTANTS---

ELL_MIN = 2
ELL_MAX = 3000
PK_KMAX = 10.0
DERIV_WINDOW = 7
DERIV_POLYORDER = 3

# Base cosmological parameters (Planck 2018)
cosmo_params = {
    "H0": 67.36,
    "ombh2": 0.02237,
    "omch2": 0.1200,
    "tau": 0.0544,
    "omk": 0.0,
    "mnu": 0.06,
}

# Output files (English names)
CLS_LCDM_DAT = DATA_DIR / "06_cls_lcdm_spectrum.dat"
CLS_MCGT_DAT = DATA_DIR / "06_cls_spectrum.dat"
DELTA_CLS_CSV = DATA_DIR / "06_delta_cls.csv"
DELTA_CLS_REL_CSV = DATA_DIR / "06_delta_cls_relative.csv"
JSON_PARAMS = DATA_DIR / "06_params_cmb.json"
CSV_RS_SCAN = DATA_DIR / "06_delta_rs_scan.csv"
CSV_RS_SCAN_FULL = DATA_DIR / "06_delta_rs_scan_2d.csv"
CSV_CHI2_2D = DATA_DIR / "06_cmb_chi2_scan_2d.csv"

# ---MCGT PHYSICAL INJECTION FUNCTION FOR CAMB---


def tweak_for_mcgt(pars, alpha, q0star):
    """
    Modify CAMB params 'pars' according to the MCGT deformation:
      • Primordial spectrum: A_s = A_S0*(1 + c1*α), ns = ns0 + c2*α
      • Curvature: Ω_k = q0star
      • (Optional) inject ΔT_m(k) from file '06_delta_Tm_scan.csv'
    """
    # 1) Modulate primordial spectrum
    pars.InitPower.set_params(As=A_S0 * (1 + C1 * alpha), ns=NS0 + C2 * alpha)

    # 2) Update curvature and base cosmology
    pars.set_cosmology(
        H0=cosmo_params["H0"],
        ombh2=cosmo_params["ombh2"],
        omch2=cosmo_params["omch2"],
        tau=cosmo_params["tau"],
        omk=q0star,
        mnu=cosmo_params["mnu"],
    )

    # 3) Optional post-processing for matter transfer ΔT_m(k)
    def post_process(results):
        try:
            tm_obj = results.get_matter_transfer_data()
            k_vals = tm_obj.q
            tm_data = tm_obj.transfer_data[0, :, 0]
            path = DATA_DIR / "06_delta_Tm_scan.csv"
            if path.exists():
                delta_k, dTm = np.loadtxt(path, delimiter=",", skiprows=1, unpack=True)
                tm_data += np.interp(k_vals, delta_k, dTm)
                tm_obj.transfer_data[0, :, 0] = tm_data
                if hasattr(results, "replace_transfer"):
                    results.replace_transfer(0, tm_data)
        except Exception:
            # If matter transfer access fails, silently continue
            pass
        return results

    pars.post_process = post_process


# ---1. LOAD pdot_plateau_z (configuration)---
PDOT_FILE = CONF_DIR / "pdot_plateau_z.dat"
logging.info("1) Reading pdot_plateau_z.dat …")
z_h, pdot = np.loadtxt(PDOT_FILE, unpack=True)
if z_h.size == 0 or pdot.size == 0:
    raise ValueError(f"Invalid file: {PDOT_FILE}")

z_grid = np.linspace(0, 50, 100)  # redshift grid for matter_power

# ---2. ΛCDM Cℓ SPECTRUM (CAMB)---
logging.info("2) Computing ΛCDM spectrum …")
pars0 = camb.CAMBparams()
pars0.set_for_lmax(ELL_MAX, max_eta_k=40000)
pars0.set_cosmology(
    H0=cosmo_params["H0"],
    ombh2=cosmo_params["ombh2"],
    omch2=cosmo_params["omch2"],
    tau=cosmo_params["tau"],
    omk=cosmo_params["omk"],
    mnu=cosmo_params["mnu"],
)
pars0.InitPower.set_params(As=A_S0, ns=NS0)
res0 = camb.get_results(pars0)
cmb0 = res0.get_cmb_power_spectra(pars0, lmax=ELL_MAX)["total"][:, 0]
cls0 = cmb0[: ELL_MAX + 1]
ells = np.arange(cls0.size)
np.savetxt(
    CLS_LCDM_DAT,
    np.column_stack([ells, cls0]),
    header="# ell   Cl_LCDM",
    comments="",
    fmt="%d %.6e",
)
logging.info(f"ΛCDM spectrum saved → {CLS_LCDM_DAT}")

# ---3. MCGT Cℓ SPECTRUM (α, q0*)---
logging.info("3) Computing MCGT spectrum …")
pars1 = camb.CAMBparams()
pars1.set_for_lmax(ELL_MAX, max_eta_k=40000)
# Inject MCGT with specified alpha and q0star
tweak_for_mcgt(pars1, alpha=ALPHA, q0star=Q0STAR)
# Configure matter power for MCGT
pars1.set_matter_power(redshifts=z_grid, kmax=PK_KMAX)
res1 = camb.get_results(pars1)
if hasattr(pars1, "post_process"):
    res1 = pars1.post_process(res1)
cmb1 = res1.get_cmb_power_spectra(pars1, lmax=ELL_MAX)["total"][:, 0]
cls1 = cmb1[: ells.size]
np.savetxt(
    CLS_MCGT_DAT,
    np.column_stack([ells, cls1]),
    header="# ell   Cl_MCGT",
    comments="",
    fmt="%d %.6e",
)
logging.info(f"MCGT spectrum saved → {CLS_MCGT_DAT}")

# ---4. ΔCℓ & relative ΔCℓ---
logging.info("4) Computing ΔCℓ …")
delta = cls1 - cls0
delta_rel = np.divide(delta, cls0, out=np.zeros_like(delta), where=cls0 > 0)
dfd = pd.DataFrame({"ell": ells, "delta_Cl": delta, "delta_Cl_rel": delta_rel})
dfd[["ell", "delta_Cl"]].to_csv(DELTA_CLS_CSV, index=False)
dfd[["ell", "delta_Cl_rel"]].to_csv(DELTA_CLS_REL_CSV, index=False)
logging.info(f"ΔCℓ → {DELTA_CLS_CSV}, {DELTA_CLS_REL_CSV}")

# ---5. SAVE PARAMETERS---
logging.info("5) Saving parameters …")
params_out = {
    "alpha": ALPHA,
    "q0star": Q0STAR,
    "ell_min": ELL_MIN,
    "ell_max": ELL_MAX,
    "n_points": int(len(ells)),
    "thresholds": {"primary": 0.01, "order2": 0.10},
    "derivative_window": DERIV_WINDOW,
    "derivative_polyorder": DERIV_POLYORDER,
    **{k: cosmo_params[k] for k in ["H0", "ombh2", "omch2", "tau", "mnu"]},
    "As0": A_S0,
    "ns0": NS0,
    "c1": C1,
    "c2": C2,
    "max_delta_Cl_rel": float(np.nanmax(np.abs(delta_rel))),
}
with open(JSON_PARAMS, "w") as f:
    json.dump(params_out, f, indent=2)
logging.info(f"JSON parameters → {JSON_PARAMS}")

# ---6. SCAN Δr_s AS FUNCTION OF q0*---
logging.info("6) Scanning Δr_s …")


def compute_rs(alpha, q0star):
    p = camb.CAMBparams()
    p.set_for_lmax(ELL_MAX, max_eta_k=40000)
    tweak_for_mcgt(p, alpha=alpha, q0star=q0star)
    return camb.get_results(p).get_derived_params()["rdrag"]


# reference r_s at (ALPHA, Q0STAR)
rs_ref = compute_rs(ALPHA, Q0STAR)

q0_grid = np.linspace(-0.1, 0.1, 41)
rows_rs = []
for q0 in q0_grid:
    rs_i = compute_rs(ALPHA, q0)
    rows_rs.append(
        {"q0star": q0, "r_s": rs_i, "delta_rs_rel": (rs_i - rs_ref) / rs_ref}
    )
df_rs = pd.DataFrame(rows_rs)
df_rs[["q0star", "delta_rs_rel"]].to_csv(CSV_RS_SCAN, index=False)
df_rs.to_csv(CSV_RS_SCAN_FULL, index=False)
logging.info(f"Δr_s scan (1D)     → {CSV_RS_SCAN}")
logging.info(f"Δr_s full scan     → {CSV_RS_SCAN_FULL}")

# ---7. 2D SCAN (α, q0*): cosmic-variance χ²---
logging.info("7) 2D Δχ² scan (cosmic variance) …")


def compute_chi2_cv(alpha, q0star):
    p1 = camb.CAMBparams()
    p1.set_for_lmax(ELL_MAX, max_eta_k=40000)
    tweak_for_mcgt(p1, alpha=alpha, q0star=q0star)
    p1.set_matter_power(redshifts=z_grid, kmax=PK_KMAX)
    res_mcgt = camb.get_results(p1)
    if hasattr(p1, "post_process"):
        res_mcgt = p1.post_process(res_mcgt)
    cls_mcgt = res_mcgt.get_cmb_power_spectra(p1, lmax=ells.size - 1)["total"][:, 0]
    cls_mcgt = cls_mcgt[: ells.size]

    Delta = cls_mcgt - cls0
    var = 2.0 * cls0**2 / (2 * ells + 1)
    mask = (ells >= ELL_MIN) & (var > 0)
    chi2 = np.sum((Delta[mask] ** 2) / var[mask])
    return float(chi2)


alpha_grid = np.linspace(-0.1, 0.1, 21)
q0_grid2 = np.linspace(-0.1, 0.1, 21)
rows2d = []
for a in alpha_grid:
    for q in q0_grid2:
        rows2d.append({"alpha": a, "q0star": q, "chi2": compute_chi2_cv(a, q)})

df2d = pd.DataFrame(rows2d, columns=["alpha", "q0star", "chi2"])
df2d.to_csv(CSV_CHI2_2D, index=False)
logging.info(f"2D Δχ² scan → {CSV_CHI2_2D}")

# ---8. ΔT_m(k) BETWEEN MCGT AND ΛCDM---

logging.info("8) Exporting ΔT_m(k) …")
# ΛCDM matter transfer
pars0_tm = camb.CAMBparams()
pars0_tm.set_cosmology(
    H0=cosmo_params["H0"],
    ombh2=cosmo_params["ombh2"],
    omch2=cosmo_params["omch2"],
    tau=cosmo_params["tau"],
    omk=cosmo_params["omk"],
    mnu=cosmo_params["mnu"],
)
pars0_tm.InitPower.set_params(As=A_S0, ns=NS0)
pars0_tm.set_matter_power(redshifts=[0], kmax=PK_KMAX)
tm0_obj = camb.get_results(pars0_tm).get_matter_transfer_data()
k_vals = tm0_obj.q
tm0_data = tm0_obj.transfer_data[0, :, 0]

pars1_tm = camb.CAMBparams()
tweak_for_mcgt(pars1_tm, alpha=ALPHA, q0star=Q0STAR)
pars1_tm.set_matter_power(redshifts=[0], kmax=PK_KMAX)
if hasattr(pars1_tm, "post_process"):
    camb_results = pars1_tm.post_process(camb.get_results(pars1_tm))
else:
    camb_results = camb.get_results(pars1_tm)
tm1_obj = camb_results.get_matter_transfer_data()
k1 = tm1_obj.q
tm1_data = tm1_obj.transfer_data[0, :, 0]
tm1_data_interp = np.interp(k_vals, k1, tm1_data)

delta_Tm = tm1_data_interp - tm0_data

OUT_TMDAT = DATA_DIR / "06_delta_Tm_scan.csv"
with open(OUT_TMDAT, "w") as f:
    f.write("# k, delta_Tm\n")
    for k, dTm in zip(k_vals, delta_Tm, strict=False):
        f.write(f"{k:.6e}, {dTm:.6e}\n")
logging.info(f"ΔT_m(k) exported → {OUT_TMDAT}")

# ---9. (Optional) duplicate alpha-evolution (kept for compatibility)---
logging.info("9) (Optional) Regenerating 06_alpha_evolution.csv …")
df_alpha.to_csv(OUT_ALPHA, index=False)
logging.info(f"06_alpha_evolution.csv overwritten → {OUT_ALPHA}")

logging.info("=== Chapter 6 generation completed ===")

# === MCGT CLI SEED v2 ===
if __name__ == "__main__":

    def _mcgt_cli_seed():
        import os
        import argparse

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
            "--seed", type=int, default=None, help="Graine aléatoire (optionnelle)."
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
            "--dpi", type=int, default=150, help="Figure DPI (default: 150)"
        )
        parser.add_argument(
            "--format",
            choices=["png", "pdf", "svg"],
            default="png",
            help="Figure format",
        )
        parser.add_argument(
            "--transparent", action="store_true", help="Transparent background"
        )

        args = parser.parse_args()
        import os
        import matplotlib as mpl

        os.makedirs(args.outdir, exist_ok=True)
        os.environ["MCGT_OUTDIR"] = args.outdir
        mpl.rcParams["savefig.dpi"] = args.dpi

    _mcgt_cli_seed()
