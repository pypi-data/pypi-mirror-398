#!/usr/bin/env python3
# zz-scripts/manifest_tools/verify_manifest.py
"""
Vérifier un manifest JSON :
- recalcule sha256, taille, mtime (UTC)
- vérifie git hash (via `git hash-object`)
- produit un rapport (console + option --output JSON)
Usage:
  python3 verify_manifest.py zz-manifests/manifest_publication.json --repo-root . --output report.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def mtime_iso_of(path):
    st = os.stat(path)
    # timezone-aware UTC
    return datetime.fromtimestamp(st.st_mtime, tz=UTC).isoformat()


def parse_iso_utc(value):
    """Parse ISO timestamps with 'Z' or offset to a UTC-aware datetime."""
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except Exception:
        return None


def git_hash_of(path, repo_root=None):
    # Return git object hash (sha1) if git available and file inside git repo.
    try:
        # run in repo_root if given
        kwargs = {"capture_output": True, "text": True}
        if repo_root:
            kwargs["cwd"] = repo_root
        # use 'git hash-object <path>' (doesn't write by default)
        r = subprocess.run(["git", "hash-object", path], **kwargs)
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return None


def check_entry(entry, repo_root):
    path = entry.get("path")
    result = {"path": path, "exists": False, "issues": [], "expected": {}, "actual": {}}
    if not path:
        result["issues"].append("no path in entry")
        return result
    # compute absolute path relative to repo_root if path is relative
    abs_path = os.path.join(repo_root, path) if not os.path.isabs(path) else path
    abs_path = os.path.normpath(abs_path)
    result["abs_path"] = abs_path
    # expected values
    for f in ("size_bytes", "sha256", "mtime_iso", "git_hash"):
        result["expected"][f] = entry.get(f)
    if not os.path.exists(abs_path):
        result["issues"].append("MISSING_FILE")
        return result
    result["exists"] = True
    # actual
    st = os.stat(abs_path)
    actual_size = st.st_size
    actual_dt = datetime.fromtimestamp(st.st_mtime, tz=UTC)
    actual_mtime = actual_dt.isoformat()
    actual_sha256 = sha256_of(abs_path)
    actual_git = git_hash_of(
        os.path.relpath(abs_path, repo_root) if repo_root else abs_path,
        repo_root=repo_root,
    )
    result["actual"]["size_bytes"] = actual_size
    result["actual"]["mtime_iso"] = actual_mtime
    result["actual"]["sha256"] = actual_sha256
    result["actual"]["git_hash"] = actual_git
    # comparisons
    if (
        entry.get("size_bytes") is not None
        and int(entry.get("size_bytes")) != actual_size
    ):
        result["issues"].append("MISMATCH_SIZE")
    if entry.get("sha256") is not None and entry.get("sha256") != actual_sha256:
        result["issues"].append("MISMATCH_SHA256")
    # tolerance: strict equality for mtime (could be fine-tuned)
    if entry.get("mtime_iso") is not None:
        entry_dt = parse_iso_utc(entry.get("mtime_iso"))
        if entry_dt is None:
            if entry.get("mtime_iso") != actual_mtime:
                result["issues"].append("MISMATCH_MTIME")
        else:
            # allow 1s tolerance to avoid formatting drift
            if abs((actual_dt - entry_dt).total_seconds()) > 1:
                result["issues"].append("MISMATCH_MTIME")
    if (
        entry.get("git_hash") is not None
        and actual_git is not None
        and entry.get("git_hash") != actual_git
    ):
        result["issues"].append("MISMATCH_GIT_HASH")
    return result


def main():
    ap = argparse.ArgumentParser(
        description="Vérifier manifest JSON (sha256, size, mtime, git hash)"
    )
    ap.add_argument("manifest", help="chemin vers manifest JSON")
    ap.add_argument(
        "--repo-root",
        default=".",
        help="racine du dépôt (pour chemins relatifs, git operations)",
    )
    ap.add_argument("--output", default=None, help="fichier JSON du rapport")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    manifest_path = args.manifest
    if not os.path.exists(manifest_path):
        print("Manifest introuvable:", manifest_path, file=sys.stderr)
        sys.exit(2)

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    entries = manifest.get("entries", [])
    repo_root = os.path.abspath(args.repo_root)

    results = []
    summary = {"total": len(entries), "missing": 0, "ok": 0, "mismatches": 0}
    for e in entries:
        r = check_entry(e, repo_root)
        results.append(r)
        if not r["exists"]:
            summary["missing"] += 1
        elif len(r["issues"]) == 0:
            summary["ok"] += 1
        else:
            summary["mismatches"] += 1

    # output human readable
    print("=" * 60)
    print(f"Manifest: {manifest_path}")
    print(f"Repo root: {repo_root}")
    print(
        f"Entries: {summary['total']}, OK: {summary['ok']}, Missing: {summary['missing']}, Mismatches: {summary['mismatches']}"
    )
    print("=" * 60)
    if args.verbose:
        for r in results:
            print(json.dumps(r, indent=2, ensure_ascii=False))

    if args.output:
        out = {
            "manifest_path": manifest_path,
            "repo_root": repo_root,
            "summary": summary,
            "results": results,
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print("Rapport écrit:", args.output)
    else:
        # print short list of problematic entries
        for r in results:
            if r.get("issues"):
                print(r["path"], "->", ", ".join(r["issues"]))
    # exit code: 0 if all ok or only missing? choose 0 if no mismatches and missing==0
    if summary["mismatches"] == 0 and summary["missing"] == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
