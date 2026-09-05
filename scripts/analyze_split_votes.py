import os, re

basedirs = {
    '2025': '/root/wisconsin-overlay-map/data/greenville_pdfs/village_board/2025',
    '2026': '/root/wisconsin-overlay-map/data/greenville_pdfs/village_board/2026',
}

print("=== SPLIT VOTES IN VILLAGE BOARD — 2025-2026 ===\n")

for year, basedir in basedirs.items():
    if not os.path.exists(basedir):
        continue
    for fname in sorted(os.listdir(basedir)):
        if not fname.endswith('_Minutes.txt'):
            continue
        fpath = os.path.join(basedir, fname)
        date = fname[:10]
        with open(fpath, 'r', errors='ignore') as f:
            content = f.read()
        
        # Find lines with non-unanimous votes
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Look for motions carried with split results
            if 'Motion carried' in line and (' - ' in line or '/' in line.split('Motion carried')[1][:10]):
                result = line.split('Motion carried')[1].strip()
                # Check if it's truly a split (not unanimous)
                parts = result.split(' - ')
                if len(parts) == 2:
                    yes = parts[0].strip()
                    no = parts[1].strip()
                    if no != '0':
                        # Get the motion context
                        ctx_start = max(0, i-8)
                        ctx = '\n'.join(lines[ctx_start:i+1])
                        print(f"\n[{date}] SPLIT VOTE: {yes} - {no}")
                        print(f"  {ctx[:300]}")
                        print()

# Now search for the specific airport vote more carefully
print("\n=== AIRPORT SSA VOTES ===")
for year, basedir in basedirs.items():
    if not os.path.exists(basedir):
        continue
    for fname in sorted(os.listdir(basedir)):
        if not fname.endswith('_Minutes.txt'):
            continue
        fpath = os.path.join(basedir, fname)
        with open(fpath, 'r', errors='ignore') as f:
            content = f.read()
        if 'Airport' in content and 'sewer' in content.lower():
            print(f"\n[{fname[:10]}] Airport/SSA content:")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if ('Airport' in line or 'sewer service' in line.lower()) and ('Motion' in line or 'carried' in line or 'deny' in line or 'approve' in line):
                    ctx = '\n'.join(lines[max(0,i-3):min(len(lines),i+3)])
                    print(f"  {ctx.strip()[:300]}")
                    print()

# Also check the Dec 15 reconsideration
print("\n=== DEC 15, 2025 AIRPORT RECONSIDERATION ===")
for year, basedir in basedirs.items():
    if not os.path.exists(basedir):
        continue
    for fname in sorted(os.listdir(basedir)):
        if not fname.endswith('_Minutes.txt'):
            continue
        fpath = os.path.join(basedir, fname)
        with open(fpath, 'r', errors='ignore') as f:
            content = f.read()
        if 'reconsider' in content.lower() and ('Airport' in content):
            print(f"\n[{fname[:10]}] Reconsideration:")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'reconsider' in line.lower() or ('Motion carried' in line and 'Airport' in '\n'.join(lines[max(0,i-5):i])):
                    ctx = '\n'.join(lines[max(0,i-3):min(len(lines),i+3)])
                    print(f"  {ctx.strip()[:300]}")
                    print()
