#!/usr/bin/env python3
"""
Query Land Portal for FOR-SALE (MLS-listed) properties in HIGH & Moderate-to-High
municipalities across all TOP 10 Wisconsin counties.
Focus: land/lots with subdivision potential, using MLS active listing filters.
"""
import json, os, time, requests
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

API_KEY = "lp_live_z5k-VLjQn5gVOnb0NuTLG-rxJ1jtZy7G"
BASE_URL = "https://api.landportal.com"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
OUTPUT_DIR = "/root/wisconsin-overlay-map/output/subdivision_leads"
WORKERS = 8

COUNTY_FIPS = {
    "Outagamie": "55087", "Brown": "55009", "Dane": "55025",
    "Waukesha": "55133", "Ozaukee": "55089", "Milwaukee": "55079",
    "Rock": "55105", "Winnebago": "55139", "Calumet": "55015", "Door": "55029"
}

# Target ZIPs with growth ratings
TARGET_ZIPS = {
    "Outagamie": {
        "54942": {"muni": "Greenville", "rating": "High", "notes": "Textbook Cody Bjugan target. FLU + water/wastewater master plans."},
        "54913": {"muni": "Grand Chute", "rating": "High", "notes": "Surrounds Appleton. US 41 corridor."},
        "54956": {"muni": "Harrison/Fox Crossing/Neenah area", "rating": "High", "notes": "East of Appleton, US 10/US 41 corridor."},
        "54113": {"muni": "Combined Locks", "rating": "High", "notes": "Adjacent to Kaukauna. Fox Cities core."},
        "54140": {"muni": "Little Chute", "rating": "High", "notes": "Fox Cities metro core."},
        "54130": {"muni": "Buchanan", "rating": "Moderate to High", "notes": "Surrounds Kaukauna."},
        "54966": {"muni": "Freedom", "rating": "Moderate to High", "notes": "SW of Appleton. Adjacent to city."},
        "54136": {"muni": "Kimberly", "rating": "Moderate to High", "notes": "Fox Cities core. Limited land."},
    },
    "Brown": {
        "54313": {"muni": "Ashwaubenon/Howard/Suamico/Scott", "rating": "High", "notes": "Green Bay growth corridor."},
        "54311": {"muni": "Bellevue", "rating": "High", "notes": "East of Green Bay."},
        "54115": {"muni": "Ledgeview/Lawrence/Humboldt", "rating": "High", "notes": "Fastest growing Brown County areas."},
        "54301": {"muni": "Allouez", "rating": "Moderate to High", "notes": "Adjacent to Green Bay. Infill."},
    },
    "Dane": {
        "53711": {"muni": "Fitchburg", "rating": "High", "notes": "South of Madison. Major residential."},
        "53593": {"muni": "Verona/Dunn", "rating": "High", "notes": "Epic Systems corridor."},
        "53590": {"muni": "Sun Prairie/Burke/Bristol", "rating": "High", "notes": "Madison east growth path."},
        "53562": {"muni": "Westport/Springfield", "rating": "High", "notes": "North of Middleton."},
        "53716": {"muni": "Blooming Grove", "rating": "High", "notes": "East of Madison."},
        "53558": {"muni": "Pleasant Springs/McFarland", "rating": "Moderate to High", "notes": "SE metro."},
        "53575": {"muni": "Montrose/Oregon", "rating": "Moderate to High", "notes": "SE growth corridor."},
        "53597": {"muni": "Waunakee", "rating": "Moderate to High", "notes": "NW metro."},
        "53532": {"muni": "DeForest", "rating": "Moderate to High", "notes": "North metro I-39/90."},
        "53598": {"muni": "Windsor", "rating": "Moderate to High", "notes": "North metro."},
    },
    "Waukesha": {
        "53051": {"muni": "Menomonee Falls", "rating": "High", "notes": "Milwaukee metro fringe."},
        "53089": {"muni": "Lisbon/Sussex", "rating": "High", "notes": "I-94 corridor."},
        "53186": {"muni": "Genesee/Waukesha Town", "rating": "High", "notes": "Near Waukesha/Milwaukee edge."},
        "53072": {"muni": "Pewaukee Village", "rating": "High", "notes": "I-94 corridor."},
        "53005": {"muni": "Brookfield Town", "rating": "High", "notes": "Adjacent to cities."},
        "53046": {"muni": "Lannon", "rating": "Moderate to High", "notes": "Near Menomonee Falls."},
    },
    "Ozaukee": {
        "53092": {"muni": "Mequon", "rating": "High", "notes": "Milwaukee north shore. High-value."},
        "53024": {"muni": "Grafton Village/Town", "rating": "High", "notes": "I-43 corridor."},
        "53080": {"muni": "Saukville", "rating": "High", "notes": "I-43 north."},
        "53012": {"muni": "Cedarburg Town/City", "rating": "High", "notes": "I-43 corridor."},
    },
    "Milwaukee": {
        "53132": {"muni": "Franklin", "rating": "Moderate", "notes": "Most greenfield potential in county."},
        "53154": {"muni": "Oak Creek", "rating": "Moderate", "notes": "SE edge. Growth corridor."},
    },
    "Rock": {
        "53511": {"muni": "Beloit Town/Turtle/Harmony", "rating": "High", "notes": "Stateline corridor. I-39/90."},
        "53545": {"muni": "Janesville Town", "rating": "High", "notes": "Surrounds Janesville."},
        "53536": {"muni": "Evansville", "rating": "Moderate to High", "notes": "North metro."},
        "53563": {"muni": "Milton Town", "rating": "Moderate to High", "notes": "Edge growth."},
        "53534": {"muni": "Fulton", "rating": "Moderate to High", "notes": "NE of Janesville."},
    },
    "Winnebago": {
        "54956": {"muni": "Neenah/Vinland/Clayton/Fox Crossing", "rating": "High", "notes": "US 41 corridor. Fox Cities edge."},
        "54952": {"muni": "Menasha Town", "rating": "High", "notes": "Surrounds Menasha."},
        "54901": {"muni": "Oshkosh Town/Algoma", "rating": "High", "notes": "US 41 corridor."},
    },
    "Calumet": {
        "54956": {"muni": "Harrison Town", "rating": "High", "notes": "South of Appleton. US 41/10."},
        "54952": {"muni": "Menasha Calumet", "rating": "High", "notes": "Fox Cities edge."},
        "53088": {"muni": "Stockbridge", "rating": "Moderate to High", "notes": "Lake Winnebago. Growing."},
        "53014": {"muni": "Brothertown", "rating": "Moderate to High", "notes": "Lakeshore."},
    },
    "Door": {
        "54234": {"muni": "Sister Bay", "rating": "Moderate to High", "notes": "Tourism corridor. Seasonal."},
    },
}

