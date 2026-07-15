#!/usr/bin/env python3
"""
Read pipeline output files and update docs/TOP_COUNTIES with Subdivision Pipeline sections.
Also updates README.md with new pipeline status.
"""
import os, json, re
from collections import defaultdict
from datetime import datetime

TOP_COUNTIES_DIR = "/root/wisconsin-overlay-map/docs/TOP_COUNTIES"
PIPELINE_DIR = "/root/wisconsin-overlay-map/output/subdivision_leads/by_county"

# Read all pipeline files
pipeline_data = {}
for fname in os.listdir(PIPELINE_DIR):
    if not fname.endswith("_pipeline.md"):
        continue
    county = fname.replace("_pipeline.md", "")
    path = os.path.join(PIPELINE_DIR, fname)
    with open(path) as f:
        content = f.read()
    pipeline_data[county] = content

# Parse pipeline stats from each file
pipeline_stats = {}
for county, content in pipeline_data.items():
    lines = content.split("\n")
    # Find stats line: "**N parcels** | M off-market | K for-sale | ..."
    for line in lines:
        if line.startswith("**") and "parcels" in line:
            m = re.match(r'\*\*(\d+) parcels\*\*\s*\|\s*(\d+) off-market\s*\|\s*(\d+) for-sale', line)
            if m:
                pipeline_stats[county] = {
                    'total': int(m.group(1)),
                    'off_market': int(m.group(2)),
                    'for_sale': int(m.group(3))
                }
            break

# Update each county's TOP_COUNTIES file
county_map = {
    'Outagamie': 'Outagamie_County.md',
    'Brown': 'Brown_County.md',
    'Dane': 'Dane_County.md',
    'Waukesha': 'Waukesha_County.md',
    'Ozaukee': 'Ozaukee_County.md',
    'Rock': 'Rock_County.md',
    'Winnebago': 'Winnebago_County.md',
    'Calumet': 'Calumet_County.md',
    'Milwaukee': 'Milwaukee_County.md',
    'Door': 'Door_County.md'
}

for county, fname in county_map.items():
    fpath = os.path.join(TOP_COUNTIES_DIR, fname)
    if not os.path.exists(fpath):
        print(f"  {county}: file not found, skipping")
        continue

    with open(fpath) as f:
        orig = f.read()

    pipeline_content = pipeline_data.get(county, "No pipeline data available.")

    # Check if there's an existing Subdivision Pipeline section
    if "## Subdivision Pipeline" in orig:
        # Replace everything from ## Subdivision Pipeline to end
        new_content = re.sub(
            r'## Subdivision Pipeline.*$',
            '## Subdivision Pipeline\n\n' + pipeline_content.strip(),
            orig,
            count=1,
            flags=re.DOTALL
        )
    elif "## Pipeline" in orig:
        # Alternative section name
        new_content = re.sub(
            r'## Pipeline.*$',
            '## Subdivision Pipeline\n\n' + pipeline_content.strip(),
            orig,
            count=1,
            flags=re.DOTALL
        )
    else:
        # Append to end
        new_content = orig.rstrip() + '\n\n## Subdivision Pipeline\n\n' + pipeline_content.strip() + '\n'

    with open(fpath, 'w') as f:
        f.write(new_content)
    print(f"  {county}: updated")

# Update README with new pipeline status
readme_path = os.path.join(TOP_COUNTIES_DIR, "README.md")
if os.path.exists(readme_path):
    with open(readme_path) as f:
        readme = f.read()

    # Build new pipeline status block
    now_str = datetime.now().strftime("%Y-%m-%d")
    status_lines = [f"## Pipeline Status (as of {now_str})\n"]
    status_lines.append("")
    status_lines.append("Live Land Portal query results for HIGH-rated towns (A+, A, A-):\n")

    for county in ['Outagamie', 'Brown', 'Dane', 'Waukesha', 'Ozaukee', 'Rock', 'Winnebago', 'Calumet']:
        stats = pipeline_stats.get(county, {'total': 0, 'off_market': 0, 'for_sale': 0})
        if stats['total'] > 0 or True:  # show all
            status_lines.append(f"  - **{county}**: {stats['total']} parcels ({stats['off_market']} off-market, {stats['for_sale']} for-sale)")

    status_lines.append("")
    new_status = "\n".join(status_lines)

    # Replace old pipeline status section
    if "## Pipeline Status" in readme:
        readme = re.sub(
            r'## Pipeline Status.*?(?=\n## |\Z)',
            new_status,
            readme,
            count=1,
            flags=re.DOTALL
        )
    else:
        # Append before last line or at end
        readme = readme.rstrip() + '\n\n' + new_status + '\n'

    with open(readme_path, 'w') as f:
        f.write(readme)
    print(f"  README: updated")

print("\nDone updating TOP_COUNTIES docs.")
print(f"\nPipeline stats summary:")
for county in ['Outagamie', 'Brown', 'Dane', 'Waukesha', 'Ozaukee', 'Rock', 'Winnebago', 'Calumet']:
    stats = pipeline_stats.get(county, {'total': 0, 'off_market': 0, 'for_sale': 0})
    print(f"  {county}: {stats['total']} parcels ({stats['off_market']} OM + {stats['for_sale']} FS)")