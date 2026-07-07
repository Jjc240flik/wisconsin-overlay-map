# Wisconsin Overlay Map
**Automated Parcel Identification Pipeline & Interactive Map**  
**Phase 1: Brown County MVP**  
**PRD v1.4 – July 6, 2026**

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

---

## Brown County Municipality Ordinance Tracking (Added in v1.4)

**Strict Scope**: Only Brown County municipalities. No ordinances from other counties are included in this build.

### Complete Municipal Zoning Ordinance Source List – All 25 Municipalities

| #  | Municipality              | Type     | Best Source                                                                 | Status                  | Notes |
|----|---------------------------|----------|-----------------------------------------------------------------------------|-------------------------|-------|
| 1  | City of Green Bay         | City     | https://library.municode.com/wi/green_bay                                   | Municode                | Full code online |
| 2  | City of De Pere           | City     | data/raw/brown/municipal/City_of_De_Pere_Zoning_Ordinance.pdf               | Downloaded (14 MB)      | Full 201-page ordinance |
| 3  | Village of Allouez        | Village  | data/raw/brown/municipal/Village_of_Allouez_Zoning_Ordinance.pdf            | Downloaded (4.1 MB)     | Full ordinance |
| 4  | Village of Ashwaubenon    | Village  | https://ashwaubenon.gov/government/municipal-code/                          | Partial only            | No single PDF |
| 5  | Village of Bellevue       | Village  | https://ecode360.com/BE3132                                                 | ecode360                | Full code online |
| 6  | Village of Denmark        | Village  | County-level baseline                                                       | Pending                 | Search ongoing |
| 7  | Village of Greenleaf      | Village  | County-level baseline                                                       | Pending                 | Search ongoing |
| 8  | Village of Hobart         | Village  | https://ecode360.com/28090647 (Chapter 295)                                 | ecode360                | Full Chapter 295 |
| 9  | Village of Howard         | Village  | https://library.municode.com/wi/howard                                      | Municode                | Full code online |
| 10 | Village of Pulaski        | Village  | County-level baseline                                                       | Pending                 | Partial overlap |
| 11 | Village of Suamico        | Village  | data/raw/brown/municipal/Village_of_Suamico_Zoning_Map.pdf + ecode360       | Map downloaded (12 MB)  | Chapter 18 on ecode360 |
| 12 | Village of Wrightstown    | Village  | County-level baseline                                                       | Pending                 | Search ongoing |
| 13 | Town of Eaton             | Town     | County-level baseline                                                       | Pending                 | Search ongoing |
| 14 | Town of Glenmore          | Town     | County-level baseline                                                       | Pending                 | Search ongoing |
| 15 | Town of Green Bay         | Town     | County-level baseline                                                       | Pending                 | Search ongoing |
| 16 | Town of Holland           | Town     | County-level baseline                                                       | Pending                 | Search ongoing |
| 17 | Town of Humboldt          | Town     | County-level baseline                                                       | Pending                 | Search ongoing |
| 18 | Town of Lawrence          | Town     | https://energyzoning.org (sample only) + ecode360                           | Partial sample          | Full code behind paywall |
| 19 | Town of Ledgeview         | Town     | https://ecode360.com/8435332 (Chapter 135)                                  | ecode360                | Full Chapter 135 |
| 20 | Town of Morrison          | Town     | County-level baseline                                                       | Pending                 | Search ongoing |
| 21 | Town of New Denmark       | Town     | County-level baseline                                                       | Pending                 | Search ongoing |
| 22 | Town of Pittsfield        | Town     | County-level baseline                                                       | Pending                 | Search ongoing |
| 23 | Town of Rockland          | Town     | County-level baseline                                                       | Pending                 | Search ongoing |
| 24 | Town of Scott             | Town     | data/raw/brown/municipal/Town_of_Scott_Zoning_Ordinance.pdf                 | Downloaded (701 KB)     | 74-page ordinance |
| 25 | Town of Wrightstown       | Town     | County-level baseline                                                       | Pending                 | Search ongoing |

**Summary**
- **Direct PDFs downloaded**: 4
- **Municode / ecode360 sources**: 6
- **Pending / County baseline only**: 15

**Rule**: Only Brown County municipalities are included in this build.