#!/usr/bin/env python3
"""
North Star Subdivision Pipeline v4.0
Outputs directly into docs/TOP_COUNTIES/ — one file per county.
Grading based on future zoning/FLU expansion areas, not growth rate.
"""
import json, os, time, requests
from collections import Counter, defaultdict
from datetime import datetime

API_KEY = "lp_live_z5k-VLjQn5gVOnb0NuTLG-rxJ1jtZy7G"
BASE_URL = "https://api.landportal.com"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
OUTPUT_DIR = "/root/wisconsin-overlay-map/docs/TOP_COUNTIES"

COUNTY_FIPS = {
    "Outagamie": "55087", "Brown": "55009", "Dane": "55025",
    "Waukesha": "55133", "Ozaukee": "55089", "Milwaukee": "55079",
    "Rock": "55105", "Winnebago": "55139", "Calumet": "55015", "Door": "55029"
}

# ZIP -> [(town, flu_zone, county, notes)]
# flu_zone: "PRIMARY" = in FLU expansion path, "EDGE" = adjacent, "SECONDARY" = near but not in path
ZIP_TOWNS = {
    "54942": [("Greenville", "PRIMARY", "Outagamie", "FLU map adopted. Water/wastewater master plans. 7 sub-area growth zones.")],
    "54913": [("Grand Chute", "PRIMARY", "Outagamie", "Surrounds Appleton. FLU shows residential expansion along US 41.")],
    "54956": [("Harrison Village", "PRIMARY", "Outagamie", "East of Appleton. US 10 corridor. Planned residential."),
              ("Harrison Town", "PRIMARY", "Calumet", "South of Appleton. US 41/10 corridor."),
              ("Neenah Town", "PRIMARY", "Winnebago", "Adjacent to Neenah/Menasha. FLU residential."),
              ("Vinland", "EDGE", "Winnebago", "North of Neenah. Edge growth."),
              ("Clayton", "EDGE", "Winnebago", "SW of Neenah."),
              ("Fox Crossing", "EDGE", "Winnebago", "Between Neenah and Menasha.")],
    "54113": [("Combined Locks", "PRIMARY", "Outagamie", "Adjacent to Kaukauna. Fox Cities core. Sewer/water.")],
    "54140": [("Little Chute", "PRIMARY", "Outagamie", "Fox Cities core. Strong metro expansion pressure.")],
    "54130": [("Buchanan", "EDGE", "Outagamie", "Surrounds Kaukauna. In outward expansion path.")],
    "54966": [("Freedom", "EDGE", "Outagamie", "SW of Appleton. Adjacent to city. Check FLU + sewer.")],
    "54136": [("Kimberly", "EDGE", "Outagamie", "Fox Cities core. Limited land, infill potential.")],
    "54313": [("Ashwaubenon", "PRIMARY", "Brown", "Adjacent to Green Bay. I-41. Sewer/water."),
              ("Howard", "PRIMARY", "Brown", "North of Green Bay. Residential expansion."),
              ("Suamico", "PRIMARY", "Brown", "North of Howard. Active subdivisions."),
              ("Scott", "EDGE", "Brown", "Near Howard. Growth along roads.")],
    "54311": [("Bellevue", "PRIMARY", "Brown", "East of Green Bay. Steady residential growth.")],
    "54115": [("Ledgeview", "PRIMARY", "Brown", "Fastest growing. Near De Pere expansion boundary."),
              ("Lawrence", "PRIMARY", "Brown", "Strong growth. I-41/I-43 access."),
              ("Humboldt", "EDGE", "Brown", "East of Green Bay. Edge growth.")],
    "54301": [("Allouez", "EDGE", "Brown", "Adjacent to Green Bay. Mostly built out.")],
    "53711": [("Fitchburg", "PRIMARY", "Dane", "South of Madison. Major residential. Sewer/water expanding.")],
    "53593": [("Verona", "PRIMARY", "Dane", "Epic Systems corridor. Massive demand."),
              ("Dunn", "EDGE", "Dane", "SW of Madison. Edge near Fitchburg/Verona.")],
    "53590": [("Sun Prairie Town", "PRIMARY", "Dane", "Surrounds city. FLU residential."),
              ("Burke", "PRIMARY", "Dane", "Between Madison and Sun Prairie."),
              ("Bristol", "EDGE", "Dane", "North of Sun Prairie.")],
    "53562": [("Westport", "PRIMARY", "Dane", "Between Middleton and Lake Mendota."),
              ("Springfield", "PRIMARY", "Dane", "North of Middleton.")],
    "53716": [("Blooming Grove", "PRIMARY", "Dane", "East of Madison.")],
    "53558": [("Pleasant Springs", "EDGE", "Dane", "South of Madison."),
              ("McFarland", "EDGE", "Dane", "SE of Madison. Lake Waubesa.")],
    "53575": [("Montrose", "EDGE", "Dane", "SE of Oregon."),
              ("Oregon", "EDGE", "Dane", "SW metro. FLU + sewer.")],
    "53597": [("Waunakee", "EDGE", "Dane", "NW metro. Strong pressure.")],
    "53532": [("DeForest", "EDGE", "Dane", "North metro. I-39/90/94.")],
    "53598": [("Windsor", "EDGE", "Dane", "North metro.")],
    "53051": [("Menomonee Falls", "PRIMARY", "Waukesha", "NE edge near Milwaukee. Strong expansion.")],
    "53089": [("Lisbon", "PRIMARY", "Waukesha", "Between Menomonee Falls and Pewaukee. FLU residential."),
              ("Sussex", "PRIMARY", "Waukesha", "Between Waukesha and Menomonee Falls.")],
    "53186": [("Genesee", "PRIMARY", "Waukesha", "Near Waukesha/Milwaukee edge."),
              ("Waukesha Town", "PRIMARY", "Waukesha", "Adjacent to city.")],
    "53072": [("Pewaukee Village", "PRIMARY", "Waukesha", "I-94 corridor. Growing rapidly.")],
    "53005": [("Brookfield Town", "PRIMARY", "Waukesha", "Adjacent to both cities.")],
    "53046": [("Lannon", "EDGE", "Waukesha", "Near Menomonee Falls.")],
    "53092": [("Mequon", "PRIMARY", "Ozaukee", "Milwaukee north shore. I-43. High-value.")],
    "53024": [("Grafton Village", "PRIMARY", "Ozaukee", "I-43 corridor. Growing."),
              ("Grafton Town", "EDGE", "Ozaukee", "I-43 corridor edge.")],
    "53080": [("Saukville", "PRIMARY", "Ozaukee", "I-43 north. Expansion potential.")],
    "53012": [("Cedarburg Town", "PRIMARY", "Ozaukee", "Adjacent to cities. FLU residential."),
              ("Cedarburg City", "EDGE", "Ozaukee", "I-43 corridor. Bedroom community.")],
    "53132": [("Franklin", "SECONDARY", "Milwaukee", "Most greenfield in county. Southern edge.")],
    "53154": [("Oak Creek", "SECONDARY", "Milwaukee", "SE edge. Growth corridor.")],
    "53511": [("Beloit Town", "PRIMARY", "Rock", "Adjacent to Beloit. Illinois line. Stateline corridor."),
              ("Turtle", "PRIMARY", "Rock", "Southern edge. Stateline corridor."),
              ("Harmony", "EDGE", "Rock", "East of Janesville.")],
    "53545": [("Janesville Town", "PRIMARY", "Rock", "Surrounds Janesville. FLU residential.")],
    "53536": [("Evansville", "EDGE", "Rock", "North metro. Bedroom community.")],
    "53563": [("Milton Town", "EDGE", "Rock", "Near City of Milton.")],
    "53534": [("Fulton", "EDGE", "Rock", "NE of Janesville.")],
    "54952": [("Menasha Town", "PRIMARY", "Winnebago", "Surrounds Menasha."),
              ("Menasha Calumet Town", "PRIMARY", "Calumet", "Adjacent to Menasha/Appleton.")],
    "54901": [("Oshkosh Town", "PRIMARY", "Winnebago", "South of Oshkosh. US 41."),
              ("Algoma", "PRIMARY", "Winnebago", "North of Oshkosh. US 41.")],
    "53088": [("Stockbridge", "EDGE", "Calumet", "Lake Winnebago. Growing.")],
    "53014": [("Brothertown", "EDGE", "Calumet", "Lakeshore.")],
    "54234": [("Sister Bay", "EDGE", "Door", "Tourism corridor. Seasonal.")],
}

