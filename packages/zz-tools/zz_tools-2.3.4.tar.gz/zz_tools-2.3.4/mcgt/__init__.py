# ruff: noqa: E402
# mcgt/__init__.py
# -----------------------------------------------------------------------------
"""
MCGT package — initialisation légère.

Ce fichier expose :
- __version__
- fonctions utilitaires pour charger la configuration du projet
- imports commodes vers les sous-modules les plus utilisés (lazy-import)
- helper pour découvrir les backends disponibles

But : rester non-intrusif (pas d'I/O obligatoire à l'import).
"""

from __future__ import annotations

__all__ = [
    "__version__",
    "load_config",
    "get_config",
    "find_config_path",
    "list_backends",
    "phase",
    "perturbations",
]

__version__ = "0.3.0"

# --- logging minimal ---
import logging

logger = logging.getLogger("mcgt")
if not logger.handlers:
    handler = logging.NullHandler()
    logger.addHandler(handler)

# --- utils for config discovery & loading (no load at import time) ---
import configparser
import importlib
import pkgutil
from pathlib import Path

# On suppose que la racine du dépôt est le parent du package
PACKAGE_ROOT = Path(__file__).resolve().parent.parent


def find_config_path(name: str = "mcgt-global-config.ini") -> Path | None:
    """
    Cherche un fichier de configuration dans cet ordre :
    1) répertoire de travail courant ./zz-configuration/<name>
    2) dossier package       ./zz-configuration/<name> (à la racine du dépôt)
    3) variable d'environnement MCGT_CONFIG
    Renvoie Path ou None si introuvable.
    """
    import os

    p = Path.cwd() / "zz-configuration" / name
    if p.exists():
        return p

    p2 = PACKAGE_ROOT / "zz-configuration" / name
    if p2.exists():
        return p2

    env = os.environ.get("MCGT_CONFIG")
    if env:
        p3 = Path(env)
        if p3.exists():
            return p3

    return None


def load_config(path: str | Path | None = None) -> configparser.ConfigParser:
    """
    Charge et retourne un `configparser.ConfigParser` à partir d'un fichier ini.
    Si `path` est None, tente find_config_path().
    Si absent, retourne un parser vide (côté appelant de gérer).
    """
    cfg = configparser.ConfigParser(interpolation=None)
    p = Path(path) if path else find_config_path()
    if p is None or not p.exists():
        logger.debug("mcgt: config not found (%s). Returning empty ConfigParser.", path)
        return cfg

    cfg.read(p, encoding="utf-8")
    logger.debug("mcgt: config loaded from %s", p)
    return cfg


# Accessor qui met en cache la config chargée
_cached_config: configparser.ConfigParser | None = None


def get_config(force_reload: bool = False) -> configparser.ConfigParser:
    """Retourne la config partagée ; utiliser force_reload=True pour relire le disque."""
    global _cached_config
    if _cached_config is None or force_reload:
        _cached_config = load_config()
    return _cached_config


# --- discovery des backends et API conviviale ---
def list_backends(package: str = "mcgt.backends") -> list[str]:
    """Retourne la liste des modules/backends disponibles dans mcgt.backends."""
    try:
        mod = importlib.import_module(package)
    except ModuleNotFoundError:
        return []
    return [name for _, name, _ in pkgutil.iter_modules(mod.__path__)]


# --- lazy imports pour commodité ---
def _lazy_import(name: str):
    try:
        return importlib.import_module(f"mcgt.{name}")
    except Exception as exc:
        logger.debug("mcgt: lazy import failed for %s: %s", name, exc)
        raise


class _LazyModuleProxy:
    def __init__(self, name: str):
        self._name = name
        self._mod = None

    def __getattr__(self, item):
        if self._mod is None:
            self._mod = _lazy_import(self._name)
        return getattr(self._mod, item)

    def __repr__(self):
        return f"<mcgt.lazy.{self._name} proxy>"


# expose proxies (noms de modules en anglais)
phase = _LazyModuleProxy("phase")
perturbations = _LazyModuleProxy("scalar_perturbations")


# --- récupérer la version depuis la métadonnée de package si dispo ---
def _load_package_version_from_metadata():
    try:
        try:
            from importlib.metadata import PackageNotFoundError, version
        except Exception:
            from importlib_metadata import PackageNotFoundError, version  # type: ignore
        try:
            return version("mcgt")
        except PackageNotFoundError:
            return None
    except Exception:
        return None


_pkg_version = _load_package_version_from_metadata()
if _pkg_version:
    pass
#     __version__ = _pkg_version


# --- helper CLI léger ---
def print_summary():
    """Affiche un résumé utile pour debug / CI."""
    _ = get_config()
    n_back = len(list_backends())
    print(f"MCGT package version: {__version__}")
    print(f"Config file: {find_config_path() or '<none>'}")
    print(f"Backends discovered: {n_back} (use mcgt.list_backends())")
    print("Modules lazy-exposed: phase, perturbations")
