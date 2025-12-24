#!/usr/bin/env python3
# add_to_manifest.py — ajoute/actualise/supprime des entrées dans zz-manifests/manifest_master.json
# Objectif : outiller l’inventaire reproductible des artefacts MCGT.
# - Aligne la structure du manifest avec diag_consistency.py (liste "entries", chemins RELATIFS).
# - Calcule sha256, taille, mtime ISO-UTC, (optionnel) git hash.
# - Accepte fichiers, motifs glob, liste depuis un fichier ou stdin.
# - Rôle auto par répertoire/extension, déduction chapterXX si possible.
# - Écriture atomique + .bak horodaté ; champs agrégés mis à jour.
#
# Exemples :
#   python zz-manifests/add_to_manifest.py zz-data/chapter10/10_mc_results.csv
#   python zz-manifests/add_to_manifest.py "zz-figures/chapter09/09_fig_*.png" --role figure
#   python zz-manifests/add_to_manifest.py --from-list paths.txt --tags "chapter09,phase"
#   git ls-files | python zz-manifests/add_to_manifest.py - --role source
#   python zz-manifests/add_to_manifest.py --remove "zz-data/chapter09/*.tmp"
#
# Codes retour :
#   0 OK | 1 aucun fichier traité | 2 erreur arguments/lecture/écriture

from __future__ import annotations

import argparse
import datetime
import glob
import hashlib
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

UTC = datetime.UTC
REPO_ROOT = Path.cwd().resolve()

# ------------------------- utilitaires horodatage / hash -------------------------