session = requests.Session()
session.headers.update(HEADERS)

def should_keep(name):
    if not name: return False
    u = name.upper().strip()
    trusts = ["TRUST", "TRST", "REVOCABLE", "REVOCABL", "IRREVOCABLE", "IRREVOCABL", "REV TR", "LIV TR", "IRREV TR", " REVO"]
    if any(t in u for t in trusts): return False
    if u.endswith(" TRST") or u.endswith(" TR"): return False
    if any(p in u for p in ["COUNTY", "TOWNSHIP", "CITY OF", "STATE OF", "NATION ", "TRIBE", "VILLAGE OF", "TOWN OF", "HOUSING AUTHORITY", "DEPT OF", "DEPARTMENT OF", "DOT", "DNR", "ELECTRIC POWER", "SCHOOL DISTRICT", "SANITARY DISTRICT"]): return False
    if any(p in u for p in ["OWNERS OF LOTS", "LOT OWNERS OF", "HOMEOWNERS ASSOC"]): return False
    if u in ("AVAILABLE NOT", "AVAILABLE NAME NOT", "AVAILABLE", "NOT AVAILABLE", "UNKNOWN", "N/A"): return False
    if " INC" in u or " CORP" in u or " INC." in u: return False
    if ("LLC" in u or "L L C" in u) and "FARM" not in u: return False
    return True

