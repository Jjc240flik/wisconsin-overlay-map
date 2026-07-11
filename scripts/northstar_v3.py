#!/usr/bin/env python3
"""
North Star Subdivision Pipeline v3.0
Town-level grading, unified for-sale + off-market, North Star Takeaways.
"""
import json, os, time, requests
from collections import Counter, defaultdict
from datetime import datetime

API_KEY = "lp_live_z5k-VLjQn5gVOnb0NuTLG-rxJ1jtZy7G"
BASE_URL = "https://api.landportal.com"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
OUTPUT_DIR = "/root/wisconsin-overlay-map/output/subdivision_leads"

COUNTY_FIPS = {
    "Outagamie": "55087", "Brown": "55009", "Dane": "55025",
    "Waukesha": "55133", "Ozaukee": "55089", "Milwaukee": "55079",
    "Rock": "55105", "Winnebago": "55139", "Calumet": "55015", "Door": "55029"
}

# ZIP -> [(town, growth_rating, county)]
ZIP_TOWNS = {
    "54942": [("Greenville", "High", "Outagamie")],
    "54913": [("Grand Chute", "High", "Outagamie")],
    "54956": [("Harrison Village", "High", "Outagamie"), ("Harrison Town", "High", "Calumet"), ("Neenah Town", "High", "Winnebago"), ("Vinland", "Moderate to High", "Winnebago"), ("Clayton", "Moderate to High", "Winnebago"), ("Fox Crossing", "Moderate to High", "Winnebago")],
    "54113": [("Combined Locks", "High", "Outagamie")],
    "54140": [("Little Chute", "High", "Outagamie")],
    "54130": [("Buchanan", "Moderate to High", "Outagamie")],
    "54966": [("Freedom", "Moderate to High", "Outagamie")],
    "54136": [("Kimberly", "Moderate to High", "Outagamie")],
    "54313": [("Ashwaubenon", "High", "Brown"), ("Howard", "High", "Brown"), ("Suamico", "High", "Brown"), ("Scott", "Moderate to High", "Brown")],
    "54311": [("Bellevue", "High", "Brown")],
    "54115": [("Ledgeview", "High", "Brown"), ("Lawrence", "High", "Brown"), ("Humboldt", "Moderate to High", "Brown")],
    "54301": [("Allouez", "Moderate to High", "Brown")],
    "53711": [("Fitchburg", "High", "Dane")],
    "53593": [("Verona", "High", "Dane"), ("Dunn", "Moderate to High", "Dane")],
    "53590": [("Sun Prairie Town", "High", "Dane"), ("Burke", "High", "Dane"), ("Bristol", "Moderate to High", "Dane")],
    "53562": [("Westport", "High", "Dane"), ("Springfield", "High", "Dane")],
    "53716": [("Blooming Grove", "High", "Dane")],
    "53558": [("Pleasant Springs", "Moderate to High", "Dane"), ("McFarland", "Moderate to High", "Dane")],
    "53575": [("Montrose", "Moderate to High", "Dane"), ("Oregon", "Moderate to High", "Dane")],
    "53597": [("Waunakee", "Moderate to High", "Dane")],
    "53532": [("DeForest", "Moderate to High", "Dane")],
    "53598": [("Windsor", "Moderate to High", "Dane")],
    "53051": [("Menomonee Falls", "High", "Waukesha")],
    "53089": [("Lisbon", "High", "Waukesha"), ("Sussex", "High", "Waukesha")],
    "53186": [("Genesee", "High", "Waukesha"), ("Waukesha Town", "High", "Waukesha")],
    "53072": [("Pewaukee Village", "High", "Waukesha")],
    "53005": [("Brookfield Town", "High", "Waukesha")],
    "53046": [("Lannon", "Moderate to High", "Waukesha")],
    "53092": [("Mequon", "High", "Ozaukee")],
    "53024": [("Grafton Village", "High", "Ozaukee"), ("Grafton Town", "Moderate to High", "Ozaukee")],
    "53080": [("Saukville", "High", "Ozaukee")],
    "53012": [("Cedarburg Town", "High", "Ozaukee"), ("Cedarburg City", "Moderate to High", "Ozaukee")],
    "53132": [("Franklin", "Moderate", "Milwaukee")],
    "53154": [("Oak Creek", "Moderate", "Milwaukee")],
    "53511": [("Beloit Town", "High", "Rock"), ("Turtle", "High", "Rock"), ("Harmony", "Moderate to High", "Rock")],
    "53545": [("Janesville Town", "High", "Rock")],
    "53536": [("Evansville", "Moderate to High", "Rock")],
    "53563": [("Milton Town", "Moderate to High", "Rock")],
    "53534": [("Fulton", "Moderate to High", "Rock")],
    "54952": [("Menasha Town", "High", "Winnebago"), ("Menasha Calumet Town", "High", "Calumet")],
    "54901": [("Oshkosh Town", "High", "Winnebago"), ("Algoma", "High", "Winnebago")],
    "53088": [("Stockbridge", "Moderate to High", "Calumet")],
    "53014": [("Brothertown", "Moderate to High", "Calumet")],
    "54234": [("Sister Bay", "Moderate to High", "Door")],
}

