#!/usr/bin/env python3
"""
Slow, paced detail extraction — respects LP rate limits.
1 request every 2 seconds = 30/min = stays under the daily cap.
Saves progress to resume on interruption.
"""
import requests, json, time, os
from datetime import datetime

KEY = "lp_live_e3C0PY-2uwItQt3DcW1eH2t-bD0MfjkQ"
BASE = "https://api.landportal.com"
H = {"Authorization": f"Bearer {KEY}"}
OUT = "/root/wisconsin-overlay-map/output/subdivision_leads"
PROGRESS_FILE = os.path.join(OUT, "detail_progress.json")
RATE_DELAY = 2.0  # seconds between requests
BATCH_PAUSE = 30   # seconds pause every 50 requests

s = requests.Session()
s.headers.update(H)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed": {}, "failed": [], "total": 0, "last_idx": 0}

def save_progress(progress):
    os.makedirs(OUT, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f)

def get_detail(pid):
    try:
        r = s.get(f"{BASE}/v2/properties/{pid}", timeout=15)
        if r.status_code == 200:
            props = r.json().get("data",{}).get("properties",{})
            return {
                "lot_size_acres": props.get("lot_size_acres"),
                "calc_acres": props.get("calc_acres"),
                "current_sale_price": props.get("current_sale_price"),
                "assessed_total_value": props.get("assessed_total_value"),
                "land_use_description": props.get("land_use_description"),
                "zoning": props.get("zoning"),
                "latitude": props.get("latitude"),
                "longitude": props.get("longitude"),
            }
        elif r.status_code == 429:
            return {"_error": "rate_limited"}
        return {"_error": f"http_{r.status_code}"}
    except Exception as e:
        return {"_error": str(e)}

def main():
    progress = load_progress()
    
    # Collect all property IDs that need data
    # Read from raw_filtered_results
    raw_path = os.path.join(OUT, "raw_filtered_results.json")
    with open(raw_path) as f:
        raw = json.load(f)
    
    all_pids = []
    for county, props in raw.items():
        for p in props:
            pid = p.get("property_id")
            if pid:
                all_pids.append({"pid": pid, "county": county})
    
    # Deduplicate
    seen = set()
    unique = []
    for item in all_pids:
        if item["pid"] not in seen:
            seen.add(item["pid"])
            unique.append(item)
    
    if not progress["total"]:
        progress["total"] = len(unique)
        save_progress(progress)
    
    print(f"Total properties: {progress['total']}")
    print(f"Already completed: {len(progress['completed'])}")
    print(f"Failed: {len(progress['failed'])}")
    print(f"Starting from index: {progress['last_idx']}")
    print(f"Rate: 1 per {RATE_DELAY}s, pause {BATCH_PAUSE}s every 50")
    print()
    
    start_idx = progress["last_idx"]
    consecutive_429 = 0
    
    for i in range(start_idx, len(unique)):
        item = unique[i]
        pid = item["pid"]
        
        if str(pid) in progress["completed"]:
            continue
        
        # Fetch
        detail = get_detail(pid)
        
        if detail.get("_error") == "rate_limited":
            consecutive_429 += 1
            print(f"  [{i+1}/{progress['total']}] PID {pid}: RATE LIMITED ({consecutive_429})")
            if consecutive_429 >= 3:
                print(f"  Hit consecutive rate limits. Pausing 5 minutes...")
                time.sleep(300)
                consecutive_429 = 0
            else:
                time.sleep(RATE_DELAY * 3)
            continue
        elif detail.get("_error"):
            print(f"  [{i+1}/{progress['total']}] PID {pid}: ERROR {detail['_error']}")
            progress["failed"].append({"pid": pid, "error": detail["_error"]})
            time.sleep(RATE_DELAY)
            continue
        
        # Success
        consecutive_429 = 0
        detail["pid"] = pid
        detail["county"] = item["county"]
        progress["completed"][str(pid)] = detail
        
        # Show progress
        acres = detail.get("calc_acres") or detail.get("lot_size_acres") or "?"
        price = detail.get("current_sale_price", "")
        pstr = f"${price:,.0f}" if price else ""
        print(f"  [{i+1}/{progress['total']}] PID {pid}: {acres}ac {pstr}")
        
        # Slow pace
        time.sleep(RATE_DELAY)
        
        # Batch pause
        if (i + 1) % 50 == 0 and i > 0:
            print(f"  --- Batch pause {BATCH_PAUSE}s, saving progress ---")
            progress["last_idx"] = i + 1
            save_progress(progress)
            time.sleep(BATCH_PAUSE)
        
        progress["last_idx"] = i + 1
    
    # Final save
    progress["last_idx"] = len(unique)
    save_progress(progress)
    
    # Build acreage lookup
    acreage_map = {}
    for pid_str, detail in progress["completed"].items():
        acres = detail.get("calc_acres") or detail.get("lot_size_acres") or 0
        acreage_map[int(pid_str)] = acres
    
    # Update raw results with acreage
    for county, props in raw.items():
        for p in props:
            pid = p.get("property_id")
            if pid in acreage_map and acreage_map[pid] > 0:
                p["lot_size_acres"] = acreage_map[pid]
    
    with open(raw_path, "w") as f:
        json.dump(raw, f, indent=2)
    
    print(f"\nDone. {len(progress['completed'])} properties fetched.")
    print(f"Raw results updated with acreage.")

if __name__ == "__main__":
    main()