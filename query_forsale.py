#!/usr/bin/env python3
"""
Resume for-sale queries with incremental saving.
"""
import json, time, os, sys, requests
from datetime import datetime

API_KEY = "lp_live_e3C0PY-2uwItQt3DcW1eH2t-bD0MfjkQ"
BASE = "https://api.landportal.com"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
CHECKPOINT_DIR = "/root/wisconsin-overlay-map/checkpoints"

LAND_CODES = ["8000", "8001", "8008", "7000", "7001"]

HIGH_TOWNS = [
    (55087, "VILLAGE OF GREENVILLE"),
    (55087, "TOWN OF GRAND CHUTE"),
    (55087, "VILLAGE OF HARRISON"),
    (55009, "TOWN OF LEDGEVIEW"),
    (55009, "VILLAGE OF HOWARD"),
    (55009, "VILLAGE OF SUAMICO"),
    (55009, "VILLAGE OF BELLEVUE"),
    (55009, "TOWN OF LAWRENCE"),
    (55009, "VILLAGE OF ASHWAUBENON"),
    (55025, "CITY OF VERONA"),
    (55025, "CITY OF FITCHBURG"),
    (55025, "TOWN OF SUN PRAIRIE"),
    (55025, "TOWN OF WESTPORT"),
    (55025, "TOWN OF SPRINGFIELD"),
    (55025, "TOWN OF BURKE"),
    (55025, "TOWN OF BLOOMING GROVE"),
    (55025, "VILLAGE OF DEFOREST"),
    (55133, "VILLAGE OF MENOMONEE FALLS"),
    (55133, "TOWN OF LISBON"),
    (55133, "TOWN OF GENESEE"),
    (55133, "VILLAGE OF PEWAUKEE"),
    (55133, "VILLAGE OF SUSSEX"),
    (55089, "VILLAGE OF GRAFTON"),
    (55089, "VILLAGE OF SAUKVILLE"),
    (55089, "TOWN OF CEDARBURG"),
    (55089, "CITY OF MEQUON"),
    (55105, "BELOIT"),
    (55105, "JANESVILLE"),
    (55105, "TURTLE"),
    (55139, "TOWN OF NEENAH"),
    (55139, "TOWN OF OSHKOSH"),
    (55139, "TOWN OF ALGOMA"),
    (55139, "TOWN OF MENASHA"),
    (55015, "TOWN OF HARRISON"),
    (55015, "TOWN OF MENASHA"),
]

def save_progress(data, name):
    tmp = name + ".tmp"
    path = os.path.join(CHECKPOINT_DIR, tmp)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    os.rename(path, os.path.join(CHECKPOINT_DIR, name))

def load_progress(name):
    path = os.path.join(CHECKPOINT_DIR, name)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def query_for_sale(fips, municipality):
    """Query for-sale parcels for a municipality across all 5 land codes."""
    all_properties = []
    for code in LAND_CODES:
        payload = {
            "fips": [str(fips)],
            "filters": [
                {"key": "municipality", "operator": "condition", "value": municipality},
                {"key": "landusecode", "operator": "condition", "value": code},
                {"key": "active_listing_toggle", "operator": "active_listing_toggle", "value": True},
            ]
        }
        page_token = None
        code_count = 0
        while True:
            params = {}
            if page_token:
                params["page_token"] = page_token
            url = f"{BASE}/v2/filter-data"
            if params:
                qs = "&".join(f"{k}={v}" for k, v in params.items())
                url = f"{url}?{qs}"
            try:
                r = requests.post(url, headers=HEADERS, json=payload, timeout=30)
                if r.status_code != 200:
                    print(f"    (code {code}) ERROR: {r.status_code} {r.text[:100]}")
                    break
                data = r.json().get("data", {})
                props = data.get("properties", [])
                all_properties.extend(props)
                code_count += len(props)
                next_token = data.get("next_page_token", "")
                if not next_token:
                    break
                page_token = next_token
                time.sleep(0.15)
            except Exception as e:
                print(f"    (code {code}) EXCEPTION: {e}")
                break
            time.sleep(0.2)
        if code_count > 0:
            print(f"    code {code}: {code_count}", end=" ", flush=True)
    return all_properties

# Load existing progress
existing = load_progress("for_sale_results.json")
completed_towns = set()
if existing:
    for p in existing:
        completed_towns.add((p.get("_query_fips"), p.get("_query_municipality")))
    print(f"Loaded existing for-sale checkpoint: {len(existing)} parcels from {len(completed_towns)} towns")
else:
    existing = []
    print("Starting fresh for-sale query")

all_for_sale = existing

print(f"\nRunning for-sale queries for {len(HIGH_TOWNS)} towns...")
t0 = time.time()
for i, (fips, municipality) in enumerate(HIGH_TOWNS):
    key = (fips, municipality)
    if key in completed_towns:
        print(f"  [{i+1}/{len(HIGH_TOWNS)}] {municipality} (FIPS {fips})... SKIPPED (already done)")
        continue
    
    print(f"  [{i+1}/{len(HIGH_TOWNS)}] {municipality} (FIPS {fips})...", end=" ", flush=True)
    props = query_for_sale(fips, municipality)
    if props:
        for p in props:
            p["_query_municipality"] = municipality
            p["_query_fips"] = fips
        all_for_sale.extend(props)
        print(f"→ {len(props)} total")
    else:
        print("→ 0")
    
    # Save progress after each town
    save_progress(all_for_sale, "for_sale_results.json")
    print(f"    Saved ({len(all_for_sale)} total)")
    time.sleep(0.2)

elapsed = time.time() - t0
print(f"\nDone! {len(all_for_sale)} for-sale parcels in {elapsed:.0f}s")
save_progress(all_for_sale, "for_sale_results.json")
print("Final checkpoint saved.")