session = requests.Session()
session.headers.update(HEADERS)

def query_mls_listings(fips, zip_code, page_token=None):
    """Query filter-data for active MLS listings (land/lots) in a ZIP."""
    filters = [
        {"key": "situszip5", "operator": "condition", "value": zip_code},
        {"key": "lotsizeacres", "operator": "range", "value": {"min": 5, "max": 500}},
        {"key": "active_listing_toggle", "operator": "active_listing_toggle", "value": True},
    ]
    
    payload = {"fips": [fips], "filters": filters}
    url = f"{BASE_URL}/v2/filter-data"
    if page_token:
        url += f"?page_token={page_token}"
    
    try:
        resp = session.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        return None

def get_detail(pid):
    try:
        resp = session.get(f"{BASE_URL}/v2/properties/{pid}", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return None

def should_keep_owner(name):
    if not name: return False
    u = name.upper().strip()
    trusts = ["TRUST", "TRST", "REVOCABLE", "REVOCABL", "IRREVOCABLE", "IRREVOCABL",
              "REV TR", "LIV TR", "IRREV TR", " REVO", " LIVING TR"]
    if any(t in u for t in trusts): return False
    if u.endswith(" TRST") or u.endswith(" TR"): return False
    if any(p in u for p in ["COUNTY", "TOWNSHIP", "CITY OF", "STATE OF", "NATION ", "TRIBE"]): return False
    if " INC" in u or " CORP" in u: return False
    if ("LLC" in u or "L L C" in u) and "FARM" not in u: return False
    return True

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    all_raw = []  # All raw MLS results
    county_results = {}  # county -> [entries]
    
    for county, zips in TARGET_ZIPS.items():
        fips = COUNTY_FIPS[county]
        print(f"\n{'='*50}")
        print(f"COUNTY: {county} (FIPS: {fips})")
        
        county_raw = []
        for zip_code, info in zips.items():
            print(f"  ZIP {zip_code} ({info['muni']})...", end=" ")
            
            result = query_mls_listings(fips, zip_code)
            if not result:
                print("ERROR")
                continue
            
            data = result.get("data", {})
            props = data.get("properties", [])
            count = data.get("count", 0)
            next_token = data.get("next_page_token", "")
            
            # Paginate
            all_page = list(props)
            while next_token:
                result = query_mls_listings(fips, zip_code, next_token)
                if not result: break
                data = result.get("data", {})
                more = data.get("properties", [])
                next_token = data.get("next_page_token", "")
                all_page.extend(more)
            
            # Tag with metadata
            for p in all_page:
                p["_county"] = county
                p["_zip"] = zip_code
                p["_muni"] = info["muni"]
                p["_rating"] = info["rating"]
                p["_notes"] = info["notes"]
            
            county_raw.extend(all_page)
            print(f"{len(all_page)} listings")
            time.sleep(0.5)
        
        all_raw.extend(county_raw)
        county_results[county] = county_raw
    
    print(f"\n{'='*50}")
    print(f"TOTAL raw MLS listings: {len(all_raw)}")
    
    # Remove duplicates by property_id
    seen_ids = set()
    unique = []
    for p in all_raw:
        pid = p.get("property_id")
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            unique.append(p)
    print(f"Unique: {len(unique)}")
    
    # Filter owners
    filtered = [p for p in unique if should_keep_owner(p.get("owner_full_name", ""))]
    print(f"After owner filter: {len(filtered)}")
    
    # Now pull details for grading
    print(f"\nPulling details for {len(filtered)} properties...")
    
    for_sale = []
    details_fetched = 0
    ids = [p["property_id"] for p in filtered]
    
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(get_detail, pid): idx for idx, pid in enumerate(ids)}
        for future in as_completed(futures):
            idx = futures[future]
            try:
                detail = future.result()
            except:
                detail = None
            
            p = filtered[idx]
            dprops = detail.get("data", {}).get("properties", {}) if detail else {}
            
            acres = dprops.get("lot_size_acres") or p.get("lot_size_acres", 0)
            sale_price = dprops.get("current_sale_price", 0) or 0
            mls_status = dprops.get("mls_status", "")
            land_use = dprops.get("land_use_description", "")
            zoning = dprops.get("zoning", "")
            assessed = dprops.get("assessed_total_value", 0) or 0
            lat = dprops.get("latitude", 0) or 0
            lon = dprops.get("longitude", 0) or 0
            
            # Grade based on growth rating
            rating = p["_rating"]
            notes = p["_notes"]
            if rating == "High":
                if "FLU" in notes or "sewer" in notes.lower() or "water" in notes.lower():
                    grade = "A — Prime target. In growth path with infrastructure."
                else:
                    grade = "A- — High growth. Verify FLU."
            elif rating == "Moderate to High":
                grade = "B+ — Good potential. Check sewer boundaries."
            else:
                grade = "B — Secondary. More due diligence needed."
            
            entry = {
                "property_id": p["property_id"],
                "apn": p.get("apn", ""),
                "address": p.get("street_address", ""),
                "owner": p.get("owner_full_name", ""),
                "acres": acres,
                "sale_price": sale_price,
                "mls_status": mls_status,
                "county": p["_county"],
                "municipality": p["_muni"],
                "zip": p["_zip"],
                "growth_rating": rating,
                "grade": grade,
                "growth_context": notes,
                "land_use": land_use,
                "zoning": zoning,
                "assessed_value": assessed,
                "latitude": lat,
                "longitude": lon,
            }
            for_sale.append(entry)
            details_fetched += 1
            if details_fetched % 20 == 0:
                print(f"  {details_fetched}/{len(filtered)}...")
    
    print(f"Fetched details for {details_fetched}/{len(filtered)}")
    
    # Multi-property owners
    owner_counts = Counter(e["owner"] for e in for_sale if e["owner"])
    multi = {o: c for o, c in owner_counts.items() if c >= 2}
    for e in for_sale:
        e["multi_property"] = e["owner"] in multi
        e["owner_parcel_count"] = multi.get(e["owner"], 1)
    
    # Sort: grade best first, then price (cheapest first for calls)
    grade_order = {"A": 0, "A-": 1, "B+": 2, "B": 3}
    for_sale.sort(key=lambda e: (grade_order.get(e["grade"][:2], 5), e["sale_price"] or 999999999, -e["acres"]))
    
    # Build output
    final = {
        "generated": datetime.now().isoformat(),
        "methodology": "Active MLS listings in HIGH & Moderate-to-High municipalities across TOP 10 counties. Filtered: trusts, non-Farm LLCs, INC, govt removed. Cross-referenced with 2040 comp plans.",
        "summary": {
            "total": len(for_sale),
            "multi_property_owners": len(multi),
            "by_county": {}
        },
        "for_sale": for_sale,
        "multi_property_owners": {o: c for o, c in sorted(multi.items(), key=lambda x: -x[1])[:30]},
    }
    
    for county in COUNTY_FIPS:
        fs = [e for e in for_sale if e["county"] == county]
        final["summary"]["by_county"][county] = len(fs)
    
    # Save JSON
    json_path = os.path.join(OUTPUT_DIR, "for_sale_leads.json")
    with open(json_path, "w") as f:
        json.dump(final, f, indent=2)
    
    # Build markdown per county
    by_county_dir = os.path.join(OUTPUT_DIR, "by_county")
    os.makedirs(by_county_dir, exist_ok=True)
    
    for county in COUNTY_FIPS:
        fs = [e for e in for_sale if e["county"] == county]
        if not fs:
            continue
        
        lines = []
        lines.append(f"# {county} County — FOR-SALE Leads")
        lines.append("")
        lines.append(f"**{len(fs)} active listings** in HIGH & Moderate-to-High growth areas")
        lines.append("")
        lines.append("## 📞 For Sale — Call First")
        lines.append("")
        
        for e in fs:
            mp = " 🔗MULTI" if e["multi_property"] else ""
            price = f"${e['sale_price']:,.0f}" if e.get("sale_price") else "N/A"
            acres_str = f"{e['acres']:.1f}ac" if e.get("acres") else "N/A ac"
            lines.append(f"- **{e['apn']}** | {acres_str} | {price} | {e['owner']}{mp} | {e['municipality']} ({e['growth_rating']}) | {e['grade']}")
        
        lines.append("")
        
        # For non-zero entries, add detail table
        top = fs[:25]  # Show top 25 with detail
        if top:
            lines.append("### Top Listings — Detail")
            lines.append("")
            lines.append("| APN | Acres | Price | Owner | Municipality | Growth | Grade | Key Context |")
            lines.append("|---|---|---|---|---|---|---|---|")
            for e in top:
                mp = " 🔗" if e["multi_property"] else ""
                price = f"${e['sale_price']:,.0f}" if e.get("sale_price") else "N/A"
                acres_str = f"{e['acres']:.1f}" if e.get("acres") else "?"
                lines.append(f"| {e['apn']} | {acres_str} | {price} | {e['owner']}{mp} | {e['municipality']} | {e['growth_rating']} | {e['grade'][:2]} | {e['growth_context'][:60]} |")
            lines.append("")
        
        path = os.path.join(by_county_dir, f"{county}_for_sale.md")
        with open(path, "w") as f:
            f.write("\n".join(lines))
    
    # Build consolidated markdown
    md_lines = []
    md_lines.append("# 📞 FOR-SALE LEADS — TOP Counties (Call First)")
    md_lines.append("")
    md_lines.append(f"**Generated:** {final['generated']}")
    md_lines.append("")
    md_lines.append("## Summary")
    md_lines.append("")
    md_lines.append("| County | Listings |")
    md_lines.append("|---|---|")
    for county, count in sorted(final["summary"]["by_county"].items()):
        md_lines.append(f"| {county} | {count} |")
    md_lines.append(f"| **TOTAL** | **{len(for_sale)}** |")
    md_lines.append("")
    
    if multi:
        md_lines.append("## Multi-Property Owners on MLS")
        md_lines.append("")
        md_lines.append("| Owner | Listings |")
        md_lines.append("|---|---|")
        for owner, count in sorted(multi.items(), key=lambda x: -x[1])[:15]:
            md_lines.append(f"| {owner} | {count} |")
        md_lines.append("")
    
    for county in sorted(final["summary"]["by_county"].keys()):
        fs = [e for e in for_sale if e["county"] == county]
        if not fs:
            continue
        md_lines.append(f"## {county} County ({len(fs)} listings)")
        md_lines.append("")
        md_lines.append("| APN | Acres | Price | Owner | Municipality | Growth | Grade |")
        md_lines.append("|---|---|---|---|---|---|---|")
        for e in fs[:30]:
            mp = " 🔗" if e["multi_property"] else ""
            price = f"${e['sale_price']:,.0f}" if e.get("sale_price") else "N/A"
            acres_str = f"{e['acres']:.1f}" if e.get("acres") else "?"
            md_lines.append(f"| {e['apn']} | {acres_str} | {price} | {e['owner']}{mp} | {e['municipality']} | {e['growth_rating']} | {e['grade'][:2]} |")
        md_lines.append("")
    
    md_path = os.path.join(OUTPUT_DIR, "for_sale_leads.md")
    with open(md_path, "w") as f:
        f.write("\n".join(md_lines))
    
    print(f"\n{'='*50}")
    print(f"DONE: {len(for_sale)} for-sale listings")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")
    print(f"  Per-county: {by_county_dir}/*_for_sale.md")
    print(f"\nCounty breakdown:")
    for county, count in sorted(final["summary"]["by_county"].items()):
        print(f"  {county}: {count}")

if __name__ == "__main__":
    main()