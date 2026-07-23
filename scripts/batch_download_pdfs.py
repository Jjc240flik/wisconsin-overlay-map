import subprocess, os, sys, re, json
from pathlib import Path

base = '/root/wisconsin-overlay-map/data/greenville_pdfs'
headers = ['User-Agent: Mozilla/5.0']

pdfs = {
    'plan_commission/2026/agenda': {
        '2026-01-12_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=880',
        '2026-02-09_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=884',
        '2026-03-09_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=890',
        '2026-04-13_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=897',
        '2026-04-27_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=903',
        '2026-05-18_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=908',
        '2026-06-22_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=917',
    },
    'plan_commission/2026/minutes': {
        '2026-01-12_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=880&doc_id=ceda54c7-f179-11f0-bb28-005056a89546',
        '2026-02-09_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=884&doc_id=176d9b92-069f-11f1-bb28-005056a89546',
        '2026-03-09_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=890&doc_id=c06eb96e-2223-11f1-bb28-005056a89546',
        '2026-04-13_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=897&doc_id=2ad1276b-3998-11f1-bb28-005056a89546',
        '2026-04-27_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=903&doc_id=543bb30f-4498-11f1-bb28-005056a89546',
        '2026-05-18_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=908&doc_id=8b6b74e3-5463-11f1-9b4d-005056a89546',
        '2026-06-22_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=917&doc_id=7b4336f1-7000-11f1-9494-005056a89546',
    },
    'plan_commission/2025/agenda': {
        '2025-01-08_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=778',
        '2025-02-10_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=797',
        '2025-02-24_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=799',
        '2025-03-10_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=802',
        '2025-03-24_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=809',
        '2025-04-14_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=811',
        '2025-04-28_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=818',
        '2025-05-12_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=821',
        '2025-05-19_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=823',
        '2025-06-23_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=830',
        '2025-07-14_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=835',
        '2025-07-28_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=839',
        '2025-08-11_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=841',
        '2025-09-08_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=844',
        '2025-10-13_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=852',
        '2025-11-10_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=871',
        '2025-12-08_PC_Agenda.pdf': 'https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=875',
    },
    'plan_commission/2025/minutes': {
        '2025-01-08_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=778&doc_id=1d3a77ce-cecf-11ef-a9e2-005056a89546',
        '2025-02-10_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=797&doc_id=76792185-ea51-11ef-a9e2-005056a89546',
        '2025-02-24_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=799&doc_id=e9b11be1-f397-11ef-ab6a-005056a89546',
        '2025-03-10_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=802&doc_id=a0d77d02-fe94-11ef-ab6a-005056a89546',
        '2025-03-24_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=809&doc_id=f0c2412e-0a4e-11f0-ab6a-005056a89546',
        '2025-04-14_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=811&doc_id=a6d3c687-1a33-11f0-955d-005056a89546',
        '2025-04-28_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=818&doc_id=363a882b-251b-11f0-9f54-005056a89546',
        '2025-05-19_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=823&doc_id=c6d9d1a3-359f-11f0-856f-005056a89546',
        '2025-06-23_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=830&doc_id=7ded0aa3-536d-11f0-b7f5-005056a89546',
        '2025-07-14_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=835&doc_id=089a4f66-6242-11f0-b7f5-005056a89546',
        '2025-07-28_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=839&doc_id=0e48ff69-6ef0-11f0-a766-005056a89546',
        '2025-08-11_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=841&doc_id=d3c26fb5-77a3-11f0-a766-005056a89546',
        '2025-09-08_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=844&doc_id=77d0f7f0-926c-11f0-8df7-005056a89546',
        '2025-10-13_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=852&doc_id=22607a08-a9e3-11f0-8df7-005056a89546',
        '2025-11-10_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=871&doc_id=c2aa2620-c008-11f0-a7da-005056a89546',
        '2025-12-08_PC_Minutes.pdf': 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=875&doc_id=fe739c72-df46-11f0-bb28-005056a89546',
    }
}

total = sum(len(v) for v in pdfs.values())
count = 0
failures = []

for folder, files in pdfs.items():
    for fname, url in files.items():
        fpath = os.path.join(base, folder, fname)
        Path(os.path.dirname(fpath)).mkdir(parents=True, exist_ok=True)
        
        cmd = f'curl -s -L -A "Mozilla/5.0" -o "{fpath}" "{url}"'
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
        
        if os.path.exists(fpath) and os.path.getsize(fpath) > 1000:
            # Extract text
            txtpath = fpath.replace('.pdf', '.txt')
            subprocess.run(['pdftotext', fpath, txtpath], capture_output=True, timeout=30)
            count += 1
            sys.stdout.write(f'  [{count}/{total}] {fname}\n')
            sys.stdout.flush()
        else:
            failures.append(fname)
            sys.stdout.write(f'  [FAIL] {fname}\n')
            sys.stdout.flush()

print(f'\nDownloaded: {count}/{total}')
if failures:
    print(f'Failed: {len(failures)}: {failures}')
