#!/usr/bin/env python3
"""
Land Portal query: HIGH-rated towns (A+, A, A-) across 8 counties.
Off-market: 20-200ac, vacant, road_frontage>=300, wetlands<=25%, FEMA<=50%, slope>=50%
For-sale: all 5 land codes (8000,8001,8008,7000,7001) + active_listing_toggle
"""
import json, time, os, sys
from datetime import datetime

API_KEY = "lp_live_e3C0PY-2uwItQt3DcW1eH2t-bD0MfjkQ"
BASE = "https://api.landportal.com"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

CHECKPOINT_DIR = "/root/wisconsin-overlay-map/checkpoints"
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

# ===== MUNICIPALITY MAP =====
# Format: (fips, municipality_name)
HIGH_TOWNS = [
    # Outagamie (55087)
    (55087, "VILLAGE OF GREENVILLE"),
    (55087, "TOWN OF GRAND CHUTE"),
    (55087, "VILLAGE OF HARRISON"),
    # Brown (55009)
    (55009, "TOWN OF LEDGEVIEW"),
    (55009, "VILLAGE OF HOWARD"),
    (55009, "VILLAGE OF SUAMICO"),
    (55009, "VILLAGE OF BELLEVUE"),
    (55009, "TOWN OF LAWRENCE"),
    (55009, "VILLAGE OF ASHWAUBENON"),
    # Dane (55025)
    (55025, "CITY OF VERONA"),
    (55025, "CITY OF FITCHBURG"),
    (55025, "TOWN OF SUN PRAIRIE"),
    (55025, "TOWN OF WESTPORT"),
    (55025, "TOWN OF SPRINGFIELD"),
    (55025, "TOWN OF BURKE"),
    (55025, "TOWN OF BLOOMING GROVE"),
    (55025, "VILLAGE OF DEFOREST"),
    # Waukesha (55133)
    (55133, "VILLAGE OF MENOMONEE FALLS"),
    (55133, "TOWN OF LISBON"),
    (55133, "TOWN OF GENESEE"),
    (55133, "VILLAGE OF PEWAUKEE"),
    (55133, "VILLAGE OF SUSSEX"),
    # Ozaukee (55089)
    (55089, "VILLAGE OF GRAFTON"),
    (55089, "VILLAGE OF SAUKVILLE"),
    (55089, "TOWN OF CEDARBURG"),
    (55089, "CITY OF MEQUON"),
    # Rock (55105)
    (55105, "BELOIT"),
    (55105, "JANESVILLE"),
    (55105, "TURTLE"),
    # Winnebago (55139)
    (55139, "TOWN OF NEENAH"),
    (55139, "TOWN OF OSHKOSH"),
    (55139, "TOWN OF ALGOMA"),
    (55139, "TOWN OF MENASHA"),
    # Calumet (55015)
    (55015, "TOWN OF HARRISON"),
    (55015, "TOWN OF MENASHA"),
]

OFF_MARKET_FILTERS = [
    {"key": "lotsizeacres", "operator": "range", "value": {"min": 20, "max": 200}},
    {"key": "vacant", "operator": "boolean", "value": True},
    {"key": "road_frontage", "operator": "range", "value": {"min": 300}},
    {"key": "wetlands_cover_percentage", "operator": "range", "value": {"max": 25}},
    {"key": "fema_cover_percentage", "operator": "range", "value": {"max": 50}},
    {"key": "sum_up_to_15", "operator": "range", "value": {"min": 50}},
]

LAND_CODES = ["8000", "8001", "8008", "7000", "7001"]

def api_post(endpoint, payload, params=None):
    """POST to filter-data with pagination support."""
    url = f"{BASE}{endpoint}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    r = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    return r

def query_off_market(fips, municipality):
    """Query off-market parcels for a municipality."""
    payload = {
        "fips": [str(fips)],
        "filters": [
            {"key": "municipality", "operator": "condition", "value": municipality},
            *OFF_MARKET_FILTERS,
        ]
    }
    
    all_properties = []
    page_token = None
    
    while True:
        params = {}
        if page_token:
            params["page_token"] = page_token
        
        r = api_post("/v2/filter-data", payload, params)
        if r.status_code != 200:
            print(f"  ERROR: {r.status_code} {r.text[:200]}")
            return all_properties
        
        data = r.json().get("data", {})
        props = data.get("properties", [])
        all_properties.extend(props)
        
        next_token = data.get("next_page_token", "")
        if not next_token:
            break
        page_token = next_token
        time.sleep(0.15)
    
    return all_properties


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
        while True:
            params = {}
            if page_token:
                params["page_token"] = page_token
            
            r = api_post("/v2/filter-data", payload, params)
            if r.status_code != 200:
                print(f"    (code {code}) ERROR: {r.status_code}")
                break
            
            data = r.json().get("data", {})
            props = data.get("properties", [])
            all_properties.extend(props)
            
            next_token = data.get("next_page_token", "")
            if not next_token:
                break
            page_token = next_token
            time.sleep(0.15)
        
        time.sleep(0.2)  # small delay between codes
    
    return all_properties


