#!/usr/bin/env python3
# generer_donnees_chapter3.py

"""
Chapitre 3 – Pipeline intégral (v3.2.0)
--------------------------------------
Stabilité de f(R) : génération des données numériques pour les figures
et les tableaux du Chapitre 3.

"""

# ----------------------------------------------------------------------
# 0. Imports & configuration globale
# ----------------------------------------------------------------------
from __future__ import annotations

import argparse
import configparser
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.integrate import quad
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

from mcgt.constants import H0_1_PER_GYR as H0  # unified

# ----------------------------------------------------------------------
# 1. Logging
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# 2. Cosmologie : inversion T↔z
# ----------------------------------------------------------------------
H0_km_s_Mpc = 67.66
Mpc_to_km = 3.0856775814913673e19  # km dans 1 Mpc
sec_per_Gyr = 3.1536e16  # s dans 1 Gyr
# H0 unifié → import
Om0, Ol0 = 0.3111, 0.6889


def T_of_z(z: float) -> float:
    """Âge de l’Univers (Gyr) à redshift z dans un ΛCDM plat."""

    def integrand(zp):
        return 1 / ((1 + zp) * H0 * np.sqrt(Om0 * (1 + zp) ** 3 + Ol0))

    T, _ = quad(integrand, z, 1e5)
    return T


def z_of_T(T: float) -> float:
    """Inverse de T_of_z; si T≥T0 renvoie 0."""
    T0 = T_of_z(0.0)
    if T >= T0:
        return 0.0
    # approximation à petit T
    thr = 1e-2
    if thr > T:
        return max(((2 / (3 * H0 * np.sqrt(Om0))) / T) ** (2 / 3) - 1, 0.0)

    # sinon root-finding
    def f(z):
        return T_of_z(z) - T

    zmax = 1e6
    if f(0) * f(zmax) > 0:
        zmax *= 10
    return brentq(f, 0.0, zmax)


# ----------------------------------------------------------------------
# 3. Outils partagés (grille log-lin)
# ----------------------------------------------------------------------
def build_loglin_grid(fmin: float, fmax: float, dlog: float) -> np.ndarray:
    if fmin <= 0 or fmax <= 0 or fmax <= fmin:
        raise ValueError("fmin>0, fmax>fmin requis.")
    n = int(np.floor((np.log10(fmax) - np.log10(fmin)) / dlog)) + 1
    return 10 ** (np.log10(fmin) + np.arange(n) * dlog)


def check_log_spacing(g: np.ndarray, atol: float = 1e-12) -> bool:
    d = np.diff(np.log10(g))
    return np.allclose(d, d[0], atol=atol)


# ----------------------------------------------------------------------
# 4. Jalons : copie si besoin
# ----------------------------------------------------------------------
def ensure_jalons(src: Path | None) -> Path:
    dst = Path("zz-data") / "chapter03" / "03_ricci_fR_milestones.csv"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return dst
    if src is None or not Path(src).exists():
        log.error("Manque 03_ricci_fR_milestones.csv – utilisez --copy-jalons")
        sys.exit(1)
    dst.write_bytes(Path(src).read_bytes())
    log.info("Jalons copiés → %s", dst)
    return dst


# ----------------------------------------------------------------------
# 5. CLI & lecture INI
# ----------------------------------------------------------------------
def parse_cli() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Génère les données du Chapitre 3.")
    p.add_argument(
        "--config", default="zz-configuration/gw_phase.ini", help="INI avec [scan]"
    )
    p.add_argument("--npts", type=int, help="nombre de points fixe")
    p.add_argument("--copy-jalons", help="chemin vers jalons si absent")
    p.add_argument("--dry-run", action="store_true", help="ne pas écrire")
    return p.parse_args()


def read_scan_section(path: Path) -> tuple[float, float, float]:
    cfg = configparser.ConfigParser()
    if not cfg.read(path) or "scan" not in cfg:
        log.error("Impossible de lire la section [scan] de %s", path)
        sys.exit(1)
    s = cfg["scan"]
    try:
        return s.getfloat("fmin"), s.getfloat("fmax"), s.getfloat("dlog")
    except ValueError as e:
        log.error("Valeurs invalides dans [scan] : %s", e)
        sys.exit(1)