# Which ZIPs go to which county FIPS
ZIP_FIPS = {}
for zip_code, towns in ZIP_TOWNS.items():
    for _, _, county in towns:
        if zip_code not in ZIP_FIPS:
            ZIP_FIPS[zip_code] = set()
        ZIP_FIPS[zip_code].add(COUNTY_FIPS[county])

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
    """North Star subdivision criteria: 20-300ac, vacant, road frontage, wetlands, FEMA"""
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
    if page_token:
        url += f"?page_token={page_token}"
    try:
        resp = session.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None

def query_for_sale(fips, zip_code):
    """Active MLS land listings"""
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
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None

# Query all - deduplicate ZIPs
print("=== QUERYING OFF-MARKET (North Star criteria) ===")
off_market_raw = []
queried_zips = set()
for zip_code, towns in ZIP_TOWNS.items():
    counties_for_zip = set(c for _, _, c in towns)
    for _, _, county in towns:
        fips = COUNTY_FIPS[county]
        query_key = (fips, zip_code)
        if query_key in queried_zips:
            continue
        queried_zips.add(query_key)
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
            p["_source"] = "off-market"
            p["_zip"] = zip_code
            p["_county"] = county
        off_market_raw.extend(all_page)
        print(f"  {zip_code} ({county}): {len(all_page)}")
        time.sleep(0.3)

print(f"\n=== QUERYING FOR-SALE (MLS land) ===")
for_sale_raw = []
queried_fs = set()
for zip_code, towns in ZIP_TOWNS.items():
    for _, _, county in towns:
        fips = COUNTY_FIPS[county]
        query_key = (fips, zip_code)
        if query_key in queried_fs:
            continue
        queried_fs.add(query_key)
        result = query_for_sale(fips, zip_code)
        if not result: continue
        props = result.get("data", {}).get("properties", [])
        for p in props:
            p["_source"] = "for-sale"
            p["_zip"] = zip_code
            p["_county"] = county
        for_sale_raw.extend(props)
        print(f"  {zip_code} ({county}): {len(props)}")
        time.sleep(0.2)

# Deduplicate and filter
print(f"\n=== PROCESSING ===")
print(f"Off-market raw: {len(off_market_raw)}, For-sale raw: {len(for_sale_raw)}")

seen_om = set()
off_market = []
for p in off_market_raw:
    pid = p.get("property_id")
    if pid and pid not in seen_om and should_keep(p.get("owner_full_name", "")):
        seen_om.add(pid)
        off_market.append(p)

seen_fs = set()
for_sale = []
for p in for_sale_raw:
    pid = p.get("property_id")
    if pid and pid not in seen_fs and should_keep(p.get("owner_full_name", "")):
        seen_fs.add(pid)
        for_sale.append(p)
        # Also remove from off-market if listed (cross-reference)
        if pid in seen_om:
            off_market = [x for x in off_market if x.get("property_id") != pid]
            seen_om.discard(pid)

print(f"Off-market filtered: {len(off_market)}, For-sale filtered: {len(for_sale)}")

# Build entries with town-level grading
def build_entry(p, source):
    zip_code = p.get("_zip", "")
    county = p.get("_county", "")
    towns = ZIP_TOWNS.get(zip_code, [])
    # Find matching towns for this county
    matching = [(t, r) for t, r, c in towns if c == county]
    if not matching:
        matching = [(f"ZIP {zip_code}", "Unknown")]
    
    # Use best-match town (first one in the list for this county)
    town_name, growth_rating = matching[0]
    
    # Grade
    if growth_rating == "High":
        grade = "A"
    elif growth_rating == "Moderate to High":
        grade = "B+"
    elif growth_rating == "Moderate":
        grade = "B"
    else:
        grade = "C"
    
    return {
        "apn": p.get("apn", ""),
        "address": p.get("street_address", ""),
        "owner": p.get("owner_full_name", ""),
        "acres": p.get("lot_size_acres", 0) or 0,
        "county": county,
        "town": town_name,
        "zip": zip_code,
        "growth": growth_rating,
        "grade": grade,
        "source": source,
        "property_id": p.get("property_id"),
    }

all_entries = []
for p in off_market:
    all_entries.append(build_entry(p, "off-market"))
for p in for_sale:
    all_entries.append(build_entry(p, "for-sale"))

# Multi-property owners
owner_counts = Counter(e["owner"] for e in all_entries if e["owner"])
multi = {o: c for o, c in owner_counts.items() if c >= 2}
for e in all_entries:
    e["multi"] = e["owner"] in multi
    e["owner_count"] = multi.get(e["owner"], 1)

