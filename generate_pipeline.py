#!/usr/bin/env python3
"""
North Star Subdivision Pipeline Generator
Generates A+/A/A-/B+/B graded pipeline from Land Portal data, writes to docs/TOP_COUNTIES/
"""
import json, os, re
from datetime import datetime, timezone
from collections import Counter

CHECKPOINT_DIR = "/root/wisconsin-overlay-map/checkpoints"
TOP_COUNTIES_DIR = "/root/wisconsin-overlay-map/docs/TOP_COUNTIES"

# ===== REZONING GRADES =====
# A+, A, A- for the user's specified HIGH-rated towns
REZONING_GRADES = {
    # Outagamie
    "VILLAGE OF GREENVILLE": "A+",
    "TOWN OF GRAND CHUTE": "A+",
    "VILLAGE OF HARRISON": "A",
    # Brown  
    "TOWN OF LEDGEVIEW": "A",
    "VILLAGE OF HOWARD": "A",
    "VILLAGE OF SUAMICO": "A",
    "VILLAGE OF BELLEVUE": "A",
    "TOWN OF LAWRENCE": "A",
    "VILLAGE OF ASHWAUBENON": "A+",
    # Dane
    "CITY OF VERONA": "A",
    "CITY OF FITCHBURG": "A+",
    "TOWN OF SUN PRAIRIE": "A+",
    "TOWN OF WESTPORT": "A",
    "TOWN OF SPRINGFIELD": "A",
    "TOWN OF BURKE": "A",
    "TOWN OF BLOOMING GROVE": "A",
    "VILLAGE OF DEFOREST": "A",
    # Waukesha
    "VILLAGE OF MENOMONEE FALLS": "A+",
    "TOWN OF LISBON": "A",
    "TOWN OF GENESEE": "A",
    "VILLAGE OF PEWAUKEE": "A",
    "VILLAGE OF SUSSEX": "A",
    # Ozaukee
    "VILLAGE OF GRAFTON": "A",
    "VILLAGE OF SAUKVILLE": "A",
    "TOWN OF CEDARBURG": "A",
    "CITY OF MEQUON": "A+",
    # Rock
    "BELOIT": "A",
    "JANESVILLE": "A",
    "TURTLE": "A",
    # Winnebago
    "TOWN OF NEENAH": "A",
    "TOWN OF OSHKOSH": "A",
    "TOWN OF ALGOMA": "A",
    "TOWN OF MENASHA": "A",
    # Calumet
    "TOWN OF HARRISON": "A",
    "TOWN OF MENASHA": "A",
}

GRADE_ORDER = {"A+": 0, "A": 1, "A-": 2, "B+": 3, "B": 4}

COUNTY_FIPS_MAP = {
    "55087": "Outagamie",
    "55009": "Brown",
    "55025": "Dane",
    "55133": "Waukesha",
    "55089": "Ozaukee",
    "55105": "Rock",
    "55139": "Winnebago",
    "55015": "Calumet",
}

# ===== OWNER FILTERING =====
def should_keep(owner_name):
    if not owner_name:
        return False
    u = owner_name.upper().strip()
    
    trusts = ["TRUST", "TRST", "REVOCABLE", "REVOCABL", "IRREVOCABLE",
              "IRREVOCABL", "REV TR", "LIV TR", "IRREV TR", " REVO", " LIVING TR"]
    if any(t in u for t in trusts):
        return False
    if u.endswith(" TRST") or u.endswith(" TR") or u.endswith(" REVO"):
        return False
    
    govt = ["COUNTY", "TOWNSHIP", "CITY OF", "STATE OF", "NATION ", "TRIBE",
            "VILLAGE OF", "TOWN OF", "HOUSING AUTHORITY", "DEPT OF",
            "DEPARTMENT OF", "DOT", "DNR"]
    if any(p in u for p in govt):
        return False
    
    utilities = ["ELECTRIC POWER", "GAS COMPANY", "WATER COMPANY",
                 "SANITARY DISTRICT", "SCHOOL DISTRICT", "UNIFIED SCHOOL"]
    if any(p in u for p in utilities):
        return False
    
    hoa = ["OWNERS OF LOTS", "LOT OWNERS OF", "OWNER`S OF LOTS",
           "HOMEOWNERS ASSOC", "PROPERTY OWNERS ASSOC"]
    if any(p in u for p in hoa):
        return False
    
    artifacts = ["AVAILABLE NOT", "AVAILABLE NAME NOT", "AVAILABLE",
                 "NOT AVAILABLE", "UNKNOWN", "N/A", "OWNER", "NO NAME"]
    if u in artifacts:
        return False
    
    if " INC" in u or " INC." in u or "INCORPORATED" in u or " CORP" in u or " CORPORATION" in u:
        return False
    
    if ("LLC" in u or "L L C" in u or "LIMITED LIABILITY" in u):
        return "FARM" in u
    
    industrial = ["ASPHALT", "QUARRY", "GRAVEL", "CONCRETE", "MINING", "SAND &"]
    if any(p in u for p in industrial):
        return False
    
    banks = ["BANK", "CREDIT UNION", "CHURCH", "DIOCESE", "ARCHDIOCESE"]
    if any(p in u for p in banks):
        return False
    
    return True


