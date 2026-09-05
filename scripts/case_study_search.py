import os, glob, re
from collections import defaultdict

base_pc = '/root/wisconsin-overlay-map/data/greenville_pdfs/plan_commission'
base_vb = '/root/wisconsin-overlay-map/data/greenville_pdfs/village_board'

# Search terms for development projects
projects = {
    'Savannah Heights': ['Savannah Heights', 'Savannah'],
    'Encore Subdivision': ['Encore'],
    'Whispering Winds': ['Whispering Winds', 'Whispering'],
    'Harvest Ridge': ['Harvest Ridge'],
    'New Creations': ['New Creations'],
    'School Road / Julius Drive': ['School Road', 'Julius Drive', 'Julius Dr'],
    'Hillview Road': ['Hillview Road'],
    'Skiba': ['Skiba'],
    'Ebbens': ['Ebbens'],
    'Data Centers': ['Data Center', 'Moratorium'],
    'Zoning Text Amendment': ['Zoning Text Amend', 'Chapter 320'],
    'Sub-Area C Final': ['Sub-Area C'],
    'Sub-Area G': ['Sub-Area G'],
    'Airport Rezone': ['Airport', 'AGD to AIR'],
    'Comprehensive Plan': ['Comp Plan', 'Comprehensive Plan'],
    'TIF District': ['TIF', 'Tax Increment'],
}

print("=== GREENVILLE DEVELOPMENT PROPOSALS - FULL CASE STUDY ===\n")

for root, dirs, files in os.walk(base_pc):
    for fname in sorted(files):
        if fname.endswith('_Minutes.txt'):
            fpath = os.path.join(root, fname)
            with open(fpath, 'r', errors='ignore') as f:
                content = f.read()
            
            for proj_name, terms in projects.items():
                for term in terms:
                    if term.lower() in content.lower():
                        # Find the relevant section
                        lines = content.split('\n')
                        hits = []
                        for i, line in enumerate(lines):
                            if term.lower() in line.lower():
                                start = max(0, i-3)
                                end = min(len(lines), i+6)
                                hits.append('\n'.join(lines[start:end]))
                        
                        body = 'PC'
                        year = fname.split('_')[0] if '_' in fname else 'unknown'
                        
                        print(f"\n{'='*80}")
                        print(f"[{body}][{year}] {proj_name}")
                        print(f"{'='*80}")
                        for h in hits[:5]:
                            print(f"  {h[:250]}")
                            print()
                        break  # one hit per project per file

for root, dirs, files in os.walk(base_vb):
    for fname in sorted(files):
        if fname.endswith('_Minutes.txt'):
            fpath = os.path.join(root, fname)
            with open(fpath, 'r', errors='ignore') as f:
                content = f.read()
            
            for proj_name, terms in projects.items():
                for term in terms:
                    if term.lower() in content.lower():
                        lines = content.split('\n')
                        hits = []
                        for i, line in enumerate(lines):
                            if term.lower() in line.lower():
                                start = max(0, i-3)
                                end = min(len(lines), i+6)
                                hits.append('\n'.join(lines[start:end]))
                        
                        body = 'VB'
                        year = fname.split('_')[0] if '_' in fname else 'unknown'
                        
                        print(f"\n{'='*80}")
                        print(f"[{body}][{year}] {proj_name}")
                        print(f"{'='*80}")
                        for h in hits[:5]:
                            print(f"  {h[:250]}")
                            print()
                        break