def query_off_market(fips, zip_code, page_token=None):
    payload = {
        "fips": [fips],
        "filters": [
            {"key": "situszip5", "operator": "condition", "value": zip_code},
            {"key": "lotsizeacres", "operator": "range", "value": {"min": 20, "max": 300}},
            {"key": "vacant", "operator": "boolean", "value": True},
            {"key": "road_frontage", "operator": "range", "value": {"min": 400}},
            {"key": "wetlands_cover_percentage", "operator": "range", "value": {"max": 30}},
            {"key": "fema_cover_percentage", "operator": "range", "value": {"max": 50}},
        ]
    }
    url = f"{BASE_URL}/v2/filter-data"
    if page_token: url += f"?page_token={page_token}"
    try:
        resp = session.post(url, json=payload, timeout=30)
        return resp.json() if resp.status_code == 200 else None
    except: return None

def query_for_sale(fips, zip_code):
    payload = {
        "fips": [fips],
        "filters": [
            {"key": "situszip5", "operator": "condition", "value": zip_code},
            {"key": "landusecode", "operator": "condition", "value": "8001"},
            {"key": "active_listing_toggle", "operator": "active_listing_toggle", "value": True},
        ]
    }
    try:
        resp = session.post(f"{BASE_URL}/v2/filter-data", json=payload, timeout=30)
        return resp.json() if resp.status_code == 200 else None
    except: return None

# Query off-market
print("=== OFF-MARKET (North Star criteria) ===")
off_market_raw = []
queried = set()
for zip_code, towns in ZIP_TOWNS.items():
    for _, _, county, _ in towns:
        fips = COUNTY_FIPS[county]
        key = (fips, zip_code)
        if key in queried: continue
        queried.add(key)
        
        result = query_off_market(fips, zip_code)
        if not result: continue
        data = result.get("data", {})
        props = data.get("properties", [])
        next_token = data.get("next_page_token", "")
        all_page = list(props)
        while next_token:
            result = query_off_market(fips, zip_code, next_token)
            if not result: break
            more = result.get("data", {}).get("properties", [])
            next_token = result.get("data", {}).get("next_page_token", "")
            all_page.extend(more)
            time.sleep(0.3)
        for p in all_page:
            p["_source"] = "off-market"; p["_zip"] = zip_code; p["_county"] = county
        off_market_raw.extend(all_page)
        print(f"  {zip_code} ({county}): {len(all_page)}")
        time.sleep(0.3)

