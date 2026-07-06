# Wisconsin Overlay Map
**Automated Parcel Identification Pipeline & Interactive Map**  
**Phase 1: Brown County MVP**  
**PRD v1.1 Approved – July 6, 2026**

## Overview
5-Agent Hybrid Swarm (Grok models) that identifies undervalued vacant agricultural parcels in the path of municipal infrastructure expansion for subdivision development.

- **Repository**: New isolated project (not mixed with WisconsinDataBuildDashboard)
- **Primary Output**: Interactive Folium map + QGIS project + APN-focused CSV mailing list
- **First County**: Brown County (existing local files processed first)

## 5-Agent Architecture
1. **Orchestrator** (Grok 4.3 Max) – High-level tasking via Hermes Delegation
2. **Data Harvester** (Grok 4.20 + Playwright) – Portal scraping with anti-bot
3. **Intelligence Analyst** (Grok 4.20 0309) – Firecrawl PDF → Markdown + Zoning Code Keys
4. **Database Ingester** (GeoPandas + PostGIS) – MultiPolygon geometry handling
5. **GIS Cartographer** (Folium + QGIS) – Interactive map with 3-layer control + popups

## Quick Start
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 1. Setup database
python db/db_setup.py

# 2. Run full pipeline (Brown County)
python main.py --county "Brown" --phase 1
```

## CI/CD Pipeline
This project uses **GitHub Actions** for automated testing and building.

**What runs on every push / pull request:**
- Code linting (`ruff`)
- Unit tests (`pytest`)
- Database setup verification
- Docker image build
- Security scanning (`trivy`)

**Workflow file:** `.github/workflows/ci.yml`

To run locally:
```bash
pytest tests/ -v
ruff check .
docker build -t wisconsin-overlay-map:latest .
```

## Docker Deployment
```bash
docker-compose up -d
```

Or use the helper script:
```bash
./scripts/deploy.sh
```

## Project Structure
- `agents/` – 5 specialized agents
- `db/` – PostgreSQL + PostGIS setup
- `scripts/` – Local ingestion + deployment helpers
- `tests/` – Unit tests
- `.github/workflows/ci.yml` – CI/CD pipeline

**Status**: Fully implemented and CI/CD ready.

## Brown County Municipality Ordinance Tracking (PRD v1.2)

**Strict Scope**: Only Brown County municipalities. No ordinances from other counties will be included in this build.

### Full Municipality List (Brown County Only)

| Municipality              | Type     | Current Zoning Ordinance Status          | Source / Notes                          | Priority | Extracted? |
|---------------------------|----------|------------------------------------------|-----------------------------------------|----------|------------|
| City of Green Bay         | City     | County-level only (CHAP011/022/023)     | Brown County Clerk Ordinances           | High     | No         |
| City of De Pere           | City     | County-level only                       | Brown County Clerk Ordinances           | High     | No         |
| Village of Allouez        | Village  | County-level only                       | Brown County Clerk Ordinances           | High     | No         |
| Village of Ashwaubenon    | Village  | County-level only                       | Brown County Clerk Ordinances           | High     | No         |
| Village of Bellevue       | Village  | County-level only                       | Brown County Clerk Ordinances           | High     | No         |
| Village of Denmark        | Village  | County-level only                       | Brown County Clerk Ordinances           | Medium   | No         |
| Village of Greenleaf      | Village  | County-level only                       | Brown County Clerk Ordinances           | Medium   | No         |
| Village of Hobart         | Village  | County-level only                       | Brown County Clerk Ordinances           | High     | No         |
| Village of Howard         | Village  | County-level only                       | Brown County Clerk Ordinances           | High     | No         |
| Village of Pulaski        | Village  | County-level only (partial)             | Brown County Clerk Ordinances           | Medium   | No         |
| Village of Suamico        | Village  | County-level only                       | Brown County Clerk Ordinances           | High     | No         |
| Village of Wrightstown    | Village  | County-level only                       | Brown County Clerk Ordinances           | Medium   | No         |
| Town of Eaton             | Town     | County-level only                       | Brown County Clerk Ordinances           | Medium   | No         |
| Town of Glenmore          | Town     | County-level only                       | Brown County Clerk Ordinances           | Medium   | No         |
| Town of Green Bay         | Town     | County-level only                       | Brown County Clerk Ordinances           | High     | No         |
| Town of Holland           | Town     | County-level only                       | Brown County Clerk Ordinances           | Medium   | No         |
| Town of Humboldt          | Town     | County-level only                       | Brown County Clerk Ordinances           | Medium   | No         |
| Town of Lawrence          | Town     | County-level only                       | Brown County Clerk Ordinances           | High     | No         |
| Town of Ledgeview         | Town     | County-level only                       | Brown County Clerk Ordinances           | High     | No         |
| Town of Morrison          | Town     | County-level only                       | Brown County Clerk Ordinances           | Medium   | No         |
| Town of New Denmark       | Town     | County-level only                       | Brown County Clerk Ordinances           | Medium   | No         |
| Town of Pittsfield        | Town     | County-level only                       | Brown County Clerk Ordinances           | Medium   | No         |
| Town of Rockland          | Town     | County-level only                       | Brown County Clerk Ordinances           | Medium   | No         |
| Town of Scott             | Town     | County-level only                       | Brown County Clerk Ordinances           | High     | No         |
| Town of Wrightstown       | Town     | County-level only                       | Brown County Clerk Ordinances           | Medium   | No         |

## High Priority Municipal Zoning Ordinance Sources (Brown County Only)

**Last Updated**: 2026-07-06

| Municipality              | Type   | Best Available Source                                      | Status                  | Notes |
|---------------------------|--------|------------------------------------------------------------|-------------------------|-------|
| City of Green Bay         | City   | https://library.municode.com/wi/green_bay                  | Municode (no direct PDF) | Full code available online |
| City of De Pere           | City   | data/raw/brown/municipal/City_of_De_Pere_Zoning_Ordinance.pdf | Downloaded (14 MB)     | Full 201-page ordinance |
| Village of Allouez        | Village| data/raw/brown/municipal/Village_of_Allouez_Zoning_Ordinance.pdf | Downloaded (4.1 MB)    | Full ordinance |
| Village of Ashwaubenon    | Village| https://ashwaubenon.gov/government/municipal-code/         | Partial code only      | No single PDF |
| Village of Bellevue       | Village| County-level only (search ongoing)                         | Pending                | - |
| Village of Denmark        | Village| County-level only                                          | Pending                | - |
| Village of Greenleaf      | Village| County-level only                                          | Pending                | - |
| Village of Hobart         | Village| County-level only                                          | Pending                | - |
| Village of Howard         | Village| https://library.municode.com/wi/howard                     | Municode               | No single PDF |
| Village of Pulaski        | Village| County-level only                                          | Pending                | Partial overlap |
| Village of Suamico        | Village| data/raw/brown/municipal/Village_of_Suamico_Zoning_Map.pdf + https://ecode360.com/36664591 | Map downloaded (12 MB) | Chapter 18 on ecode360 |
| Village of Wrightstown    | Village| County-level only                                          | Pending                | - |
| Town of Eaton             | Town   | County-level only                                          | Pending                | - |
| Town of Glenmore          | Town   | County-level only                                          | Pending                | - |
| Town of Green Bay         | Town   | County-level only                                          | Pending                | - |
| Town of Holland           | Town   | County-level only                                          | Pending                | - |
| Town of Humboldt          | Town   | County-level only                                          | Pending                | - |
| Town of Lawrence          | Town   | County-level only                                          | Pending                | - |
| Town of Ledgeview         | Town   | https://ecode360.com/8435332 (Chapter 135)                 | ecode360               | Full Chapter 135 |
| Town of Morrison          | Town   | County-level only                                          | Pending                | - |
| Town of New Denmark       | Town   | County-level only                                          | Pending                | - |
| Town of Pittsfield        | Town   | County-level only                                          | Pending                | - |
| Town of Rockland          | Town   | County-level only                                          | Pending                | - |
| Town of Scott             | Town   | County-level only                                          | Pending                | - |
| Town of Wrightstown       | Town   | County-level only                                          | Pending                | - |

**Extraction Status Legend**:
- **Downloaded** = Full ordinance PDF saved locally
- **Municode / ecode360** = Full code available online (will extract via browser if needed)
- **Pending** = Source search ongoing

**Next Actions**: Extract zoning keys from downloaded PDFs (De Pere, Allouez, Suamico map) then proceed to next batch.

**Legend**:
- **Extracted?** = Whether municipality-specific zoning ordinance has been downloaded and processed into zoning keys.
- All current work uses **Brown County Clerk** ordinances (CHAP011, CHAP014, CHAP022, Ch23_Floodplains) as baseline.
- Next phase: Systematically pull and extract individual municipal zoning ordinances starting with High priority.

**PRD Update Note**: This table replaces any previous partial references. Only Brown County entries are permitted.