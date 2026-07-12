#!/usr/bin/env python3
"""
LP Export Pipeline — batch extract all 3,325 parcels into one CSV.
Uses v2/exports endpoint: one call, all fields, no 3,325 individual detail calls.
"""
import requests, json, time, os, csv
from datetime import datetime

API_KEY = "lp_live_z5k-VLjQn5gVOnb0NuTLG-rxJ1jtZy7G"  # Replace with new key
BASE = "https://api.landportal.com"
H = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
OUT = "/root/wisconsin-overlay-map/output/subdivision_leads"

# Load all property IDs from the pipeline files
def load_all_property_ids():
    """Extract all property IDs from the raw data or pipeline files."""
    # Read from the raw filtered results
    raw_path = os.path.join(OUT, "raw_filtered_results.json")
    if os.path.exists(raw_path):
        with open(raw_path) as f:
            data = json.load(f)
        ids = []
        for county, props in data.items():
            for p in props:
                pid = p.get("property_id")
                if pid:
                    ids.append(pid)
        return ids
    
    # Fallback: parse from pipeline markdown files
    ids = set()
    pipe_dir = os.path.join(OUT, "by_county")
    for fname in os.listdir(pipe_dir):
        if not fname.endswith("_pipeline.md"):
            continue
        # Property IDs aren't in the markdown - need to get from for_sale_leads.json
    return list(ids)

def main():
    os.makedirs(OUT, exist_ok=True)
    
    # Collect all property IDs
    # Read from for_sale_leads.json and subdivision_leads.json
    all_ids = []
    
    for fname in ["for_sale_leads.json", "subdivision_leads.json"]:
        path = os.path.join(OUT, fname)
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            props = data.get("for_sale", data.get("off_market", []))
            for p in props:
                pid = p.get("property_id")
                if pid:
                    all_ids.append(pid)
    
    if not all_ids:
        # Try to read from raw data
        ids = load_all_property_ids()
        if ids:
            all_ids = ids
    
    all_ids = list(set(all_ids))  # Deduplicate
    print(f"Total unique property IDs: {len(all_ids)}")
    
    if not all_ids:
        print("ERROR: No property IDs found!")
        return
    
    # Create export in batches of 10,000 (API limit)
    batch_size = 10000
    export_ids = []
    
    for i in range(0, len(all_ids), batch_size):
        batch = all_ids[i:i+batch_size]
        print(f"\nBatch {i//batch_size + 1}: {len(batch)} IDs")
        
        payload = {
            "export_type": "property_csv",
            "property_ids": batch
        }
        
        r = requests.post(f"{BASE}/v2/exports", json=payload, headers=H, timeout=30)
        print(f"  HTTP {r.status_code}")
        
        if r.status_code == 200:
            d = r.json()
            export_id = d.get("data", {}).get("export_id")
            rows_left = d.get("meta", {}).get("rows_left", "?")
            print(f"  Export ID: {export_id}, Rows left: {rows_left}")
            export_ids.append(export_id)
        elif r.status_code == 429:
            print(f"  RATE LIMITED: {r.json().get('message', '')}")
            print("  Stopping. Need to regenerate API key or wait for quota reset.")
            break
        else:
            print(f"  ERROR: {r.text[:300]}")
            break
        
        time.sleep(1)
    
    if not export_ids:
        print("\nNo exports created.")
        return
    
    # Poll for completion
    print(f"\n=== POLLING {len(export_ids)} EXPORTS ===")
    completed = {}
    
    for _ in range(30):  # Max 5 minutes
        time.sleep(10)
        r = requests.get(f"{BASE}/v2/exports", headers=H, timeout=10)
        if r.status_code != 200:
            continue
        
        exports = r.json().get("data", {}).get("exports", [])
        for e in exports:
            eid = e.get("export_id")
            status = e.get("status")
            rows = e.get("rows", 0)
            url = e.get("download_url", "")
            
            if eid in export_ids and eid not in completed:
                print(f"  {eid}: {status} ({rows} rows)")
                if status == "completed" and url:
                    completed[eid] = url
                elif status == "failed":
                    print(f"    FAILED: {e.get('error_message', '')}")
        
        if len(completed) == len(export_ids):
            print(f"\nAll {len(completed)} exports completed!")
            break
    
    # Download
    print(f"\n=== DOWNLOADING ===")
    for eid, url in completed.items():
        r = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=60)
        if r.status_code == 200:
            fname = os.path.join(OUT, f"export_{eid[:8]}.csv")
            with open(fname, "wb") as f:
                f.write(r.content)
            print(f"  {fname}: {len(r.content)} bytes")
        else:
            print(f"  {eid}: HTTP {r.status_code}")
    
    print(f"\nDone at {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()