#!/usr/bin/env python3
"""
Brown County Local Data Ingestion Script
Parses the existing Research Digest and Land Development Lookup files
to seed the pipeline before any web scraping.
"""

import os
import re
from pathlib import Path

BROWN_DIGEST_PATH = "/root/Hermes Brain/30_Projects/Wisconsin Data Build/Wisconsin Data Build Dashboard/Research Digests/Brown County — Research Digest.md"
BROWN_LOOKUP_PATH = "/root/Hermes Brain/30_Projects/Wisconsin Data Build/Wisconsin Data Build Dashboard/Counties/Brown — Land Development Lookup.md"

def extract_urls_from_markdown(content: str) -> list:
    """Extract all https URLs from markdown content."""
    urls = re.findall(r'https?://[^\s\)\]]+', content)
    return list(set(urls))

def parse_brown_county_digest():
    print("Parsing local Brown County Research Digest...")

    if not os.path.exists(BROWN_DIGEST_PATH):
        print(f"File not found: {BROWN_DIGEST_PATH}")
        return []

    with open(BROWN_DIGEST_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    urls = extract_urls_from_markdown(content)

    print(f"Found {len(urls)} unique URLs in Brown County digest:")
    for url in urls[:15]:  # Show first 15
        print(f"  - {url}")

    # Key sources we care about
    key_sources = [u for u in urls if "browncountywi.gov" in u or "Comp%20Plans" in u or "Future%20Land%20Use" in u]
    print(f"\nKey Brown County official sources identified: {len(key_sources)}")
    return key_sources

def parse_land_development_lookup():
    if not os.path.exists(BROWN_LOOKUP_PATH):
        print("Land Development Lookup not found.")
        return

    with open(BROWN_LOOKUP_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    print("\nBrown — Land Development Lookup file loaded successfully.")
    # Future: parse tables for existing parcel candidates, builder contacts, etc.

if __name__ == "__main__":
    sources = parse_brown_county_digest()
    parse_land_development_lookup()
    print("\nLocal Brown County ingestion complete. Ready to feed Intelligence Analyst.")