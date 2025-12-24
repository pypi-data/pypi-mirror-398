#!/usr/bin/env python3
"""Fig. 04 – Écarts relatifs des invariants I2 et I3 (Chapter 04)."""

from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import tempfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import LogLocator

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
ROOT = Path(__file__).resolve().parents[2]
DATA_CSV = ROOT / "zz-data" / "chapter04" / "04_dimensionless_invariants.csv"
OUT_FIG = ROOT / "zz-figures" / "chapter04" / "04_fig_04_relative_deviations.png"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_save(filepath, fig=None, **savefig_kwargs):
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with tempfile.NamedTemporaryFile(delete=False, suffix=path.suffix) as tmp:
            tmp_path = Path(tmp.name)
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


def _load_csv(possible_paths: list[Path]) -> tuple[pd.DataFrame, Path]:
    for p in possible_paths:
        if p.is_file():
            return pd.read_csv(p), p
    raise FileNotFoundError(f"Aucun CSV trouvé parmi : {possible_paths}")


def main() -> None:
    df, used_path = _load_csv(
        [DATA_CSV, Path("/mnt/data/04_dimensionless_invariants.csv")]
    )
    print(f"Chargé {used_path}")

    needed = {"T_Gyr", "I2", "I3"}
    missing = sorted(needed - set(df.columns))
    if missing:
        raise KeyError(f"Colonnes manquantes dans {used_path}: {missing}")

    T = df["T_Gyr"].to_numpy(float)
    I2 = df["I2"].to_numpy(float)
    I3 = df["I3"].to_numpy(float)

    I2_ref = 1e-35
    I3_ref = 1e-6

    eps2 = (I2 - I2_ref) / I2_ref
    eps3 = (I3 - I3_ref) / I3_ref

    tol = 0.10
    # Debug: show raw values without masking to inspect full range
    eps2_plot = eps2
    eps3_plot = eps3

    Tp = 0.087  # Gyr

    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.set_xscale("log")

    # Keep eps3 above to avoid visual gaps when NaNs are masked
    ax.plot(
        T,
        eps2_plot,
        label=r"$\varepsilon_2=\frac{I_2-I_{2,\mathrm{ref}}}{I_{2,\mathrm{ref}}}$",
        zorder=2,
        linewidth=2.5,
        alpha=0.8,
    )
    ax.plot(
        T,
        eps3_plot,
        label=r"$\varepsilon_3=\frac{I_3-I_{3,\mathrm{ref}}}{I_{3,\mathrm{ref}}}$",
        zorder=3,
        linewidth=2.5,
        alpha=0.8,
    )

    ax.axhline(0.01, color="k", linestyle="--", label=r"$\pm1\%$")
    ax.axhline(-0.01, color="k", linestyle="--")
    ax.axhline(0.10, color="gray", linestyle=":", label=r"$\pm10\%$")
    ax.axhline(-0.10, color="gray", linestyle=":")
    ax.axvline(Tp, linestyle=":", label=rf"$T_p = {Tp:.3f}\ \mathrm{{Gyr}}$")

    ax.set_yscale("symlog", linthresh=0.1)
    ax.set_ylim(-2, 1e7)
    ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=range(1, 10)))
    ax.xaxis.set_tick_params(which="minor", length=3)

    ax.set_xlabel(r"$T$ [Gyr]")
    ax.set_ylabel(r"$\varepsilon_i$")
    ax.set_title(r"Relative Deviations of Invariants $I_2$ and $I_3$", pad=26)

    ax.grid(True, which="both", linestyle=":", linewidth=0.5, zorder=0)
    ax.legend(fontsize="small", loc="lower left", bbox_to_anchor=(0.02, 0.02))

    safe_save(OUT_FIG, fig=fig, dpi=300)
    print(f"Figure sauvegardée : {OUT_FIG}")


if __name__ == "__main__":
    main()
