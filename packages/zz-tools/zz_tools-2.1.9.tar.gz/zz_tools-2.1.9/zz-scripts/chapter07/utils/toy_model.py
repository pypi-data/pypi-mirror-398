"""Toy model de démonstration pour le Chapitre 07.

Ce script ne dépend d’aucune donnée externe : il génère une courbe jouet
en fonction de k et enregistre une figure PNG. Il est volontairement simple
pour servir de cible de test dans homog_smoke.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def build_toy_model(k: np.ndarray) -> np.ndarray:
    """Retourne une courbe jouet lisse, bornée entre 0 et 1."""
    # simple sigmoïde log10(k)
    return 0.5 * (1.0 + np.tanh(np.log10(k + 1e-6)))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Toy model pour les perturbations scalaires (Chapitre 07)."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("zz-out/smoke/chapter07/utils/toy_model.png"),
        help="Chemin de sortie pour la figure (PNG).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=96,
        help="Résolution de la figure (dots per inch).",
    )
    args = parser.parse_args()

    # Assure que le répertoire de sortie existe
    args.out.parent.mkdir(parents=True, exist_ok=True)

    # Grille en k (log-uniforme)
    k = np.logspace(-4, 0, 128)
    y = build_toy_model(k)

    # Figure
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(k, y)
    ax.set_xscale("log")
    ax.set_xlabel(r"$k$")
    ax.set_ylabel(r"toy(k)")
    ax.set_title("Toy model – Chapitre 07")
    fig.tight_layout()

    fig.savefig(args.out, dpi=args.dpi)


if __name__ == "__main__":
    main()
