#!/usr/bin/env python3
# zz-scripts/manifest_tools/remplir_manifest.py
"""
Remplir / mettre à jour un manifest JSON (mise à jour size_bytes, sha256, mtime_iso, git_hash).
Fonctions principales:
 - support --repo-root pour rendre les chemins relatifs et éviter fuite d'info absolue
 - timezone-aware datetimes
 - option --search pour tenter de retrouver un fichier manquant par basename
 - option --sign {gpg,sha256} pour signer le manifeste ou ajouter checksum
Usage:
  python3 remplir_manifest.py zz-manifests/manifest_publication.json --repo-root /home/jplal/MCGT --force --sign sha256
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from fnmatch import fnmatch


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def mtime_iso_of(path):
    st = os.stat(path)
    return datetime.fromtimestamp(st.st_mtime, tz=UTC).isoformat()


def git_hash_of(path, repo_root=None):
    # uses git hash-object (doesn't write object)
    try:
        kwargs = {"capture_output": True, "text": True}
        if repo_root:
            kwargs["cwd"] = repo_root
            # compute relative path from repo_root
            rel = os.path.relpath(path, start=repo_root)
            r = subprocess.run(["git", "hash-object", rel], **kwargs)
        else:
            r = subprocess.run(["git", "hash-object", path], **kwargs)
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return None


def find_by_basename(basename, repo_root, max_results=10):
    matches = []
    for root, dirs, files in os.walk(repo_root):
        if basename in files:
            matches.append(os.path.join(root, basename))
            if len(matches) >= max_results:
                break
    return matches


def should_exclude(path, exclude_patterns):
    for pat in exclude_patterns:
        if fnmatch(path, pat) or fnmatch(os.path.basename(path), pat):
            return True
    return False


def process_manifest(
    manifest_path, repo_root, force=False, exclude_patterns=None, search_missing=False
):
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    entries = manifest.get("entries", [])
    updated = 0
    missing = 0
    for e in entries:
        # determine canonical relative path under repo_root
        entry_path = e.get("path")
        if not entry_path:
            continue
        if should_exclude(entry_path, exclude_patterns or []):
            continue
        # if path is absolute, try to convert to rel if inside repo_root
        if os.path.isabs(entry_path):
            # try to relativize
            try:
                rel = os.path.relpath(entry_path, start=repo_root)
                rel_candidate = rel
            except Exception:
                rel_candidate = entry_path
        else:
            rel_candidate = entry_path

        abs_path = os.path.normpath(os.path.join(repo_root, rel_candidate))
        if not os.path.exists(abs_path) and search_missing:
            # attempt to find by basename
            basename = os.path.basename(rel_candidate)
            found = find_by_basename(basename, repo_root)
            if len(found) == 1:
                abs_path = found[0]
                rel_candidate = os.path.relpath(abs_path, start=repo_root)
                print(f"[search] found unique {basename} -> {rel_candidate}")
            elif len(found) > 1:
                print(f"[search] multiple matches for {basename}, leaving as-is")
            else:
                # not found
                pass

        # update fields only if file exists
        if os.path.exists(abs_path):
            # fill relative path & remove absolute _found_path
            e["found_path_rel"] = os.path.relpath(abs_path, start=repo_root)
            if "_found_path" in e:
                e.pop("_found_path", None)
            st = os.stat(abs_path)
            size_bytes = st.st_size
            mtime_iso = datetime.fromtimestamp(st.st_mtime, tz=UTC).isoformat()
            sha = None
            try:
                sha = sha256_of(abs_path)
            except Exception as exc:
                print(f"Erreur lecture sha256 {abs_path}: {exc}")
            git_hash = git_hash_of(abs_path, repo_root=repo_root)
            # assign/overwrite only if missing or force
            changed = False
            for k, v in (
                ("size_bytes", size_bytes),
                ("mtime_iso", mtime_iso),
                ("sha256", sha),
                ("git_hash", git_hash),
            ):
                if v is None:
                    # skip if cannot compute
                    continue
                if force or e.get(k) is None or e.get(k) != v:
                    e[k] = v
                    changed = True
            if changed:
                updated += 1
        else:
            # file missing
            missing += 1
            e.setdefault("missing", True)
    # Update manifest-level fields
    manifest["generated_at"] = datetime.now(UTC).isoformat()
    # compute totals
    manifest["total_entries"] = len(manifest.get("entries", []))
    total_size = 0
    for e in manifest.get("entries", []):
        sb = e.get("size_bytes")
        if isinstance(sb, int):
            total_size += sb
        else:
            try:
                total_size += int(sb)
            except Exception:
                pass
    manifest["total_size_bytes"] = total_size
    return manifest, updated, missing


def backup_file(path):
    bak = path + ".bak"
    shutil.copy2(path, bak)
    return bak


def sign_manifest(manifest_path, method="sha256"):
    if method == "gpg":
        # try to create detached signature
        sig_path = manifest_path + ".sig"
        try:
            r = subprocess.run(
                [
                    "gpg",
                    "--batch",
                    "--yes",
                    "--output",
                    sig_path,
                    "--detach-sign",
                    manifest_path,
                ]
            )
            if r.returncode == 0:
                return {
                    "signed_by": "gpg",
                    "signature_file": os.path.basename(sig_path),
                }
        except Exception:
            pass
        return {"signed_by": None}
    elif method == "sha256":
        h = sha256_of(manifest_path)
        return {"manifest_signature": {"algorithm": "sha256", "value": h}}
    else:
        return {}


def main():
    ap = argparse.ArgumentParser(
        description="Remplir / mettre à jour manifest JSON (sha256, size, mtime, git_hash)"
    )
    ap.add_argument("manifest", help="chemin vers manifest JSON")
    ap.add_argument(
        "--repo-root",
        default=".",
        help="racine du dépôt (répertoire) — convertira paths en relatifs par rapport à cette racine",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="forcer la réécriture des champs même s'ils sont présents",
    )
    ap.add_argument(
        "--search",
        action="store_true",
        help="si fichier introuvable, tenter une recherche par basename sous repo-root (unique match)",
    )
    ap.add_argument(
        "--exclude",
        action="append",
        help="pattern à exclure (glob) pour ne pas mettre à jour certaines entrées; peut être utilisé plusieurs fois",
    )
    ap.add_argument(
        "--sign",
        choices=["gpg", "sha256"],
        help="signer le manifeste (gpg) ou ajouter digest sha256 (sha256)",
    )
    ap.add_argument(
        "--no-backup", action="store_true", help="ne pas créer de backup (danger !)"
    )
    args = ap.parse_args()

    manifest_path = args.manifest
    repo_root = os.path.abspath(args.repo_root)

    if not os.path.exists(manifest_path):
        print("Manifest non trouvé:", manifest_path, file=sys.stderr)
        sys.exit(2)

    if not args.no_backup:
        bak = backup_file(manifest_path)
        print("Backup créé :", bak)

    manifest, updated_count, missing_count = process_manifest(
        manifest_path,
        repo_root,
        force=args.force,
        exclude_patterns=args.exclude or [],
        search_missing=args.search,
    )

    # write manifest
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Manifest écrit : {manifest_path}")
    print(f"Entries mises à jour : {updated_count}, missing files: {missing_count}")

    # optional signing
    if args.sign:
        sign_info = sign_manifest(manifest_path, method=args.sign)
        # for sha256 we embed signature into the manifest
        if args.sign == "sha256" and "manifest_signature" in sign_info:
            # reload, patch and save
            with open(manifest_path, encoding="utf-8") as f:
                m = json.load(f)
            m["manifest_signature"] = sign_info["manifest_signature"]
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(m, f, indent=2, ensure_ascii=False)
            print("Signature (sha256) ajoutée au manifeste.")
        elif args.sign == "gpg":
            if sign_info.get("signed_by") == "gpg":
                print("Signature GPG produite :", manifest_path + ".sig")
            else:
                print("Signature GPG échouée (gpg non disponible ou erreur).")
    # exit code: 0 normal
    sys.exit(0)


if __name__ == "__main__":
    main()