# ----------------------------------------------------------------------
# 6. Construction des grilles T, z et R
# ----------------------------------------------------------------------
def build_T_z_R_grids(fmin: float, fmax: float, dlog: float, npts: int | None):
    # 6.1 Grille log-lin en fréquence
    if npts:
        dlog = (np.log10(fmax) - np.log10(fmin)) / (npts - 1)
    freqs = build_loglin_grid(fmin, fmax, dlog)

    # 6.2 Grille temps & redshift (avant filtrage)
    logTmin, logTmax = np.log10(1e-6), np.log10(14.0)
    T_full = 10 ** np.arange(logTmin, logTmax + dlog, dlog)
    z_full = np.array([z_of_T(T) for T in T_full])

    # 6.3 Grille R/R₀ normalisée (avant filtrage)
    H_z = H0 * np.sqrt(Om0 * (1 + z_full) ** 3 + Ol0)
    R_full = 12 * H_z**2 / (12 * H0**2)  # = R/R₀

    # 6.4 Élimination des doublons tout en conservant l’ordre
    #     On récupère aussi les indices pour aligner T et z
    R_unique, indices = np.unique(R_full, return_index=True)
    T_grid = T_full[indices]
    z_grid = z_full[indices]

    log.info(
        "Grille R/R₀ unique prête : %d points (%.3e → %.3e).",
        R_unique.size,
        R_unique.min(),
        R_unique.max(),
    )
    return freqs, T_grid, z_grid, R_unique


# ----------------------------------------------------------------------
# 7. Calcul de stabilité
# ----------------------------------------------------------------------
def calculer_stabilite(jalons: pd.DataFrame, Rgrid: np.ndarray):
    logRj = np.log10(jalons["R_over_R0"])
    fR_i = PchipInterpolator(logRj, np.log10(jalons["f_R"]), extrapolate=True)
    fRR_i = PchipInterpolator(logRj, np.log10(jalons["f_RR"]), extrapolate=True)

    logRg = np.log10(Rgrid)
    fRg = 10 ** fR_i(logRg)
    fRRg = 10 ** fRR_i(logRg)
    ms2 = (fRg - Rgrid * fRRg) / (3 * fRRg)

    df = pd.DataFrame(
        {"R_over_R0": Rgrid, "f_R": fRg, "f_RR": fRRg, "m_s2_over_R0": ms2}
    )
    dom = pd.DataFrame(
        {"beta": Rgrid, "gamma_min": np.zeros_like(ms2), "gamma_max": ms2.clip(max=1e8)}
    )
    frt = dom.query("gamma_min==gamma_max").rename(
        columns={"gamma_max": "gamma_limit"}
    )[["beta", "gamma_limit"]]
    return df, dom, frt


# ----------------------------------------------------------------------
# 8. Exports CSV & métadonnées
# ----------------------------------------------------------------------
def exporter_csv(df: pd.DataFrame, dom: pd.DataFrame, frt: pd.DataFrame, dry: bool):
    out = Path("zz-data") / "chapter03"
    out.mkdir(parents=True, exist_ok=True)
    if dry:
        log.info("--dry-run : je n’écris pas les CSV.")
        return
    df.to_csv(out / "03_fR_stability_data.csv", index=False)
    dom.to_csv(out / "03_fR_stability_domain.csv", index=False)
    frt.to_csv(out / "03_fR_stability_boundary.csv", index=False)
    meta = {
        "n_points": int(df.shape[0]),
        "files": [
            "03_fR_stability_data.csv",
            "03_fR_stability_domain.csv",
            "03_fR_stability_boundary.csv",
        ],
    }
    (out / "03_fR_stability_meta.json").write_text(json.dumps(meta, indent=2))
    log.info("Données principales et métadonnées écrites.")


