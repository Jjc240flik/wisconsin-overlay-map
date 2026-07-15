#!/usr/bin/env python3
"""Test batch: Waukesha County HIGH towns only. Paced for rate limits."""
import requests, time

KEY = "lp_live_e3C0PY-2uwItQt3DcW1eH2t-bD0MfjkQ"
BASE = "https://api.landportal.com"
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
FIPS = "55133"
TOWNS = ["VILLAGE OF MENOMONEE FALLS","TOWN OF LISBON","TOWN OF GENESEE","VILLAGE OF PEWAUKEE","VILLAGE OF SUSSEX"]

s = requests.Session(); s.headers.update(H)

def ok(name):
    if not name: return False
    u = name.upper().strip()
    for t in ["TRUST","TRST","REVOCABLE","REVOCABL","IRREVOCABLE","IRREVOCABL","REV TR","LIV TR","IRREV TR"," REVO"]:
        if t in u: return False
    if u.endswith(" TRST") or u.endswith(" TR"): return False
    for p in ["COUNTY","TOWNSHIP","CITY OF","STATE OF","NATION ","TRIBE","VILLAGE OF","TOWN OF","HOUSING AUTHORITY","DEPT OF","DEPARTMENT OF","DOT","DNR","ELECTRIC POWER","SCHOOL DISTRICT","SANITARY DISTRICT","UNIFIED SCHOOL"]:
        if p in u: return False
    if "OWNERS OF LOTS" in u or "LOT OWNERS OF" in u: return False
    if u in ("AVAILABLE NOT","AVAILABLE NAME NOT","AVAILABLE","NOT AVAILABLE","UNKNOWN","N/A"): return False
    if " INC" in u or " CORP" in u: return False
    if ("LLC" in u or "L L C" in u) and "FARM" not in u: return False
    return True

all_om, all_fs = [], []

for town in TOWNS:
    short = town.replace("VILLAGE OF ","").replace("TOWN OF ","")
    
    # Off-market
    r = s.post(f"{BASE}/v2/filter-data", json={"fips":[FIPS],"filters":[
        {"key":"municipality","operator":"condition","value":town},
        {"key":"lotsizeacres","operator":"range","value":{"min":20,"max":200}},
        {"key":"vacant","operator":"boolean","value":True},
        {"key":"road_frontage","operator":"range","value":{"min":300}},
        {"key":"wetlands_cover_percentage","operator":"range","value":{"max":25}},
        {"key":"fema_cover_percentage","operator":"range","value":{"max":50}},
        {"key":"sum_up_to_15","operator":"range","value":{"min":50}},
    ]}, timeout=15)
    if r.status_code == 200:
        for p in r.json().get("data",{}).get("properties",[]):
            if ok(p.get("owner_full_name","")): all_om.append({**p, "_town":short})
    time.sleep(0.3)
    
    # For-sale
    for code in ["8000","8001","8008","7000","7001"]:
        r = s.post(f"{BASE}/v2/filter-data", json={"fips":[FIPS],"filters":[
            {"key":"municipality","operator":"condition","value":town},
            {"key":"landusecode","operator":"condition","value":code},
            {"key":"active_listing_toggle","operator":"active_listing_toggle","value":True},
        ]}, timeout=15)
        if r.status_code == 200:
            for p in r.json().get("data",{}).get("properties",[]):
                if ok(p.get("owner_full_name","")): all_fs.append({**p, "_town":short})
        time.sleep(0.15)
    
    omc = len([p for p in all_om if p["_town"]==short])
    fsc = len({p.get("property_id") for p in all_fs if p["_town"]==short})
    print(f"  {short}: {omc} OM + {fsc} FS")

# Dedup FS
seen = set()
fs_dedup = []
for p in all_fs:
    pid = p.get("property_id")
    if pid and pid not in seen: seen.add(pid); fs_dedup.append(p)

print(f"\nTotal: {len(all_om)} OM + {len(fs_dedup)} FS = {len(all_om)+len(fs_dedup)}")

# Detail for OM missing acreage
need = [p for p in all_om if not (p.get("lot_size_acres") or 0)]
print(f"Need detail: {len(need)}")

if need:
    print("Paced detail (2s/req, 30s pause/50)...")
    done, c429 = 0, 0
    results = {}
    for i, p in enumerate(need):
        pid = p["property_id"]
        try:
            r = s.get(f"{BASE}/v2/properties/{pid}", timeout=10)
            if r.status_code == 200:
                d = r.json().get("data",{}).get("properties",{})
                results[pid] = {"acres": d.get("lot_size_acres") or d.get("calc_acres") or 0, "price": d.get("current_sale_price") or 0}
                done += 1
                if done % 10 == 0: print(f"  {done}/{len(need)}")
            elif r.status_code == 429:
                c429 += 1
                if c429 >= 3: print(f"  RATE LIMITED at {done}"); break
                time.sleep(5)
            else: results[pid] = {"acres":0,"price":0}
        except: results[pid] = {"acres":0,"price":0}
        time.sleep(2)
        if (i+1) % 50 == 0: time.sleep(30)
    
    for p in all_om:
        if p["property_id"] in results:
            p["lot_size_acres"] = results[p["property_id"]]["acres"]
    print(f"  Detail: {done}/{len(need)}")

# Save
import json, os
os.makedirs("/root/wisconsin-overlay-map/output/subdivision_leads", exist_ok=True)
with open("/root/wisconsin-overlay-map/output/subdivision_leads/waukesha_test.json","w") as f:
    json.dump({"off_market": all_om, "for_sale": fs_dedup}, f, indent=2)

print("\nDone. Saved.")