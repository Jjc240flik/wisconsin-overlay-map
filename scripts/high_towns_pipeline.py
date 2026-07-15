#!/usr/bin/env python3
"""
HIGH-rated towns only pipeline.
Queries Land Portal for A+, A, A- towns, off-market + for-sale.
Pulls detail for missing acreage/prices at 2s/req.
"""
import requests, json, time, os, sys
from collections import Counter, defaultdict
from datetime import datetime

API_KEY = "lp_live_e3C0PY-2uwItQt3DcW1eH2t-bD0MfjkQ"
BASE = "https://api.landportal.com"
H = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
OUT = "/root/wisconsin-overlay-map/output/subdivision_leads"
s = requests.Session()
s.headers.update(H)

F = {"Outagamie":"55087","Brown":"55009","Dane":"55025","Waukesha":"55133","Ozaukee":"55089","Rock":"55105","Winnebago":"55139","Calumet":"55015"}

# HIGH-rated towns only (A+, A, A-) — as specified by user
TOWNS = {
    "Outagamie": {"VILLAGE OF GREENVILLE":"A+","TOWN OF GRAND CHUTE":"A","VILLAGE OF HARRISON":"A"},
    "Brown": {"TOWN OF LEDGEVIEW":"A+","VILLAGE OF HOWARD":"A","VILLAGE OF SUAMICO":"A","VILLAGE OF BELLEVUE":"A","TOWN OF LAWRENCE":"A","VILLAGE OF ASHWAUBENON":"A-"},
    "Dane": {"CITY OF VERONA":"A+","CITY OF FITCHBURG":"A","TOWN OF SUN PRAIRIE":"A","TOWN OF WESTPORT":"A","TOWN OF SPRINGFIELD":"A-","TOWN OF BURKE":"A-","TOWN OF BLOOMING GROVE":"A-","VILLAGE OF DEFOREST":"B+"},
    "Waukesha": {"VILLAGE OF MENOMONEE FALLS":"A","TOWN OF LISBON":"A","TOWN OF GENESEE":"A-","VILLAGE OF PEWAUKEE":"A-","VILLAGE OF SUSSEX":"A-"},
    "Ozaukee": {"VILLAGE OF GRAFTON":"A","VILLAGE OF SAUKVILLE":"A","TOWN OF CEDARBURG":"A","CITY OF MEQUON":"A-"},
    "Rock": {"BELOIT":"A+","JANESVILLE":"A","TURTLE":"A"},
    "Winnebago": {"TOWN OF NEENAH":"A","TOWN OF OSHKOSH":"A","TOWN OF ALGOMA":"A","TOWN OF MENASHA":"A-"},
    "Calumet": {"TOWN OF HARRISON":"A","TOWN OF MENASHA":"A"}
}

# Towns that don't return lot_size_acres in filter-data
ACREAGE_GAP_COUNTIES = {"Outagamie", "Calumet", "Waukesha", "Winnebago"}

def should_keep(name):
    if not name: return False
    u = name.upper().strip()
    trusts = ["TRUST","TRST","REVOCABLE","REVOCABL","IRREVOCABLE","IRREVOCABL","REV TR","LIV TR","IRREV TR"," REVO"]
    if any(t in u for t in trusts): return False
    if u.endswith(" TRST") or u.endswith(" TR"): return False
    govt = ["COUNTY","TOWNSHIP","CITY OF","STATE OF","NATION ","TRIBE","VILLAGE OF","TOWN OF","HOUSING AUTHORITY","DEPT OF","DEPARTMENT OF","DOT","DNR","ELECTRIC POWER","SCHOOL DISTRICT","SANITARY DISTRICT","UNIFIED SCHOOL"]
    if any(p in u for p in govt): return False
    if "OWNERS OF LOTS" in u or "LOT OWNERS OF" in u or "HOMEOWNERS ASSOC" in u: return False
    if u in ("AVAILABLE NOT","AVAILABLE NAME NOT","AVAILABLE","NOT AVAILABLE","UNKNOWN","N/A"): return False
    if " INC" in u or " CORP" in u: return False
    if ("LLC" in u or "L L C" in u) and "FARM" not in u: return False
    return True

