#!/usr/bin/env python3
"""Update TOP_COUNTIES files with fresh LP pipeline data for Kenosha and Washington."""
import json, os

COUNTY_DIR = "/root/wisconsin-overlay-map/docs/TOP_COUNTIES"
LEADS_DIR = "/root/wisconsin-overlay-map/output/subdivision_leads/by_county"

GRADES = {
    "Kenosha": {
        "PLEASANT PRAIRIE": "A",
        "SOMERS": "A",
        "BRISTOL": "A",
        "SALEM LAKES": "A",
    },
    "Washington": {
        "GERMANTOWN": "A",
        "JACKSON": "A+",
        "RICHFIELD": "A",
        "SLINGER": "A",
        "HARTFORD": "A-",
    }
}

for county in ["Kenosha", "Washington"]:
    leads_file = os.path.join(LEADS_DIR, f"{county}_leads.json")
    county_file = os.path.join(COUNTY_DIR, f"{county}_County.md")
    
    if not os.path.exists(leads_file):
        print(f"No leads file: {leads_file}")
        continue
    
    with open(leads_file) as f:
        data = json.load(f)
    
    with open(county_file) as f:
        content = f.read()
    
    # Remove old pipeline section if exists
    if "## Subdivision Pipeline" in content:
        content = content.split("## Subdivision Pipeline")[0].rstrip()
    
    # Build pipeline section
    towns = data.get("towns", [])
    grades = GRADES.get(county, {})
    
    total_om = sum(len(t.get("off_market",[])) for t in towns)
    total_fs = sum(len(t.get("for_sale",[])) for t in towns)
    
    pipe = f"\n\n## Subdivision Pipeline\n\n"
    pipe += f"**{total_om+total_fs} parcels** | {total_om} off-market | {total_fs} for-sale | Category 1 filters: 20-200ac, 300ft road, ≤25% wetlands, ≤50% FEMA, ≥50% slope <15°\n\n"
    pipe += "## Parcels Ranked by Rezoning Potential\n\n"
    pipe += "| Rezoning | Town | Acres | Owner | APN | Status |\n"
    pipe += "|---|---|---|---|---|---|\n"
    
    row_count = 0
    for town_data in towns:
        town = town_data["town"]
        grade = grades.get(town, "A")
        
        # Off-market first (mail targets)
        for p in town_data.get("off_market",[]):
            if row_count >= 250: break
            acres = p.get("lot_size_acres", "?") or "?"
            owner = (p.get("owner_full_name","") or "")[:30]
            apn = (p.get("apn","") or "")[:20]
            pipe += f"| **{grade}** | {town} | {acres} | {owner} | {apn} | 📬 |\n"
            row_count += 1
        
        # For-sale (call targets)
        seen_fs = set()
        for p in town_data.get("for_sale",[]):
            if row_count >= 250: break
            pid = p.get("property_id")
            if pid and pid in seen_fs: continue
            if pid: seen_fs.add(pid)
            acres = p.get("lot_size_acres", "?") or "?"
            owner = (p.get("owner_full_name","") or "")[:30]
            apn = (p.get("apn","") or "")[:20]
            pipe += f"| **{grade}** | {town} | {acres} | {owner} | {apn} | 📞 |\n"
            row_count += 1
    
    if row_count >= 250:
        pipe += f"| ... | ... | ... (+{total_om+total_fs - 250} more) | ... | ... |\n"
    
    pipe += "\n## Rezoning Analysis\n\n"
    pipe += "### 🔥 A+/A — Prime Ag→Subdivision Targets\n"
    pipe += "*Directly adjacent to city limits. FLU maps show ag→residential. Sewer/water planned or active.*\n\n"
    
    # Top 10 off-market by acreage
    all_om = []
    for town_data in towns:
        for p in town_data.get("off_market",[]):
            acres = p.get("lot_size_acres", 0) or 0
            if acres:
                all_om.append((acres, p, town_data["town"]))
    all_om.sort(key=lambda x: x[0], reverse=True)
    
    for acres, p, town in all_om[:10]:
        owner = (p.get("owner_full_name","") or "")[:35]
        apn = (p.get("apn","") or "")[:15]
        pipe += f"- **{apn}** | {acres}ac | {owner} | {town}\n"
    
    pipe += "\n### Clusters\n"
    for town_data in towns:
        town = town_data["town"]
        grade = grades.get(town, "A")
        om = len(town_data.get("off_market",[]))
        fs = len({p.get("property_id") for p in town_data.get("for_sale",[]) if p.get("property_id")})
        om_acres = sum(p.get("lot_size_acres", 0) or 0 for p in town_data.get("off_market",[]))
        if om + fs > 0:
            pipe += f"**{town}** ({grade}): {om+fs} parcels, ~{om_acres:.0f}ac\n"
            if fs > 0:
                pipe += f"  {fs} MLS — call first\n"
            if om > 0:
                # Count multi-owners
                owners = [p.get("owner_full_name","") for p in town_data.get("off_market",[])]
                multi = len(owners) - len(set(owners))
                if multi > 0:
                    pipe += f"  {multi} multi-owners\n"
    
    pipe += "\n### 📞 For-Sale\n"
    for town_data in towns:
        town = town_data["town"]
        grade = grades.get(town, "A")
        fs = len({p.get("property_id") for p in town_data.get("for_sale",[]) if p.get("property_id")})
        if fs > 0:
            pipe += f"- **{town}** ({grade}): {fs}\n"
    
    pipe += "\n### 📬 Off-Market\n"
    for town_data in towns:
        town = town_data["town"]
        grade = grades.get(town, "A")
        om = len(town_data.get("off_market",[]))
        if om > 0:
            owners = [p.get("owner_full_name","") for p in town_data.get("off_market",[])]
            multi = len(owners) - len(set(owners))
            pipe += f"- **{town}** ({grade}): {om}"
            if multi > 0:
                pipe += f" — {multi} multi-owners"
            pipe += "\n"
    
    pipe += f"\n---\n*{json.dumps(__import__('datetime').datetime.now().isoformat()[:16])} | North Star / Cody Bjugan criteria. HIGH-rated towns only. Category 1 filters.*\n"
    
    new_content = content + pipe
    
    with open(county_file, "w") as f:
        f.write(new_content)
    
    print(f"  {county}_County.md: updated — {total_om} OM + {total_fs} FS")

print("Done")