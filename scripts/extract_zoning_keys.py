#!/usr/bin/env python3
"""
Extract Zoning Code Keys from the scraped Land Use Chapter
"""

import os
import re

def extract_zoning_table(markdown_path: str, output_path: str):
    if not os.path.exists(markdown_path):
        print(f"File not found: {markdown_path}")
        return

    with open(markdown_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Look for common zoning table patterns
    # This is a simple heuristic - in production we'd use LLM or better parsing
    lines = content.split("\n")
    zoning_lines = []

    for line in lines:
        # Look for lines that look like zoning codes (e.g. AG-1, RR-1, etc.)
        if re.search(r'\b(AG|RR|RS|RM|R-|B-|C-|I-)[-\dA-Z]+\b', line, re.IGNORECASE):
            zoning_lines.append(line.strip())

    # Create a simple markdown table
    table = "# Brown County Zoning Code Keys (from Land Use Chapter)\n\n"
    table += "| Zoning Code | Description / Notes |\n"
    table += "|-------------|---------------------|\n"

    for line in zoning_lines[:30]:  # Limit to first 30 matches
        table += f"| {line} | (extracted) |\n"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(table)

    print(f"Zoning Code Keys extracted and saved to: {output_path}")
    print(f"Found {len(zoning_lines)} potential zoning references.")

if __name__ == "__main__":
    extract_zoning_table(
        "/root/wisconsin-overlay-map/data/processed/brown/land_use_chapter_direct.md",
        "/root/wisconsin-overlay-map/data/processed/brown/zoning_keys_from_land_use.md"
    )