#!/usr/bin/env python3
"""
zz-scripts/chapter09/fetch_gwtc3_confident.py

Télécharge (ou tente) la liste d'événements "GWTC-3-confident" depuis GWOSC,
écrit un fichier de configuration minimal dans zz-configuration/ et un cache riche
dans zz-data/chapter09/.

Usage:
    python zz-scripts/chapter09/fetch_gwtc3_confident.py
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sys

OUT_CFG = "zz-configuration/GWTC-3-confident-events.json"
OUT_DATA = "zz-data/chapter09/gwtc3_confident_parameters.json"
URL_BASE = "https://gwosc.org/api/v2/catalogs/GWTC-3-confident/events"


def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8192), b""):
            h.update(b)
    return h.hexdigest(), os.path.getsize(path)


def fetch_with_requests(url):
    import requests

    headers = {"Accept": "application/json", "User-Agent": "mcgt-fetch/1.0"}
    r = requests.get(url, headers=headers, timeout=25)
    r.raise_for_status()
    return r.json()


def fetch_with_urllib(url):
    from urllib.request import Request, urlopen

    req = Request(
        url, headers={"Accept": "application/json", "User-Agent": "mcgt-fetch/1.0"}
    )
    with urlopen(req, timeout=25) as resp:
        data = resp.read()
    return json.loads(data.decode("utf-8", "replace"))


def try_fetch():
    """
    Essaie plusieurs variantes d'URL/format et retourne (obj_json, url_used).
    Lève RuntimeError si tout échoue.
    """
    candidates = [URL_BASE, URL_BASE + "?format=json", URL_BASE + "?format=api"]
    errs = []
    for url in candidates:
        try:
            # prefer requests if available
            try:
                obj = fetch_with_requests(url)
            except Exception:
                obj = fetch_with_urllib(url)
            return obj, url
        except Exception as e:
            errs.append((url, str(e)))
            print(f"[WARN] fetch failed for {url}: {e}", file=sys.stderr)
    raise RuntimeError(f"All fetch attempts failed: {errs}")


def normalize_events(json_obj):
    """
    Normalise structure retournée par l'API:
    - si dict avec key 'events' => événements = that list
    - si dict avec key 'data' => that list
    - si list => use list
    """
    if isinstance(json_obj, list):
        return json_obj
    if isinstance(json_obj, dict):
        if "events" in json_obj and isinstance(json_obj["events"], list):
            return json_obj["events"]
        if "data" in json_obj and isinstance(json_obj["data"], list):
            return json_obj["data"]
        # fallback: pick first list-valued entry
        for v in json_obj.values():
            if isinstance(v, list):
                return v
    # unknown form -> wrap
    return [json_obj]


def build_minimal_and_rich(events_list, url_used):
    event_ids = []
    rich_events = []
    for e in events_list:
        if not isinstance(e, dict):
            # best-effort: string event id
            name = str(e)
            raw = e
        else:
            name = (
                e.get("name")
                or e.get("event_id")
                or e.get("id")
                or e.get("event")
                or e.get("common_name")
            )
            raw = e
        if name is None:
            # generate canonical name if missing
            name = "UNKNOWN"
        event_ids.append(name)
        # extract common numeric fields if present
        f_peak = raw.get("f_peak_Hz") if isinstance(raw, dict) else None
        if f_peak is None:
            f_peak = raw.get("f_peak") if isinstance(raw, dict) else None
        phi_ref = raw.get("phi_ref_at_fpeak") if isinstance(raw, dict) else None
        if phi_ref is None:
            phi_ref = raw.get("phi_ref") if isinstance(raw, dict) else None

        entry = {
            "name": name,
            "source_url": raw.get("url") if isinstance(raw, dict) else None,
            "raw": raw,
        }
        if f_peak is not None:
            entry["f_peak_Hz"] = f_peak
        if phi_ref is not None:
            entry["phi_ref_at_fpeak"] = phi_ref
        rich_events.append(entry)

    now = datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat() + "Z"
    minimal = {
        "catalog": "GWTC-3-confident",
        "source_url": url_used,
        "fetched_at": now,
        "n_events": len(event_ids),
        "event_ids": event_ids,
    }
    rich = {
        "generated_at": now,
        "source_url": url_used,
        "n_events": len(rich_events),
        "events": rich_events,
    }
    return minimal, rich


def safe_write(path, obj):
    tmp = path + ".tmp"
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)
    return sha256_of_file(path)


def main():
    try:
        api_json, url_used = try_fetch()
    except Exception as e:
        print("[ERROR] fetch failed:", e, file=sys.stderr)
        print(
            "→ Si l'API bloque, télécharger manuellement et placer le fichier dans zz-data/chapter09/"
        )
        sys.exit(2)

    events_list = normalize_events(api_json)
    minimal, rich = build_minimal_and_rich(events_list, url_used)

    h_cfg, sz_cfg = safe_write(OUT_CFG, minimal)
    print(f"[WROTE] {OUT_CFG}  sha256={h_cfg}  bytes={sz_cfg}")
    h_data, sz_data = safe_write(OUT_DATA, rich)
    print(f"[WROTE] {OUT_DATA}  sha256={h_data}  bytes={sz_data}")

    print(f"Fetched {minimal['n_events']} events. Minimal & rich files written.")
    print(
        f"Validate with: python -m json.tool {OUT_CFG} && python -m json.tool {OUT_DATA}"
    )


if __name__ == "__main__":
    main()
