#!/usr/bin/env python
import argparse
import json
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def compute_fs_info(repo_root: Path, rel_path: str):
    """
    Calcule les infos réelles sur le FS pour un chemin relatif donné.
    Retourne un dict avec path, size_bytes, size, sha256, mtime, mtime_iso, git_hash.
    """
    rel = Path(rel_path)
    norm_rel = rel.as_posix()
    file_path = repo_root / rel

    st = file_path.stat()
    size_bytes = st.st_size
    mtime = int(st.st_mtime)
    mtime_iso = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    sha256 = h.hexdigest()

    git_hash = None
    try:
        out = subprocess.check_output(
            ["git", "log", "-n", "1", "--pretty=format:%H", "--", norm_rel],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        out = out.strip()
        if out:
            git_hash = out
    except Exception:
        git_hash = None

    return {
        "path": norm_rel,
        "size_bytes": size_bytes,
        "size": size_bytes,
        "sha256": sha256,
        "mtime": mtime,
        "mtime_iso": mtime_iso,
        "git_hash": git_hash,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Synchronise une ou plusieurs entrées de manifest avec le filesystem."
    )
    parser.add_argument(
        "manifest",
        help="Chemin du manifest JSON (ex.: zz-manifests/manifest_master.json)",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help=("Chemins à synchroniser (ex.: zz-data/chapter09/09_metrics_phase.json)"),
    )
    args = parser.parse_args()

    repo_root = Path(".").resolve()
    manifest_path = (repo_root / args.manifest).resolve()

    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Localise le tableau d’entrées
    if "files" in data and isinstance(data["files"], list):
        entries = data["files"]
    elif "entries" in data and isinstance(data["entries"], list):
        entries = data["entries"]
    else:
        raise SystemExit("Manifest ne contient ni tableau 'files' ni 'entries'.")

    total_updated = 0
    synced_paths = []

    for rel in args.paths:
        info = compute_fs_info(repo_root, rel)
        norm_rel = info["path"]

        updated_here = 0
        for entry in entries:
            if entry.get("path") == norm_rel:
                entry["size_bytes"] = info["size_bytes"]
                entry["size"] = info["size"]
                entry["sha256"] = info["sha256"]
                entry["mtime"] = info["mtime"]
                entry["mtime_iso"] = info["mtime_iso"]
                if info["git_hash"] is not None:
                    entry["git_hash"] = info["git_hash"]
                updated_here += 1

        if updated_here == 0:
            print(f"[WARN] Aucune entrée de manifest pour path={norm_rel} – ignoré.")
        else:
            total_updated += updated_here
            synced_paths.append(norm_rel)

    if total_updated == 0:
        print("[INFO] Aucune entrée mise à jour, manifest inchangé.")
        return

    # Incrémente entries_updated
    data["entries_updated"] = int(data.get("entries_updated", 0)) + total_updated

    # Recalcule total_size_bytes si présent
    if "total_size_bytes" in data:
        data["total_size_bytes"] = sum(int(e.get("size_bytes", 0)) for e in entries)

    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print(
        f"Wrote: {manifest_path}  "
        f"(entries_updated={total_updated}, total_size_bytes={data.get('total_size_bytes', 'n/a')})"
    )
    print("  Synced paths:")
    for p in synced_paths:
        print(f"    - {p}")


if __name__ == "__main__":
    main()