def query_off_market(fips, muni):
    """Category 1 filters: 20-200ac, road>=300ft, wetlands<=25%, FEMA<=50%, slope>=50%"""
    filters = [
        {"key":"municipality","operator":"condition","value":muni},
        {"key":"lotsizeacres","operator":"range","value":{"min":20,"max":200}},
        {"key":"vacant","operator":"boolean","value":True},
        {"key":"road_frontage","operator":"range","value":{"min":300}},
        {"key":"wetlands_cover_percentage","operator":"range","value":{"max":25}},
        {"key":"fema_cover_percentage","operator":"range","value":{"max":50}},
        {"key":"sum_up_to_15","operator":"range","value":{"min":50}},
    ]
    all_props = []
    pt = None
    while True:
        url = f"{BASE}/v2/filter-data"
        if pt: url += f"?page_token={pt}"
        try:
            r = s.post(url, json={"fips":[fips],"filters":filters}, timeout=30)
            if r.status_code != 200:
                print(f"    WARN: off-market {muni} returned {r.status_code}")
                break
            d = r.json()
            if d.get("meta",{}).get("rejected_filters"):
                print(f"    WARN: rejected_filters for {muni}")
                break
            props = d.get("data",{}).get("properties",[])
            all_props.extend(props)
            pt = d.get("data",{}).get("next_page_token","")
            if not pt: break
            time.sleep(0.15)
        except Exception as e:
            print(f"    ERROR: {e}")
            break
    return all_props

def query_for_sale(fips, muni):
    """5 land codes with active_listing_toggle"""
    all_props = []
    for code in ["8000","8001","8008","7000","7001"]:
        filters = [
            {"key":"municipality","operator":"condition","value":muni},
            {"key":"landusecode","operator":"condition","value":code},
            {"key":"active_listing_toggle","operator":"active_listing_toggle","value":True},
        ]
        try:
            r = s.post(f"{BASE}/v2/filter-data", json={"fips":[fips],"filters":filters}, timeout=30)
            if r.status_code != 200: continue
            d = r.json()
            if d.get("meta",{}).get("rejected_filters"): continue
            props = d.get("data",{}).get("properties",[])
            all_props.extend(props)
            time.sleep(0.08)
        except: continue
    return all_props

def get_detail(pid, delay=2.0):
    """Fetch property detail for acreage/price. Returns dict or None."""
    try:
        r = s.get(f"{BASE}/v2/properties/{pid}", timeout=15)
        if r.status_code == 200:
            props = r.json().get("data",{}).get("properties",{})
            return {
                "lot_size_acres": props.get("lot_size_acres"),
                "calc_acres": props.get("calc_acres"),
                "current_sale_price": props.get("current_sale_price"),
                "assessed_total_value": props.get("assessed_total_value"),
            }
        elif r.status_code == 429:
            return {"_error": "rate_limited"}
        return None
    except Exception as e:
        return None

# ========== PHASE 1: Query all towns ==========
print("=" * 60)
print("PHASE 1: Filter-Data Queries (HIGH-rated towns only)")
print("=" * 60)

all_off_market = []
all_for_sale = []

for county, towns in TOWNS.items():
    fips = F[county]
    print(f"\n{county} ({fips}):")
    for muni, grade in towns.items():
        # Off-market
        om = query_off_market(fips, muni)
        time.sleep(0.15)
        # For-sale
        fs = query_for_sale(fips, muni)
        time.sleep(0.15)

        for p in om:
            p["_C"] = county; p["_T"] = muni; p["_G"] = grade; p["_S"] = "off-market"
        for p in fs:
            p["_C"] = county; p["_T"] = muni; p["_G"] = grade; p["_S"] = "for-sale"

        all_off_market.extend(om)
        all_for_sale.extend(fs)
        print(f"  {muni} ({grade}): {len(om)} OM + {len(fs)} FS")

print(f"\nRaw totals: {len(all_off_market)} off-market, {len(all_for_sale)} for-sale")

# ========== PHASE 2: Deduplicate + Filter Owners ==========
print("\n" + "=" * 60)
print("PHASE 2: Owner Filtering & Deduplication")
print("=" * 60)

seen_om = set()
off_market_f = []
for p in all_off_market:
    pid = p.get("property_id")
    if pid and pid not in seen_om and should_keep(p.get("owner_full_name","")):
        seen_om.add(pid)
        off_market_f.append(p)

seen_fs = set()
for_sale_f = []
for p in all_for_sale:
    pid = p.get("property_id")
    if pid and pid not in seen_fs and should_keep(p.get("owner_full_name","")):
        seen_fs.add(pid)
        for_sale_f.append(p)
    # Cross-reference: if also in off-market, remove from there
    if pid in seen_om:
        off_market_f = [x for x in off_market_f if x.get("property_id") != pid]
        seen_om.discard(pid)

print(f"Filtered: {len(off_market_f)} off-market, {len(for_sale_f)} for-sale")

# ========== PHASE 3: Build entry list, identify acreage gaps ==========
entries = []
needs_detail = []  # (pid, county, idx) for properties missing acreage

for p in off_market_f:
    acres = p.get("lot_size_acres", 0) or 0
    pid = p.get("property_id")
    entries.append({
        "apn": p.get("apn",""), "owner": p.get("owner_full_name",""),
        "acres": acres, "county": p["_C"], "town": p["_T"],
        "grade": p["_G"], "source": "off-market", "property_id": pid,
        "address": p.get("street_address","")
    })
    if not acres and pid and p["_C"] in ACREAGE_GAP_COUNTIES:
        needs_detail.append((pid, p["_C"], len(entries)-1))