def simplify_town(name):
    """Normalize town names for matching."""
    n = name.upper().replace("TOWN OF ", "").replace("VILLAGE OF ", "").replace("CITY OF ", "").strip()
    # Handle Rock County bare names
    return n


# ===== LOAD DATA =====
off = json.load(open(f"{CHECKPOINT_DIR}/off_market_results.json"))
fs = json.load(open(f"{CHECKPOINT_DIR}/for_sale_results.json"))
detail = {}
detail_path = f"{CHECKPOINT_DIR}/detail_extraction.json"
if os.path.exists(detail_path):
    detail = json.load(open(detail_path)).get("details", {})

print(f"Loaded {len(off)} off-market parcels")
print(f"Loaded {len(fs)} for-sale parcels")
print(f"Loaded {len(detail)} detail records")

# Build property_id -> detail map for fast lookup
detail_map = {}
for pid_str, d in detail.items():
    detail_map[int(pid_str)] = d

# ===== PROCESS OFF-MARKET =====
off_filtered = []
off_rejected_owners = 0
off_no_owner = 0

for p in off:
    owner = p.get("owner_full_name", "").strip()
    if not owner:
        off_no_owner += 1
        continue
    if not should_keep(owner):
        off_rejected_owners += 1
        continue
    
    pid = p["property_id"]
    d = detail_map.get(pid, {})
    
    # Get acreage
    acres = p.get("lot_size_acres") or d.get("acres") or d.get("calc_acres") or 0
    if not acres:
        acres = d.get("lot_size_acres", 0)
    
    town_display = simplify_town(p.get("_query_municipality", ""))
    
    off_filtered.append({
        "property_id": pid,
        "owner": owner,
        "apn": p.get("apn", ""),
        "acres": acres,
        "town": p.get("_query_municipality", ""),
        "town_display": town_display,
        "fips": str(p.get("fips", p.get("_query_fips", ""))),
        "address": p.get("street_address", ""),
        "sale_price": d.get("sale_price", 0),
        "sale_date": d.get("sale_date", ""),
        "needs_detail": not p.get("lot_size_acres") and not d.get("calc_acres"),
    })

print(f"\nOff-market filtering:")
print(f"  Total: {len(off)}")
print(f"  No owner: {off_no_owner}")
print(f"  Rejected (owner): {off_rejected_owners}")
print(f"  Kept: {len(off_filtered)}")

# ===== PROCESS FOR-SALE =====
fs_filtered = []
fs_rejected_owners = 0
fs_no_owner = 0

for p in fs:
    owner = p.get("owner_full_name", "").strip()
    if not owner:
        fs_no_owner += 1
        continue
    if not should_keep(owner):
        fs_rejected_owners += 1
        continue
    
    pid = p["property_id"]
    d = detail_map.get(pid, {})
    
    acres = p.get("lot_size_acres") or d.get("acres") or d.get("calc_acres") or 0
    
    town_display = simplify_town(p.get("_query_municipality", ""))
    
    fs_filtered.append({
        "property_id": pid,
        "owner": owner,
        "apn": p.get("apn", ""),
        "acres": acres,
        "town": p.get("_query_municipality", ""),
        "town_display": town_display,
        "fips": str(p.get("fips", p.get("_query_fips", ""))),
        "address": p.get("street_address", ""),
        "sale_price": d.get("sale_price", 0),
        "sale_date": d.get("sale_date", ""),
    })

print(f"\nFor-sale filtering:")
print(f"  Total: {len(fs)}")
print(f"  No owner: {fs_no_owner}")
print(f"  Rejected (owner): {fs_rejected_owners}")
print(f"  Kept: {len(fs_filtered)}")

# Deduplicate: remove for-sale from off-market if same property_id
off_ids = set(p["property_id"] for p in off_filtered)
fs_ids = set(p["property_id"] for p in fs_filtered)
fs_only_ids = fs_ids - off_ids

off_final = off_filtered
fs_final = [p for p in fs_filtered if p["property_id"] in fs_only_ids]

