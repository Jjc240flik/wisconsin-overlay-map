from pathlib import Path

src = Path('/root/wisconsin-overlay-map/docs/County_Growth_Breakdowns')
dst = Path('/root/wisconsin-overlay-map/docs/TOP_COUNTIES')

county_map = {
    'Brown_County.md': 'Brown_County_Future_Growth.md',
    'Calumet_County.md': 'Calumet_County_Future_Growth.md',
    'Dane_County.md': 'Dane_County_Future_Growth.md',
    'Door_County.md': 'Door_County_Future_Growth.md',
    'Milwaukee_County.md': 'Milwaukee_County_Future_Growth.md',
    'Outagamie_County.md': 'Outagamie_County_Future_Growth.md',
    'Ozaukee_County.md': 'Ozaukee_County_Future_Growth.md',
    'Rock_County.md': 'Rock_County_Future_Growth.md',
    'Waukesha_County.md': 'Waukesha_County_Future_Growth.md',
    'Winnebago_County.md': 'Winnebago_County_Future_Growth.md'
}

for top_name, source_name in county_map.items():
    src_path = src / source_name
    dst_path = dst / top_name
    
    if not src_path.exists():
        continue
    
    src_content = src_path.read_text()
    
    # Find and extract just the table section
    lines = src_content.split('\n')
    in_table = False
    table_started = False
    
    for i, line in enumerate(lines):
        if 'Future Growth Expectations by Municipality' in line:
            # Capture from here
            table_lines = []
            for j in range(i, len(lines)):
                tl = lines[j]
                strip_tl = tl.strip()
                
                # Collect header + data rows
                if '| Municipality | Type | Expected Future Growth | Notes |' in tl:
                    table_started = True
                
                if table_started:
                    if tl.startswith('|') or tl.startswith('---') or tl == '':
                        if tl.startswith('|') or tl.startswith('---'):
                            table_lines.append(tl)
                        if tl == '' and len(table_lines) > 3:
                            # Empty line after table - we're done if we haven't seen a non-empty
                            pass
                    else:
                        if len(table_lines) > 3:
                            break
            
            # Now we have the clean table
            clean_table = '\n'.join(table_lines)
            
            # Read the TOP COUNTIES version 
            top_content = dst_path.read_text()
            
            # Replace the table section
            # Find the old table in TOP COUNTIES file
            top_lines = top_content.split('\n')
            new_lines = []
            in_new_table = False
            table_replaced = False
            
            for line in top_lines:
                strip_line = line.strip()
                
                if 'Future Growth Expectations by Municipality' in line:
                    # Keep the header
                    new_lines.append(line)
                    continue
                
                if 'Municipality' in line and 'Type' in line and 'Expected Future Growth' in line:
                    # Replace with clean table
                    new_lines.append(clean_table)
                    table_replaced = True
                    continue
                
                if table_replaced:
                    # Skip old table rows
                    if strip_line.startswith('|') or strip_line.startswith('|---'):
                        continue
                    elif strip_line == '':
                        new_lines.append(line)
                    else:
                        new_lines.append(line)
                        table_replaced = False
                else:
                    new_lines.append(line)
            
            dst_path.write_text('\n'.join(new_lines))
            print(f"{top_name}: Table restored from source")
            break
    
    if not table_started:
        print(f"{top_name}: Could not find table")