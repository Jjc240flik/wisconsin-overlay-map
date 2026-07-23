import subprocess, os, re, sys
from pathlib import Path

base = '/root/wisconsin-overlay-map/data/greenville_pdfs/2024'

# Clip IDs from the Granicus page that are likely 2024 meetings
# 2024 VB and PC clip_ids based on pattern analysis (2025 starts at ~778)
clip_ids = {
    # Village Board 2024 meetings (from vision: Oct-Dec 2024)
    'VB': [683, 691, 698, 707, 722, 735, 765, 766, 767],
    # Plan Commission 2024 meetings - we need to discover these
}

total = 0
for body, ids in clip_ids.items():
    for cid in ids:
        for doc_type in ['Agenda', 'Minutes']:
            if doc_type == 'Agenda':
                url = f'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id={cid}'
                fname = f'{body}_clip{cid}_Agenda.pdf'
            else:
                # Minutes need doc_id - we don't have these for 2024
                continue
            
            fpath = os.path.join(base, body, fname)
            Path(os.path.dirname(fpath)).mkdir(parents=True, exist_ok=True)
            
            cmd = f'curl -s -L -A "Mozilla/5.0" -o "{fpath}" "{url}"'
            subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
            
            if os.path.exists(fpath) and os.path.getsize(fpath) > 1000:
                txtpath = fpath.replace('.pdf', '.txt')
                subprocess.run(['pdftotext', fpath, txtpath], capture_output=True, timeout=30)
                total += 1
                # Extract date from text
                with open(txtpath, 'r', errors='ignore') as f:
                    text = f.read()
                # Look for date pattern
                dates = re.findall(r'(\w+ \d{1,2}, 202\d)', text)
                if dates:
                    print(f'  clip_id={cid} {doc_type}: {dates[0]}')
                else:
                    print(f'  clip_id={cid} {doc_type}: (no date found, {len(text)} chars)')
                sys.stdout.flush()

print(f'\nDownloaded: {total} files')
