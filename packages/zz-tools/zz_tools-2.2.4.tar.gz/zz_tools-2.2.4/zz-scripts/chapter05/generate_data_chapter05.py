import os
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
from scipy.signal import savgol_filter

# — Répertoires —
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "zz-data" / "chapter05"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# — Fichiers d’entrée et de sortie (noms harmonisés en anglais) —
JALONS_FILE = DATA_DIR / "05_bbn_milestones.csv"
GRILLE_FILE = DATA_DIR / "05_bbn_grid.csv"
PRED_FILE = DATA_DIR / "05_bbn_data.csv"
CHI2_FILE = DATA_DIR / "05_chi2_bbn_vs_T.csv"
DERIV_FILE = DATA_DIR / "05_dchi2_vs_T.csv"
PARAMS_FILE = DATA_DIR / "05_bbn_params.json"

# Seuils de classification (relative error)
THRESHOLDS = {"primary": 0.01, "order2": 0.10}


def main(args=None) -> None:
    """Génère les grilles BBN, les prédictions et les métriques associées."""

    # 1) Chargement des jalons
    jalons = pd.read_csv(JALONS_FILE)
    # Tri global en T_Gyr pour garantir un ordre croissant
    jalons = jalons.sort_values("T_Gyr")

    # Sous-ensembles nettoyés : on enlève les NaN et on déduplique T_Gyr
    jalons_DH = jalons.dropna(subset=["DH_obs"]).drop_duplicates(subset=["T_Gyr"])
    jalons_Yp = jalons.dropna(subset=["Yp_obs"]).drop_duplicates(subset=["T_Gyr"])

    # Sanity checks minimaux
    if len(jalons_DH) < 2:
        raise ValueError(
            "Besoin d'au moins deux jalons avec DH_obs pour l'interpolation PCHIP."
        )
    if len(jalons_Yp) == 0:
        raise ValueError("Aucun jalon avec Yp_obs trouvé dans 05_bbn_milestones.csv.")

    # 2) Construction de la grille logarithmique en T [Gyr]
    t_min, t_max = 1e-6, 14.0
    log_min, log_max = np.log10(t_min), np.log10(t_max)
    step = 0.01
    num = int(round((log_max - log_min) / step)) + 1
    T = np.logspace(log_min, log_max, num=num)
    pd.DataFrame({"T_Gyr": T}).to_csv(GRILLE_FILE, index=False)

    # 3) Interpolations monotones (PCHIP) en log–log

    # Deutérium
    x_DH = np.log10(jalons_DH["T_Gyr"].to_numpy())
    y_DH = np.log10(jalons_DH["DH_obs"].to_numpy())
    interp_DH = PchipInterpolator(x_DH, y_DH, extrapolate=True)
    DH_calc = 10 ** interp_DH(np.log10(T))

    # Hélium-4
    if len(jalons_Yp) > 1:
        x_Yp = np.log10(jalons_Yp["T_Gyr"].to_numpy())
        y_Yp = np.log10(jalons_Yp["Yp_obs"].to_numpy())
        interp_Yp = PchipInterpolator(x_Yp, y_Yp, extrapolate=True)
        Yp_calc = 10 ** interp_Yp(np.log10(T))
    else:
        # Si un seul point, on met une constante
        Yp_calc = np.full_like(T, jalons_Yp["Yp_obs"].iloc[0])

    # 4) Sauvegarde des prédictions
    df_pred = pd.DataFrame(
        {
            "T_Gyr": T,
            "DH_calc": DH_calc,
            "Yp_calc": Yp_calc,
        }
    )
    df_pred.to_csv(PRED_FILE, index=False)

    # 5) Calcul du χ² total (DH + Yp)
    chi2_vals: list[float] = []
    for dh_c, yp_c in zip(DH_calc, Yp_calc, strict=False):
        c1 = ((dh_c - jalons_DH["DH_obs"]) ** 2 / jalons_DH["sigma_DH"] ** 2).sum()
        c2 = ((yp_c - jalons_Yp["Yp_obs"]) ** 2 / jalons_Yp["sigma_Yp"] ** 2).sum()
        chi2_vals.append(float(c1 + c2))

    pd.DataFrame({"T_Gyr": T, "chi2_nucleosynthesis": chi2_vals}).to_csv(
        CHI2_FILE, index=False
    )

    # 6) Dérivée et lissage de χ²
    dchi2_raw = np.gradient(chi2_vals, T)
    # Fenêtre impaire ≤ 21 pour éviter oversmoothing
    win = min(21, (len(dchi2_raw) // 2) * 2 + 1)
    dchi2_smooth = savgol_filter(dchi2_raw, win, polyorder=3, mode="interp")
    pd.DataFrame({"T_Gyr": T, "dchi2_smooth": dchi2_smooth}).to_csv(
        DERIV_FILE, index=False
    )

    # 7) Calcul des tolérances ε = |pred–obs|/obs
    eps_records: list[dict[str, float]] = []

    for _, row in jalons.iterrows():
        if pd.notna(row.get("DH_obs")):
            dh_pred = 10 ** interp_DH(np.log10(row["T_Gyr"]))
            eps = abs(dh_pred - row["DH_obs"]) / row["DH_obs"]
            eps_records.append(
                {
                    "epsilon": float(eps),
                    "sigma_rel": float(row["sigma_DH"] / row["DH_obs"]),
                }
            )

        if pd.notna(row.get("Yp_obs")):
            if len(jalons_Yp) > 1:
                yp_pred = 10 ** interp_Yp(np.log10(row["T_Gyr"]))
            else:
                yp_pred = jalons_Yp["Yp_obs"].iloc[0]
            eps = abs(yp_pred - row["Yp_obs"]) / row["Yp_obs"]
            eps_records.append(
                {
                    "epsilon": float(eps),
                    "sigma_rel": float(row["sigma_Yp"] / row["Yp_obs"]),
                }
            )

    df_eps = pd.DataFrame(eps_records)
    max_e1 = df_eps[df_eps["sigma_rel"] <= THRESHOLDS["primary"]]["epsilon"].max()
    max_e2 = df_eps[
        (df_eps["sigma_rel"] > THRESHOLDS["primary"])
        & (df_eps["sigma_rel"] <= THRESHOLDS["order2"])
    ]["epsilon"].max()

    # 8) Sauvegarde des paramètres
    with open(PARAMS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "max_epsilon_primary": float(max_e1) if not pd.isna(max_e1) else None,
                "max_epsilon_order2": float(max_e2) if not pd.isna(max_e2) else None,
            },
            f,
            indent=2,
        )

    print("✓ Chapitre 05 : données générées avec succès.")


# === MCGT CLI SEED v2 ===
if __name__ == "__main__":

    def _mcgt_cli_seed() -> None:
        import argparse
        import sys
        import traceback
        import matplotlib as mpl

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
            "--seed",
            type=int,
            default=None,
            help="Graine aléatoire (optionnelle).",
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
            "--dpi",
            type=int,
            default=150,
            help="Figure DPI (default: 150)",
        )
        parser.add_argument(
            "--format",
            choices=["png", "pdf", "svg"],
            default="png",
            help="Figure format",
        )
        parser.add_argument(
            "--transparent",
            action="store_true",
            help="Transparent background",
        )

        args = parser.parse_args()

        # Préparation générique de l'environnement (optionnelle pour ce script)
        os.makedirs(args.outdir, exist_ok=True)
        os.environ["MCGT_OUTDIR"] = args.outdir

        mpl.rcParams["savefig.dpi"] = args.dpi
        mpl.rcParams["savefig.format"] = args.format
        mpl.rcParams["savefig.transparent"] = args.transparent

        try:
            main(args)
        except SystemExit:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"[CLI seed] main() a levé: {e}", file=sys.stderr)
            traceback.print_exc()
            sys.exit(1)

    _mcgt_cli_seed()