# Sort: grade, then acres desc
grade_order = {"A": 0, "A-": 1, "B+": 2, "B": 3, "C": 4, "Unknown": 5}
for e in all_entries:
    e["_sort"] = (grade_order.get(e["grade"], 5), -e["acres"])
all_entries.sort(key=lambda e: e["_sort"])

# Build deliverable by county
os.makedirs(OUTPUT_DIR, exist_ok=True)

for county in COUNTY_FIPS:
    entries = [e for e in all_entries if e["county"] == county]
    if not entries:
        continue
    
    # Group by town
    by_town = defaultdict(list)
    for e in entries:
        by_town[e["town"]].append(e)
    
    # Build markdown
    lines = []
    lines.append(f"# {county} County — North Star Subdivision Pipeline")
    lines.append("")
    lines.append(f"**{len(entries)} total parcels** | HIGH & Moderate-to-High growth towns | {len([e for e in entries if e['source']=='off-market'])} off-market | {len([e for e in entries if e['source']=='for-sale'])} for-sale")
    lines.append("")
    lines.append("## Parcels Ranked by Growth Potential")
    lines.append("")
    lines.append("| Growth | Town | Acres | Owner | APN | Status |")
    lines.append("|---|---|---|---|---|---|")
    
    for e in entries:
        status = "📞 MLS" if e["source"] == "for-sale" else "📬 Mail"
        mp = " 🔗" if e["multi"] else ""
        ac = f"{e['acres']:.1f}" if e.get("acres") else "?"
        lines.append(f"| {e['growth']} | {e['town']} | {ac} | {e['owner']}{mp} | {e['apn']} | {status} |")
    
    lines.append("")
    
    # North Star Takeaway
    lines.append("## North Star Takeaway")
    lines.append("")
    
    # Find clusters: towns with 3+ parcels
    clusters = {town: parcels for town, parcels in by_town.items() if len(parcels) >= 3}
    for town, parcels in sorted(clusters.items(), key=lambda x: -len(x[1])):
        total_acres = sum(e["acres"] for e in parcels)
        growth = parcels[0]["growth"]
        multi_owners = [e["owner"] for e in parcels if e["multi"]]
        unique_multi = set(multi_owners)
        
        lines.append(f"### {town} Cluster — {len(parcels)} parcels, ~{total_acres:.0f} acres ({growth} growth)")
        lines.append(f"- **{len(parcels)} parcels** totaling approximately **{total_acres:.0f} acres** in {town}, a {growth}-growth town in {county} County.")
        if unique_multi:
            lines.append(f"- **{len(unique_multi)} multi-property owner(s)** with multiple parcels in this cluster.")
        lines.append("")
    
    # For-sale vs off-market breakdown
    fs_towns = defaultdict(list)
    om_towns = defaultdict(list)
    for e in entries:
        if e["source"] == "for-sale":
            fs_towns[e["town"]].append(e)
        else:
            om_towns[e["town"]].append(e)
    
    if fs_towns:
        lines.append("### 📞 For-Sale Priority Targets")
        for town, parcels in sorted(fs_towns.items(), key=lambda x: -len(x[1])):
            best = parcels[0]
            lines.append(f"- **{town}** ({best['growth']}): {len(parcels)} MLS-listed parcels — call first")
    
    if om_towns:
        lines.append("")
        lines.append("### 📬 Off-Market Priority Targets")
        for town, parcels in sorted(om_towns.items(), key=lambda x: -len(x[1])):
            best = parcels[0]
            multi_count = len(set(e["owner"] for e in parcels if e["multi"]))
            lines.append(f"- **{town}** ({best['growth']}): {len(parcels)} off-market parcels — mail campaign")
            if multi_count:
                lines.append(f"  - {multi_count} multi-property owners to prioritize")
    
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Methodology: North Star / Cody Bjugan subdivision criteria. Town-level grading from county 2040 comprehensive plans.*")
    lines.append(f"*Note: Town assignment based on ZIP code. Some parcels may belong to adjacent towns sharing the same ZIP. Verify with parcel coordinates.*")
    lines.append("")
    
    path = os.path.join(OUTPUT_DIR, "by_county", f"{county}_pipeline.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines))
    
    print(f"  {county}: {len(entries)} entries -> {path}")

# Master summary
print(f"\n===== COMPLETE =====")
total_om = len([e for e in all_entries if e["source"] == "off-market"])
total_fs = len([e for e in all_entries if e["source"] == "for-sale"])
print(f"Off-market: {total_om}, For-sale: {total_fs}, Total: {len(all_entries)}")
for county in COUNTY_FIPS:
    om = len([e for e in all_entries if e["county"] == county and e["source"] == "off-market"])
    fs = len([e for e in all_entries if e["county"] == county and e["source"] == "for-sale"])
    print(f"  {county}: {om} off-market + {fs} for-sale = {om+fs}")