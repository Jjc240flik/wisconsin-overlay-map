#!/usr/bin/env python3
"""
Slow-paced detail extraction: 1 req/2s, 30s pause every 50.
Prioritizes off-market parcels missing acreage, then for-sale.
"""
import json, time, os, sys, requests
from datetime import datetime

API_KEY = "lp_live_e3C0PY-2uwItQt3DcW1eH2t-bD0MfjkQ"
BASE = "https://api.landportal.com"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
CHECKPOINT_DIR = "/root/wisconsin-overlay-map/checkpoints"

RATE_DELAY = 2.0
BATCH_SIZE = 50
BATCH_PAUSE = 30

def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, default=str)
    os.replace(tmp, path)

def get_detail(property_id):
    """Fetch detail for a single property. Returns dict or None."""
    url = f"{BASE}/v2/properties/{property_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r.json().get("data", {})
        elif r.status_code == 429:
            return {"_rate_limited": True}
        elif r.status_code == 404:
            return {"_not_found": True}
        else:
            print(f"    HTTP {r.status_code} for {property_id}")
            return None
    except Exception as e:
        print(f"    Exception for {property_id}: {e}")
        return None

# Load off-market and for-sale data
off = load_json(f"{CHECKPOINT_DIR}/off_market_results.json")
fs = load_json(f"{CHECKPOINT_DIR}/for_sale_results.json")
detail_progress = load_json(f"{CHECKPOINT_DIR}/detail_extraction.json") or {"details": {}, "processed": [], "status": {}}

if not off or not fs:
    print("ERROR: Missing checkpoint files")
    sys.exit(1)

print(f"Off-market: {len(off)} parcels")
print(f"For-sale: {len(fs)} parcels")
print(f"Already processed: {len(detail_progress['details'])} properties")

# Build priority list: off-market missing acres first
fips_wo_acres = {'55087': 'Outagamie', '55133': 'Waukesha', '55139': 'Winnebago'}
off_missing_acres = [p for p in off if p.get('lot_size_acres') is None]
off_with_acres = [p for p in off if p.get('lot_size_acres') is not None]

print(f"\nPriority 1: {len(off_missing_acres)} off-market parcels missing acreage")
print(f"Priority 2: {len(off_with_acres)} off-market with acreage")
print(f"Priority 3: {len(fs)} for-sale parcels")

# All property_ids to process, in priority order
# For off-market missing acres, we need detail (for calc_acres)
# For off-market with acres, we still want detail for sale prices/zoning
# For for-sale, we want detail for sale prices

# Build processing queue
priority_ids = []
for p in off_missing_acres:
    pid = str(p['property_id'])
    if pid not in detail_progress['details']:
        priority_ids.append(p['property_id'])

# Add off-market with acres (for sale prices)
for p in off_with_acres:
    pid = str(p['property_id'])
    if pid not in detail_progress['details']:
        priority_ids.append(p['property_id'])

# Add for-sale (if quota remains)
# Only add for-sale parcels that aren't already in off-market
fs_ids_set = set(p['property_id'] for p in off)
for p in fs:
    pid = p['property_id']
    if pid not in fs_ids_set and str(pid) not in detail_progress['details']:
        priority_ids.append(pid)

print(f"\nQueued for detail extraction: {len(priority_ids)}")
print(f"Estimated time: {len(priority_ids) * RATE_DELAY / 60:.1f} min (at {RATE_DELAY}s/req)")

# Process
consecutive_429 = 0
stats = {"success": 0, "rate_limited": 0, "not_found": 0, "errors": 0}
t0 = time.time()

