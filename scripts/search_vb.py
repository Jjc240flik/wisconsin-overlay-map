import os, glob

base = '/root/wisconsin-overlay-map/data/greenville_pdfs/village_board'

terms = ['Gunderson', 'gunderson', 'Whispering', 'whispering', 'Doug', 'douglas',
         'subdivision', 'rezoning', 'Everglade', 'Mayflower', 'Sub-Area C', 'Sub-Area']

for root, dirs, files in os.walk(base):
    for fname in sorted(files):
        if fname.endswith('_Minutes.txt') or fname.endswith('_Agenda.txt'):
            fpath = os.path.join(root, fname)
            with open(fpath, 'r', errors='ignore') as f:
                content = f.read()
            
            for term in terms:
                if term.lower() in content.lower():
                    # Find context
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if term.lower() in line.lower():
                            ctx = '\n'.join(lines[max(0,i-2):min(len(lines),i+3)])
                            print(f'[{fname}] {term}:')
                            print(f'  {ctx.strip()[:200]}')
                            print()
                            break
                    break  # one hit per file
