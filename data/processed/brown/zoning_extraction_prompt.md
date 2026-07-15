# Zoning Code Keys Extraction Prompt

You are analyzing the Brown County Land Use Chapter (2040 Comprehensive Plan).

Below is the scraped content from the official Land Use Chapter PDF.

**Task:**
Extract every Zoning Code / District mentioned in the document.

Return a clean, well-formatted Markdown table with these exact columns:

| Zoning Code | Description | Future Residential / Growth Notes |

**Rules:**
- Only include actual zoning codes (e.g. AG-1, RR-1, etc.).
- If a code has notes about future residential use, transition zones, or growth areas, include them in the third column.
- If no future residential notes exist for a code, leave the cell empty or write "No specific notes".
- Sort the table alphabetically by Zoning Code.

---

**Document Content:**

{{PASTE_SCRAPED_CONTENT_HERE}}