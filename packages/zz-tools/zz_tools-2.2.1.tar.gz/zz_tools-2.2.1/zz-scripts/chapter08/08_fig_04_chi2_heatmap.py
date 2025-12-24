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

"""
zz-scripts/chapter08/plot_fig04_chi2_heatmap.py
Carte de chaleur χ2(q0⋆, p2) avec contours de confiance
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LogNorm

# --- chemins ---
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "zz-data" / "chapter08"
FIG_DIR = ROOT / "zz-figures" / "chapter08"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# --- importer le scan 2D ---
csv2d = DATA_DIR / "08_chi2_scan2D.csv"
if not csv2d.exists():
    raise FileNotFoundError(f"Scan 2D χ2 introuvable : {csv2d}")
df = pd.read_csv(csv2d)

# extraire les grilles
p1 = np.sort(df["q0star"].unique())
p2 = np.sort(df["param2"].unique())

# pivoter en matrice
M = df.pivot(index="param2", columns="q0star", values="chi2").loc[p2, p1].values

# calculer les bords pour pcolormesh
dp1 = np.diff(p1).mean()
dp2 = np.diff(p2).mean()
x_edges = np.concatenate([p1 - dp1 / 2, [p1[-1] + dp1 / 2]])
y_edges = np.concatenate([p2 - dp2 / 2, [p2[-1] + dp2 / 2]])

# trouver le minimum global
i_min, j_min = np.unravel_index(np.argmin(M), M.shape)
q0_min = p1[j_min]
p2_min = p2[i_min]
chi2_min = M[i_min, j_min]

# tracer
plt.rcParams.update({"font.size": 12})
fig, ax = plt.subplots(figsize=(7.5, 5.0))

# heatmap en lognorm pour renforcer le contraste
pcm = ax.pcolormesh(
    x_edges,
    y_edges,
    M,
    norm=LogNorm(vmin=M.min(), vmax=M.max()),
    cmap="viridis",
    shading="auto",
)

# contours de confiance Δχ² = 2.30, 6.17, 11.8 (68%, 95%, 99.7% pour 2 paramètres)
levels = chi2_min + np.array([2.30, 6.17, 11.8])
cont = ax.contour(
    p1,
    p2,
    M,
    levels=levels,
    colors="white",
    linestyles=["-", "--", ":"],
    linewidths=1.2,
)
ax.clabel(
    cont,
    fmt={lvl: f"{int(lvl - chi2_min)}" for lvl in levels},
    inline=True,
    fontsize=10,
)
# Décale légèrement les étiquettes de niveaux pour éviter la superposition
label_offset = 0.015 * (p1.max() - p1.min())
for lbl in cont.labelTexts:
    x, y = lbl.get_position()
    lbl.set_position((x + label_offset, y))
    lbl.set_ha("left")

# point du minimum
ax.plot(q0_min, p2_min, "o", color="black", ms=6)

# annotation du minimum
bbox = dict(boxstyle="round,pad=0.4", fc="white", ec="gray", alpha=0.8)
txt = (
    rf"$\min \chi^2 = {chi2_min:.1f}$"
    + "\n"
    + rf"$q_0^\star = {q0_min:.3f}$"
    + "\n"
    + rf"$p_2 = {p2_min:.3f}$"
)
ax.text(0.98, 0.95, txt, transform=ax.transAxes, va="top", ha="right", bbox=bbox)

# axes et titre

ax.set_xlabel(r"$q_0^\star$")
ax.set_ylabel(r"$p_2$")
ax.set_title(r"$\chi^2$ Heatmap (2D Scan)")

# quadrillage discret
ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.5)

# colorbar ajustée
cbar = fig.colorbar(pcm, ax=ax, extend="both")
cbar.set_label(r"$\chi^2$ (log)", labelpad=10)
cbar.ax.yaxis.set_label_position("right")
cbar.ax.tick_params(labelsize=10)

fig.subplots_adjust(left=0.04, right=0.98, bottom=0.06, top=0.96)
safe_save(FIG_DIR / "08_fig_04_chi2_heatmap.png", dpi=300)
print(f"✅ fig_04_chi2_heatmap.png générée dans {FIG_DIR}")

# === MCGT CLI SEED v2 ===

if __name__ == "__main__":
    # CLI simplifiée pour le pipeline minimal : le tracé est exécuté au
    # niveau top-level, ici on se contente de configurer le dossier de sortie
    # via MCGT_OUTDIR pour rester homogène avec les autres scripts.
    import argparse

    parser = argparse.ArgumentParser(
        description="Entry point fig_04 χ² heatmap – pipeline minimal."
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
