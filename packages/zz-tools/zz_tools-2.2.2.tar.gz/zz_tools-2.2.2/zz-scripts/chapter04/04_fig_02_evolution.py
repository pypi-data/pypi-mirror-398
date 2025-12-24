#!/usr/bin/env python3
"""Fig. 02 – Scalar field evolution φ(T)."""

import hashlib
import shutil
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

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
DATA_FILE = ROOT / "zz-data" / "chapter04" / "04_P_vs_T.dat"
FIG_PATH = ROOT / "zz-figures" / "chapter04" / "04_fig_02_evolution.png"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_save(filepath: Path, fig=None, **savefig_kwargs) -> bool:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    if filepath.exists():
        with tempfile.NamedTemporaryFile(delete=False, suffix=filepath.suffix) as tmp:
            tmp_path = Path(tmp.name)
        try:
            (fig or plt).savefig(tmp_path, **savefig_kwargs)
            if _sha256(tmp_path) == _sha256(filepath):
                tmp_path.unlink()
                return False
            shutil.move(tmp_path, filepath)
            return True
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
    (fig or plt).savefig(filepath, **savefig_kwargs)
    return True


def main() -> None:
    df = pd.read_csv(DATA_FILE, delim_whitespace=True)
    T = df.iloc[:, 0].to_numpy(dtype=float)
    phi = df.iloc[:, 1].to_numpy(dtype=float)

    fig, ax = plt.subplots(dpi=300)
    ax.plot(T, phi, label="Optimized Field", color="tab:orange", linewidth=1.8)
    ax.plot(T, phi, linestyle="--", color="gray", linewidth=1.2, label="Initial Field")

    ax.set_xscale("log")
    ax.set_xlabel(r"$T$ [Gyr]")
    ax.set_ylabel(r"$\phi(T)$")
    ax.set_title(r"Scalar Field Evolution $\phi(T)$")
    ax.grid(True, which="both", linestyle=":", linewidth=0.6)
    ax.legend(loc="best")

    safe_save(FIG_PATH, fig)
    plt.close(fig)
    print(f"Saved figure → {FIG_PATH}")


if __name__ == "__main__":
    main()
