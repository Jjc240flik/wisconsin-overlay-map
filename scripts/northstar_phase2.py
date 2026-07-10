#!/usr/bin/env python3
"""
Phase 2: Fast parallel property detail lookups and deliverable generation.
Uses ThreadPoolExecutor for parallel API calls.
"""
import json
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import requests

API_KEY = "lp_live_z5k-VLjQn5gVOnb0NuTLG-rxJ1jtZy7G"
BASE_URL = "https://api.landportal.com"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
OUTPUT_DIR = "/root/wisconsin-overlay-map/output/subdivision_leads"
RAW_FILE = os.path.join(OUTPUT_DIR, "raw_filtered_results.json")
WORKERS = 10  # Parallel workers

session = requests.Session()
session.headers.update(HEADERS)

def get_detail_safe(pid):
    """Get one property detail, return None on failure."""
    try:
        resp = session.get(f"{BASE_URL}/v2/properties/{pid}", timeout=15)
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None

def classify_property(data):
    """Determine if property is for-sale based on detail data."""
    if not data:
        return "off-market", {}
    
    props = data.get("data", {}).get("properties", {})
    
    mls_status = str(props.get("mls_status", "")).lower()
    listing_status = str(props.get("listing_status", "")).lower()
    sale_price = props.get("current_sale_price", 0) or 0
    
    if mls_status in ("active", "for sale", "pending"):
        return "for-sale", props
    if listing_status in ("active", "for sale", "pending"):
        return "for-sale", props
    if sale_price > 0 and mls_status:
        return "for-sale", props
    
    return "off-market", props

