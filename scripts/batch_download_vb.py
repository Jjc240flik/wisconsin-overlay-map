import subprocess, os, sys
from pathlib import Path

base = '/root/wisconsin-overlay-map/data/greenville_pdfs/village_board'

# VB 2026 meetings
vb2026 = {
    '2026-07-13_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=926',
    '2026-07-13_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=926&doc_id=22f3e32b-7fa4-11f1-94fc-005056a89546',
    '2026-07-08_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=924',
    '2026-07-08_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=924&doc_id=c77931f7-7f99-11f1-94fc-005056a89546',
    '2026-06-29_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=918',
    '2026-06-29_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=918&doc_id=a1649077-7487-11f1-9494-005056a89546',
    '2026-06-08_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=914',
    '2026-06-08_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=914&doc_id=d62f37a0-65d7-11f1-9494-005056a89546',
    '2026-05-22_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=911',
    '2026-05-22_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=911&doc_id=7ad65b18-55f2-11f1-9b4d-005056a89546',
    '2026-05-20_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=910',
    '2026-05-20_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=910&doc_id=eaca0853-59cc-11f1-9b4d-005056a89546',
    '2026-05-18_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=907',
    '2026-05-18_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=907&doc_id=a698a951-5389-11f1-9b4d-005056a89546',
    '2026-05-11_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=906',
    '2026-05-11_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=906&doc_id=d087d6e3-4ee2-11f1-9b4d-005056a89546',
    '2026-05-04_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=904',
    '2026-05-04_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=904&doc_id=3871a8c0-48ad-11f1-9b4d-005056a89546',
    '2026-04-21_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=902',
    '2026-04-21_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=902&doc_id=559575be-47c8-11f1-9b4d-005056a89546',
    '2026-04-13_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=898',
    '2026-04-13_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=898&doc_id=75ad1aaa-3a70-11f1-bb28-005056a89546',
}

# VB 2025 meetings (from screenshots)
vb2025 = {
    '2025-12-15_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=878',
    '2025-12-15_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=878&doc_id=d221466c-df48-11f0-bb28-005056a89546',
    '2025-12-08_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=876',
    '2025-12-08_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=876&doc_id=e9be1fe2-df48-11f0-bb28-005056a89546',
    '2025-11-17_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=873',
    '2025-11-17_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=873&doc_id=22282a9b-c483-11f0-a7da-005056a89546',
    '2025-11-10_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=872',
    '2025-11-10_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=872&doc_id=10213d4d-c0d5-11f0-a7da-005056a89546',
    '2025-11-04_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=869',
    '2025-11-04_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=869&doc_id=69b2d99b-ba60-11f0-a7da-005056a89546',
    '2025-10-21_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=866',
    '2025-10-21_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=866&doc_id=b4b8f69f-af5f-11f0-8df7-005056a89546',
    '2025-10-13_VB_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=853',
    '2025-10-13_VB_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=853&doc_id=892ac220-a9fe-11f0-8df7-005056a89546',
}

all_pdfs = {**vb2026, **vb2025}
total = len(all_pdfs)
count = 0

for fname, url in all_pdfs.items():
    year = '2026' if '2026-' in fname else '2025'
    fpath = os.path.join(base, year, fname)
    Path(os.path.dirname(fpath)).mkdir(parents=True, exist_ok=True)
    
    cmd = f'curl -s -L -A "Mozilla/5.0" -o "{fpath}" "{url}"'
    r = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
    
    if os.path.exists(fpath) and os.path.getsize(fpath) > 1000:
        txtpath = fpath.replace('.pdf', '.txt')
        subprocess.run(['pdftotext', fpath, txtpath], capture_output=True, timeout=30)
        count += 1
        sys.stdout.write(f'  [{count}/{total}] {fname}\n')
        sys.stdout.flush()
    else:
        sys.stdout.write(f'  [FAIL] {fname}\n')
        sys.stdout.flush()

print(f'\nDownloaded: {count}/{total}')
