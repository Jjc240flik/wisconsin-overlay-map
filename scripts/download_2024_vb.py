import subprocess, os, re, sys
from pathlib import Path

base = '/root/wisconsin-overlay-map/data/greenville_pdfs/2024/VB'

# Additional VB 2024 meetings to download (Aug-Dec, clip_ids 770+)
vb2024 = {
    '2024-10-29_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=767',
    '2024-09-03_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=766',
    '2024-08-12_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=765',
    '2024-07-09_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=735',
    '2024-05-28_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=722',
    '2024-04-09_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=707',
    '2024-03-12_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=698',
    '2024-02-13_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=691',
    '2024-01-17_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=683',
}

# Also try to find 2024 PC clip_ids - check if these are PC or other committees
additional = {
    # clip_ids we found on the page that might be 2024 PC meetings
}

all_pdfs = {**vb2024, **additional}
total = len(all_pdfs)
count = 0

for fname, url in all_pdfs.items():
    fpath = os.path.join(base, fname)
    Path(os.path.dirname(fpath)).mkdir(parents=True, exist_ok=True)
    
    cmd = f'curl -s -L -A "Mozilla/5.0" -o "{fpath}" "{url}"'
    subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
    
    if os.path.exists(fpath) and os.path.getsize(fpath) > 1000:
        txtpath = fpath.replace('.pdf', '.txt')
        subprocess.run(['pdftotext', fpath, txtpath], capture_output=True, timeout=30)
        count += 1
        sys.stdout.write(f'  [{count}/{total}] {fname}\n')
        sys.stdout.flush()

print(f'\nDownloaded: {count}/{total}')