def main():
    # Load raw results
    with open(RAW_FILE) as f:
        all_results = json.load(f)
    
    print(f"Loaded {sum(len(v) for v in all_results.values())} properties from {len(all_results)} counties")
    
    # Flatten all properties with IDs
    flat = []
    for county, props in all_results.items():
        for p in props:
            pid = p.get("property_id")
            if pid:
                p["_county"] = county  # Ensure county is set
                flat.append(p)
    
    print(f"Flattened: {len(flat)} properties")
    
    # Parallel detail lookups
    off_market = []
    for_sale = []
    pid_to_detail = {}
    
    # Batch into groups by property_id
    ids = [p["property_id"] for p in flat]
    print(f"Fetching details for {len(ids)} properties with {WORKERS} workers...")
    
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(get_detail_safe, pid): pid for pid in ids}
        for future in as_completed(futures):
            pid = futures[future]
            try:
                detail = future.result()
                pid_to_detail[pid] = detail
            except:
                pid_to_detail[pid] = None
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(ids)}...")
    
    print(f"Fetched {len(pid_to_detail)} details")
    
    # Classify and build entries
    for p in flat:
        pid = p["property_id"]
        detail = pid_to_detail.get(pid)
        classification, dprops = classify_property(detail)
        
        # Extract detail fields
        land_use = dprops.get("land_use_description", "") if dprops else ""
        zoning = dprops.get("zoning", "") if dprops else ""
        assessed_value = dprops.get("assessed_total_value", 0) if dprops else 0
        latitude = dprops.get("latitude", 0) if dprops else 0
        longitude = dprops.get("longitude", 0) if dprops else 0
        mls_status = dprops.get("mls_status", "") if dprops else ""
        sale_price = dprops.get("current_sale_price", 0) if dprops else 0
        legal = dprops.get("legal_description", "") if dprops else ""
        
        entry = {
            "property_id": pid,
            "apn": p.get("apn", ""),
            "address": p.get("street_address", ""),
            "owner": p.get("owner_full_name", ""),
            "acres": p.get("lot_size_acres", 0),
            "county": p.get("_county", ""),
            "municipality": p.get("_municipality", ""),
            "zip": p.get("_zip", ""),
            "growth_rating": p.get("_rating", ""),
            "muni_notes": p.get("_muni_notes", ""),
            "land_use": land_use,
            "zoning": zoning,
            "assessed_value": assessed_value,
            "latitude": latitude,
            "longitude": longitude,
            "mls_status": mls_status,
            "sale_price": sale_price,
            "legal_description": legal[:200] if legal else "",
        }
        
        if classification == "for-sale":
            for_sale.append(entry)
        else:
            off_market.append(entry)
    
    # Find multi-property owners
    owner_counts = Counter(e["owner"] for e in off_market + for_sale if e["owner"])
    multi_owners = {o: c for o, c in owner_counts.items() if c >= 2}
    
    for entry in off_market + for_sale:
        owner = entry["owner"]
        entry["multi_property"] = owner in multi_owners
        entry["owner_parcel_count"] = multi_owners.get(owner, 1)
    
    # Generate grading based on growth rating + in-path status
    for entry in off_market + for_sale:
        rating = entry["growth_rating"]
        muni = entry["municipality"]
        notes = entry["muni_notes"]
        
        if rating == "High":
            if "FLU" in notes or "sewer" in notes.lower() or "water" in notes.lower():
                entry["grade"] = "A — Prime subdivision target. In growth path with confirmed infrastructure."
            else:
                entry["grade"] = "A- — Strong growth area. High development pressure. Verify FLU details."
        elif rating == "Moderate to High":
            entry["grade"] = "B+ — Good subdivision potential. Edge-adjacent growth. Check sewer boundaries."
        elif rating == "Moderate":
            entry["grade"] = "B — Secondary growth ring. Feasible but requires more due diligence."
        else:
            entry["grade"] = "C — Lower growth area. May still work but verify comps and builder demand."
    
    # Sort each list by grade (best first), then acres
    grade_order = {"A": 0, "A-": 1, "B+": 2, "B": 3, "C": 4}
    off_market.sort(key=lambda e: (grade_order.get(e["grade"], 5), -e["acres"]))
    for_sale.sort(key=lambda e: (grade_order.get(e["grade"], 5), -e["acres"]))
    
    # Build the final deliverable
    final = {
        "generated": datetime.now().isoformat(),
        "methodology": "North Star / Cody Bjugan — Subdivision Only (20-300 acres, vacant, road frontage 400+ft, wetlands ≤30%, FEMA ≤50%). Excludes trusts, LLCs (non-Farm), INC, govt/tribal. Cross-referenced with county 2040 comprehensive plans.",
        "summary": {
            "total_properties": len(off_market) + len(for_sale),
            "off_market": len(off_market),
            "for_sale": len(for_sale),
            "multi_property_owners": len(multi_owners),
            "high_rated": len([e for e in off_market + for_sale if e["growth_rating"] == "High"]),
            "moderate_to_high": len([e for e in off_market + for_sale if e["growth_rating"] == "Moderate to High"]),
        },
        "off_market": off_market,
        "for_sale": for_sale,
        "multi_property_owners": {o: c for o, c in sorted(multi_owners.items(), key=lambda x: -x[1])[:50]},
        "county_breakdown": {},
    }
    
    for county in sorted(set(e["county"] for e in off_market + for_sale)):
        om = [e for e in off_market if e["county"] == county]
        fs = [e for e in for_sale if e["county"] == county]
        final["county_breakdown"][county] = {
            "off_market": len(om),
            "for_sale": len(fs),
            "total": len(om) + len(fs),
        }
    
    # Write the JSON
    json_path = os.path.join(OUTPUT_DIR, "subdivision_leads.json")
    with open(json_path, "w") as f:
        json.dump(final, f, indent=2)
    
    # Write a human-readable markdown report
    md_path = os.path.join(OUTPUT_DIR, "subdivision_leads.md")
    _write_markdown(final, md_path)
    
    print(f"\n{'='*60}")
    print(f"DONE:")
    print(f"  Off-Market: {len(off_market)}")
    print(f"  For Sale: {len(for_sale)}")
    print(f"  Multi-Property Owners: {len(multi_owners)}")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")
    print(f"{'='*60}")
    
    # County breakdown
    print("\nCounty Breakdown:")
    hdr = f"{'County':<15} {'Off-Market':>10} {'For Sale':>10} {'Total':>8}"
    print(hdr)
    print("-" * len(hdr))
    for county, counts in sorted(final["county_breakdown"].items()):
        print(f"{county:<15} {counts['off_market']:>10} {counts['for_sale']:>10} {counts['total']:>8}")