def save_checkpoint(data, name):
    """Save data to a checkpoint file."""
    path = os.path.join(CHECKPOINT_DIR, name)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    return path


def load_checkpoint(name):
    """Load data from a checkpoint file."""
    path = os.path.join(CHECKPOINT_DIR, name)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


# Import requests
import requests

# ===== MAIN =====
print("=" * 70)
print(f"LAND PORTAL QUERY — HIGH TOWNS ONLY")
print(f"Started: {datetime.now().isoformat()}")
print("=" * 70)

# Check for existing progress
existing_off = load_checkpoint("off_market_results.json")
existing_forsale = load_checkpoint("for_sale_results.json")
existing_detail = load_checkpoint("detail_extraction.json")

if existing_off and existing_forsale:
    print(f"\nFound existing checkpoints:")
    print(f"  Off-market: {len(existing_off)} parcels")
    print(f"  For-sale: {len(existing_forsale)} parcels")
    print(f"  Detail progress: {len(existing_detail.get('details', {})) if existing_detail else 0} properties")
    
    # Only do detail extraction if already have data
    all_off_ids = set(p["property_id"] for p in existing_off)
    all_forsale_ids = set(p["property_id"] for p in existing_forsale)
    processed_ids = set(existing_detail.get("details", {}).keys()) if existing_detail else set()
    remaining = (all_off_ids | all_forsale_ids) - processed_ids
    print(f"  Remaining for detail extraction: {len(remaining)}")

print("\n" + "=" * 70)
print("PHASE 1: OFF-MARKET QUERIES")
print("=" * 70)

if not existing_off:
    all_off_market = []
    town_counts = {}
    
    for i, (fips, municipality) in enumerate(HIGH_TOWNS):
        print(f"\n  [{i+1}/{len(HIGH_TOWNS)}] {municipality} (FIPS {fips})...", end=" ", flush=True)
        props = query_off_market(fips, municipality)
        if props:
            # Tag each property with its municipality
            for p in props:
                p["_query_municipality"] = municipality
                p["_query_fips"] = fips
            all_off_market.extend(props)
            town_counts[municipality] = len(props)
            print(f"{len(props)} parcels")
        else:
            print("0 parcels")
        time.sleep(0.15)
    
    print(f"\n  TOTAL off-market: {len(all_off_market)} parcels across {len(town_counts)} towns")
    for t, c in sorted(town_counts.items(), key=lambda x: -x[1]):
        print(f"    {t}: {c}")
    
    save_checkpoint(all_off_market, "off_market_results.json")
    print(f"  Saved to checkpoints/off_market_results.json")
else:
    print(f"  Using existing checkpoint: {len(existing_off)} parcels")
    all_off_market = existing_off

print("\n" + "=" * 70)
print("PHASE 2: FOR-SALE QUERIES")
print("=" * 70)

if not existing_forsale:
    all_for_sale = []
    forsale_town_counts = {}
    
    for i, (fips, municipality) in enumerate(HIGH_TOWNS):
        print(f"\n  [{i+1}/{len(HIGH_TOWNS)}] {municipality} (FIPS {fips})...", end=" ", flush=True)
        props = query_for_sale(fips, municipality)
        if props:
            for p in props:
                p["_query_municipality"] = municipality
                p["_query_fips"] = fips
            all_for_sale.extend(props)
            forsale_town_counts[municipality] = len(props)
            print(f"{len(props)} parcels")
        else:
            print("0 parcels")
        time.sleep(0.15)
    
    print(f"\n  TOTAL for-sale: {len(all_for_sale)} parcels across {len(forsale_town_counts)} towns")
    for t, c in sorted(forsale_town_counts.items(), key=lambda x: -x[1]):
        print(f"    {t}: {c}")
    
    save_checkpoint(all_for_sale, "for_sale_results.json")
    print(f"  Saved to checkpoints/for_sale_results.json")
else:
    print(f"  Using existing checkpoint: {len(existing_forsale)} parcels")
    all_for_sale = existing_forsale

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"  Off-market: {len(all_off_market)} parcels")
print(f"  For-sale:   {len(all_for_sale)} parcels")
print(f"  Total:      {len(all_off_market) + len(all_for_sale)} parcels")

# Save combined summary
summary = {
    "generated_at": datetime.now().isoformat(),
    "off_market_count": len(all_off_market),
    "for_sale_count": len(all_for_sale),
    "total_count": len(all_off_market) + len(all_for_sale),
    "towns_queried": len(HIGH_TOWNS),
}
save_checkpoint(summary, "query_summary.json")
print(f"\n  Summary saved to checkpoints/query_summary.json")