#!/usr/bin/env python3
# ruff: noqa: E402
import json
import pathlib
import subprocess
import sys
from importlib import metadata

manifest_path = pathlib.Path("zz-data/chapter10/10_mc_run_manifest.json")
if not manifest_path.exists():
    print("Manifest missing:", manifest_path)
    sys.exit(1)


def sha256(fpath):
    res = subprocess.run(["sha256sum", str(fpath)], capture_output=True, text=True)
    if res.returncode != 0:
        return None
    return res.stdout.split()[0]


files = {
    "ref_phases": "zz-data/chapter09/09_phases_imrphenom.csv",
    "metrics_phase_json": "zz-data/chapter09/09_metrics_phase.json",
    "results_csv": "zz-data/chapter10/10_mc_results.csv",
    "results_agg_csv": "zz-data/chapter10/10_mc_results.agg.csv",
    "best_json": "zz-data/chapter10/10_mc_best.json",
    "milestones_csv": "zz-data/chapter10/10_mc_milestones_eval.csv",
}

h = {}
for k, p in files.items():
    pth = pathlib.Path(p)
    if pth.exists():
        h[k] = {
            "path": str(pth.resolve()),
            "sha256": sha256(pth),
            "size": pth.stat().st_size,
        }
    else:
        h[k] = {"path": str(pth.resolve()), "sha256": None, "size": None}

# versions libs
versions = {}
for pkg in ("numpy", "pandas", "scipy", "matplotlib", "joblib", "pycbc"):
    try:
        versions[pkg] = metadata.version(pkg)
    except Exception:
        versions[pkg] = None

# python version
import platform

pyv = platform.python_version()

m = json.loads(manifest_path.read_text())
m["file_hashes"] = h
m["env"] = {"python_version": pyv, "packages": versions}
manifest_path.write_text(json.dumps(m, indent=2, sort_keys=True, ensure_ascii=False))
print("Manifest mis à jour:", manifest_path)
