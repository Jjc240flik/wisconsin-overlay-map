import os, re
from collections import defaultdict

basedirs = {
    '2025': '/root/wisconsin-overlay-map/data/greenville_pdfs/village_board/2025',
    '2026': '/root/wisconsin-overlay-map/data/greenville_pdfs/village_board/2026',
}

# Development-related keywords to identify substantive votes
dev_keywords = ['subdivision', 'rezoning', 'concept plan', 'Whispering Winds', 'Savannah Heights', 
                'Encore', 'Harvest Ridge', 'New Creations', 'Special Exception', 'PUD',
                'Final Plat', 'Preliminary Plat', 'Developers Agreement', 'Moratorium',
                'Airport', 'sewer service area', 'SSA Amendment', 'comprehensive plan',
                'zoning map amendment', 'TIF', 'public improvement', 'CSM']

# Known board members
board_members = ['Jack Anderson', 'Andy Peters', 'Mark Strobel', 'Dean Culbertson', 
                 'Brittany Helf', 'Brian Mulroy']

print("=== VILLAGE BOARD VOTING ANALYSIS ===\n")

for year, basedir in basedirs.items():
    if not os.path.exists(basedir):
        continue
    print(f"\n{'='*80}")
    print(f"  {year} VILLAGE BOARD MEETINGS")
    print(f"{'='*80}")
    
    for fname in sorted(os.listdir(basedir)):
        if not fname.endswith('_Minutes.txt'):
            continue
        fpath = os.path.join(basedir, fname)
        date = fname[:10]
        
        with open(fpath, 'r', errors='ignore') as f:
            content = f.read()
        
        # Extract board members present
        present = []
        for m in board_members:
            if m in content:
                present.append(m)
        
        # Find development-related items
        found_items = []
        for kw in dev_keywords:
            if kw.lower() in content.lower():
                found_items.append(kw)
        
        if not found_items:
            continue
        
        # Extract motions and votes
        lines = content.split('\n')
        motions = []
        for i, line in enumerate(lines):
            if 'Motion by' in line and 'second by' in line:
                # Extract the motion maker, second, and result
                motion_match = re.search(r'Motion by ([^,]+), second by ([^)]+)\)? to (.+)', line)
                if motion_match:
                    maker = motion_match.group(1).strip()
                    seconder = motion_match.group(2).strip()
                    action = motion_match.group(3).strip()[:100]
                    # Look for result in next few lines
                    result = ''
                    for j in range(i+1, min(i+5, len(lines))):
                        rmatch = re.search(r'Motion carried (\d+ - \d+)|Motion carried (\w+)', lines[j])
                        if rmatch:
                            result = rmatch.group(0) or rmatch.group(1) or rmatch.group(2)
                            break
                    if result:
                        motions.append(f"  Motion: {maker} / {seconder} → {action}\n  Result: {result}")
        
        print(f"\n{date} — Present: {', '.join(present) if present else 'unknown'}")
        for m in found_items:
            print(f"  [{m}]")
        for m in motions:
            print(m)

print("\n\n=== VOTE TALLY BY MEMBER ===")
# Count how many times each member made or seconded motions
motion_count = defaultdict(int)
second_count = defaultdict(int)
for year, basedir in basedirs.items():
    if not os.path.exists(basedir):
        continue
    for fname in sorted(os.listdir(basedir)):
        if not fname.endswith('_Minutes.txt'):
            continue
        fpath = os.path.join(basedir, fname)
        with open(fpath, 'r', errors='ignore') as f:
            content = f.read()
        # Count appearances
        for m in board_members:
            if f'Motion by {m}' in content:
                motion_count[m] += 1
            if f'second by {m}' in content:
                second_count[m] += 1

for m in board_members:
    print(f"{m}: Made {motion_count.get(m,0)} motions, Seconded {second_count.get(m,0)}")
