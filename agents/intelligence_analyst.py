#!/usr/bin/env python3
"""
Intelligence Analyst Agent - Direct Firecrawl API (no SDK)
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

BROWN_LAND_USE_URL = "https://www.browncountywi.gov/i/f/files/Planning-and-Land-Services/BC%20Comp%20Plans/Land%20Use%20Chapter.pdf"

def scrape_with_firecrawl_direct(url: str, timeout: int = 120):
    """Call Firecrawl API directly using requests."""
    endpoint = "https://api.firecrawl.dev/v1/scrape"

    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True
    }

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "markdown": data.get("data", {}).get("markdown", "")[:10000]
            }
        else:
            return {
                "status": "failed",
                "error": f"HTTP {response.status_code}: {response.text}"
            }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

def process_brown_land_use():
    print("Calling Firecrawl API directly on Brown County Land Use Chapter...")
    result = scrape_with_firecrawl_direct(BROWN_LAND_USE_URL)

    if result["status"] == "success":
        print("Successfully retrieved content via direct API.")
        os.makedirs("data/processed/brown", exist_ok=True)
        with open("data/processed/brown/land_use_chapter_direct.md", "w") as f:
            f.write(result["markdown"])
        print("Saved to data/processed/brown/land_use_chapter_direct.md")
    else:
        print(f"Failed: {result.get('error')}")

if __name__ == "__main__":
    process_brown_land_use()