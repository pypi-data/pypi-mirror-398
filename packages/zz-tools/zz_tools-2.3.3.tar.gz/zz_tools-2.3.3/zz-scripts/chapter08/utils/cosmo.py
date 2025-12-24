# cosmo.py
# Version robuste pour Chapitre 8 Couplage sombre – MCGT

import numpy as np
from scipy.integrate import quad

from mcgt.constants import H0_KM_S_PER_MPC as H0  # unified

# Constantes cosmologiques de référence
# H0 unifié → import
c_kms = 299792.458  # km/s
Omega_m0 = 0.3111
Omega_lambda0 = 0.6889

# Valeurs de tolérance
_EPS = 1e-8
_MAX_CHI2 = 1e8
_INT_EPSABS = 1e-8
_INT_EPSREL = 1e-8


def Hubble(z, q0star=0.0):
    """
    H(z) = H0 * sqrt( Omega_m*(1+z)^3 + q0*(1+z)^2 + Omega_lambda )
    Avec clamp pour garantir positivité.
    """
    inside = Omega_m0 * (1 + z) ** 3 + q0star * (1 + z) ** 2 + Omega_lambda0
    # Éviter underflow/overflow et négatif sous la racine
    inside = np.maximum(inside, _EPS)
    return H0 * np.sqrt(inside)


def comoving_distance(z, q0star=0.0):
    """
    ∫_0^z [c / H(z')] dz' en Mpc, avec gestion d'erreur.
    """
    if z <= 0:
        return 0.0

    def integrand(zp):
        return c_kms / Hubble(zp, q0star)

    try:
        dc, err = quad(
            integrand, 0.0, z, epsabs=_INT_EPSABS, epsrel=_INT_EPSREL, limit=200
        )
        return dc
    except Exception:
        return _MAX_CHI2


def lum_distance(z, q0star=0.0):
    dc = comoving_distance(z, q0star)
    return dc * (1 + z)


def distance_modulus(z, q0star=0.0):
    dl = lum_distance(z, q0star)
    if not np.isfinite(dl) or dl <= 0:
        return 5 * np.log10(_MAX_CHI2) + 25
    return 5.0 * np.log10(dl) + 25.0


def DV(z, q0star=0.0):
    """
    DV ≡ [ (1+z)^2 D_A^2 c z / H(z) ]^(1/3), avec D_A = DC/(1+z).
    """
    if z <= 0:
        return 0.0
    dc = comoving_distance(z, q0star)
    Hz = Hubble(z, q0star)
    if not np.isfinite(dc) or not np.isfinite(Hz) or Hz <= 0:
        return _MAX_CHI2
    DA = dc / (1 + z)
    factor = (1 + z) ** 2 * DA**2 * (c_kms * z / Hz)
    factor = np.maximum(factor, _EPS)
    return factor ** (1 / 3)


# Self-test rapide
if __name__ == "__main__":
    for q in [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0]:
        for z in [0.1, 0.5, 1.0, 2.0]:
            dv = DV(z, q)
            mu = distance_modulus(z, q)
            print(f"q0={q:+.2f}, z={z:.1f} → DV={dv:.2f}, μ={mu:.2f}")
