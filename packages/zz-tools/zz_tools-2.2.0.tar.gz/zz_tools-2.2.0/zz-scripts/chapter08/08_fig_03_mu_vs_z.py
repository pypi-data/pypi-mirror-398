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
import os
# plot_fig03_mu_vs_z.py
# ---------------------------------------------------------------
# Plot μ_obs(z) vs μ_th(z) for Chapter 8 (Dark coupling) of the MCGT project
# ---------------------------------------------------------------

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# -- Chemins
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "zz-data" / "chapter08"
FIG_DIR = ROOT / "zz-figures" / "chapter08"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# -- Chargement des données
pantheon = pd.read_csv(DATA_DIR / "08_pantheon_data.csv", encoding="utf-8")
theory = pd.read_csv(DATA_DIR / "08_mu_theory_z.csv", encoding="utf-8")
params = json.loads((DATA_DIR / "08_coupling_params.json").read_text(encoding="utf-8"))
q0star = params.get("q0star_optimal", None)  # ou autre clé selon ton JSON

# -- Tri par redshift
pantheon = pantheon.sort_values("z")
theory = theory.sort_values("z")

# -- Configuration du tracé
plt.rcParams.update({"font.size": 11})
fig, ax = plt.subplots(figsize=(6.5, 4.5))

# -- Observations avec barres d'erreur
ax.errorbar(
    pantheon["z"],
    pantheon["mu_obs"],
    yerr=pantheon["sigma_mu"],
    fmt="o",
    markersize=5,
    capsize=3,
    label="Pantheon + obs",
)

# -- Courbe théorique
label_th = (
    rf"$\mu^{{\rm th}}(z; q_0^*={q0star:.3f})$"
    if q0star is not None
    else r"$\mu^{\rm th}(z)$"
)
ax.semilogx(theory["z"], theory["mu_calc"], "-", lw=2, label=label_th)

# -- Labels & titre
ax.set_xlabel("Redshift $z$")
ax.set_ylabel(r"Distance modulaire $\mu$\;[mag]")
ax.set_title(r"Comparaison $\mu^{\rm obs}$ vs $\mu^{\rm th}$")

# -- Grille & légende
ax.grid(which="both", ls=":", lw=0.5, alpha=0.6)
ax.legend(loc="lower right")

# -- Mise en page & sauvegarde
fig.subplots_adjust(left=0.04, right=0.98, bottom=0.06, top=0.96)
safe_save(FIG_DIR / "08_fig_03_mu_vs_z.png", dpi=300)
print("✅ fig_03_mu_vs_z.png générée dans", FIG_DIR)

# === MCGT CLI SEED v2 ===

if __name__ == "__main__":
    # CLI simplifiée pour le pipeline minimal : on ne rappelle pas la logique
    # (le tracé est déjà exécuté au niveau top-level), on se contente de
    # configurer le dossier de sortie via MCGT_OUTDIR.
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Entry point fig_03 μ(z) – pipeline minimal."
    )
    parser.add_argument(
        "--outdir",
        default=os.environ.get("MCGT_OUTDIR", str(FIG_DIR)),
        help="Dossier de sortie (défaut: MCGT_OUTDIR ou zz-figures/chapter08).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Niveau de verbosité (-v, -vv).",
    )

    args = parser.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    os.environ["MCGT_OUTDIR"] = args.outdir