print(f"\nAfter dedup:")
print(f"  Off-market (unique): {len(off_final)}")
print(f"  For-sale (unique): {len(fs_final)}")

# ===== GROUP BY COUNTY =====
def get_grade(town_name):
    return REZONING_GRADES.get(town_name, "B")

def sort_key(item):
    grade = get_grade(item["town"])
    grade_order = GRADE_ORDER.get(grade, 99)
    acres = item.get("acres", 0) or 0
    return (grade_order, -acres)

# Multi-property detection
off_owner_counts = Counter(p["owner"] for p in off_final)
multi_owners = {o for o, c in off_owner_counts.items() if c >= 2}
fs_owner_counts = Counter(p["owner"] for p in fs_final)
fs_multi = {o for o, c in fs_owner_counts.items() if c >= 2}

# ===== GENERATE COUNTY PIPELINE SECTIONS =====
generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")

county_results = {}
for fips, county_name in COUNTY_FIPS_MAP.items():
    c_off = [p for p in off_final if p["fips"] == fips]
    c_fs = [p for p in fs_final if p["fips"] == fips]
    
    # Sort off-market by grade then acres
    c_off.sort(key=sort_key)
    c_fs.sort(key=sort_key)
    
    total = len(c_off) + len(c_fs)
    town_off_counts = Counter(p["town"] for p in c_off)
    town_fs_counts = Counter(p["town"] for p in c_fs)
    
    county_results[county_name] = {
        "off": c_off,
        "fs": c_fs,
        "total": total,
        "town_off": town_off_counts,
        "town_fs": town_fs_counts,
    }

