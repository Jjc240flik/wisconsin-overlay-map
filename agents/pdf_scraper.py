#!/usr/bin/env python3
"""
PDF Scraper using Firecrawl Direct API
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

def scrape_pdf_direct(pdf_url: str, output_name: str):
    print(f"Scraping PDF: {pdf_url}")

    endpoint = "https://api.firecrawl.dev/v1/scrape"
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": pdf_url,
        "formats": ["markdown"],
        "onlyMainContent": True
    }

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=180)
        if response.status_code == 200:
            data = response.json()
            markdown = data.get("data", {}).get("markdown", "")

            os.makedirs("/data/raw/brown/pdfs", exist_ok=True)
            output_path = f"/data/raw/brown/pdfs/{output_name}.md"
            with open(output_path, "w") as f:
                f.write(markdown)

            print(f"Successfully scraped. Saved to {output_path} ({len(markdown)} chars)")
            return True
        else:
            print(f"Failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # CHAP011.pdf
    chap011_url = "https://www.browncountywi.gov/i/f/files/County-Clerk/Ordinances/CHAP011.pdf"
    scrape_pdf_direct(chap011_url, "CHAP011")

    # CHAP022.pdf
    chap022_url = "https://www.browncountywi.gov/i/f/files/County-Clerk/Ordinances/CHAP022.pdf"
    scrape_pdf_direct(chap022_url, "CHAP022")