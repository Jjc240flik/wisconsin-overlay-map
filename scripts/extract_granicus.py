import re, sys

with open('/tmp/granicus_page.html', 'r', errors='ignore') as f:
    html = f.read()

# Find VILLAGE BOARD tab
vb_pos = html.find('VILLAGE BOARD</div>')
while vb_pos > 0:
    before = html[max(0,vb_pos-100):vb_pos]
    if 'CollapsiblePanelTab' in before:
        break
    vb_pos = html.find('VILLAGE BOARD</div>', vb_pos+1)

print(f"VILLAGE BOARD found at position: {vb_pos}")

if vb_pos >= 0:
    content_start = html.find('<div class="CollapsiblePanelContent"', vb_pos)
    if content_start >= 0:
        depth = 1
        pos = html.find('>', content_start) + 1
        while depth > 0 and pos < len(html):
            if html[pos:pos+4] == '<!--':
                endc = html.find('-->', pos)
                if endc >= 0:
                    pos = endc + 3
                    continue
            if html[pos:pos+6] == '<div ' or html[pos:pos+5] == '<div\t':
                depth += 1
            elif html[pos:pos+6] == '</div>':
                depth -= 1
            if depth > 0:
                pos += 1
        
        content = html[content_start:pos+6]
        print(f"\nContent length: {len(content)} chars")
        
        year_tabs = re.findall(r'class="yearTab[^"]*"[^>]*>(\d{4})<', content)
        print(f"Year tabs: {year_tabs}")
        
        event_ids = re.findall(r'event_id=(\d+)', content)
        print(f"Event IDs: {event_ids[:30]}")
        
        # Extract rows for 2025 and 2026
        for year in ['2025', '2026']:
            print(f"\n=== {year} MEETINGS ===")
            # Find year tab section
            y_pos = content.find(f'class="yearTab"{year}')
            if y_pos < 0:
                y_pos = content.find(f'class="yearTab"', content.find(f'>{year}<'))
            
            # Extract table rows in this section
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', content[y_pos:y_pos+5000] if y_pos >= 0 else '')
            print(f"  Rows found: {len(rows)}")

# Also find PLANNING COMMISSION
pc_pos = html.find('PLANNING COMMISSION</div>')
while pc_pos > 0:
    before = html[max(0,pc_pos-100):pc_pos]
    if 'CollapsiblePanelTab' in before:
        break
    pc_pos = html.find('PLANNING COMMISSION</div>', pc_pos+1)

print(f"\nPLANNING COMMISSION found at position: {pc_pos}")
