import subprocess, os, glob, json
from collections import defaultdict

base = '/root/wisconsin-overlay-map/data/greenville_pdfs/plan_commission'

search_terms = [
    'Gunderson', 'Whispering Winds', 'gunderson', 'whispering',
    'Everglade', 'everglade',
    'Mayflower', 'mayflower',
    'Skiba', 'skiba',
    'Sub-Area Plan C', 'Sub-Area', 'sub-area', 'Sub Area',
    'lift station', 'Lift Station', 'sewer',
    'rezoning', 'Rezoning',
    'concept plan', 'Concept Plan',
    'Greenville Drive',
    'School Road',
    'Hillview Road',
    'Douglas', 'douglas',
    'Lenz',
    'Barbara', 'Estler', 'estler',
    'acre', 'lot size', 'density',
]

results = {term: [] for term in search_terms}

# Search all txt files
for root, dirs, files in os.walk(base):
    for fname in files:
        if fname.endswith('.txt'):
            fpath = os.path.join(root, fname)
            with open(fpath, 'r', errors='ignore') as f:
                content = f.read()
            
            for term in search_terms:
                if term.lower() in content.lower():
                    # Find context
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if term.lower() in line.lower():
                            ctx_before = max(0, i-1)
                            ctx_after = min(len(lines), i+2)
                            context = '\n'.join(lines[ctx_before:ctx_after])
                            results[term].append({
                                'file': fname,
                                'line': i+1,
                                'context': context.strip()
                            })
                            break  # one hit per file per term

# Print summary
print("=== SEARCH RESULTS ===\n")
for term, hits in results.items():
    if hits:
        print(f"\n--- {term} ({len(hits)} files) ---")
        for h in hits[:5]:
            print(f"  [{h['file']}] {h['context'][:200]}")
            print()

# Also collect all meeting attendees
attendees = defaultdict(int)
for root, dirs, files in os.walk(base):
    for fname in files:
        if fname.endswith('_Minutes.txt'):
            fpath = os.path.join(root, fname)
            with open(fpath, 'r', errors='ignore') as f:
                content = f.read()
            # Look for PRESENT: line
            for line in content.split('\n'):
                if 'PRESENT:' in line or 'PRESENT' in line:
                    # Extract names
                    names = line.replace('PRESENT:', '').replace('PRESENT', '').strip()
                    for name in names.split(','):
                        name = name.strip()
                        if name and len(name) > 3:
                            attendees[name] += 1

print("\n=== PLANNING COMMISSION MEMBERS ===")
for name, count in sorted(attendees.items(), key=lambda x: -x[1]):
    if count >= 3:  # Only regular attendees
        print(f"  {name}: attended {count} meetings")