# Query for-sale
print(f"\n=== FOR-SALE (MLS land) ===")
for_sale_raw = []
queried_fs = set()
for zip_code, towns in ZIP_TOWNS.items():
    for _, _, county, _ in towns:
        fips = COUNTY_FIPS[county]
        key = (fips, zip_code)
        if key in queried_fs: continue
        queried_fs.add(key)
        result = query_for_sale(fips, zip_code)
        if not result: continue
        props = result.get("data", {}).get("properties", [])
        for p in props:
            p["_source"] = "for-sale"; p["_zip"] = zip_code; p["_county"] = county
        for_sale_raw.extend(props)
        print(f"  {zip_code} ({county}): {len(props)}")
        time.sleep(0.2)

# Deduplicate and filter
seen_om = set()
off_market = []
for p in off_market_raw:
    pid = p.get("property_id")
    if pid and pid not in seen_om and should_keep(p.get("owner_full_name", "")):
        seen_om.add(pid); off_market.append(p)

seen_fs = set()
for_sale = []
for p in for_sale_raw:
    pid = p.get("property_id")
    if pid and pid not in seen_fs and should_keep(p.get("owner_full_name", "")):
        seen_fs.add(pid); for_sale.append(p)
        if pid in seen_om:
            off_market = [x for x in off_market if x.get("property_id") != pid]
            seen_om.discard(pid)

print(f"\nOff-market: {len(off_market)}, For-sale: {len(for_sale)}")

# Build entries
all_entries = []
for p in off_market + for_sale:
    zip_code = p.get("_zip", "")
    county = p.get("_county", "")
    source = p.get("_source", "off-market")
    towns = [t for t in ZIP_TOWNS.get(zip_code, []) if t[2] == county]
    if not towns: towns = [(f"ZIP {zip_code}", "SECONDARY", county, "")]
    
    town_name, flu_zone, _, notes = towns[0]
    
    # Grade based on FLU zone
    if flu_zone == "PRIMARY":
        grade = "HIGH"
    elif flu_zone == "EDGE":
        grade = "MOD"
    else:
        grade = "LOW"
    
    all_entries.append({
        "apn": p.get("apn", ""),
        "address": p.get("street_address", ""),
        "owner": p.get("owner_full_name", ""),
        "acres": p.get("lot_size_acres", 0) or 0,
        "county": county,
        "town": town_name,
        "zip": zip_code,
        "flu_zone": flu_zone,
        "grade": grade,
        "source": source,
        "notes": notes,
        "property_id": p.get("property_id"),
    })

# Multi-property
owner_counts = Counter(e["owner"] for e in all_entries if e["owner"])
multi = {o: c for o, c in owner_counts.items() if c >= 2}
for e in all_entries:
    e["multi"] = e["owner"] in multi
    e["owner_count"] = multi.get(e["owner"], 1)

# Sort: grade, then acres desc
grade_order = {"HIGH": 0, "MOD": 1, "LOW": 2}
for e in all_entries:
    e["_sort"] = (grade_order.get(e["grade"], 5), -e["acres"])
all_entries.sort(key=lambda e: e["_sort"])

# Generate per-county pipeline files
os.makedirs(OUTPUT_DIR, exist_ok=True)

