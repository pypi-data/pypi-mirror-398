# mcgt/backends/ref_phase.py
# -----------------------------------------------------------------------------
# Wrapper pour calculer la phase de référence φ_ref(f | m1, m2) en domaine
# fréquentiel. Priorité PyCBC (get_fd_waveform, IMRPhenomD), fallback LALSuite.
#
# Caching :
# - Cache mémoire LRU (taille limitée)
# - Cache disque atomique (.npz) avec verrouillage fichier

from __future__ import annotations

import hashlib
import logging
import os
import time
from collections import OrderedDict

import numpy as np

# Tentatives d'import robustes pour PyCBC / LALSuite et filelock
_have_pyc = False
_have_lal = False
_have_filelock = False
try:
    from filelock import FileLock

    _have_filelock = True
except Exception:
    FileLock = None

try:
    from pycbc.waveform import get_fd_waveform

    _have_pyc = True
except Exception:
    _have_pyc = False

try:
    import lal
    import lalsimulation as lalsim

    _have_lal = True
except Exception:
    _have_lal = False

# Logging
logger = logging.getLogger("mcgt.ref_phase")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Constantes / paramètres de cache
CACHE_DIR_DEFAULT = os.path.join("zz-data", "chapter10", ".cache_ref")  # <— anglais
CACHE_MAX_ENTRIES_MEM = 128
CACHE_DISK_QUOTA_BYTES = int(2 * 1024**3)  # 2 Go
CACHE_FILE_SUFFIX = ".npz"
CACHE_LOCK_SUFFIX = ".lock"
CACHE_PART_SUFFIX = ".part"
LOCK_TIMEOUT = 120.0

# LRU mémoire simple
_memcache = OrderedDict()


# ------------------------- Helpers cache / I-O ------------------------- #
def _ensure_cache_dir(cache_dir: str):
    os.makedirs(cache_dir, exist_ok=True)


def _hash_fgrid(f_Hz: np.ndarray) -> str:
    """SHA1 sur les bytes de la grille f_Hz (float64) pour clé de cache."""
    arr = np.asarray(f_Hz, dtype=np.float64)
    return hashlib.sha1(arr.tobytes()).hexdigest()


def _cache_key(approximant: str, m1: float, m2: float, fhash: str) -> str:
    name = f"{approximant}_m1-{m1:.6f}_m2-{m2:.6f}_f-{fhash}"
    safe = "".join(c if (c.isalnum() or c in "._-") else "_" for c in name)
    return safe + CACHE_FILE_SUFFIX


def _atomic_write_npz(path: str, data: dict):
    """
    Écrire atomiquement un .npz via .part -> replace. Évite les corruptions
    en cas d'accès concurrents.
    """
    part = path + CACHE_PART_SUFFIX
    parent = os.path.dirname(part)
    if parent:
        os.makedirs(parent, exist_ok=True)
    try:
        with open(part, "wb") as fh:
            np.savez_compressed(fh, **data)  # pas d’ajout d’extension en file-like
        os.replace(part, path)
    finally:
        # si le .part demeure pour une raison quelconque
        try:
            if os.path.exists(part):
                os.remove(part)
        except Exception:
            pass


def _evict_cache_if_needed(cache_dir: str, quota_bytes: int = CACHE_DISK_QUOTA_BYTES):
    """Supprime les fichiers les plus anciens jusqu'à respecter le quota."""
    try:
        files = []
        total = 0
        for fn in os.listdir(cache_dir):
            if fn.endswith(CACHE_FILE_SUFFIX):
                p = os.path.join(cache_dir, fn)
                try:
                    st = os.stat(p)
                except FileNotFoundError:
                    continue
                files.append((st.st_mtime, p, st.st_size))
                total += st.st_size
        if total <= quota_bytes:
            return
        files.sort(key=lambda x: x[0])  # plus ancien d'abord
        logger.info("Cache disque: dépassement quota (%d bytes). Eviction…", total)
        for _, p, size in files:
            try:
                os.remove(p)
                total -= size
                if total <= quota_bytes:
                    break
            except Exception as e:
                logger.warning("Impossible de supprimer %s : %s", p, e)
    except Exception as e:
        logger.warning("Échec de l'éviction du cache: %s", e)


