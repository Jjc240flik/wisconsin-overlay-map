#!/usr/bin/env python3
"""
Direct PDF Downloader + Extractor for Brown County Ordinances
Bypasses anti-bot protection on the county site.
Uses requests + pdfplumber (local, zero cost, reliable for direct PDF links).
"""

import os
import requests
from pathlib import Path
import pdfplumber

# Project-relative paths
RAW_DIR = Path("data/raw/brown/pdfs")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# The 4 Brown County ordinance PDFs (direct links)
ORDINANCES = [
    {
        "name": "CHAP011",
        "url": "https://www.browncountywi.gov/i/f/files/County-Clerk/Ordinances/CHAP011.pdf",
        "description": "Zoning Ordinance (Chapter 11)"
    },
    {
        "name": "CHAP014",
        "url": "https://www.browncountywi.gov/i/f/files/County-Clerk/Ordinances/CHAP014-UPDATED%209-5-07.pdf",
        "description": "Non-Metallic Mining Reclamation"
    },
    {
        "name": "CHAP022",
        "url": "https://www.browncountywi.gov/i/f/files/County-Clerk/Ordinances/CHAP022.pdf",
        "description": "Zoning Ordinance (Chapter 22)"
    },
    {
        "name": "Ch23_Floodplains",
        "url": "https://www.browncountywi.gov/i/f/files/County-Clerk/Ordinances/NEW%20Ch%2023%20Floodplains%20-%20redlined%20removed%20-%20dph%20-%2002-16-2023.pdf",
        "description": "Floodplain Zoning (Chapter 23)"
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/pdf,application/octet-stream,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.browncountywi.gov/",
}

def download_and_extract(ordinance: dict) -> bool:
    name = ordinance["name"]
    url = ordinance["url"]
    output_path = RAW_DIR / f"{name}.md"

    print(f"Downloading {name}: {url}")

    try:
        # Direct download (bypasses browser anti-bot)
        response = requests.get(url, headers=HEADERS, timeout=120, stream=True)
        response.raise_for_status()

        # Save temp PDF
        temp_pdf = RAW_DIR / f"{name}_temp.pdf"
        with open(temp_pdf, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"  Downloaded {temp_pdf.stat().st_size} bytes")

        # Extract text with pdfplumber
        text_content = []
        with pdfplumber.open(temp_pdf) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    text_content.append(f"--- Page {i+1} ---\n{text}")

        full_text = "\n\n".join(text_content)

        if len(full_text) < 100:
            print(f"  ✗ Extracted text too short ({len(full_text)} chars)")
            temp_pdf.unlink(missing_ok=True)
            return False

        # Save as Markdown
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# {name} - {ordinance['description']}\n\n")
            f.write(f"Source: {url}\n\n")
            f.write(full_text)

        print(f"  ✓ Saved {len(full_text)} chars to {output_path}")

        # Cleanup temp
        temp_pdf.unlink(missing_ok=True)
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    print("=== Brown County Ordinance PDF Scraper (Direct Download + pdfplumber) ===\n")
    print(f"Output directory: {RAW_DIR.absolute()}\n")

    results = []
    for ordinance in ORDINANCES:
        success = download_and_extract(ordinance)
        results.append((ordinance["name"], success))

    print("\n=== Summary ===")
    for name, success in results:
        status = "SUCCESS" if success else "FAILED"
        print(f"  {name}: {status}")

    successful = sum(1 for _, s in results if s)
    print(f"\nCompleted: {successful}/{len(ORDINANCES)} ordinances scraped.")

if __name__ == "__main__":
    main()