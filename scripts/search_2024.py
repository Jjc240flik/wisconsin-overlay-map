import os, re

base = '/root/wisconsin-overlay-map/data/greenville_pdfs/2024'

search_terms = ['Essler', 'essler', 'Barbara', 'barbara', 'Nine Twenty', 'nine twenty', 
                'Estler', 'estler', '920 Realty', 'Mayflower', 'mayflower',
                'Concept Plan', 'concept plan', 'subdivision', 'rezoning',
                'Lot', 'lot', 'AGD', '11-1-0412', '11-1-0410',
                '111041200', '111041000']

for root, dirs, files in os.walk(base):
    for fname in sorted(files):
        if fname.endswith('.txt'):
            fpath = os.path.join(root, fname)
            with open(fpath, 'r', errors='ignore') as f:
                content = f.read()
            
            for term in search_terms:
                if term.lower() in content.lower():
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if term.lower() in line.lower():
                            ctx = '\n'.join(lines[max(0,i-2):min(len(lines),i+3)])
                            print(f'[{fname}] {term}:')
                            print(f'  {ctx.strip()[:200]}')
                            print()
                            break
                    break
