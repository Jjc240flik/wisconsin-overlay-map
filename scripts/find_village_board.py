import re

with open('/tmp/granicus_page.html', 'r', errors='ignore') as f:
    html = f.read()

# Find data around the VILLAGE BOARD collapsible panel
# Look for the panel content divs that might have archive data loaded
# Search for patterns like event_id that appear near VILLAGE BOARD

# First find VILLAGE BOARD section
vb_sections = list(re.finditer(r'VILLAGE BOARD', html))
print(f"Found VILLAGE BOARD {len(vb_sections)} times")

# For each occurrence, show what's around it
for i, m in enumerate(vb_sections):
    start = max(0, m.start() - 200)
    end = min(len(html), m.end() + 500)
    section = html[start:end]
    print(f"\n=== Occurrence {i+1} at position {m.start()} ===")
    # Extract event IDs in this section
    events = re.findall(r'event_id=(\d+)', section)
    print(f"  Event IDs: {events}")
    # Extract dates
    dates = re.findall(r'(\d{4}-\d{2}-\d{2})', section)
    print(f"  Dates: {dates}")
    # Extract meeting names
    names = re.findall(r'listItem[^>]*headers="Name[^"]*"[^>]*>([^<]+)', section)
    print(f"  Names: {[n.strip() for n in names]}")
