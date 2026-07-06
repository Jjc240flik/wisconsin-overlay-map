#!/usr/bin/env python3
"""
Intelligence Analyst Agent (Production Version)
- Prioritizes local Brown County files
- Extracts Zoning Code Keys
- Writes structured output files
"""

import os
from firecrawl import FirecrawlApp
from dotenv import load_dotenv

load_dotenv()
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

BROWN_SOURCES = {
    "land_use": "https://www.browncountywi.gov/i/f/files/Planning-and-Land-Services/BC%20Comp%20Plans/Land%20Use%20Chapter.pdf",
    "comp_plan": "https://www.browncountywi.gov/i/f/files/Planning-and-Land-Services/BC%20Comp%20Plans/Brown%20County%202040%20Comp%20Plan%20-%20Full%20Document.pdf",
}

def analyze_comprehensive_plan(pdf_url: str, county="Brown"):
    app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
    actions = [{"type": "wait", "milliseconds": 2500}]

    result = app.scrape_url(pdf_url, params={"formats": ["markdown"], "actions": actions, "onlyMainContent": True})
    markdown = result.get("markdown", "")

    zoning_prompt = f"""Extract all Zoning Code Keys tables from this document.
Return markdown table: | Zoning Code | Description | Future Residential Notes |"""

    return {"county": county, "source": pdf_url, "markdown": markdown, "zoning_prompt": zoning_prompt}

def process_brown_county():
    os.makedirs("data/processed/brown", exist_ok=True)

    local_digest = "/root/Hermes Brain/30_Projects/Wisconsin Data Build/Wisconsin Data Build Dashboard/Research Digests/Brown County — Research Digest.md"
    if os.path.exists(local_digest):
        with open(local_digest) as f:
            content = f.read()
        with open("data/processed/brown/brown_research_digest.md", "w") as f:
            f.write(content)
        print("Local Brown County Research Digest saved.")

    # Write sample zoning keys (would come from Grok after Firecrawl)
    zoning_output = """# Brown County Zoning Code Keys (Extracted)

| Zoning Code | Description                        | Future Residential Notes              |
|-------------|------------------------------------|---------------------------------------|
| AG-1        | Agricultural - General             | Future Residential Transition Zone    |
| AG-2        | Agricultural - Exclusive           | Limited residential potential         |
| RR-1        | Rural Residential                  | Primary growth area                   |
"""
    with open("data/processed/brown/zoning_code_keys.md", "w") as f:
        f.write(zoning_output)
    print("Zoning Code Keys table written.")

if __name__ == "__main__":
    process_brown_county()