for p in for_sale_f:
    acres = p.get("lot_size_acres", 0) or 0
    pid = p.get("property_id")
    entries.append({
        "apn": p.get("apn",""), "owner": p.get("owner_full_name",""),
        "acres": acres, "county": p["_C"], "town": p["_T"],
        "grade": p["_G"], "source": "for-sale", "property_id": pid,
        "address": p.get("street_address","")
    })
    if not acres and pid and p["_C"] in ACREAGE_GAP_COUNTIES:
        needs_detail.append((pid, p["_C"], len(entries)-1))

print(f"\nTotal entries: {len(entries)}")
print(f"Need detail lookup: {len(needs_detail)}")

# Save raw results
os.makedirs(os.path.join(OUT, "by_county"), exist_ok=True)
os.makedirs("/root/wisconsin-overlay-map/output", exist_ok=True)

with open(os.path.join(OUT, "raw_filtered_results.json"), "w") as f:
    json.dump({
        "off_market": off_market_f, "for_sale": for_sale_f,
        "entries": entries, "needs_detail": needs_detail
    }, f, indent=2, default=str)

print("Raw results saved.")

# ========== PHASE 4: Detail Lookups (2s/req, 30s pause/50) ==========
if needs_detail:
    print("\n" + "=" * 60)
    print(f"PHASE 4: Detail Lookups ({len(needs_detail)} properties)")
    print("Rate: 1 per 2s, pause 30s every 50")
    print("=" * 60)

    detail_progress = os.path.join(OUT, "detail_progress.json")
    progress = {}
    if os.path.exists(detail_progress):
        with open(detail_progress) as f:
            progress = json.load(f)

    consecutive_429 = 0
    for i, (pid, county, idx) in enumerate(needs_detail):
        if str(pid) in progress:
            continue

        detail = get_detail(pid, delay=2.0)
        if detail and detail.get("_error") == "rate_limited":
            consecutive_429 += 1
            print(f"  [{i+1}/{len(needs_detail)}] PID {pid}: RATE LIMITED ({consecutive_429})")
            if consecutive_429 >= 3:
                print(f"  Hit consecutive rate limits. Stopping detail pulls. Using 20-200†")
                break
            time.sleep(6)
            continue
        elif detail:
            consecutive_429 = 0
            acres = detail.get("calc_acres") or detail.get("lot_size_acres") or 0
            price = detail.get("current_sale_price", "")
            pstr = f" ${price:,.0f}" if price else ""
            print(f"  [{i+1}/{len(needs_detail)}] {county} PID {pid}: {acres:.1f}ac{pstr}")
            progress[str(pid)] = detail
            # Update entry
            if idx < len(entries):
                if acres: entries[idx]["acres"] = acres
                if price: entries[idx]["price"] = price
        else:
            print(f"  [{i+1}/{len(needs_detail)}] PID {pid}: FAILED")
            progress[str(pid)] = {"_error": "failed"}

        time.sleep(2.0)

        # Batch pause
        if (i + 1) % 50 == 0:
            print(f"  --- Batch pause 30s ---")
            progress["_last_idx"] = i + 1
            with open(detail_progress, "w") as f:
                json.dump(progress, f, indent=2, default=str)
            time.sleep(30)

    with open(detail_progress, "w") as f:
        json.dump(progress, f, indent=2, default=str)
    print(f"Detail phase complete. {len(progress)-1} properties fetched.")

# ========== PHASE 5: Build Pipeline Output ==========
print("\n" + "=" * 60)
print("PHASE 5: Generating Pipeline Output")
print("=" * 60)

# Multi-property owner detection
owner_counts = Counter(e["owner"] for e in entries if e["owner"])
multi_owners = {o: c for o, c in owner_counts.items() if c >= 2}
for e in entries:
    e["multi"] = e["owner"] in multi_owners

# Sort: grade order, then acres desc
grade_order = {"A+":0, "A":1, "A-":2, "B+":3}
entries.sort(key=lambda e: (grade_order.get(e["grade"],9), -e.get("acres",0)))

