#!/usr/bin/env python3
"""
Light Data Harvester - Extracts links and metadata from Brown County sources
"""

import os
import re
from pathlib import Path

def extract_urls_from_file(filepath: str) -> list:
    """Extract all https URLs from a markdown/text file."""
    if not os.path.exists(filepath):
        return []
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    urls = re.findall(r'https?://[^\s\)\]]+', content)
    return sorted(set(urls))

def run_light_harvest():
    print("=== Light Data Harvester for Brown County ===\n")
    
    sources_file = "/root/wisconsin-overlay-map/data/processed/brown/brown_county_sources.md"
    
    if not os.path.exists(sources_file):
        print("Sources file not found. Running Intelligence Analyst first...")
        return
    
    urls = extract_urls_from_file(sources_file)
    
    print(f"Found {len(urls)} unique URLs from Brown County sources:\n")
    
    key_urls = [u for u in urls if "browncountywi.gov" in u]
    
    print("Key Brown County Official Sources:")
    for url in key_urls[:10]:
        print(f"  - {url}")
    
    # Save extracted links
    os.makedirs("/data/raw/brown", exist_ok=True)
    with open("/data/raw/brown/extracted_urls.txt", "w") as f:
        for url in urls:
            f.write(url + "\n")
    
    print(f"\nExtracted URLs saved to /data/raw/brown/extracted_urls.txt")
    print("Light harvest complete.")

if __name__ == "__main__":
    run_light_harvest()