def _acquire_lock(path: str, timeout: float = LOCK_TIMEOUT):
    """Retourne un context manager de verrou. FileLock si dispo, sinon fallback simple."""
    lock_path = path + CACHE_LOCK_SUFFIX
    if _have_filelock and FileLock is not None:
        return FileLock(lock_path, timeout=timeout)

    # Fallback minimaliste (répertoire .dirlock)
    class _SimpleLock:
        def __init__(self, p, timeout):
            self.lockdir = p + ".dirlock"
            self.timeout = timeout

        def __enter__(self):
            t0 = time.time()
            while True:
                try:
                    os.mkdir(self.lockdir)
                    return self
                except FileExistsError:
                    if (time.time() - t0) > self.timeout:
                        raise TimeoutError(
                            f"Timeout acquiring simple lock: {self.lockdir}"
                        )
                    time.sleep(0.1)

        def __exit__(self, exc_type, exc, tb):
            try:
                os.rmdir(self.lockdir)
            except Exception:
                pass

    return _SimpleLock(lock_path, timeout)


# ------------------------- Backends de calcul ------------------------- #
def _phi_ref_via_pyc(
    f_Hz: np.ndarray, m1: float, m2: float, approximant: str = "IMRPhenomD"
) -> np.ndarray:
    """Calcul via PyCBC/get_fd_waveform. Retourne la phase (radians) sur f_Hz."""
    if not _have_pyc:
        raise RuntimeError("PyCBC indisponible")

    f_Hz = np.asarray(f_Hz, dtype=np.float64)
    if f_Hz.size < 2 or not np.all(np.diff(f_Hz) > 0):
        raise ValueError("f_Hz doit être 1D strictement croissant (≥2 points).")

    df_array = np.diff(f_Hz)
    delta_f = float(np.median(df_array))
    f_lower = float(f_Hz[0])
    f_final = float(f_Hz[-1])

    try:
        hp, _hc = get_fd_waveform(
            approximant=approximant,
            mass1=float(m1),
            mass2=float(m2),
            spin1z=0.0,
            spin2z=0.0,
            inclination=0.0,
            distance=1.0,
            coa_phase=0.0,
            f_lower=f_lower,
            f_final=f_final,
            delta_f=delta_f,
        )
    except Exception as e:
        raise RuntimeError(f"REF_COMPUTE_FAIL (PyCBC) : {e}")

    # Récupérer phase sur la grille source, puis interpoler sur f_Hz
    try:
        f_src = np.asarray(hp.sample_frequencies, dtype=np.float64)
    except Exception:
        try:
            f_src = np.asarray(hp.sample_frequencies(), dtype=np.float64)
        except Exception:
            raise RuntimeError(
                "REF_COMPUTE_FAIL: impossible d'extraire sample_frequencies de PyCBC waveform"
            )

    data = np.asarray(hp.data, dtype=np.complex128)
    phase_src = np.unwrap(np.angle(data))
    phi_on_grid = np.interp(f_Hz, f_src, phase_src).astype(np.float64)
    return phi_on_grid


def _phi_ref_via_lalsim(
    f_Hz: np.ndarray, m1: float, m2: float, approximant: str = "IMRPhenomD"
) -> np.ndarray:
    """Calcul via LALSimulation (API indicative ; peut nécessiter adaptation selon version)."""
    if not _have_lal:
        raise RuntimeError("LALSuite/lalsimulation indisponible")

    f_Hz = np.asarray(f_Hz, dtype=np.float64)
    if f_Hz.size < 2 or not np.all(np.diff(f_Hz) > 0):
        raise ValueError("f_Hz doit être 1D strictement croissant (≥2 points).")

    try:
        m1_si = float(m1) * lal.MSUN_SI
        m2_si = float(m2) * lal.MSUN_SI
        approximant_map = {"IMRPhenomD": lalsim.IMRPhenomD}
        approx_enum = approximant_map.get(approximant, lalsim.IMRPhenomD)

        # NB : Interface indicative — peut varier suivant la version.
        hp_fd = lalsim.SimInspiralChooseFDWaveform(
            m1_si,
            m2_si,
            0.0,
            0.0,
            0.0,  # spins
            0.0,
            1.0,
            1.0,  # orientation/distance placeholders
            f_Hz[0],
            f_Hz[-1],
            0.0,
            approx_enum,
        )
        # Extraction (indicative) — adapter si nécessaire
        f_src = np.arange(len(hp_fd.data), dtype=float)
        data = np.asarray(hp_fd.data, dtype=np.complex128)
        phase_src = np.unwrap(np.angle(data))
        phi_on_grid = np.interp(f_Hz, f_src, phase_src).astype(np.float64)
        return phi_on_grid
    except Exception as e:
        raise RuntimeError(f"REF_COMPUTE_FAIL (LALSuite) : {e}")


