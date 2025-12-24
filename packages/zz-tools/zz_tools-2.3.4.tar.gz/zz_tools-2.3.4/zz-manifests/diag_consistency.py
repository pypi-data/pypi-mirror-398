#!/usr/bin/env python3
"""
diag_consistency.py — Audit de manifeste + cohérence transverse MCGT (règles intégrées).

Fonctions principales
---------------------
- Vérifie chaque entrée de `entries[]` OU `files[]` dans le manifeste (existence, taille, sha256,
  mtime ISO-UTC, git hash facultatif, chemins RELATIFS).
- Lit des règles de cohérence (zz-schemas/consistency_rules.json) et exécute des
  contrôles de contenu sur certains JSON/CSV référencés (constantes canoniques,
  fenêtres métriques, seuils, paramètres de dérivation, classes d’items, ID d’événements,
  alias de chemins, etc.).
- Génère un rapport (texte, JSON, Markdown) avec comptage erreurs/avertissements.
- Optionnellement applique des corrections :
  • MAJ des champs techniques du manifeste (--fix)
  • normalisation d’alias de chemin (--apply-aliases)
  • normalisation des classes dans certains CSV (--fix-content, avec .bak)

Codes de retour
---------------
0 : OK (aucune erreur; warnings possibles selon --fail-on)
2 : Warnings au moins (si --fail-on=warnings)
3 : Erreurs au moins (si --fail-on=errors)

Remarques
---------
- Les noms de fichiers/répertoires utilisés dans ce script sont **en anglais** (ex. chapter09).
- Les fichiers .tex peuvent rester en français, mais ils ne sont pas ciblés par les contrôles de contenu.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

UTC = UTC


# ------------------------- Utilitaires temps / hash / git -------------------------


def utc_now_iso() -> str:
    """Horodatage ISO-8601 en UTC, sans microsecondes."""
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iso_from_mtime(ts: float) -> str:
    """Convertit un mtime POSIX en ISO-8601 UTC, sans microsecondes."""
    return (
        datetime.fromtimestamp(ts, UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_of(path: Path) -> str:
    """Calcule le SHA-256 d’un fichier."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_hash_of(path: Path) -> str | None:
    """Retourne le hash git-blob si git est disponible (sinon None)."""
    try:
        res = subprocess.run(
            ["git", "hash-object", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return None


def ensure_relative(p: Path) -> bool:
    """True si le chemin n’est pas absolu (doit être relatif au dépôt)."""
    return not p.is_absolute()


# ------------------------- Structures de rapport -------------------------


@dataclass
class Issue:
    severity: str  # "ERROR" | "WARN"
    code: str
    message: str
    entry_index: int
    path: str


@dataclass
class EntryCheck:
    idx: int
    path: str
    exists: bool
    size_bytes_ok: bool
    sha256_ok: bool
    mtime_ok: bool
    git_ok: bool
    rel_ok: bool
    issues: list[Issue]


# ------------------------- Lecture / gestion des règles -------------------------


def load_rules(path: Path | None) -> dict[str, Any]:
    if not path:
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_path_aliases(rel_path: str, rules: dict[str, Any]) -> str:
    """
    Applique les alias de chemins définis dans rules['path_aliases'].
    Remplace d’abord les préfixes les plus longs pour éviter les collisions partielles.
    """
    aliases = rules.get("path_aliases", {})
    if not aliases:
        return rel_path
    items = sorted(aliases.items(), key=lambda kv: len(kv[0]), reverse=True)
    norm = rel_path
    for src, dst in items:
        if norm.startswith(src):
            norm = dst + norm[len(src) :]
    return norm


def within_tolerance(value: float, target: float, tol: Any) -> bool:
    """
    tol peut être un nombre (tolérance absolue) ou un dict {'abs': ..., 'rel': ...}.
    """
    if value is None or target is None:
        return False
    if isinstance(tol, (int, float)):
        return abs(float(value) - float(target)) <= float(tol)

    abs_ok = True
    rel_ok = True
    if isinstance(tol, dict):
        if tol.get("abs") is not None:
            abs_ok = abs(float(value) - float(target)) <= float(tol["abs"])
        if tol.get("rel") is not None:
            denom = max(abs(float(target)), 1e-30)
            rel_ok = abs(float(value) - float(target)) / denom <= float(tol["rel"])
    return abs_ok and rel_ok


def try_get(d: dict[str, Any], keys: list[str], default=None):
    """Essaye plusieurs chemins 'a.b.c' pour récupérer une valeur d’un dict JSON."""
    for k in keys:
        cur = d
        ok = True
        for part in k.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok:
            return cur
    return default


# ------------------------- Manifeste: entries[] OU files[] -------------------------


def normalize_manifest_items(obj: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    """
    Détecte la liste d’items du manifeste: 'entries' ou 'files'.
    Normalise chaque item en dict (si un item est une string -> {'path': item}).
    Retourne (key, items).
    """
    if not isinstance(obj, dict):
        raise ValueError("Manifest root must be a JSON object (dict).")

    key: str | None = None
    if isinstance(obj.get("entries"), list):
        key = "entries"
    elif isinstance(obj.get("files"), list):
        key = "files"

    if key is None:
        raise ValueError(
            "Unexpected manifest format: expected 'entries'[] or 'files'[] at root."
        )

    raw = obj.get(key, [])
    items: list[dict[str, Any]] = []
    for it in raw:
        if isinstance(it, dict):
            items.append(it)
        elif isinstance(it, str):
            items.append({"path": it})
        else:
            raise ValueError(
                f"Unexpected item type in manifest.{key}[]: {type(it).__name__}"
            )

    obj[key] = items
    return key, items


# ------------------------- Vérification d'une entrée du manifeste -------------------------


def _compare_field(stored: Any, computed: Any) -> bool:
    return stored == computed


def compute_info(
    repo_root: Path, rel_path: str
) -> tuple[dict[str, Any] | None, Issue | None]:
    p = Path(rel_path)
    if p.is_absolute():
        return None, Issue(
            "ERROR", "ABSOLUTE_PATH", f"Chemin absolu interdit: {p}", -1, rel_path
        )
    full = (repo_root / p).resolve()
    if not full.exists():
        return None, Issue(
            "ERROR", "FILE_MISSING", f"Fichier introuvable: {rel_path}", -1, rel_path
        )
    st = full.stat()
    info = {
        "size_bytes": st.st_size,
        "sha256": sha256_of(full),
        "mtime_iso": iso_from_mtime(st.st_mtime),
        "git_hash": git_hash_of(full),
    }
    return info, None


def check_entry(e: dict[str, Any], idx: int, repo_root: Path) -> EntryCheck:
    issues: list[Issue] = []
    rel = e.get("path", "")
    rel_ok = ensure_relative(Path(rel))
    if not rel_ok:
        issues.append(
            Issue("ERROR", "ABSOLUTE_PATH", f"path doit être relatif: {rel}", idx, rel)
        )

    info, err = compute_info(repo_root, rel)
    if err:
        issues.append(Issue(err.severity, err.code, err.message, idx, rel))
        return EntryCheck(idx, rel, False, False, False, False, False, rel_ok, issues)

    exists = True
    size_ok = _compare_field(e.get("size_bytes"), info["size_bytes"])
    if e.get("size_bytes") is None:
        issues.append(Issue("WARN", "SIZE_MISSING", "size_bytes manquant", idx, rel))
    elif not size_ok:
        issues.append(
            Issue(
                "ERROR",
                "SIZE_MISMATCH",
                f"size_bytes {e.get('size_bytes')} != {info['size_bytes']}",
                idx,
                rel,
            )
        )

    sha_ok = _compare_field(e.get("sha256"), info["sha256"])
    if e.get("sha256") is None:
        issues.append(Issue("WARN", "SHA_MISSING", "sha256 manquant", idx, rel))
    elif not sha_ok:
        issues.append(
            Issue(
                "ERROR",
                "SHA_MISMATCH",
                f"sha256 {e.get('sha256')} != {info['sha256']}",
                idx,
                rel,
            )
        )

    mt_ok = _compare_field(e.get("mtime_iso"), info["mtime_iso"])
    if e.get("mtime_iso") is None:
        issues.append(Issue("WARN", "MTIME_MISSING", "mtime_iso manquant", idx, rel))
    elif not mt_ok:
        issues.append(
            Issue(
                "WARN",
                "MTIME_DIFFERS",
                f"mtime_iso diffère (manifest={e.get('mtime_iso')}, fs={info['mtime_iso']})",
                idx,
                rel,
            )
        )

    gh_stored = e.get("git_hash")
    gh_comp = info["git_hash"]
    git_ok = (gh_stored == gh_comp) or (gh_stored is None and gh_comp is None)
    if gh_stored is None:
        issues.append(
            Issue(
                "WARN",
                "GIT_HASH_MISSING",
                "git_hash manquant (ok si hors git)",
                idx,
                rel,
            )
        )
    elif gh_comp is None:
        issues.append(
            Issue("WARN", "GIT_HASH_UNAVAILABLE", "git hash non disponible", idx, rel)
        )
    elif not git_ok:
        issues.append(
            Issue(
                "WARN",
                "GIT_HASH_DIFFERS",
                f"git_hash diffère (manifest={gh_stored}, git={gh_comp})",
                idx,
                rel,
            )
        )

    return EntryCheck(idx, rel, exists, size_ok, sha_ok, mt_ok, git_ok, rel_ok, issues)


# ------------------------- I/O manifeste -------------------------


def load_manifest(path: Path) -> tuple[dict[str, Any], str]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError("Manifest root must be a JSON object (dict).")
    key, _items = normalize_manifest_items(obj)
    return obj, key


def write_manifest_atomic(path: Path, obj: dict[str, Any]) -> None:
    fd, tmppath = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    tmp = Path(tmppath)
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
            f.write("\n")
        bak = path.with_suffix(
            path.suffix + f".{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.bak"
        )
        if path.exists():
            shutil.copy2(path, bak)
        shutil.move(str(tmp), str(path))
    finally:
        try:
            os.close(fd)
        except Exception:
            pass
        if tmp.exists():
            tmp.unlink(missing_ok=True)


# ------------------------- Rapport (agrégé) -------------------------


def build_report(
    results: list[EntryCheck], content_issues: list[Issue], rules_meta: dict[str, Any]
) -> dict[str, Any]:
    errors, warnings = 0, 0
    issues = []
    for r in results:
        for it in r.issues:
            if it.severity == "ERROR":
                errors += 1
            else:
                warnings += 1
            issues.append(asdict(it))
    for it in content_issues:
        if it.severity == "ERROR":
            errors += 1
        else:
            warnings += 1
        issues.append(asdict(it))
    rep = {"errors": errors, "warnings": warnings, "issues": issues}
    if rules_meta:
        rep["rules"] = rules_meta
    return rep


def print_report(report: dict[str, Any], mode: str, stream=sys.stdout) -> None:
    if mode == "json":
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
        return
    if mode == "md":
        stream.write("# Consistency report\n\n")
        stream.write(f"- Errors: **{report['errors']}**\n")
        stream.write(f"- Warnings: **{report['warnings']}**\n\n")
        if report.get("rules"):
            stream.write(
                f"- Rules version: `{report['rules'].get('schema_version', 'n/a')}`\n\n"
            )
        if report["issues"]:
            stream.write("| Sev | Code | Entry | Path | Message |\n")
            stream.write("|-----|------|-------|------|---------|\n")
            for it in report["issues"]:
                stream.write(
                    f"| {it['severity']} | {it['code']} | {it['entry_index']} | `{it['path']}` | {it['message']} |\n"
                )
        else:
            stream.write("No problems detected.\n")
        return
    # texte
    stream.write(f"Errors: {report['errors']}  |  Warnings: {report['warnings']}\n")
    for it in report["issues"]:
        stream.write(
            f"- [{it['severity']}] {it['code']} (#{it['entry_index']}:{it['path']}): {it['message']}\n"
        )
    if not report["issues"]:
        stream.write("OK: no problems detected.\n")


# ------------------------- Corrections manifeste -------------------------


def apply_fixes(
    manifest: dict[str, Any],
    list_key: str,
    results: list[EntryCheck],
    repo_root: Path,
    normalize_paths: bool,
    strip_internal: bool,
) -> int:
    updated = 0
    items: list[dict[str, Any]] = manifest.get(list_key, [])

    for r in results:
        if not r.exists:
            continue
        if r.idx < 0 or r.idx >= len(items):
            continue

        e = items[r.idx]
        info, err = compute_info(repo_root, e.get("path", ""))
        if err or info is None:
            continue

        # Remplir/corriger champs techniques
        for key in ("size_bytes", "sha256", "mtime_iso"):
            if e.get(key) != info[key]:
                e[key] = info[key]
                updated += 1
        if e.get("git_hash") != info["git_hash"]:
            e["git_hash"] = info["git_hash"]
            updated += 1

        # Normaliser chemins additionnels s'ils existent
        if normalize_paths:
            if "_found_path" in e:
                e["_found_path"] = str(Path(e["_found_path"]).name)
                updated += 1
            if "found_path_rel" in e:
                e["found_path_rel"] = e.get("path", "")
                updated += 1

        if strip_internal:
            for k in list(e.keys()):
                if k.startswith("_"):
                    del e[k]
                    updated += 1

    # Top-level: on évite de “forcer” un schema, on s’adapte.
    if list_key == "entries":
        manifest["generated_at"] = utc_now_iso()
        manifest["total_entries"] = len(items)
        manifest["total_size_bytes"] = int(
            sum((e.get("size_bytes") or 0) for e in items)
        )
        manifest["entries_updated"] = updated
    else:
        # schema 'files' (actuel): on ne convertit pas, on reste discret.
        manifest["files_updated"] = updated
        # Si un champ timestamp existe déjà, on le met à jour *seulement* s’il n’est pas volontairement __LOCAL__.
        if (
            "generatedAt" in manifest
            and str(manifest.get("generatedAt")).strip() != "__LOCAL__"
        ):
            manifest["generatedAt"] = utc_now_iso()

    return updated


# ------------------------- Corrections alias de chemin -------------------------


def apply_aliases_to_manifest_paths(
    manifest: dict[str, Any], list_key: str, repo_root: Path, rules: dict[str, Any]
) -> int:
    """Remplace e['path'] via les alias, si le fichier existe au chemin normalisé."""
    updated = 0
    for idx, e in enumerate(manifest.get(list_key, [])):
        rel = e.get("path", "")
        norm = normalize_path_aliases(rel, rules)
        if norm != rel and (repo_root / norm).exists():
            e["path"] = norm
            updated += 1
    if updated and "generated_at" in manifest:
        manifest["generated_at"] = utc_now_iso()
    return updated


# ------------------------- Contrôles de contenu (transverses) -------------------------


def _content_issue(sev: str, code: str, msg: str, idx: int, path: str) -> Issue:
    return Issue(sev, code, msg, idx, path)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _check_canonical_constants(
    json_obj: dict[str, Any], rules: dict[str, Any], idx: int, rel: str
) -> list[Issue]:
    issues: list[Issue] = []
    canon = rules.get("canonical_constants", {})
    toler = rules.get("tolerances", {})

    # H0
    H0 = try_get(json_obj, ["H0", "cosmo.H0"])
    if H0 is not None and "H0" in canon:
        tol = toler.get("H0", {"abs": 0.5})
        if not within_tolerance(float(H0), float(canon["H0"]), tol):
            issues.append(
                _content_issue(
                    "WARN",
                    "CONST_MISMATCH",
                    f"H0={H0} deviates from canonical {canon['H0']} (tol={tol})",
                    idx,
                    rel,
                )
            )

    # A_s0 / As0
    As = try_get(json_obj, ["A_s0", "As0", "primordial.A_s0"])
    if As is not None and "A_s0" in canon:
        tol = toler.get("A_s0", {"rel": 0.05})
        if not within_tolerance(float(As), float(canon["A_s0"]), tol):
            issues.append(
                _content_issue(
                    "WARN",
                    "CONST_MISMATCH",
                    f"A_s0={As} deviates from canonical {canon['A_s0']} (tol={tol})",
                    idx,
                    rel,
                )
            )

    # n_s0 / ns0
    ns = try_get(json_obj, ["n_s0", "ns0", "primordial.ns0"])
    if ns is not None and "ns0" in canon:
        tol = toler.get("ns0", {"abs": 0.01})
        if not within_tolerance(float(ns), float(canon["ns0"]), tol):
            issues.append(
                _content_issue(
                    "WARN",
                    "CONST_MISMATCH",
                    f"ns0={ns} deviates from canonical {canon['ns0']} (tol={tol})",
                    idx,
                    rel,
                )
            )

    return issues


def _check_thresholds(
    json_obj: dict[str, Any], rules: dict[str, Any], idx: int, rel: str
) -> list[Issue]:
    issues: list[Issue] = []
    want = rules.get("thresholds", {})
    have = try_get(json_obj, ["thresholds"])
    if isinstance(have, dict) and want:
        for k in ("primary", "order2"):
            if k in want and k in have and float(have[k]) != float(want[k]):
                issues.append(
                    _content_issue(
                        "WARN",
                        "THRESHOLD_DIFFERS",
                        f"thresholds.{k}={have[k]} vs canonical {want[k]}",
                        idx,
                        rel,
                    )
                )
    return issues


def _check_derivative(
    json_obj: dict[str, Any], rules: dict[str, Any], idx: int, rel: str
) -> list[Issue]:
    issues: list[Issue] = []
    want = rules.get("derivative", {})
    if not want:
        return issues
    w = try_get(json_obj, ["derivative_window"])
    p = try_get(json_obj, ["derivative_polyorder"])
    if w is not None and "window" in want and int(w) != int(want["window"]):
        issues.append(
            _content_issue(
                "WARN",
                "DERIV_WINDOW_DIFFERS",
                f"derivative_window={w} vs canonical {want['window']}",
                idx,
                rel,
            )
        )
    if p is not None and "polyorder" in want and int(p) != int(want["polyorder"]):
        issues.append(
            _content_issue(
                "WARN",
                "DERIV_POLYORDER_DIFFERS",
                f"derivative_polyorder={p} vs canonical {want['polyorder']}",
                idx,
                rel,
            )
        )
    return issues


def _check_metrics_window(
    json_obj: dict[str, Any], rules: dict[str, Any], idx: int, rel: str
) -> list[Issue]:
    issues: list[Issue] = []
    want = rules.get("metric_windows", {}).get("phase_20_300")
    have = try_get(json_obj, ["metrics_active.metrics_window_Hz", "metrics_window_Hz"])
    if want and isinstance(have, list) and len(have) == 2:
        wtuple = (float(have[0]), float(have[1]))
        wwant = (float(want[0]), float(want[1]))
        if wtuple != wwant:
            issues.append(
                _content_issue(
                    "WARN",
                    "METRIC_WINDOW_DIFFERS",
                    f"metrics_window_Hz={wtuple} vs canonical {wwant}",
                    idx,
                    rel,
                )
            )
    return issues


def _check_csv_milestones(
    path: Path, rules: dict[str, Any], idx: int, rel: str, fix_content: bool
) -> list[Issue]:
    """
    Vérifie le CSV des jalons de comparaison (chapter09/09_comparison_milestones.csv).
    - classes autorisées/normalisation
    - motif d’ID d’événement
    - sigma_phase > 0 si présent
    """
    issues: list[Issue] = []
    allowed = set(rules.get("classes", {}).get("allowed", ["primary", "order2"]))
    normalize_map: dict[str, str] = rules.get("classes", {}).get("normalize", {})
    event_pat = rules.get("events", {}).get("id_regex", r"^GW\d{6}_[0-9]{6}-v\d+$")
    evrx = re.compile(event_pat)

    changed = False
    rows_out: list[dict[str, str]] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ev = row.get("event", "")
                cl = row.get("classe", "")
                if ev and not evrx.match(ev):
                    issues.append(
                        _content_issue(
                            "WARN",
                            "EVENT_ID_PATTERN",
                            f"event '{ev}' does not match regex {event_pat}",
                            idx,
                            rel,
                        )
                    )
                if cl not in allowed:
                    norm = normalize_map.get(cl, cl)
                    issues.append(
                        _content_issue(
                            "WARN",
                            "CLASS_LABEL_UNKNOWN",
                            f"classe '{cl}' not in {sorted(allowed)}; normalize→'{norm}'",
                            idx,
                            rel,
                        )
                    )
                    if fix_content and norm in allowed:
                        row["classe"] = norm
                        changed = True
                sp = row.get("sigma_phase")
                if sp is not None and sp != "":
                    try:
                        if float(sp) <= 0:
                            issues.append(
                                _content_issue(
                                    "ERROR",
                                    "NEGATIVE_SIGMA",
                                    f"sigma_phase={sp} ≤ 0",
                                    idx,
                                    rel,
                                )
                            )
                    except ValueError:
                        issues.append(
                            _content_issue(
                                "ERROR",
                                "NONNUMERIC_SIGMA",
                                f"sigma_phase not numeric: {sp}",
                                idx,
                                rel,
                            )
                        )
                rows_out.append(row)

        if fix_content and changed and rows_out:
            bak = path.with_suffix(
                path.suffix + f".{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.bak"
            )
            shutil.copy2(path, bak)
            with path.open("w", encoding="utf-8", newline="") as fw:
                writer = csv.DictWriter(fw, fieldnames=rows_out[0].keys())
                writer.writeheader()
                writer.writerows(rows_out)
    except FileNotFoundError:
        issues.append(
            _content_issue("ERROR", "FILE_MISSING", f"CSV not found: {rel}", idx, rel)
        )
    except Exception as e:
        issues.append(
            _content_issue(
                "ERROR", "CSV_READ_ERROR", f"{type(e).__name__}: {e}", idx, rel
            )
        )

    return issues


def run_content_checks(
    manifest: dict[str, Any],
    list_key: str,
    repo_root: Path,
    rules: dict[str, Any],
    do_checks: bool,
    fix_content: bool,
    apply_aliases_hint: bool,
) -> list[Issue]:
    if not do_checks or not rules:
        return []
    issues: list[Issue] = []

    # Suffixes ciblés (EN uniquement)
    json_cmb_suffix = ("chapter06/06_params_cmb.json",)
    json_primordial_suffix = (
        "chapter02/02_primordial_spectrum.json",
        "chapter02/02_primordial_spectrum_spec.json",
    )
    json_threshold_like = (
        "chapter02/02_optimal_parameters.json",
        "chapter05/05_bbn_params.json",
        "chapter05/05_nucleosynthesis_parameters.json",
        "chapter06/06_params_cmb.json",
        "chapter07/07_perturbations_params.json",
        "chapter08/08_coupling_params.json",
        "chapter09/09_metrics_phase.json",
    )
    metrics_phase_suffix = ("chapter09/09_metrics_phase.json",)
    milestones_csv_suffix = ("chapter09/09_comparison_milestones.csv",)

    # Parcours des entrées/files du manifeste
    for idx, e in enumerate(manifest.get(list_key, [])):
        rel = e.get("path", "")
        if not rel:
            continue

        # Alerte si un alias est applicable mais non demandé en écriture
        alias_rel = normalize_path_aliases(rel, rules)
        if alias_rel != rel and (repo_root / alias_rel).exists():
            if not apply_aliases_hint:
                issues.append(
                    _content_issue(
                        "WARN",
                        "PATH_ALIAS_CANDIDATE",
                        f"path '{rel}' → canonical '{alias_rel}' exists; consider --apply-aliases",
                        idx,
                        rel,
                    )
                )

        full = repo_root / rel
        low = rel.replace("\\", "/")

        # JSON – constantes/seuils/dérivées/fenêtres métriques
        if (
            low.endswith(json_cmb_suffix)
            or low.endswith(json_primordial_suffix)
            or low.endswith(metrics_phase_suffix)
            or low.endswith(json_threshold_like)
        ):
            jobj = _read_json(full)
            if jobj is None:
                issues.append(
                    _content_issue(
                        "ERROR", "JSON_READ_ERROR", "unable to parse JSON", idx, rel
                    )
                )
            else:
                issues += _check_canonical_constants(jobj, rules, idx, rel)
                issues += _check_thresholds(jobj, rules, idx, rel)
                issues += _check_derivative(jobj, rules, idx, rel)
                if low.endswith(metrics_phase_suffix):
                    issues += _check_metrics_window(jobj, rules, idx, rel)

        # CSV – jalons (chap. 09)
        for suf in milestones_csv_suffix:
            if low.endswith(suf):
                issues += _check_csv_milestones(full, rules, idx, rel, fix_content)
                break

    return issues


# ------------------------- Signature / empreintes -------------------------


def write_sha256sum(path: Path) -> Path:
    h = sha256_of(path)
    out = path.with_suffix(path.suffix + ".sha256sum")
    out.write_text(f"{h}  {path.name}\n", encoding="utf-8")
    return out


def gpg_sign(path: Path) -> Path | None:
    try:
        res = subprocess.run(
            ["gpg", "--armor", "--detach-sign", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            sig = path.with_suffix(path.suffix + ".asc")
            if sig.exists():
                dest = path.with_suffix(path.suffix + ".sig")
                sig.rename(dest)
                return dest
    except Exception:
        pass
    return None


# ------------------------- CLI -------------------------


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Manifest audit + transverse consistency checks for MCGT."
    )
    p.add_argument(
        "manifest",
        help="Chemin du manifeste JSON (p.ex. zz-manifests/manifest_publication.json)",
    )
    p.add_argument("--repo-root", default=".", help="Racine du dépôt (défaut: .)")
    p.add_argument(
        "--rules",
        default="zz-schemas/consistency_rules.json",
        help="Fichier de règles de cohérence",
    )
    p.add_argument(
        "--report",
        choices=["text", "json", "md"],
        default="text",
        help="Format du rapport",
    )
    p.add_argument(
        "--fix",
        action="store_true",
        help="Applique les corrections techniques et réécrit le manifeste",
    )
    p.add_argument(
        "--normalize-paths",
        action="store_true",
        help="Normalise les champs internes *_path du manifeste",
    )
    p.add_argument(
        "--strip-internal",
        action="store_true",
        help="Supprime les clés internes commençant par '_'",
    )
    p.add_argument(
        "--set-repo-root",
        action="store_true",
        help="Force repository_root='.' dans le manifeste",
    )
    p.add_argument(
        "--fail-on",
        choices=["errors", "warnings", "none"],
        default="errors",
        help="Politique d'échec (code retour)",
    )
    p.add_argument(
        "--sha256-out",
        action="store_true",
        help="Écrit un fichier .sha256sum du manifeste",
    )
    p.add_argument(
        "--gpg-sign",
        action="store_true",
        help="Génère une signature GPG détachée (.sig)",
    )
    # Nouveaux contrôles / corrections
    p.add_argument(
        "--content-check",
        action="store_true",
        help="Active les contrôles de contenu via les règles de cohérence",
    )
    p.add_argument(
        "--apply-aliases",
        action="store_true",
        help="Réécrit les chemins du manifeste selon les alias si la cible existe",
    )
    p.add_argument(
        "--fix-content",
        action="store_true",
        help="Normalise en place les classes dans CSV jalons (backup .bak horodaté)",
    )
    return p.parse_args(argv)


# ------------------------- main -------------------------


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    manifest_path = Path(args.manifest).resolve()
    repo_root = Path(args.repo_root).resolve()

    manifest, list_key = load_manifest(manifest_path)

    # Enforce repository_root if requested
    if args.set_repo_root:
        manifest["repository_root"] = "."

    # Load rules (optional)
    rules_path = Path(args.rules) if args.rules else None
    rules = load_rules(rules_path) if (rules_path and rules_path.exists()) else {}
    rules_meta = {}
    if rules:
        rules_meta = {
            "rules_path": str(rules_path),
            "schema_version": rules.get("schema_version", "n/a"),
            "aliases": bool(rules.get("path_aliases")),
        }

    # Optionally normalize paths using aliases
    if rules and args.apply_aliases:
        updated_aliases = apply_aliases_to_manifest_paths(
            manifest, list_key, repo_root, rules
        )
        if updated_aliases:
            manifest.setdefault("notes", [])
            manifest["notes"].append(
                f"apply_aliases: {updated_aliases} paths normalized at {utc_now_iso()}"
            )

    # Per-entry technical checks
    checks: list[EntryCheck] = []
    for idx, e in enumerate(manifest.get(list_key, [])):
        checks.append(check_entry(e, idx, repo_root))

    # Transverse content checks
    content_issues: list[Issue] = run_content_checks(
        manifest,
        list_key,
        repo_root,
        rules,
        do_checks=(args.content_check or bool(rules)),
        fix_content=args.fix_content,
        apply_aliases_hint=args.apply_aliases,
    )

    # Build & print report
    report = build_report(checks, content_issues, rules_meta)
    print_report(report, args.report)

    # Apply technical fixes to manifest if requested
    if args.fix:
        updated = apply_fixes(
            manifest,
            list_key,
            checks,
            repo_root,
            normalize_paths=args.normalize_paths,
            strip_internal=args.strip_internal,
        )
        manifest.setdefault("manifest_tool_version", "diag_consistency.py")
        manifest.setdefault(
            "generated_by", os.getenv("USER") or os.getenv("USERNAME") or "unknown"
        )
        write_manifest_atomic(manifest_path, manifest)

        upd_key = "entries_updated" if list_key == "entries" else "files_updated"
        print(
            f"\nWrote: {manifest_path}  ({upd_key}={manifest.get(upd_key)}, updated_fields={updated})"
        )

    # Optional outputs
    if args.sha256_out:
        out = write_sha256sum(manifest_path)
        print(f"SHA256 manifest → {out.name}")
    if args.gpg_sign:
        sig = gpg_sign(manifest_path)
        if sig:
            print(f"GPG signature → {sig.name}")
        else:
            print("WARN: GPG signature not produced (gpg missing or no key configured)")

    # Exit policy
    code = 0
    if args.fail_on == "errors" and report["errors"] > 0:
        code = 3
    elif args.fail_on == "warnings" and (
        report["errors"] > 0 or report["warnings"] > 0
    ):
        code = 2
    else:
        code = 0
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
