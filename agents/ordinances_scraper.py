#!/usr/bin/env python3
"""
Ordinances Page Scraper - Brown County
"""

import os
import requests
from bs4 import BeautifulSoup

ORDINANCES_URL = "https://www.browncountywi.gov/departments/planning-and-land-services/zoning/ordinances/"

def scrape_ordinances_page(url: str, output_dir: str = "/data/raw/brown"):
    print(f"Scraping Brown County Ordinances page: {url}")

    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"Failed: HTTP {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        pdf_links = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if href.lower().endswith(".pdf"):
                if href.startswith("http"):
                    full_url = href
                elif href.startswith("/"):
                    full_url = "https://www.browncountywi.gov" + href
                else:
                    full_url = url.rsplit("/", 1)[0] + "/" + href

                pdf_links.append({"text": text, "url": full_url})

        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "ordinances_pdfs.txt")

        with open(output_file, "w") as f:
            for link in pdf_links:
                f.write(f"{link['text']}: {link['url']}\n")

        print(f"Found {len(pdf_links)} PDF links on the Ordinances page.")
        print(f"Saved to {output_file}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_ordinances_page(ORDINANCES_URL)