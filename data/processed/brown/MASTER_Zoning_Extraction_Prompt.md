# Master Zoning Code Extraction Prompt - Brown County Ordinances

You are analyzing two Brown County Ordinance chapters scraped from the official site.

**Files:**
- CHAP011.md (31k chars)
- CHAP022.md (94k chars)

**Task:**
Extract **all** zoning districts, zoning codes, and land use regulations from both documents.

Return **one consolidated Markdown table** with these columns:

| Zoning Code / District | Description | Key Regulations / Notes | Source Chapter |

**Rules:**
- Merge duplicates across both chapters.
- Prioritize Agricultural, Residential, Commercial, Industrial, Floodplain, and Shoreland districts.
- If a code appears in both chapters, note any differences.

---

**CHAP011 Content:**

{{PASTE_CHAP011_HERE}}

---

**CHAP022 Content:**

{{PASTE_CHAP022_HERE}}