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