# mcgt/phase.py
# -----------------------------------------------------------------------------
"""
mcgt.phase
==========

Module central pour le calcul de la phase fréquentielle MCGT.

Fonctions exposées
------------------
- PhaseParams            : dataclass des paramètres physiques / numériques
- build_loglin_grid()    : grille log–uniforme entre fmin et fmax
- check_log_spacing()    : validation de l’espacement log uniforme
- phi_gr()               : phase GR (SPA) jusqu’à 3.5-PN (approximation)
- corr_phase()           : correcteur analytique δφ(f) = ∫δt(f) df
- solve_mcgt()           : phase MCGT = φ_GR − δφ
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from mcgt.constants import G_SI

__all__ = [
    "PhaseParams",
    "build_loglin_grid",
    "check_log_spacing",
    "phi_gr",
    "corr_phase",
    "solve_mcgt",
]


# ----------------------------------------------------------------------#
# 0. Dataclass des paramètres
# ----------------------------------------------------------------------#
@dataclass
class PhaseParams:
    m1: float  # masse primaire [M☉]
    m2: float  # masse secondaire [M☉]
    q0star: float  # amplitude du correcteur MCGT
    alpha: float  # exposant α (param2)
    phi0: float = 0.0  # phase initiale à fmin [rad]
    tc: float = 0.0  # temps de coalescence t_c [s]
    tol: float = 1e-8  # tolérance numérique


# ----------------------------------------------------------------------#
# 1. Outils grille log–uniforme
# ----------------------------------------------------------------------#
def build_loglin_grid(fmin: float, fmax: float, dlog: float) -> np.ndarray:
    """Grille log-uniforme entre fmin et fmax avec pas Δlog₁₀=dlog (bornes incluses)."""
    if not (fmax > fmin > 0.0):
        raise ValueError("Exige fmax > fmin > 0.")
    if dlog <= 0.0:
        raise ValueError("Exige dlog > 0.")
    logf_min = np.log10(float(fmin))
    logf_max = np.log10(float(fmax))
    n = int(np.floor((logf_max - logf_min) / dlog)) + 1
    grid = 10 ** (logf_min + np.arange(n) * dlog)
    # garantir l’inclusion exacte de fmax si la division tombe pile
    if grid[-1] < fmax * (1 - 1e-14):
        grid = np.append(grid, fmax)
    return grid.astype(float)


def check_log_spacing(grid: np.ndarray, atol: float = 1e-12) -> bool:
    """Vérifie que Δlog₁₀ est (quasi) constant sur la grille (tolérance = atol)."""
    g = G_SI
    if g.ndim != 1 or g.size < 2 or not np.all(np.diff(g) > 0):
        return False
    logg = np.log10(g)
    diff = np.diff(logg)
    return np.allclose(diff, diff[0], atol=atol, rtol=0.0)


# ----------------------------------------------------------------------#
# 2. Coefficients PN (0 → 3.5 PN) — schéma simple (illustratif)
# ----------------------------------------------------------------------#
_CPN = {
    0: 1.0,
    2: (3715 / 756 + 55 / 9),  # coefficients simplifiés
    3: -16 * np.pi,
    4: (15293365 / 508032 + 27145 / 504 + 3085 / 72),
    5: np.pi * (38645 / 756 - 65 / 9) * (1 + 3 * np.log(np.pi)),
    6: (
        11583231236531 / 4694215680 - 640 / 3 * np.pi**2 - 6848 / 21 * np.log(4 * np.pi)
    ),
    7: np.pi * (77096675 / 254016 + 378515 / 1512),
}


def _symmetric_eta(m1: float, m2: float) -> float:
    """Rapport de masse symétrique η = m1 m2 / (m1+m2)^2 (∈ (0,0.25])."""
    return m1 * m2 / (m1 + m2) ** 2


# ----------------------------------------------------------------------#
# 3. Phase GR en Stationary-Phase Approximation (SPA)
# ----------------------------------------------------------------------#
def phi_gr(freqs: np.ndarray, p: PhaseParams) -> np.ndarray:
    """
    Phase fréquentielle GR (SPA) jusqu’à 3.5-PN (schéma illustratif).

    Parameters
    ----------
    freqs : np.ndarray
        Grille 1-D de fréquences (Hz), strictement croissante.
    p : PhaseParams
        Paramètres physiques incluant masses, tc, phi0.

    Returns
    -------
    np.ndarray
        Phase φ_GR(f) en radians.
    """
    freqs = np.asarray(freqs, dtype=float)
    if freqs.ndim != 1 or not np.all(np.diff(freqs) > 0):
        raise ValueError("La grille freqs doit être 1D et strictement croissante.")

    # Conversion masse solaire → secondes (G = c = 1)
    M_s = (p.m1 + p.m2) * 4.925490947e-6  # masse totale (s)
    eta = _symmetric_eta(p.m1, p.m2)
    v = (np.pi * M_s * freqs) ** (1 / 3)  # vitesse PN

    # Série PN
    series = np.zeros_like(freqs)
    for k, c_k in _CPN.items():
        series += c_k * v**k
    prefac = 3 / (128 * eta) * v ** (-5)

    return 2 * np.pi * freqs * p.tc - p.phi0 - np.pi / 4 + prefac * series


# ----------------------------------------------------------------------#
# 4. Correcteur analytique δφ (δt(f) = q0★ · f^(−α))
# ----------------------------------------------------------------------#
def corr_phase(
    freqs: np.ndarray, fmin: float, q0star: float, alpha: float
) -> np.ndarray:
    """
    Correction δφ(f) induite par un décalage temporel δt(f)=q0★·f^(−α).

    cas α=1 : δφ(f) = 2π q0★ ln(f/fmin)
    cas α≠1 : δφ(f) = 2π q0★/(1−α) [ f^(1−α) − fmin^(1−α) ]
    """
    freqs = np.asarray(freqs, dtype=float)
    if np.isclose(alpha, 1.0):
        return 2 * np.pi * q0star * np.log(freqs / fmin)
    return (2 * np.pi * q0star / (1 - alpha)) * (
        freqs ** (1 - alpha) - fmin ** (1 - alpha)
    )


# ----------------------------------------------------------------------#
# 5. Solveur global MCGT
# ----------------------------------------------------------------------#
def solve_mcgt(
    freqs: np.ndarray, p: PhaseParams, fmin: float | None = None
) -> np.ndarray:
    """
    Calcule la phase MCGT sur `freqs` :

        φ_MCGT(f) = φ_GR(f) − δφ(f)

    Paramètres
    ----------
    freqs : np.ndarray
        Grille (Hz), strictement croissante.
    p : PhaseParams
        Paramètres physiques et numériques.
    fmin : float, optional
        Référence f_min pour δφ. Si None, on prend freqs[0].

    Retour
    ------
    np.ndarray
        Phase φ_MCGT(f) en radians.
    """
    freqs = np.asarray(freqs, dtype=float)
    if freqs.ndim != 1 or not np.all(np.diff(freqs) > 0):
        raise ValueError("La grille freqs doit être 1D et strictement croissante.")
    f0 = float(freqs[0] if fmin is None else fmin)

    phi_ref = phi_gr(freqs, p)
    delta = corr_phase(freqs, f0, p.q0star, p.alpha)
    return phi_ref - delta