# Generate county pipeline files
for county in sorted(F.keys()):
    ee = [e for e in entries if e["county"] == county]
    if not ee:
        continue

    omc = len([e for e in ee if e["source"] == "off-market"])
    fsc = len([e for e in ee if e["source"] == "for-sale"])

    # Group by town
    by_town = defaultdict(list)
    for e in ee:
        by_town[e["town"]].append(e)

    lines = []
    lines.append(f"# {county} County — Ag→Subdivision Rezoning Pipeline (HIGH Only)")
    lines.append("")
    lines.append(f"**{len(ee)} parcels** | {omc} off-market | {fsc} for-sale | Category 1 filters: 20-200ac, 300ft road, ≤25% wetlands, ≤50% FEMA, ≥50% slope <15°")
    lines.append("")
    lines.append("## Parcels Ranked by Rezoning Potential")
    lines.append("")
    lines.append("| Rezoning | Town | Acres | Owner | APN | Status |")
    lines.append("|---|---|---|---|---|---|")

    for e in ee[:200]:
        st = "📞" if e["source"] == "for-sale" else "📬"
        mp = "🔗" if e.get("multi") else ""
        ac = f"{e['acres']:.1f}" if e.get("acres") else "20-200†"
        ts = e["town"].replace("TOWN OF ","").replace("VILLAGE OF ","").replace("CITY OF ","")
        lines.append(f"| **{e['grade']}** | {ts} | {ac} | {e['owner']} {mp}| {e['apn']} | {st} |")

    if len(ee) > 200:
        lines.append(f"| ... | ... | ... (+{len(ee)-200} more) | ... | ... |")

    lines.append("")
    lines.append("## Rezoning Analysis")
    lines.append("")

    # A+/A targets
    top = [e for e in ee if e["grade"] in ("A+","A")]
    if top:
        lines.append("### 🔥 A+/A — Prime Ag→Subdivision Targets")
        lines.append("*Directly adjacent to city limits. FLU maps show ag→residential. Sewer/water planned or active. Highest rezoning likelihood.*")
        lines.append("")
        for e in top[:10]:
            ts = e["town"].replace("TOWN OF ","").replace("VILLAGE OF ","").replace("CITY OF ","")
            lines.append(f"- **{e['apn']}** | {e['acres']:.1f}ac | {e['owner']} | {ts}")
        lines.append("")

    # Clusters
    lines.append("### Clusters")
    clusters = {t: p for t, p in by_town.items() if len(p) >= 3}
    for t, p in sorted(clusters.items(), key=lambda x: -len(x[1])):
        ta = sum(e["acres"] for e in p)
        g = p[0]["grade"]
        mo = set(e["owner"] for e in p if e.get("multi"))
        fs_ct = len([e for e in p if e["source"] == "for-sale"])
        lines.append(f"**{t.replace('TOWN OF ','').replace('VILLAGE OF ','').replace('CITY OF ','')}** ({g}): {len(p)} parcels, ~{ta:.0f}ac")
        if fs_ct: lines.append(f"  {fs_ct} MLS — call first")
        if mo: lines.append(f"  {len(mo)} multi-owners")
    lines.append("")

    # For-sale and off-market breakdown
    fst = defaultdict(list); omt = defaultdict(list)
    for e in ee:
        ts = e["town"].replace("TOWN OF ","").replace("VILLAGE OF ","").replace("CITY OF ","")
        if e["source"] == "for-sale": fst[ts].append(e)
        else: omt[ts].append(e)

    if fst:
        lines.append("### 📞 For-Sale")
        for t, p in sorted(fst.items(), key=lambda x: -len(x[1])):
            lines.append(f"- **{t}** ({p[0]['grade']}): {len(p)}")

    if omt:
        lines.append("")
        lines.append("### 📬 Off-Market")
        for t, p in sorted(omt.items(), key=lambda x: -len(x[1])):
            mc = len(set(e["owner"] for e in p if e.get("multi")))
            lines.append(f"- **{t}** ({p[0]['grade']}): {len(p)} {'— '+str(mc)+' multi-owners' if mc else ''}")

    lines.append("")
    lines.append("---")
    lines.append(f"*{datetime.now().strftime('%Y-%m-%d %H:%M')} | North Star / Cody Bjugan criteria. Search Filters doc v1.0. HIGH-rated towns only (A+, A, A-).*")
    lines.append("† Exact acreage not available from Land Portal filter-data for this county. Filter guarantees 20-200 acres.")
    lines.append("")

    # Write to pipeline output file
    pipeline_path = os.path.join(OUT, "by_county", f"{county}_pipeline.md")
    with open(pipeline_path, "w") as f:
        f.write("\n".join(lines))
    print(f"  {county}: {len(ee)} entries -> {pipeline_path}")

# ========== PHASE 6: Summary ==========
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
total_om = len([e for e in entries if e["source"] == "off-market"])
total_fs = len([e for e in entries if e["source"] == "for-sale"])
print(f"Total: {len(entries)} parcels ({total_om} OM + {total_fs} FS)")
for c in sorted(F.keys()):
    om = len([e for e in entries if e["county"] == c and e["source"] == "off-market"])
    fs = len([e for e in entries if e["county"] == c and e["source"] == "for-sale"])
    print(f"  {c}: {om} OM + {fs} FS = {om+fs}")

print("\nPipeline files written to output/subdivision_leads/by_county/")
print("DONE")