for county in COUNTY_FIPS:
    entries = [e for e in all_entries if e["county"] == county]
    if not entries: continue
    
    by_town = defaultdict(list)
    for e in entries: by_town[e["town"]].append(e)
    
    om = len([e for e in entries if e["source"] == "off-market"])
    fs = len([e for e in entries if e["source"] == "for-sale"])
    
    lines = []
    lines.append(f"## {county} County — Subdivision Pipeline")
    lines.append("")
    lines.append(f"**{len(entries)} parcels** | {om} off-market (mail) | {fs} for-sale (call)")
    lines.append("")
    lines.append("### Parcels Ranked by Future Zoning / FLU")
    lines.append("")
    lines.append("| Zone | Town | Acres | Owner | APN | Status |")
    lines.append("|---|---|---|---|---|---|")
    
    for e in entries:
        status = "📞 MLS" if e["source"] == "for-sale" else "📬 Mail"
        mp = " 🔗" if e["multi"] else ""
        ac = f"{e['acres']:.1f}" if e.get("acres") else "?"
        lines.append(f"| {e['grade']} | {e['town']} | {ac} | {e['owner']}{mp} | {e['apn']} | {status} |")
    
    lines.append("")
    
    # Cluster analysis
    lines.append("### North Star Takeaway")
    lines.append("")
    
    clusters = {town: parcels for town, parcels in by_town.items() if len(parcels) >= 3}
    for town, parcels in sorted(clusters.items(), key=lambda x: -sum(e["acres"] for e in x[1])):
        total_acres = sum(e["acres"] for e in parcels)
        flu = parcels[0]["flu_zone"]
        grade = parcels[0]["grade"]
        notes = parcels[0]["notes"]
        multi_owners = len(set(e["owner"] for e in parcels if e["multi"]))
        
        lines.append(f"#### {town} — {len(parcels)} parcels, ~{total_acres:.0f} acres ({grade}, {flu})")
        lines.append(f"- **{len(parcels)} parcels** totaling ~{total_acres:.0f} acres")
        if notes: lines.append(f"- **FLU context:** {notes}")
        if multi_owners: lines.append(f"- **{multi_owners} multi-property owners** in this cluster")
        lines.append("")
    
    # Call vs Mail breakdown
    fs_towns = defaultdict(list)
    om_towns = defaultdict(list)
    for e in entries:
        if e["source"] == "for-sale": fs_towns[e["town"]].append(e)
        else: om_towns[e["town"]].append(e)
    
    if fs_towns:
        lines.append("#### 📞 For-Sale Priority (Call)")
        for town, parcels in sorted(fs_towns.items(), key=lambda x: -len(x[1])):
            lines.append(f"- **{town}**: {len(parcels)} MLS-listed parcels")
    
    if om_towns:
        lines.append("")
        lines.append("#### 📬 Off-Market Priority (Mail)")
        for town, parcels in sorted(om_towns.items(), key=lambda x: -len(x[1])):
            multi_count = len(set(e["owner"] for e in parcels if e["multi"]))
            line = f"- **{town}**: {len(parcels)} parcels"
            if multi_count: line += f" — {multi_count} multi-owners"
            lines.append(line)
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Read the existing county file and append the pipeline data
    county_file = os.path.join(OUTPUT_DIR, f"{county}_County.md")
    
    # Check if existing file has the pipeline section
    existing_content = ""
    if os.path.exists(county_file):
        with open(county_file) as f:
            existing_content = f.read()
    
    # Remove any existing pipeline section
    if "## Subdivision Pipeline" in existing_content:
        existing_content = existing_content.split("## Subdivision Pipeline")[0].rstrip()
    
    # Append new pipeline section
    pipeline_section = "\n\n## Subdivision Pipeline\n\n" + "\n".join(lines)
    new_content = existing_content + pipeline_section
    
    with open(county_file, "w") as f:
        f.write(new_content)
    
    print(f"  {county}: {len(entries)} entries -> {county_file}")

print(f"\n===== DONE =====")
print(f"Off-market: {len(off_market)}, For-sale: {len(for_sale)}, Total: {len(all_entries)}")
for county in COUNTY_FIPS:
    e = [x for x in all_entries if x["county"] == county]
    print(f"  {county}: {len(e)}")