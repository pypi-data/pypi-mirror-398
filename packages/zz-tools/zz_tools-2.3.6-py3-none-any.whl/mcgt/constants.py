from __future__ import annotations

from typing import Final

C_LIGHT_M_S: Final[float] = 299_792_458.0
C_LIGHT_KM_S: Final[float] = C_LIGHT_M_S / 1000.0
G_SI: Final[float] = 6.67430e-11

# -*- coding: utf-8 -*-

# --- Canonical physical constants (SI) ---

"""
Constantes MCGT — point unique de vérité.

H0 est défini canoniquement en km·s⁻¹·Mpc⁻¹ (par défaut 67.4, Planck 2018).
On expose aussi la conversion en Gyr⁻¹ pour les modules qui en ont besoin.
"""


# --- unités / conversions de base ---
METER_PER_PC = 3.085_677_581_491_367e16
METER_PER_MPC = METER_PER_PC * 1.0e6
KM_PER_MPC = METER_PER_MPC / 1_000.0
DAYS_PER_YEAR = 365.25
SEC_PER_YEAR = DAYS_PER_YEAR * 24.0 * 3600.0
SEC_PER_GYR = SEC_PER_YEAR * 1.0e9

# --- H0 canonique ---
H0_KM_S_PER_MPC: float = 67.4


def H0_to_per_Gyr(h0_km_s_mpc: float | None = None) -> float:
    """Convertit H0 [km/s/Mpc] -> [Gyr^-1]."""
    if h0_km_s_mpc is None:
        h0_km_s_mpc = H0_KM_S_PER_MPC
    return h0_km_s_mpc / KM_PER_MPC * SEC_PER_GYR


# version directement utilisable
H0_1_PER_GYR: float = H0_to_per_Gyr(H0_KM_S_PER_MPC)

__all__ = [
    "METER_PER_PC",
    "METER_PER_MPC",
    "KM_PER_MPC",
    "SEC_PER_YEAR",
    "SEC_PER_GYR",
    "H0_KM_S_PER_MPC",
    "H0_1_PER_GYR",
    "H0_to_per_Gyr",
]

# === Canonical physics constants (SI & handy units) ===
try:
    from math import pi
except Exception:  # pragma: no cover
    pi = 3.141592653589793

# Speed of light

# Newtonian gravitational constant (CODATA 2018)


# Helper converters (rely on existing H0 utilities if defined)
def km_s_per_Mpc_to_per_s(x: float) -> float:
    try:
        return x * 1000.0 / (METER_PER_MPC)  # type: ignore[name-defined]
    except NameError:
        METER_PER_PC = 3.085677581491367e16
        METER_PER_MPC = METER_PER_PC * 1_000_000.0
        return x * 1000.0 / METER_PER_MPC


# Canonical constant (auto-fixed)

# Canonical constant (auto-fixed)

# Canonical constant (auto-fixed)
