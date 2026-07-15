#!/usr/bin/env python3
"""
Zoning Page Scraper (Reusable for Brown County Pilot)
"""

import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

ZONING_PAGE_URL = "https://www.browncountywi.gov/departments/planning-and-land-services/zoning/"

def scrape_zoning_page(url: str, output_dir: str = "/data/raw/brown"):
    print(f"Scraping Brown County Zoning page: {url}")

    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"Failed to fetch page: HTTP {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")

        # Find all links on the page
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if href.startswith("http"):
                links.append({"text": text, "url": href})
            elif href.startswith("/"):
                full_url = "https://www.browncountywi.gov" + href
                links.append({"text": text, "url": full_url})

        # Filter for likely zoning documents
        zoning_links = [l for l in links if any(kw in l["url"].lower() for kw in ["zoning", "ordinance", "map", "pdf"])]

        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "zoning_page_links.txt")

        with open(output_file, "w") as f:
            for link in zoning_links:
                f.write(f"{link['text']}: {link['url']}\n")

        print(f"Found {len(zoning_links)} relevant zoning links.")
        print(f"Links saved to {output_file}")

    except Exception as e:
        print(f"Error scraping zoning page: {e}")

if __name__ == "__main__":
    scrape_zoning_page(ZONING_PAGE_URL)