# ===== WRITE TO COUNTY FILES =====
for county_name, cr in county_results.items():
    filepath = f"{TOP_COUNTIES_DIR}/{county_name}_County.md"
    if not os.path.exists(filepath):
        print(f"  WARNING: {filepath} not found, skipping")
        continue
    
    c_off = cr["off"]
    c_fs = cr["fs"]
    town_off = cr["town_off"]
    town_fs = cr["town_fs"]
    
    # Build pipeline section
    lines = []
    lines.append(f"\n## Subdivision Pipeline\n")
    lines.append(f"# {county_name} County — North Star Subdivision Pipeline\n")
    lines.append(f"**{len(c_off) + len(c_fs)} total parcels** | {len(town_off)} HIGH-rated towns | {len(c_off)} off-market (📬) | {len(c_fs)} for-sale (📞)\n")
    
    if not c_off and not c_fs:
        lines.append("*No qualifying parcels found in HIGH-rated towns.*\n")
        # Skip rest
    else:
        lines.append("| Rezoning | Town | Acres | Owner | APN | Status |\n")
        lines.append("|---|---|---|---|---|---|\n")
        
        # Write off-market
        for p in c_off:
            grade = get_grade(p["town"])
            acres_str = f"{p['acres']:.1f}" if p['acres'] and p['acres'] > 0 else "?"
            owner_display = p["owner"]
            if p["owner"] in multi_owners:
                owner_display += " 🔗"
            status = "📬 Mail"
            if p["needs_detail"]:
                acres_str += "⚠️"
            lines.append(f"| **{grade}** | {p['town_display']} | {acres_str} | {owner_display} | {p['apn']} | {status} |\n")
        
        # Write for-sale
        for p in c_fs:
            grade = get_grade(p["town"])
            acres_str = f"{p['acres']:.1f}" if p['acres'] and p['acres'] > 0 else "?"
            owner_display = p["owner"]
            if p["owner"] in fs_multi:
                owner_display += " 🔗"
            lines.append(f"| **{grade}** | {p['town_display']} | {acres_str} | {owner_display} | {p['apn']} | 📞 MLS |\n")
    
    # North Star Takeaway
    lines.append("\n## North Star Takeaway\n")
    
    # Cluster by town
    town_clusters_off = Counter(p["town"] for p in c_off)
    town_clusters_fs = Counter(p["town"] for p in c_fs)
    
    # Off-market clusters (3+ parcels)
    for town, count in sorted(town_clusters_off.items(), key=lambda x: -x[1]):
        if count >= 3:
            town_parcels = [p for p in c_off if p["town"] == town]
            total_acres = sum(p["acres"] or 0 for p in town_parcels)
            multi_count = len([p for p in town_parcels if p["owner"] in multi_owners])
            grade = get_grade(town)
            town_display = simplify_town(town)
            lines.append(f"### 📬 {town_display} Cluster — {count} parcels, ~{total_acres:.0f} acres ({grade})\n")
            lines.append(f"- {count} parcels totaling approximately {total_acres:.0f} acres in {town_display}, a {grade}-rated town in {county_name} County.\n")
            lines.append(f"- {multi_count} multi-property owner(s) with multiple parcels in this cluster.\n")
    
    # For-sale clusters (3+ parcels)
    for town, count in sorted(town_clusters_fs.items(), key=lambda x: -x[1]):
        if count >= 3:
            town_parcels = [p for p in c_fs if p["town"] == town]
            total_acres = sum(p["acres"] or 0 for p in town_parcels)
            grade = get_grade(town)
            town_display = simplify_town(town)
            lines.append(f"### 📞 {town_display} Cluster — {count} parcels, ~{total_acres:.0f} acres ({grade})\n")
            lines.append(f"- {count} parcels totaling approximately {total_acres:.0f} acres in {town_display}, a {grade}-rated town in {county_name} County.\n")
    
    # Priority Targets
    lines.append("\n### 📞 For-Sale Priority Targets\n")
    for town, count in sorted(town_clusters_fs.items(), key=lambda x: -x[1]):
        if count > 0:
            grade = get_grade(town)
            town_display = simplify_town(town)
            lines.append(f"- **{town_display}** ({grade}): {count} MLS-listed parcels — call first\n")
    
    lines.append("\n### 📬 Off-Market Priority Targets\n")
    for town, count in sorted(town_clusters_off.items(), key=lambda x: -x[1]):
        if count > 0:
            grade = get_grade(town)
            town_display = simplify_town(town)
            multi_count = len([p for p in c_off if p["owner"] in multi_owners])
            lines.append(f"- **{town_display}** ({grade}): {count} off-market parcels — mail campaign\n")
            if multi_count > 0:
                lines.append(f"  - {multi_count} multi-property owners to prioritize\n")
    
    lines.append(f"\n*Generated: {generated_at} | North Star / Cody Bjugan criteria. Category 1 filters: 20-200ac, 300ft road, ≤25% wetlands, ≤50% FEMA, ≥50% slope <15°. Town-level queries via municipality filter. Rezoning grades from county 2040 comprehensive plans.*\n")
    
    pipeline_text = "".join(lines)
    
    # Read existing file and find/replace the pipeline section
    with open(filepath, "r") as f:
        content = f.read()
    
    # Check if pipeline section exists and replace it
    if "## Subdivision Pipeline" in content:
        # Find the pipeline section boundaries
        pipeline_start = content.index("## Subdivision Pipeline")
        # Remove from pipeline_start to end
        old_section = content[pipeline_start:]
        new_content = content[:pipeline_start] + pipeline_text
    else:
        # Append to file
        new_content = content + "\n" + pipeline_text
    
    with open(filepath, "w") as f:
        f.write(new_content)
    
    print(f"✅ {county_name}: {len(c_off)} off-market + {len(c_fs)} for-sale = {len(c_off)+len(c_fs)} total")
    if any(p["needs_detail"] for p in c_off):
        needs = sum(1 for p in c_off if p["needs_detail"])
        print(f"   ⚠️ {needs} parcels flagged for detail extraction (acreage pending)")

print(f"\n{'='*60}")
print("PIPELINE GENERATION COMPLETE")
print(f"{'='*60}")
print(f"Total off-market: {sum(len(cr['off']) for cr in county_results.values())}")
print(f"Total for-sale: {sum(len(cr['fs']) for cr in county_results.values())}")
print(f"Grand total: {sum(cr['total'] for cr in county_results.values())}")

# ===== UPDATE README =====
readme_path = f"{TOP_COUNTIES_DIR}/README.md"
with open(readme_path, "r") as f:
    readme = f.read()

# Update the pipeline counts
pipeline_status = []
for county_name in ["Outagamie", "Brown", "Dane", "Waukesha", "Ozaukee", "Rock", "Winnebago", "Calumet"]:
    cr = county_results.get(county_name, {"off": [], "fs": [], "total": 0})
    off_count = len(cr["off"])
    fs_count = len(cr["fs"])
    total = off_count + fs_count
    pipeline_status.append(f"  - {county_name}: {total} parcels ({off_count} off-market, {fs_count} for-sale)")

# Add pipeline summary to README
pipeline_section = f"""
## Pipeline Status (as of {generated_at})

Live Land Portal query results for HIGH-rated towns (A+, A, A-):
"""
pipeline_section += "\n".join(pipeline_status)
pipeline_section += "\n"

# Append to README if not already there
if "## Pipeline Status" not in readme:
    readme += pipeline_section
    with open(readme_path, "w") as f:
        f.write(readme)
    print(f"\n✅ README updated with pipeline status")

print("\nDone!")