#!/usr/bin/env python3
"""
Extract Zoning Code Keys from all Brown County Ordinance PDFs using Crawl4AI-generated Markdown.
Generates consolidated zoning_keys_from_ordinances.md table.
Integrates with existing land-use and master zoning keys.
"""

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "brown" / "pdfs"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "brown"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# All 4 ordinance files (nice names)
ORDINANCE_FILES = [
    {"name": "CHAP011", "file": "CHAP011.md", "chapter": "CHAP011"},
    {"name": "CHAP014", "file": "CHAP014.md", "chapter": "CHAP014"},
    {"name": "CHAP022", "file": "CHAP022.md", "chapter": "CHAP022"},
    {"name": "Ch23_Floodplains", "file": "Ch23_Floodplains.md", "chapter": "Ch23_Floodplains"},
]

# Enhanced regex patterns for zoning districts and terms
ZONING_PATTERNS = [
    r'\b(AG|RR|RS|RM|R-|B-|C-|I-|PUD|FP|SW|MH|EX|PD|PRD)[-\dA-Z]*\b',
    r'\b(Agricultural|Residential|Business|Commercial|Industrial|Planned Unit|Floodplain|Shoreland|Conservation)[-\s]*(District|Zone|Zoning)?\b',
    r'\b(AG-\d+|RR-\d+|RS-\d+|RM-\d+|B-\d+|C-\d+|I-\d+)\b',
]

def extract_zoning_from_file(filepath: Path) -> list[dict]:
    """Extract zoning-related terms with context from a Markdown ordinance file."""
    if not filepath.exists():
        print(f"  WARNING: {filepath} not found")
        return []

    content = filepath.read_text(encoding="utf-8", errors="ignore")

    entries = []
    seen = set()

    for pattern in ZONING_PATTERNS:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            term = match.group(0).strip()
            if len(term) < 3 or term.upper() in seen:
                continue
            seen.add(term.upper())

            # Grab surrounding context (up to 200 chars before/after) for description/regulation hints
            start = max(0, match.start() - 150)
            end = min(len(content), match.end() + 150)
            context = content[start:end].replace('\n', ' ').strip()

            # Simple heuristic for description/regulation
            desc = ""
            if "district" in context.lower() or "zone" in context.lower():
                desc = context[:300]

            entries.append({
                "term": term,
                "chapter": filepath.stem,
                "context": context[:500],
                "description": desc[:400] if desc else "See full ordinance text"
            })

    return entries

def generate_consolidated_table():
    print("=== Extracting Zoning Code Keys from Brown County Ordinances ===\n")

    all_entries = []
    for ord_info in ORDINANCE_FILES:
        filepath = RAW_DIR / ord_info["file"]
        print(f"Processing {ord_info['name']}...")
        entries = extract_zoning_from_file(filepath)
        all_entries.extend(entries)
        print(f"  Found {len(entries)} zoning references")

    # Deduplicate by term (keep first occurrence with source)
    unique = {}
    for e in all_entries:
        key = e["term"].upper()
        if key not in unique:
            unique[key] = e

    sorted_terms = sorted(unique.values(), key=lambda x: (x["chapter"], x["term"]))

    # Build Markdown table
    table = "# Brown County Zoning Code Keys (from Ordinances)\n\n"
    table += f"**Source:** {len(ORDINANCE_FILES)} ordinance PDFs (Crawl4AI scraped Markdown)\n"
    table += f"**Total unique terms extracted:** {len(sorted_terms)}\n\n"
    table += "| Zoning Code / Term | Source Chapter | Description / Regulations | Context Snippet |\n"
    table += "|--------------------|----------------|---------------------------|-----------------|\n"

    for e in sorted_terms:
        term = e["term"].replace("|", "\\|")
        chapter = e["chapter"]
        desc = e.get("description", "See ordinance")[:200].replace("|", "\\|").replace("\n", " ")
        context = e["context"][:150].replace("|", "\\|").replace("\n", " ")
        table += f"| {term} | {chapter} | {desc} | {context} |\n"

    # Write the consolidated file
    output_path = PROCESSED_DIR / "zoning_keys_from_ordinances.md"
    output_path.write_text(table, encoding="utf-8")
    print(f"\n✓ Consolidated table saved to {output_path}")
    print(f"  Total unique zoning terms: {len(sorted_terms)}")

    # Also update the master zoning_code_keys.md by appending new terms (simple merge)
    master_path = PROCESSED_DIR / "zoning_code_keys.md"
    if master_path.exists():
        existing = master_path.read_text(encoding="utf-8")
        new_section = f"\n\n## Merged from Ordinances ({len(sorted_terms)} new terms)\n\n"
        new_section += "| Term | Chapter | Notes |\n|------|---------|-------|\n"
        for e in sorted_terms[:50]:  # Limit to avoid bloat
            new_section += f"| {e['term']} | {e['chapter']} | Extracted from ordinance |\n"
        master_path.write_text(existing + new_section, encoding="utf-8")
        print(f"✓ Merged into {master_path}")

    return output_path

if __name__ == "__main__":
    generate_consolidated_table()