# ------------------------- Interface publique ------------------------- #
def compute_phi_ref(
    f_Hz: np.ndarray,
    m1: float,
    m2: float,
    *,
    approximant: str = "IMRPhenomD",
    cache_dir: str | None = None,
    force_recompute: bool = False,
) -> np.ndarray:
    """
    Calculer (ou récupérer depuis cache) la phase de référence φ_ref(f) pour (m1,m2).

    Paramètres
    ----------
    f_Hz : ndarray
        Grille 1D (Hz), strictement croissante.
    m1, m2 : float
        Masses en M_sun (source-frame).
    approximant : str
        Nom d'approximant (ex. "IMRPhenomD").
    cache_dir : str | None
        Dossier de cache (par défaut zz-data/chapter10/.cache_ref).
    force_recompute : bool
        Ignore le cache si True.

    Retour
    ------
    np.ndarray (float64), même shape que f_Hz, phase en radians.

    Exceptions
    ----------
    ValueError, RuntimeError("REF_BACKEND_MISSING" | "REF_COMPUTE_FAIL")
    """
    f_Hz = np.asarray(f_Hz, dtype=np.float64)
    if f_Hz.ndim != 1 or f_Hz.size < 2 or not np.all(np.diff(f_Hz) > 0):
        raise ValueError("f_Hz doit être 1D, ≥2 points et strictement croissant.")
    if not np.all(np.isfinite(f_Hz)):
        raise ValueError("f_Hz contient des valeurs non finies.")

    if cache_dir is None:
        cache_dir = CACHE_DIR_DEFAULT
    _ensure_cache_dir(cache_dir)

    fhash = _hash_fgrid(f_Hz)
    cache_filename = _cache_key(approximant, float(m1), float(m2), fhash)
    cache_path = os.path.join(cache_dir, cache_filename)

    # 1) cache mémoire
    mem_key = (approximant, float(m1), float(m2), fhash)
    if not force_recompute and mem_key in _memcache:
        phi = _memcache.pop(mem_key)
        _memcache[mem_key] = phi
        return np.array(phi, dtype=np.float64)

    # 2) cache disque
    if not force_recompute and os.path.exists(cache_path):
        try:
            with _acquire_lock(cache_path):
                data = np.load(cache_path)
                if "phi_on_grid" in data:
                    phi = np.array(data["phi_on_grid"], dtype=np.float64)
                    _memcache[mem_key] = phi
                    while len(_memcache) > CACHE_MAX_ENTRIES_MEM:
                        _memcache.popitem(last=False)
                    return phi
        except Exception as e:
            logger.warning(
                "Cache disque illisible (%s), on recalcule : %s", cache_path, e
            )

    # 3) calcul (avec verrou pour éviter courses multiples)
    with _acquire_lock(cache_path):
        # re-check (un autre worker a pu écrire)
        if not force_recompute and os.path.exists(cache_path):
            try:
                data = np.load(cache_path)
                if "phi_on_grid" in data:
                    phi = np.array(data["phi_on_grid"], dtype=np.float64)
                    _memcache[mem_key] = phi
                    while len(_memcache) > CACHE_MAX_ENTRIES_MEM:
                        _memcache.popitem(last=False)
                    return phi
            except Exception:
                logger.warning("Lecture cache échouée après lock; recalcul.")

        last_exc = None
        phi_on_grid = None

        if _have_pyc:
            try:
                phi_on_grid = _phi_ref_via_pyc(f_Hz, m1, m2, approximant=approximant)
            except Exception as e:
                last_exc = e
                logger.warning("PyCBC a échoué (m1=%s, m2=%s) : %s", m1, m2, e)

        if phi_on_grid is None and _have_lal:
            try:
                phi_on_grid = _phi_ref_via_lalsim(f_Hz, m1, m2, approximant=approximant)
            except Exception as e:
                last_exc = e
                logger.warning("LALSuite a échoué (m1=%s, m2=%s) : %s", m1, m2, e)

        if phi_on_grid is None:
            if not (_have_pyc or _have_lal):
                raise RuntimeError(
                    "REF_BACKEND_MISSING: aucun backend (PyCBC/LALSuite) disponible"
                )
            raise RuntimeError(
                f"REF_COMPUTE_FAIL: backends disponibles ont échoué: {last_exc}"
            )

        # Écriture cache disque + LRU mémoire
        try:
            _atomic_write_npz(
                cache_path, {"phi_on_grid": np.asarray(phi_on_grid, dtype=np.float64)}
            )
            _evict_cache_if_needed(
                cache_dir=cache_dir, quota_bytes=CACHE_DISK_QUOTA_BYTES
            )
        except Exception as e:
            logger.warning("Écriture cache disque impossible (%s) : %s", cache_path, e)

        _memcache[mem_key] = np.asarray(phi_on_grid, dtype=np.float64)
        while len(_memcache) > CACHE_MAX_ENTRIES_MEM:
            _memcache.popitem(last=False)

        return np.array(phi_on_grid, dtype=np.float64)