for i, pid in enumerate(priority_ids):
    # Check if already processed (from a previous run)
    if str(pid) in detail_progress['details']:
        continue
    
    detail = get_detail(pid)
    
    if detail is None:
        stats["errors"] += 1
        detail_progress["processed"].append({"pid": pid, "status": "error", "time": datetime.now().isoformat()})
    elif detail.get("_rate_limited"):
        stats["rate_limited"] += 1
        consecutive_429 += 1
        print(f"  [{i+1}/{len(priority_ids)}] RATE LIMITED (429) — consecutive: {consecutive_429}")
        if consecutive_429 >= 3:
            pause = 300
            print(f"  3 consecutive 429s — pausing {pause}s...")
            time.sleep(pause)
            consecutive_429 = 0
        detail_progress["processed"].append({"pid": pid, "status": "rate_limited", "time": datetime.now().isoformat()})
    elif detail.get("_not_found"):
        stats["not_found"] += 1
        detail_progress["details"][str(pid)] = {"_not_found": True}
        detail_progress["processed"].append({"pid": pid, "status": "not_found", "time": datetime.now().isoformat()})
        consecutive_429 = 0
    else:
        stats["success"] += 1
        # Extract key fields
        acres = detail.get("lot_size_acres") or detail.get("calc_acres") or 0
        apn = detail.get("apn") or detail.get("apn_or_pin") or ""
        owner = detail.get("owner_full_name") or ""
        sale_price = detail.get("sale_price") or detail.get("last_sale_amount") or 0
        sale_date = detail.get("sale_date") or detail.get("last_sale_date") or ""
        zoning = detail.get("zoning_code") or detail.get("zoning") or ""
        street = detail.get("street_address") or ""
        city = detail.get("situs_city") or detail.get("city") or ""
        state = detail.get("situs_state") or detail.get("state") or ""
        zip5 = detail.get("situs_zip5") or detail.get("zip") or ""
        
        detail_progress["details"][str(pid)] = {
            "acres": acres,
            "calc_acres": detail.get("calc_acres"),
            "lot_size_acres": detail.get("lot_size_acres"),
            "apn": apn,
            "owner_full_name": owner,
            "sale_price": sale_price,
            "sale_date": sale_date,
            "zoning_code": zoning,
            "street_address": street,
            "city": city,
            "state": state,
            "zip5": zip5,
        }
        detail_progress["processed"].append({"pid": pid, "status": "success", "time": datetime.now().isoformat()})
        consecutive_429 = 0
    
    # Save progress every request
    if (i + 1) % 5 == 0 or i == len(priority_ids) - 1:
        save_json(f"{CHECKPOINT_DIR}/detail_extraction.json", detail_progress)
    
    # Checkpoint + pause every BATCH_SIZE
    if (i + 1) % BATCH_SIZE == 0 and i < len(priority_ids) - 1:
        save_json(f"{CHECKPOINT_DIR}/detail_extraction.json", detail_progress)
        elapsed = time.time() - t0
        rate = (i + 1) / (elapsed / 60)
        remaining = len(priority_ids) - (i + 1)
        remaining_min = remaining * RATE_DELAY / 60
        print(f"\n  CHECKPOINT [{i+1}/{len(priority_ids)}] — {stats['success']} success, {stats['rate_limited']} rate-limited, {stats['errors']} errors")
        print(f"  Elapsed: {elapsed/60:.1f}min | Rate: {rate:.1f} req/min | Est remaining: {remaining_min:.1f}min")
        print(f"  Pausing {BATCH_PAUSE}s...")
        time.sleep(BATCH_PAUSE)
    
    # Rate limit
    time.sleep(RATE_DELAY)
    
    # Stop if we've hit serious rate limiting
    if stats['rate_limited'] > 5:
        print("\n⚠️  Multiple rate limits hit — stopping to preserve quota.")
        break

# Final save
save_json(f"{CHECKPOINT_DIR}/detail_extraction.json", detail_progress)
elapsed = time.time() - t0
print(f"\n{'='*60}")
print(f"DETAIL EXTRACTION COMPLETE")
print(f"{'='*60}")
print(f"Time: {elapsed/60:.1f} min")
print(f"Success: {stats['success']}")
print(f"Rate limited: {stats['rate_limited']}")
print(f"Not found: {stats['not_found']}")
print(f"Errors: {stats['errors']}")
print(f"Total in DB: {len(detail_progress['details'])}")