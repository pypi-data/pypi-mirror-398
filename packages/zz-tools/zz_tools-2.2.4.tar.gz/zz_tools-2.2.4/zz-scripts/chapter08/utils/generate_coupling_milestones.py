#!/usr/bin/env python3
# === [PASS5-AUTOFIX-SHIM] ===
if __name__ == "__main__":
    try:
        import sys
        import os
        import atexit

        _argv = sys.argv[1:]
        # 1) Shim --help universel
        if any(a in ("-h", "--help") for a in _argv):
            import argparse

            _p = argparse.ArgumentParser(
                description="MCGT (shim auto-injecté Pass5)",
                add_help=True,
                allow_abbrev=False,
            )
            _p.add_argument(
                "--out", help="Chemin de sortie pour fig.savefig (optionnel)"
            )
            _p.add_argument(
                "--dpi", type=int, default=120, help="DPI (par défaut: 120)"
            )
            _p.add_argument(
                "--show",
                action="store_true",
                help="Force plt.show() en fin d'exécution",
            )
            # parse_known_args() affiche l'aide et gère les options de base
            _p.parse_known_args()
            sys.exit(0)
        # 2) Shim sauvegarde figure si --out présent (sans bloquer)
        _out = None
        if "--out" in _argv:
            try:
                i = _argv.index("--out")
                _out = _argv[i + 1] if i + 1 < len(_argv) else None
            except Exception:
                _out = None
        if _out:
            os.environ.setdefault("MPLBACKEND", "Agg")
            try:
                import matplotlib.pyplot as plt

                # Neutralise show() pour éviter le blocage en headless
                def _shim_show(*a, **k):
                    pass

                plt.show = _shim_show
                # Récupère le dpi si fourni
                _dpi = 120
                if "--dpi" in _argv:
                    try:
                        _dpi = int(_argv[_argv.index("--dpi") + 1])
                    except Exception:
                        _dpi = 120

                @atexit.register
                def _pass5_save_last_figure():
                    try:
                        fig = plt.gcf()
                        fig.savefig(_out, dpi=_dpi)
                        print(f"[PASS5] Wrote: {_out}")
                    except Exception as _e:
                        print(f"[PASS5] savefig failed: {_e}")
            except Exception:
                # matplotlib indisponible: ignorer silencieusement
                pass
    except Exception:
        # N'empêche jamais le script original d'exécuter
        pass
# === [/PASS5-AUTOFIX-SHIM] ===
import os

import pandas as pd

# Répertoires
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../zz-data/chapter08"))

# 1) Charger BAO depuis le CSV final
df_bao = pd.read_csv(os.path.join(DATA_DIR, "08_bao_data.csv"))
df_bao = df_bao.rename(columns={"DV_obs": "obs", "sigma_DV": "sigma_obs"})
df_bao["jalon"] = df_bao["z"].apply(lambda z: f"BAO_z={z:.3f}")
df_bao["classe"] = df_bao.apply(
    lambda row: "primaire" if row.sigma_obs / row.obs <= 0.01 else "ordre2", axis=1
)

# 2) Charger Pantheon+ depuis le CSV final
df_sn = pd.read_csv(os.path.join(DATA_DIR, "08_pantheon_data.csv"))
df_sn = df_sn.rename(columns={"mu_obs": "obs", "sigma_mu": "sigma_obs"})
# Création du libellé SN0, SN1, …
df_sn["jalon"] = df_sn.index.map(lambda i: f"SN{i}")
df_sn["classe"] = df_sn.apply(
    lambda row: "primaire" if row.sigma_obs / row.obs <= 0.01 else "ordre2", axis=1
)

# 3) Concaténer et ordonner les colonnes
df_all = pd.concat(
    [
        df_bao[["jalon", "z", "obs", "sigma_obs", "classe"]],
        df_sn[["jalon", "z", "obs", "sigma_obs", "classe"]],
    ],
    ignore_index=True,
)

# 4) Exporter le CSV final
out_csv = os.path.join(DATA_DIR, "08_coupling_milestones.csv")
df_all.to_csv(out_csv, index=False, encoding="utf-8")
print(f"✅ 08_coupling_milestones.csv généré : {out_csv}")
