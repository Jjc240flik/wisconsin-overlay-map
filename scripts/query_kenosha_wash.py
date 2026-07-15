#!/usr/bin/env python3
"""Query Land Portal for Kenosha + Washington counties — HIGH towns only."""
import requests, time, json, os

KEY = "lp_live_e3C0PY-2uwItQt3DcW1eH2t-bD0MfjkQ"
BASE = "https://api.landportal.com"
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

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

COUNTIES = {
    "Kenosha": {
        "fips": "55059",
        "high": ["PLEASANT PRAIRIE", "SOMERS", "BRISTOL", "SALEM LAKES"]
    },
    "Washington": {
        "fips": "55131",
        "high": ["GERMANTOWN", "JACKSON", "RICHFIELD", "SLINGER", "HARTFORD"]
    }
}

all_results = {}

for county, info in COUNTIES.items():
    fips = info["fips"]
    towns = info["high"]
    
    print(f"\n=== {county.upper()} COUNTY (FIPS {fips}) ===\n")
    
    # Step 1: Discover municipality names
    print("Discovering municipality names...")
    r = s.get(f"{BASE}/v2/filter-data/filters/municipality/values?fips={fips}", timeout=15)
    time.sleep(0.2)
    
    lp_names = {}
    if r.status_code == 200:
        vals = r.json().get("data",{}).get("values",{})
        for code, name in vals.items():
            lp_names[name.upper()] = name
        print(f"  Found {len(lp_names)} municipality values")
    
    # Map our town names to LP names
    town_map = {}
    for town in towns:
        found = False
        for lp_name in lp_names.values():
            if town in lp_name.upper():
                town_map[town] = lp_name
                found = True
                break
        if not found:
            print(f"  ⚠️ {town}: NOT FOUND in LP municipality list")
            # Show similar names
            for lp_name in lp_names.values():
                if any(w in lp_name.upper() for w in town.split()):
                    print(f"    Maybe: {lp_name}")
    
    county_results = []
    
    for town, lp_name in town_map.items():
        all_om = []
        all_fs = []
        
        # Off-market
        r = s.post(f"{BASE}/v2/filter-data", json={"fips":[fips],"filters":[
            {"key":"municipality","operator":"condition","value":lp_name},
            {"key":"lotsizeacres","operator":"range","value":{"min":20,"max":200}},
            {"key":"vacant","operator":"boolean","value":True},
            {"key":"road_frontage","operator":"range","value":{"min":300}},
            {"key":"wetlands_cover_percentage","operator":"range","value":{"max":25}},
            {"key":"fema_cover_percentage","operator":"range","value":{"max":50}},
            {"key":"sum_up_to_15","operator":"range","value":{"min":50}},
        ]}, timeout=15)
        time.sleep(0.3)
        
        if r.status_code == 200:
            props = r.json().get("data",{}).get("properties",[])
            for p in props:
                if ok(p.get("owner_full_name","")): all_om.append({**p, "_town":town})
        
        # For-sale — all 5 land codes
        for code in ["8000","8001","8008","7000","7001"]:
            r = s.post(f"{BASE}/v2/filter-data", json={"fips":[fips],"filters":[
                {"key":"municipality","operator":"condition","value":lp_name},
                {"key":"landusecode","operator":"condition","value":code},
                {"key":"active_listing_toggle","operator":"active_listing_toggle","value":True},
            ]}, timeout=15)
            time.sleep(0.15)
            
            if r.status_code == 200:
                props = r.json().get("data",{}).get("properties",[])
                for p in props:
                    if ok(p.get("owner_full_name","")): all_fs.append({**p, "_town":town, "_code":code})
        
        om_count = len(all_om)
        fs_count = len({p.get("property_id") for p in all_fs})
        print(f"  {town}: {om_count} OM + {fs_count} FS")
        
        county_results.append({
            "town": town, "lp_name": lp_name, "off_market": all_om, "for_sale": all_fs
        })
    
    all_results[county] = county_results
    
    total_om = sum(len(r["off_market"]) for r in county_results)
    total_fs = sum(len({p.get("property_id") for p in r["for_sale"]}) for r in county_results)
    print(f"  TOTAL: {total_om} OM + {total_fs} FS = {total_om+total_fs}")

# Save results
os.makedirs("/root/wisconsin-overlay-map/output/subdivision_leads/by_county", exist_ok=True)

for county, results in all_results.items():
    out = {"county": county, "towns": results}
    fname = f"/root/wisconsin-overlay-map/output/subdivision_leads/by_county/{county}_leads.json"
    # Clean for JSON
    for r in results:
        r["off_market"] = [p for p in r["off_market"]]
        r["for_sale"] = [p for p in r["for_sale"]]
    with open(fname, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nSaved: {fname}")