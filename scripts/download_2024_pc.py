import subprocess, os, sys, re
from pathlib import Path

base = '/root/wisconsin-overlay-map/data/greenville_pdfs/2024'

# 2024 Plan Commission meetings (from subagent)
pc_2024 = {
    '2024-01-10_PC_Agenda.pdf': ('https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=680', 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=680&doc_id=979d7d7b-b0ac-11ee-bb82-0050569183fa'),
    '2024-02-07_PC_Agenda.pdf': ('https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=689', 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=689&doc_id=07f92cd3-f8d6-11ee-b231-0050569183fa'),
    '2024-03-13_PC_Agenda.pdf': ('https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=700', 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=700&doc_id=b29af73a-e234-11ee-98bb-0050569183fa'),
    '2024-04-10_PC_Agenda.pdf': ('https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=709', 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=709&doc_id=04ecd08f-fb47-11ee-b231-0050569183fa'),
    '2024-05-08_PC_Agenda.pdf': ('https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=718', 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=718&doc_id=41048a03-0e2d-11ef-b231-0050569183fa'),
    '2024-06-12_PC_Agenda.pdf': ('https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=726', 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=726&doc_id=ab6b8f0a-2d72-11ef-81ef-005056a89546'),
    '2024-07-10_PC_Agenda.pdf': ('https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=736', 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=736&doc_id=4d29c9c8-4515-11ef-8c72-005056a89546'),
    '2024-08-14_PC_Agenda.pdf': ('https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=742', 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=742&doc_id=7589ad45-7c3b-11ef-9b71-005056a89546'),
    '2024-10-09_PC_Agenda.pdf': ('https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=754', 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=754&doc_id=d6f99d4f-8748-11ef-ab4b-005056a89546'),
    '2024-11-13_PC_Agenda.pdf': ('https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=763', 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=763&doc_id=b1373343-a2a9-11ef-ab4b-005056a89546'),
    '2024-12-11_PC_Agenda.pdf': ('https://greenvillewi.granicus.com/AgendaViewer.php?view_id=1&clip_id=772', 'https://greenvillewi.granicus.com/MinutesViewer.php?view_id=1&clip_id=772&doc_id=4d8663ae-b8c3-11ef-ab4b-005056a89546'),
}

total = 0
for fname, (agenda_url, minutes_url) in pc_2024.items():
    date = fname[:10]
    # Download Agenda
    apath = os.path.join(base, 'plan_commission', date + '_PC_Agenda.pdf')
    Path(os.path.dirname(apath)).mkdir(parents=True, exist_ok=True)
    cmd = f'curl -s -L -A "Mozilla/5.0" -o "{apath}" "{agenda_url}"'
    subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
    if os.path.exists(apath) and os.path.getsize(apath) > 1000:
        subprocess.run(['pdftotext', apath, apath.replace('.pdf','.txt')], capture_output=True, timeout=30)
        total += 1
        sys.stdout.write(f'  [{total}/22] {date}_PC_Agenda.pdf\n')
        sys.stdout.flush()
    
    # Download Minutes
    mpath = os.path.join(base, 'plan_commission', date + '_PC_Minutes.pdf')
    cmd = f'curl -s -L -A "Mozilla/5.0" -o "{mpath}" "{minutes_url}"'
    subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
    if os.path.exists(mpath) and os.path.getsize(mpath) > 1000:
        subprocess.run(['pdftotext', mpath, mpath.replace('.pdf','.txt')], capture_output=True, timeout=30)
        total += 1
        sys.stdout.write(f'  [{total}/22] {date}_PC_Minutes.pdf\n')
        sys.stdout.flush()

print(f'\nDownloaded: {total}/22 PC PDFs')