def _write_markdown(final, path):
    """Generate the human-readable markdown report."""
    lines = []
    lines.append("# North Star Subdivision Leads — TOP Counties")
    lines.append("")
    lines.append(f"**Generated:** {final['generated']}")
    lines.append(f"**Methodology:** {final['methodology']}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    s = final["summary"]
    lines.append(f"| Metric | Count |")
    lines.append(f"|---|---|")
    lines.append(f"| Total Properties | {s['total_properties']} |")
    lines.append(f"| Off-Market (Mail) | {s['off_market']} |")
    lines.append(f"| For Sale (Call) | {s['for_sale']} |")
    lines.append(f"| Multi-Property Owners | {s['multi_property_owners']} |")
    lines.append(f"| High Growth Areas | {s['high_rated']} |")
    lines.append(f"| Moderate-to-High Growth | {s['moderate_to_high']} |")
    lines.append("")
    
    # County breakdown table
    lines.append("## County Breakdown")
    lines.append("")
    lines.append("| County | Off-Market | For Sale | Total |")
    lines.append("|---|---|---|---|")
    for county, counts in sorted(final["county_breakdown"].items()):
        lines.append(f"| {county} | {counts['off_market']} | {counts['for_sale']} | {counts['total']} |")
    lines.append("")
    
    # Multi-property owners
    lines.append("## Multi-Property Owners (High-Value Targets)")
    lines.append("")
    lines.append("These owners have 2+ qualifying parcels. One conversation can unlock multiple deals.")
    lines.append("")
    lines.append("| Owner | Parcels | Counties |")
    lines.append("|---|---|---|")
    for owner, count in sorted(final["multi_property_owners"].items(), key=lambda x: -x[1])[:30]:
        # Find which counties this owner has parcels in
        counties = set()
        for e in final["off_market"] + final["for_sale"]:
            if e["owner"] == owner:
                counties.add(e["county"])
        lines.append(f"| {owner} | {count} | {', '.join(sorted(counties))} |")
    lines.append("")
    
    # OFF-MARKET section
    lines.append("---")
    lines.append("")
    lines.append("# 📬 OFF-MARKET LEADS (Mail Campaign)")
    lines.append("")
    lines.append(f"**{len(final['off_market'])} properties** — These owners are not actively selling. Mail campaign recommended.")
    lines.append("")
    
    for county in sorted(final["county_breakdown"].keys()):
        county_props = [e for e in final["off_market"] if e["county"] == county]
        if not county_props:
            continue
        
        lines.append(f"## {county} County — Off-Market ({len(county_props)})")
        lines.append("")
        
        for i, e in enumerate(county_props):
            grade = e["grade"]
            mp = "🔗 **MULTI-PROPERTY** " if e["multi_property"] else ""
            lines.append(f"### {i+1}. {e['apn']} — {e['acres']:.1f} acres — {e['grade']}")
            lines.append("")
            lines.append(f"| Field | Value |")
            lines.append(f"|---|---|")
            lines.append(f"| **APN** | {e['apn']} |")
            lines.append(f"| **Address** | {e['address']} |")
            lines.append(f"| **Owner** | {e['owner']} {mp}|")
            lines.append(f"| **Acres** | {e['acres']:.1f} |")
            lines.append(f"| **Municipality** | {e['municipality']} |")
            lines.append(f"| **Growth Rating** | {e['growth_rating']} |")
            lines.append(f"| **Location** | {e['county']} County, ZIP {e['zip']} |")
            if e['latitude'] and e['longitude']:
                lines.append(f"| **Coordinates** | {e['latitude']}, {e['longitude']} |")
            if e['land_use']:
                lines.append(f"| **Land Use** | {e['land_use']} |")
            if e['zoning']:
                lines.append(f"| **Zoning** | {e['zoning']} |")
            if e['assessed_value']:
                lines.append(f"| **Assessed Value** | ${e['assessed_value']:,.0f} |")
            lines.append(f"| **Grade** | {grade} |")
            lines.append(f"| **Growth Context** | {e['muni_notes']} |")
            if e['multi_property']:
                lines.append(f"| **Owner Portfolio** | {e['owner_parcel_count']} qualifying parcels across target counties |")
            lines.append("")
    
    # FOR-SALE section
    lines.append("---")
    lines.append("")
    lines.append("# 📞 FOR-SALE LEADS (Call First)")
    lines.append("")
    lines.append(f"**{len(final['for_sale'])} properties** — These appear to be actively listed. Call agents/owners directly.")
    lines.append("")
    
    for county in sorted(final["county_breakdown"].keys()):
        county_props = [e for e in final["for_sale"] if e["county"] == county]
        if not county_props:
            continue
        
        lines.append(f"## {county} County — For Sale ({len(county_props)})")
        lines.append("")
        
        for i, e in enumerate(county_props):
            mp = "🔗 **MULTI-PROPERTY** " if e["multi_property"] else ""
            lines.append(f"### {i+1}. {e['apn']} — {e['acres']:.1f} acres — {e['grade']}")
            lines.append("")
            lines.append(f"| Field | Value |")
            lines.append(f"|---|---|")
            lines.append(f"| **APN** | {e['apn']} |")
            lines.append(f"| **Address** | {e['address']} |")
            lines.append(f"| **Owner** | {e['owner']} {mp}|")
            lines.append(f"| **Acres** | {e['acres']:.1f} |")
            lines.append(f"| **Municipality** | {e['municipality']} |")
            lines.append(f"| **Growth Rating** | {e['growth_rating']} |")
            lines.append(f"| **Location** | {e['county']} County, ZIP {e['zip']} |")
            if e['latitude'] and e['longitude']:
                lines.append(f"| **Coordinates** | {e['latitude']}, {e['longitude']} |")
            if e['sale_price']:
                lines.append(f"| **List Price** | ${e['sale_price']:,.0f} |")
            if e['mls_status']:
                lines.append(f"| **MLS Status** | {e['mls_status']} |")
            if e['land_use']:
                lines.append(f"| **Land Use** | {e['land_use']} |")
            if e['zoning']:
                lines.append(f"| **Zoning** | {e['zoning']} |")
            lines.append(f"| **Grade** | {grade} |")
            lines.append(f"| **Growth Context** | {e['muni_notes']} |")
            if e['multi_property']:
                lines.append(f"| **Owner Portfolio** | {e['owner_parcel_count']} qualifying parcels across target counties |")
            lines.append("")
    
    # Write file
    with open(path, "w") as f:
        f.write("\n".join(lines))
    
    # Generate per-county markdown files
    for county in sorted(final["county_breakdown"].keys()):
        county_dir = os.path.join(OUTPUT_DIR, "by_county")
        os.makedirs(county_dir, exist_ok=True)
        
        om = [e for e in final["off_market"] if e["county"] == county]
        fs = [e for e in final["for_sale"] if e["county"] == county]
        
        clines = []
        clines.append(f"# {county} County — Subdivision Leads")
        clines.append("")
        clines.append(f"**Off-Market:** {len(om)} | **For Sale:** {len(fs)} | **Total:** {len(om)+len(fs)}")
        clines.append("")
        
        if om:
            clines.append("## 📬 Off-Market")
            clines.append("")
            for e in om:
                mp = " 🔗MULTI" if e["multi_property"] else ""
                clines.append(f"- **{e['apn']}** | {e['acres']:.1f}ac | {e['owner']}{mp} | {e['municipality']} ({e['growth_rating']}) | {e['grade']}")
            clines.append("")
        
        if fs:
            clines.append("## 📞 For Sale")
            clines.append("")
            for e in fs:
                mp = " 🔗MULTI" if e["multi_property"] else ""
                price = f" ${e['sale_price']:,.0f}" if e['sale_price'] else ""
                clines.append(f"- **{e['apn']}** | {e['acres']:.1f}ac{price} | {e['owner']}{mp} | {e['municipality']} ({e['growth_rating']}) | {e['grade']}")
            clines.append("")
        
        with open(os.path.join(county_dir, f"{county}_leads.md"), "w") as f:
            f.write("\n".join(clines))
    
    print(f"\n  Per-county files written to: {county_dir}/")

if __name__ == "__main__":
    main()