# ------------------------- API utilitaires ------------------------- #
def clear_ref_cache(cache_dir: str | None = None):
    """Purge tout le cache disque (attention : irréversible)."""
    if cache_dir is None:
        cache_dir = CACHE_DIR_DEFAULT
    if not os.path.isdir(cache_dir):
        return
    for fn in os.listdir(cache_dir):
        p = os.path.join(cache_dir, fn)
        try:
            if os.path.isfile(p):
                os.remove(p)
        except Exception as e:
            logger.warning("clear_ref_cache: impossible de supprimer %s : %s", p, e)


def ref_cache_info(cache_dir: str | None = None) -> dict:
    """Retourne des informations sommaires sur le cache disque (taille, n fichiers)."""
    if cache_dir is None:
        cache_dir = CACHE_DIR_DEFAULT
    info = {"cache_dir": cache_dir, "n_files": 0, "total_bytes": 0, "entries": []}
    if not os.path.isdir(cache_dir):
        return info
    for fn in os.listdir(cache_dir):
        if fn.endswith(CACHE_FILE_SUFFIX):
            p = os.path.join(cache_dir, fn)
            try:
                st = os.stat(p)
                info["n_files"] += 1
                info["total_bytes"] += st.st_size
                info["entries"].append(
                    {"file": fn, "size": st.st_size, "mtime": st.st_mtime}
                )
            except Exception:
                continue
    return info


# ------------------------- Petit test local ------------------------- #
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Test rapide du backend φ_ref (PyCBC/LALSuite) et cache."
    )
    parser.add_argument("--fmin", type=float, default=10.0)
    parser.add_argument("--fmax", type=float, default=2041.7379)
    parser.add_argument("--dlog10", type=float, default=0.01)
    parser.add_argument("--m1", type=float, default=30.0)
    parser.add_argument("--m2", type=float, default=30.0)
    parser.add_argument("--approximant", type=str, default="IMRPhenomD")
    parser.add_argument("--cache-dir", type=str, default=CACHE_DIR_DEFAULT)
    args = parser.parse_args()

    # Construire grille log10
    n = int(np.ceil((np.log10(args.fmax) - np.log10(args.fmin)) / args.dlog10)) + 1
    fgrid = np.logspace(np.log10(args.fmin), np.log10(args.fmax), n)
    logger.info(
        "Test compute_phi_ref: grille %d points, m1=%s m2=%s",
        fgrid.size,
        args.m1,
        args.m2,
    )
    try:
        phi = compute_phi_ref(
            fgrid,
            args.m1,
            args.m2,
            approximant=args.approximant,
            cache_dir=args.cache_dir,
        )
        logger.info(
            "Phase calculée, %d points (min/max) = (%g, %g)",
            phi.size,
            float(np.min(phi)),
            float(np.max(phi)),
        )
    except Exception as e:
        logger.exception("Échec compute_phi_ref (test) : %s", e)
