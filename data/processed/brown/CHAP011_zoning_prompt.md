# CHAP011 Zoning Code Extraction Prompt

You are analyzing **CHAP011.pdf** from the Brown County Code of Ordinances.

**Task:**
Extract every zoning district, zoning code, or land use regulation mentioned.

Return a clean Markdown table with these columns:

| Zoning Code / District | Description | Key Regulations / Notes |

---

**Document Content:**

""" + open("data/raw/brown/pdfs/CHAP011.md").read() + """