def utc_now_iso() -> str:
    return (
        datetime.datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def iso_mtime(path: Path) -> str:
    t = datetime.datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return t.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def git_hash_of(path: Path) -> str | None:
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


# ------------------------- heuristiques rôle / chapitre / type -------------------


def guess_role(p: Path) -> str:
    s = str(p).replace("\\", "/")
    if "/zz-schemas/" in s:
        return "schema"
    if "/zz-manifests/" in s:
        return "manifest"
    if "/zz-configuration/" in s:
        return "config"
    if "/zz-scripts/" in s:
        return "script"
    if "/zz-figures/" in s:
        return "figure"
    if "/zz-data/" in s or "/zz-donnees/" in s:
        return "data"
    if p.suffix.lower() in {".tex", ".bib"}:
        return "source"
    return "artifact"


def guess_chapter_tag(p: Path) -> str | None:
    s = p.as_posix().lower()
    # supporte chapter09, chapter9, chapitre9, etc.
    for token in s.split("/"):
        if token.startswith("chapter"):
            suf = token.replace("chapter", "")
            if suf.isdigit():
                return f"chapter{int(suf):02d}"
        if token.startswith("chapitre"):
            suf = token.replace("chapitre", "")
            if suf.isdigit():
                return f"chapter{int(suf):02d}"
    # essaie via préfixe fichier (ex: 09_..., 10_...)
    stem = p.name
    if len(stem) >= 2 and stem[:2].isdigit():
        return f"chapter{int(stem[:2]):02d}"
    return None


def guess_media_type(p: Path) -> str:
    mt, _ = mimetypes.guess_type(p.name)
    return mt or {
        ".json": "application/json",
        ".csv": "text/csv",
        ".dat": "text/plain",
        ".png": "image/png",
        ".ini": "text/plain",
        ".md": "text/markdown",
        ".tex": "text/x-tex",
    }.get(p.suffix.lower(), "application/octet-stream")


# ------------------------- I/O manifest -------------------------


def manifest_skeleton() -> dict[str, Any]:
    return {
        "manifest_version": "1.0",
        "project": "MCGT",
        "repository_root": ".",
        "generated_at": utc_now_iso(),
        "total_entries": 0,
        "total_size_bytes": 0,
        "entries": [],  # liste d'objets {path, role, size_bytes, sha256, mtime_iso, ...}
    }


def load_manifest(path_manifest: Path) -> dict[str, Any]:
    if path_manifest.exists():
        try:
            obj = json.loads(path_manifest.read_text(encoding="utf-8"))
            # Migration legacy: si "files" utilisé, convertir -> "entries"
            if isinstance(obj, dict) and "entries" not in obj and "files" in obj:
                ent: list[dict[str, Any]] = []
                for it in obj.get("files", []):
                    if isinstance(it, dict):
                        ent.append(it)
                    elif isinstance(it, str):
                        ent.append({"path": it})
                obj["entries"] = ent
                obj.pop("files", None)
            return obj
        except Exception as e:
            print(
                f"ERROR: cannot parse manifest: {path_manifest} -> {e}", file=sys.stderr
            )
            sys.exit(2)
    return manifest_skeleton()


def write_manifest_atomic(
    path: Path, obj: dict[str, Any], do_backup: bool = True
) -> None:
    # champs agrégés
    obj["generated_at"] = utc_now_iso()
    entries = obj.get("entries", [])
    obj["total_entries"] = len(entries)
    obj["total_size_bytes"] = int(sum(int(e.get("size_bytes") or 0) for e in entries))

    tmp_fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")

    if do_backup and path.exists():
        bak = path.with_suffix(
            path.suffix
            + "."
            + datetime.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            + ".bak"
        )
        shutil.copy2(path, bak)
        print("Backup manifest ->", bak)

    Path(tmp_name).replace(path)
    print("Wrote:", path)


# ------------------------- collecte des chemins -------------------------


def expand_paths(arg_path: str) -> list[Path]:
    # "-" -> stdin (une voie par ligne)
    if arg_path == "-":
        items = [ln.strip() for ln in sys.stdin.read().splitlines() if ln.strip()]
        paths: list[Path] = []
        for it in items:
            paths.extend(
                Path().glob(it) if any(ch in it for ch in "*?[]") else [Path(it)]
            )
        return [
            p.resolve()
            for sub in paths
            for p in ([sub] if isinstance(sub, Path) else [])
        ]
    # motif glob ?
    if any(ch in arg_path for ch in "*?[]"):
        return [Path(p).resolve() for p in glob.glob(arg_path)]
    return [Path(arg_path).expanduser().resolve()]


def read_list_file(path: Path) -> list[Path]:
    items = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        if any(ch in ln for ch in "*?[]"):
            items.extend(Path().glob(ln))
        else:
            items.append(Path(ln))
    return [p.resolve() for p in items]


def to_rel_repo(p: Path) -> str:
    try:
        rel = p.relative_to(REPO_ROOT)
    except Exception:
        # si hors dépôt, on garde un chemin relatif "propre" si possible
        rel = Path(os.path.relpath(str(p), str(REPO_ROOT)))
    return rel.as_posix()


# ------------------------- opérations sur le manifest -------------------------


def upsert_entry(
    manifest: dict[str, Any],
    path: Path,
    role: str | None,
    tags: list[str],
    set_git: bool,
) -> tuple[bool, dict[str, Any]]:
    if not path.exists():
        print("WARN: file not found, skip ->", path, file=sys.stderr)
        return False, {}

    rel = to_rel_repo(path)
    sha = sha256_of_file(path)
    size = path.stat().st_size
    mti = iso_mtime(path)
    r = role or guess_role(path)
    chap = guess_chapter_tag(path)
    mt = guess_media_type(path)
    gh = git_hash_of(path) if set_git else None

    # rechercher entrée existante
    entries: list[dict[str, Any]] = manifest.setdefault("entries", [])
    found = None
    for e in entries:
        if e.get("path") == rel:
            found = e
            break

    payload = {
        "path": rel,
        "role": r,
        "size_bytes": size,
        "sha256": sha,
        "mtime_iso": mti,
        "media_type": mt,
    }
    if chap and chap not in (e for e in tags):
        tags = [*tags, chap]
    if tags:
        payload["tags"] = sorted(set(tags))
    if gh is not None:
        payload["git_hash"] = gh

    if found:
        changed = False
        for k, v in payload.items():
            if found.get(k) != v:
                found[k] = v
                changed = True
        if not changed:
            print("UNCHANGED:", rel)
        else:
            print("UPDATED  :", rel)
        return True, found

    entries.append(payload)
    print("ADDED    :", rel)
    return True, payload


def remove_entries(manifest: dict[str, Any], pattern: str) -> int:
    # pattern sur le champ "path" (glob)
    import fnmatch

    entries: list[dict[str, Any]] = manifest.get("entries", [])
    keep = []
    removed = 0
    for e in entries:
        p = e.get("path", "")
        if fnmatch.fnmatch(p, pattern):
            print("REMOVED  :", p)
            removed += 1
        else:
            keep.append(e)
    manifest["entries"] = keep
    return removed


# ------------------------- CLI -------------------------


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Register/update files in zz-manifests/manifest_master.json (repro inventory)."
    )
    gsrc = p.add_mutually_exclusive_group(required=False)
    gsrc.add_argument(
        "path",
        nargs="?",
        default=None,
        help="file path or glob (use '-' to read from stdin)",
    )
    gsrc.add_argument(
        "--from-list",
        dest="from_list",
        help="text file listing paths/globs (one per line)",
    )
    p.add_argument(
        "--manifest",
        default="zz-manifests/manifest_master.json",
        help="manifest JSON path (default: zz-manifests/manifest_master.json)",
    )
    p.add_argument(
        "--role",
        choices=[
            "data",
            "figure",
            "schema",
            "manifest",
            "config",
            "script",
            "artifact",
            "source",
        ],
        help="force role for all inputs",
    )
    p.add_argument(
        "--tags",
        default="",
        help="comma-separated tags to attach (e.g., chapter09,phase)",
    )
    p.add_argument(
        "--no-backup",
        action="store_true",
        help="do not create timestamped .bak before writing",
    )
    p.add_argument(
        "--with-git-hash",
        action="store_true",
        help="store git blob hash (if available)",
    )
    p.add_argument(
        "--remove",
        metavar="GLOB",
        help="remove entries whose path matches this glob (e.g., 'zz-data/chapter09/*.tmp')",
    )
    p.add_argument(
        "--dry-run", action="store_true", help="do not write manifest (report only)"
    )
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    manifest_path = Path(args.manifest)

    manifest = load_manifest(manifest_path)
    manifest.setdefault("repository_root", ".")
    manifest.setdefault("project", "MCGT")
    manifest.setdefault("manifest_version", "1.0")

    # suppression (optionnelle)
    if args.remove:
        removed = remove_entries(manifest, args.remove)
        if removed == 0:
            print("No entries removed for pattern:", args.remove)
        if args.dry_run:
            print("DRY-RUN: not writing manifest.")
            return 0
        write_manifest_atomic(manifest_path, manifest, do_backup=not args.no_backup)
        return 0

    # collecter les chemins
    paths: list[Path] = []
    if args.from_list:
        paths.extend(read_list_file(Path(args.from_list)))
    if args.path is not None:
        paths.extend(expand_paths(args.path))

    # dédoublonner et filtrer (fichiers uniquement)
    seen = set()
    input_files: list[Path] = []
    for p in paths:
        if p.is_dir():
            # ajoute récursivement les fichiers de ce répertoire
            for sub in p.rglob("*"):
                if sub.is_file():
                    rp = sub.resolve()
                    if rp not in seen:
                        input_files.append(rp)
                        seen.add(rp)
        elif p.is_file():
            rp = p.resolve()
            if rp not in seen:
                input_files.append(rp)
                seen.add(rp)
        else:
            # motif qui n'a rien trouvé ou chemin inexistant
            continue

    if not input_files:
        print("No input files to register.", file=sys.stderr)
        return 1

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    ok_any = False
    for f in sorted(input_files):
        ok, _ = upsert_entry(manifest, f, args.role, tags, set_git=args.with_git_hash)
        ok_any = ok_any or ok

    if not ok_any:
        print("No entries added/updated.", file=sys.stderr)
        return 1

    if args.dry_run:
        print("DRY-RUN: not writing manifest.")
        return 0

    write_manifest_atomic(manifest_path, manifest, do_backup=not args.no_backup)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
