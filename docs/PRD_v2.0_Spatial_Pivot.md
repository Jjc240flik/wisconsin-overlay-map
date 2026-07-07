# PRD v2.0: Wisconsin Overlay Map (The Spatial Pivot Spec)
**System Identity**: Automated Geometry Intersection Pipeline & Target Identification System
**Target Scope**: Phase 1 MVP - Brown County, WI
**Release Date**: July 6, 2026
**Status**: Approved for Hermes Orchestrator Injection (Supersedes v1.1 & v1.4)

## 1. Executive Summary & Thesis
PRD v2.0 pivots away from unstructured municipal text/PDF processing. The system will identify high-value, undervalued vacant agricultural parcels ripe for development using strict **PostGIS spatial intersection logic** across three standardized regional layers.

### The Core Logic
If a parcel is currently classed as **Agricultural Land**, falls inside a **Future Land Use Zone** designated for development, and sits inside the **Sewer Service Area (SSA) boundary**, it is an optimal subdivision target regardless of which of the 25 local municipal borders it crosses.

---

## 2. Re-Engineered 3-Agent Architecture

### Agent 1: Data Harvester (Python + Requests)
**Objective**: Bypasses municipal websites entirely. Programmatically acquires raw GIS vector data from centralized county and state open data endpoints.

**Payload Deliverables**: Downloads the following 3 layers into `/data/raw/` in GeoJSON or Shapefile format:

1. **Layer A (Base Parcels)**: Brown County Parcel boundaries containing Tax Roll attributes, Land Class Codes, Owner Names, and Owner Mailing Addresses.
2. **Layer B (Future Land Use)**: Brown County 2040 Comprehensive Plan Land Use polygon layer.
3. **Layer C (Utility Limits)**: Brown County Sewer Service Area (SSA) Expansion and Sanitary District polygons.

### Agent 2: Database Ingester (GeoPandas + PostGIS)
**Objective**: Cleans, re-projects, and uploads raw vector data to PostgreSQL/PostGIS. Executes the deterministic target identification matrix.

**Transformation Requirements**:
- Normalize all spatial layers to Coordinate Reference System **EPSG:3071** (NAD83 / Wisconsin Transverse Mercator).
- Execute a spatial join query to flag intersection zones.

**Core PostGIS Query Definition**:
```sql
CREATE TABLE pipeline_targets AS
SELECT 
    p.parcel_id AS apn,
    p.owner_name,
    p.owner_address,
    p.owner_city_state_zip,
    p.calculated_acres AS acres,
    p.assessed_value,
    f.planned_use AS future_designation,
    ST_Transform(p.geom, 4326) AS geom_wgs84
FROM brown_county_parcels p
JOIN future_land_use f ON ST_Intersects(p.geom, f.geom)
JOIN sewer_service_area s ON ST_Intersects(p.geom, s.geom)
WHERE 
    (p.land_class_code ILIKE '%AG%' OR p.zoning_description ILIKE '%agri%')
    AND f.planned_use IN ('Residential', 'Commercial', 'Mixed-Use', 'Industrial')
    AND s.is_serviceable = TRUE
    AND p.calculated_acres >= 5.0;
```

### Agent 3: GIS Visualizer & Cartographer (Folium)
**Objective**: Renders query records into production outputs.

**Map Requirements**: Generates an interactive, lightweight single-file HTML map (`/output/map.html`) utilizing Folium.

- **Layer 1 Control**: Base Maps (OpenStreetMap & Satellite Toggle).
- **Layer 2 Control**: Choropleth or boundary overlay of the Sewer Service Area line (Red vector line).
- **Layer 3 Control**: Neon Green highlighted polygons of the identified `pipeline_targets`.
- **Popup Specs**: Clicking a target parcel displays: APN, Owner, Acres, Assessed Value, and Future Use Designation.

**Data Output Specs**: Exports a refined mailing list CSV (`/output/mailing_list.csv`) sorting targets by total acreage descending.

---

## 3. Preservation of Technical Stack & Infrastructure
All pre-built infrastructure from v1.1/v1.4 is frozen and reused.

- **Database Engine**: PostgreSQL 15+ with PostGIS 3+ extension enabled via Docker-Compose.
- **Testing Suite**: `pytest` validates spatial table existence and tests geometric intersection functions.
- **CI/CD Pipeline**: `.github/workflows/ci.yml` continues to run linting (`ruff`), container build security (`trivy`), and schema test suites on every push.

---

## 4. Execution Workflow for Orchestrator
When Hermes executes `main.py --county "Brown" --phase 1`, it must force the following task execution sequences:

1. **Initialize Environment**: Verify containerized PostGIS instance is live and accessible.
2. **Execute Harvester**: Fetch the 3 targeted layers from open data repositories.
3. **Execute Ingester**: Drop stale tables, populate base layers, reproject to EPSG:3071, and write `pipeline_targets`.
4. **Execute Cartographer**: Build map frame, inject Folium layer toggles, bind target data, and write final HTML and CSV files.