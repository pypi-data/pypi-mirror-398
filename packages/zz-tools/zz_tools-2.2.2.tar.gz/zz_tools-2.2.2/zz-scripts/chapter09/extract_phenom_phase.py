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
"""
zz-scripts/chapter09/extract_phenom_phase.py

Génère 09_phases_imrphenom.csv :
– f_Hz    : fréquence (Hz) sur grille log-lin
– phi_ref : phase IMRPhenomD (radians)
"""

import argparse

import numpy as np
import pandas as pd
from pycbc.waveform import get_fd_waveform


def parse_args():
    p = argparse.ArgumentParser(
        description="Extraire la phase de référence IMRPhenomD (PyCBC)"
    )
    p.add_argument("--fmin", type=float, required=True, help="Fréquence minimale (Hz)")
    p.add_argument("--fmax", type=float, required=True, help="Fréquence maximale (Hz)")
    p.add_argument("--dlogf", type=float, required=True, help="Pas Δlog10(f)")
    p.add_argument("--m1", type=float, required=True, help="Masse primaire (M☉)")
    p.add_argument("--m2", type=float, required=True, help="Masse secondaire (M☉)")
    p.add_argument("--phi0", type=float, default=0.0, help="Phase initiale φ0 (rad)")
    p.add_argument("--dist", type=float, required=True, help="Distance (Mpc)")
    p.add_argument(
        "--outcsv",
        type=str,
        default="09_phases_imrphenom.csv",
        help="Nom du fichier CSV de sortie",
    )
    return p.parse_args()


def main():
    args = parse_args()

    # Conversion unités
    m1 = args.m1
    m2 = args.m2
    distance = args.dist

    # Générer le waveform fréquentiel
    hp, hc = get_fd_waveform(
        approximant="IMRPhenomD",
        mass1=m1,
        mass2=m2,
        spin1z=0.0,
        spin2z=0.0,
        delta_f=10 ** (np.log10(args.fmin + args.dlogf) - np.log10(args.fmin))
        * args.fmin,
        f_lower=args.fmin,
        f_final=args.fmax,
        distance=distance,
        phi0=args.phi0,
    )

    # Récupérer fréquences et phases
    freqs = hp.sample_frequencies.numpy()
    phase = np.unwrap(np.angle(hp.numpy()))

    # Filtrer la grille log-lin manuellement si nécessaire
    # Ici on suppose que PyCBC renvoie une grille lin-équidistante en delta_f
    # Pour une grille log-lin, on reconstruirait la grille :
    # freqs = 10**np.arange(np.log10(args.fmin), np.log10(args.fmax)+1e-12, args.dlogf)
    # phase = np.interp(freqs, hp.sample_frequencies, np.unwrap(np.angle(hp)))

    # Sauvegarder en CSV
    df = pd.DataFrame({"f_Hz": freqs, "phi_ref": phase})
    df.to_csv(args.outcsv, index=False, float_format="%.8e", encoding="utf-8")
    print(f"Écrit : {args.outcsv}")


if __name__ == "__main__":
    main()
