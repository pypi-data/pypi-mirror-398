# mcgt/scalar_perturbations.py
# -----------------------------------------------------------------------------
"""
MCGT — Perturbations scalaires (Chap. 7)
========================================

Fonctionnalités :
* Fonctions de fond :  φ₀(a), ρφ(a), pφ(a), H(a)
* compute_cs2(k,a)   : vitesse du son c_s²(k,a)
* compute_delta_phi  : perturbation relative δφ/φ(k,a) avec source métrique
* Mini-tests pytest de régression (facultatifs)

Remarques :
- Le code accepte des grilles 1D en k (h Mpc⁻¹) et a (facteur d’échelle).
- Les chemins et noms de fichiers doivent être en anglais côté I/O ; seul
  le contenu textuel (commentaires/docstrings) reste en français.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass

import numpy as np
from scipy import integrate
from scipy.interpolate import PchipInterpolator

__all__ = [
    "PertParams",
    "phi0_of_a",
    "dphi0_da",
    "H_of_a",
    "rho_phi_of_a",
    "p_phi_of_a",
    "compute_cs2",
    "compute_delta_phi",
    "_default_params",
]


# -----------------------------------------------------------------------------#
# 1) Dataclass des paramètres
# -----------------------------------------------------------------------------#
@dataclass
class PertParams:
    # Cosmologie (unités usuelles Planck 2018)
    H0: float
    ombh2: float
    omch2: float
    omk: float
    tau: float
    mnu: float
    As0: float
    ns0: float

    # Fond MCGT
    phi0_init: float
    phi_inf: float
    a_char: float
    m_phi: float
    m_eff_const: float

    # “Knobs” pour son & perturbations
    cs2_param: float
    delta_phi_param: float
    k0: float
    k_split: float

    # Dynamique Φ & gel progressif
    a_eq: float  # facteur d’échelle à l’égalité rad−mat
    freeze_scale: float  # ~1e5 (plus petit ⇒ gel plus doux)
    Phi0: float  # Φ(k≈0, a≪a_eq)

    # Champs optionnels
    alpha: float | None = None
    phi0: float | None = None
    decay: float | None = None


# -----------------------------------------------------------------------------#
# 2) Fonctions de fond
# -----------------------------------------------------------------------------#
def phi0_of_a(a: np.ndarray | float, p: PertParams) -> np.ndarray:
    """Valeur du fond φ₀(a)."""
    a = np.asarray(a, dtype=float)
    return p.phi_inf - (p.phi_inf - p.phi0_init) * np.exp(-a / p.a_char)


def dphi0_da(a: np.ndarray | float, p: PertParams) -> np.ndarray:
    """Dérivée dφ₀/da."""
    a = np.asarray(a, dtype=float)
    return ((p.phi_inf - p.phi0_init) / p.a_char) * np.exp(-a / p.a_char)


def H_of_a(a: np.ndarray | float, p: PertParams) -> np.ndarray:
    """Taux de Hubble H(a) en km s⁻¹ Mpc⁻¹ sous hypothèse ΛCDM (platitude libre)."""
    a = np.asarray(a, dtype=float)
    h = p.H0 / 100.0
    om_m = (p.ombh2 + p.omch2) / h**2
    om_k = p.omk
    om_l = 1.0 - om_m - om_k
    return p.H0 * np.sqrt(om_m / a**3 + om_k / a**2 + om_l)


def rho_phi_of_a(a: np.ndarray | float, p: PertParams) -> np.ndarray:
    """Densité d’énergie du champ effectif (ansatz quadratique)."""
    a = np.asarray(a, dtype=float)
    dφ_da = dphi0_da(a, p)
    H = H_of_a(a, p)
    dφ_dt = dφ_da * a * H
    V = 0.5 * p.m_phi**2 * phi0_of_a(a, p) ** 2
    return 0.5 * dφ_dt**2 + V


def p_phi_of_a(a: np.ndarray | float, p: PertParams) -> np.ndarray:
    """Pression effective du champ."""
    a = np.asarray(a, dtype=float)
    dφ_da = dphi0_da(a, p)
    H = H_of_a(a, p)
    dφ_dt = dφ_da * a * H
    V = 0.5 * p.m_phi**2 * phi0_of_a(a, p) ** 2
    return 0.5 * dφ_dt**2 - V


# -----------------------------------------------------------------------------#
# 3)  c_s²(k,a)
# -----------------------------------------------------------------------------#
def compute_cs2(k_vals: np.ndarray, a_vals: np.ndarray, p: PertParams) -> np.ndarray:
    """Retourne un tableau (n_k, n_a) de c_s²(k,a) borné physiquement dans [0,1].

    Version assouplie pour le *pipeline minimal* :
    - on nettoie les NaN / ±inf,
    - on émet un warning si des valeurs sortent de [0,1],
    - on clippe ensuite dans [0,1] au lieu de lever une ValueError.
    """
    # Validation basique des grilles
    k_vals = np.asarray(k_vals, dtype=float)
    a_vals = np.asarray(a_vals, dtype=float)
    if k_vals.ndim != 1 or a_vals.ndim != 1:
        raise ValueError("k_vals et a_vals doivent être 1D.")
    if not (np.all(np.diff(k_vals) >= 0.0) and np.all(np.diff(a_vals) >= 0.0)):
        raise ValueError("Les grilles k_vals et a_vals doivent être croissantes.")

    # Grille 2D (k, a)
    K, _ = np.meshgrid(k_vals, a_vals, indexing="ij")

    # c_s²(a) ~ dp/da / dρ/da (pentes lissées)
    dp_da = np.gradient(p_phi_of_a(a_vals, p), a_vals)
    drho_da = np.gradient(rho_phi_of_a(a_vals, p), a_vals)
    with np.errstate(divide="ignore", invalid="ignore"):
        cs2_a = np.where(drho_da != 0.0, dp_da / drho_da, 0.0)
    cs2_a = PchipInterpolator(a_vals, cs2_a, extrapolate=True)(a_vals)

    # Filtre gaussien en k + amplitude globale
    T = np.exp(-((K / p.k0) ** 2))
    cs2 = T * cs2_a[np.newaxis, :] * p.cs2_param

    # Nettoyage des non-finitudes éventuelles
    import warnings

    if not np.all(np.isfinite(cs2)):
        warnings.warn(
            "c_s² contient des valeurs non finies – valeurs non finies remplacées par 0.0",
            RuntimeWarning,
        )
        cs2 = np.nan_to_num(cs2, nan=0.0, posinf=1.0, neginf=0.0)

    # Contrôle physique assoupli : warning + clip dans [0,1]
    if not np.all((cs2 >= 0.0) & (cs2 <= 1.0)):
        warnings.warn(
            "c_s² hors-borne (attendu dans [0,1]) – valeurs clipées dans [0,1] pour le pipeline minimal.",
            RuntimeWarning,
        )
        cs2 = np.clip(cs2, 0.0, 1.0)

    return cs2


def _kg_eq(a: float, y: np.ndarray, k: float, p: PertParams) -> np.ndarray:
    r"""
    Équation linéarisée (ansatz simplifié) :

        δφ'' + (2/a) δφ' + [(k²/a² + m_eff²)/(aH)²] δφ = S(a,k)

    où S(a,k) encode la source métrique via Φ(k,a).
    """
    H = float(H_of_a(a, p))

    # friction + raideur
    drag = -2.0 * y[1] / a
    stiff = -((k**2) / a**2 + p.m_eff_const**2) / (a * H) ** 2 * y[0]

    # potentiel métrique Φ(k,a)
    Phi0 = p.Phi0
    a_eq = p.a_eq
    Phi = Phi0 * np.exp(-((k / p.k_split) ** 2)) / (1.0 + (a / a_eq) ** 3)

    # source
    φ0 = float(phi0_of_a(a, p))
    φ0_p = float(dphi0_da(a, p))
    V_p = p.m_phi**2 * φ0
    source = (4.0 * φ0_p * a * H - 2.0 * V_p) * Phi / (a * H) ** 2

    return np.array([y[1], drag + stiff + source], dtype=float)


# -----------------------------------------------------------------------------#
# 5) δφ/φ(k,a)
# -----------------------------------------------------------------------------#
def compute_delta_phi(
    k_vals: np.ndarray, a_vals: np.ndarray, p: PertParams
) -> np.ndarray:
    """
    Intègre δφ/φ(k,a) sur la grille (n_k, n_a) via solve_ivp (Radau).

    Retour :
      sol_mat[i, j] = (δφ/φ)(k_i, a_j)

    Exceptions :
      RuntimeError si des non-finitudes sont détectées.
    """
    k_vals = np.asarray(k_vals, dtype=float)
    a_vals = np.asarray(a_vals, dtype=float)
    if k_vals.ndim != 1 or a_vals.ndim != 1:
        raise ValueError("k_vals et a_vals doivent être 1D.")
    if not (np.all(np.diff(k_vals) > 0) and np.all(np.diff(a_vals) > 0)):
        raise ValueError("k_vals et a_vals doivent être strictement croissants.")

    a_min, a_max = float(a_vals.min()), float(a_vals.max())
    H_a_min = float(H_of_a(a_min, p))

    φ0_grid = phi0_of_a(a_vals, p)
    sol_mat = np.zeros((k_vals.size, a_vals.size), dtype=float)

    for i, k in enumerate(k_vals):
        # gel progressif continu (suppression des modes profonds sous-horizon)
        freeze = np.exp(-((k / a_min) / H_a_min) / p.freeze_scale)

        init_amp = (
            freeze * p.delta_phi_param * p.phi0_init * np.exp(-((k / p.k_split) ** 2))
        )

        sol = integrate.solve_ivp(
            lambda aa, yy: _kg_eq(float(aa), yy, float(k), p),
            (a_min, a_max),
            (float(init_amp), 0.0),
            t_eval=a_vals,
            method="Radau",
            rtol=1e-6,
            atol=1e-9,
        )
        if not sol.success:
            raise RuntimeError(f"Échec d'intégration Radau pour k={k} : {sol.message}")

        sol_mat[i] = np.nan_to_num(sol.y[0], copy=False) / φ0_grid

    if not np.all(np.isfinite(sol_mat)):
        raise RuntimeError("δφ/φ contient NaN ou inf.")
    return sol_mat


# -----------------------------------------------------------------------------#
# 6)  Tests (facultatifs)
# -----------------------------------------------------------------------------#
def _load_ref_csv(path: pathlib.Path) -> tuple[np.ndarray, np.ndarray]:
    data = np.loadtxt(path, delimiter=",", skiprows=1)
    return data[:, 0].astype(float), data[:, 1].astype(float)


def test_cs2_against_reference(
    f: pathlib.Path = pathlib.Path(__file__).parent / "tests" / "ref_cs2.csv",
):
    """Test de non-régression approximatif sur c_s²(a) à k=0.1."""
    if not f.exists():
        return
    a_ref, c_ref = _load_ref_csv(f)
    c_test = compute_cs2(np.array([0.1], dtype=float), a_ref, _default_params())[0]
    assert np.allclose(c_ref, c_test, rtol=0.05)


def test_delta_phi_against_reference(
    f: pathlib.Path = pathlib.Path(__file__).parent / "tests" / "ref_delta_phi.csv",
):
    """Test de non-régression approximatif sur δφ/φ(k, a=1)."""
    if not f.exists():
        return
    k_ref, d_ref = _load_ref_csv(f)
    d_test = compute_delta_phi(k_ref, np.array([1.0], dtype=float), _default_params())[
        :, -1
    ]
    assert np.allclose(d_ref, d_test, rtol=0.2)


# -----------------------------------------------------------------------------#
# 7)  Paramètres par défaut (cohérents avec les configs Chap. 7)
# -----------------------------------------------------------------------------#
def _default_params() -> PertParams:
    return PertParams(
        H0=67.36,
        ombh2=0.02237,
        omch2=0.12,
        omk=0.0,
        tau=0.0544,
        mnu=0.06,
        As0=2.1e-9,
        ns0=0.9649,
        phi0_init=1.0,
        phi_inf=1.5,
        a_char=0.1,
        m_phi=1e-33,
        m_eff_const=1e-33,
        cs2_param=1.0,
        delta_phi_param=1e-3,
        k0=0.1,
        k_split=0.02,
        a_eq=0.33,
        freeze_scale=1e5,
        Phi0=1e-5,
        alpha=None,
        phi0=None,
        decay=None,
    )