# ----------------------------------------------------------------------
# 9. Génération des fichiers R ↔ z et R ↔ T  (section remise à jour)
# ----------------------------------------------------------------------
def exporter_jalons_inverses(
    df_R: pd.DataFrame,
    jalons: pd.DataFrame,
    zgrid: np.ndarray,
    Tgrid: np.ndarray,
    dry: bool,
) -> None:
    """
    Construit deux fichiers :

    * 03_ricci_fR_vs_z.csv  : jalons + redshift interpolé
    * 03_ricci_fR_vs_T.csv  : jalons + âge interpolé

    Les jalons hors domaine d’interpolation **sont ignorés** afin
    d’éviter les z = 0 artificiels.
    """
    out = Path("zz-data") / "chapter03"
    out.mkdir(parents=True, exist_ok=True)
    if dry:
        log.info("--dry-run : pas d’export R↔z / R↔T")
        return

    # ------------------------------------------------------------------
    # 9-A  Interpolation R → z  (monotone PCHIP, sans extrapolation)
    # ------------------------------------------------------------------
    df_z = (
        pd.DataFrame({"R_over_R0": df_R["R_over_R0"], "z": zgrid})
        .drop_duplicates("R_over_R0")
        .sort_values("R_over_R0")
    )

    p_z = PchipInterpolator(
        np.log10(df_z["R_over_R0"]),
        df_z["z"],
        extrapolate=False,  # <- évite les z = 0 parasites
    )

    jal_z = jalons.copy()
    mask_in = (jal_z["R_over_R0"] >= df_z["R_over_R0"].min()) & (
        jal_z["R_over_R0"] <= df_z["R_over_R0"].max()
    )
    jal_z.loc[mask_in, "z"] = p_z(np.log10(jal_z.loc[mask_in, "R_over_R0"]))

    # Ne garder **que** les jalons interpolables
    jal_z = jal_z.dropna(subset=["z"]).sort_values("R_over_R0")

    # ------------------------------------------------------------------
    # 9-A  Interpolation R → z  (monotone, sans extrapolation)
    # ------------------------------------------------------------------
    df_zfull = pd.DataFrame({"R_over_R0": df_R["R_over_R0"], "z": zgrid}).query(
        "z > 0"
    )  # z strictement positifs

    # on garde, pour chaque R, le z le plus grand (plus ancien)
    df_zfull.sort_values(["R_over_R0", "z"], ascending=[True, False], inplace=True)
    df_z = df_zfull.drop_duplicates("R_over_R0").sort_values("R_over_R0")

    p_z = PchipInterpolator(np.log10(df_z["R_over_R0"]), df_z["z"], extrapolate=False)

    jal_z = jalons.copy()
    in_domain = jal_z["R_over_R0"].between(
        df_z["R_over_R0"].min(), df_z["R_over_R0"].max()
    )
    jal_z.loc[in_domain, "z"] = p_z(np.log10(jal_z.loc[in_domain, "R_over_R0"]))

    # on ne garde que les jalons réellement interpolés
    jal_z = jal_z.dropna(subset=["z"]).sort_values("R_over_R0")

    # garantir z croissant avec R
    jal_z["z"] = jal_z["z"].cummax()

    jal_z.to_csv(out / "03_ricci_fR_vs_z.csv", index=False)
    log.info("→ 03_ricci_fR_vs_z.csv généré (%d jalons)", len(jal_z))

    # ------------------------------------------------------------------
    # 9-B  Interpolation R → T  (log-log, toujours définie : extrapolate=True)
    # ------------------------------------------------------------------
    df_T = (
        pd.DataFrame({"R_over_R0": df_R["R_over_R0"], "T_Gyr": Tgrid})
        .drop_duplicates("R_over_R0")
        .sort_values("R_over_R0")
    )

    p_T = PchipInterpolator(
        np.log10(df_T["R_over_R0"]),
        np.log10(df_T["T_Gyr"]),
        extrapolate=True,  # extrapolation OK pour T
    )

    jal_T = jal_z.copy()  # même sous-ensemble que pour z
    jal_T["T_Gyr"] = 10 ** p_T(np.log10(jal_T["R_over_R0"]))

    # Assurer la décroissance de T (le passé ne doit pas dépasser le présent)
    T_vals = jal_T["T_Gyr"].values
    for i in range(1, len(T_vals)):
        T_vals[i] = min(T_vals[i], T_vals[i - 1])
    jal_T["T_Gyr"] = T_vals

    jal_T.to_csv(out / "03_ricci_fR_vs_T.csv", index=False)
    log.info("→ 03_ricci_fR_vs_T.csv généré (%d jalons)", len(jal_T))


# ----------------------------------------------------------------------
# 10. Main
# ----------------------------------------------------------------------
def main() -> None:
    args = parse_cli()
    fmin, fmax, dlog = read_scan_section(Path(args.config))

    # 10.1 prépare toutes les grilles
    freqs, Tgrid, zgrid, Rgrid = build_T_z_R_grids(fmin, fmax, dlog, args.npts)

    # 10.2 charge les jalons
    jalon_path = ensure_jalons(Path(args.copy_jalons) if args.copy_jalons else None)
    jalons = (
        pd.read_csv(jalon_path)
        .rename(columns=str.strip)
        .query("R_over_R0>0")
        .drop_duplicates("R_over_R0")
        .sort_values("R_over_R0")
    )

    # 10.3 calcul de stabilité
    df_R, domaine, frontiere = calculer_stabilite(jalons, Rgrid)

    # 10.4 exports principaux
    exporter_csv(df_R, domaine, frontiere, args.dry_run)

    # 10.5 exports inverses ricci↔z et ricci↔T
    exporter_jalons_inverses(df_R, jalons, zgrid, Tgrid, args.dry_run)

    log.info("Pipeline Chapitre 3 terminé.")


if __name__ == "__main__":
    main()
