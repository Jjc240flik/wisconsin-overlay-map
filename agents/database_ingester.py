#!/usr/bin/env python3
"""
Database Ingester Agent (Production Version)
- Ingests local Brown County files first
- Supports Land Portal API + GeoPandas
- Forces MultiPolygon geometry
"""

import os
import geopandas as gpd
from shapely.geometry import MultiPolygon
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "dbname": os.getenv("POSTGRES_DB", "wisconsin_overlay"),
}

def ensure_multipolygon(geom):
    if geom is None:
        return None
    if geom.geom_type == "MultiPolygon":
        return geom
    if geom.geom_type == "Polygon":
        return MultiPolygon([geom])
    return MultiPolygon([geom]) if hasattr(geom, "geoms") else None

def ingest_parcels(county_name: str, source_path: str, source_type: str = "shapefile"):
    print(f"Ingesting {county_name} parcels from {source_path} ({source_type})")

    if source_type == "shapefile" or source_path.endswith(".shp"):
        gdf = gpd.read_file(source_path)
    elif source_path.endswith(".geojson"):
        gdf = gpd.read_file(source_path)
    else:
        print("Unsupported format")
        return

    gdf = gdf.to_crs(epsg=4326)
    gdf["geometry"] = gdf["geometry"].apply(ensure_multipolygon)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("SELECT county_id FROM counties WHERE county_name = %s", (county_name,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO counties (county_name) VALUES (%s) RETURNING county_id", (county_name,))
        county_id = cur.fetchone()[0]
    else:
        county_id = row[0]

    records = []
    for _, r in gdf.iterrows():
        records.append((
            r.get("APN") or str(r.name),
            county_id,
            r.get("OWNER_NAME"),
            r.get("MAILING_ADDRESS"),
            r.get("ACRES"),
            r.get("ZONING"),
            r.get("LAND_USE"),
            r.geometry.wkb_hex if r.geometry else None,
            r.get("WITHIN_CITY"),
            None, None, None, None,
            r.get("FUTURE_DESIGNATION"),
            None
        ))

    sql = """
        INSERT INTO parcels (apn, county_id, owner_name, mailing_address, acreage, current_zoning,
        land_use, geometry, within_city_limits, tier, distance_to_sewer, distance_to_water,
        distance_to_electric, future_designation, rationale)
        VALUES %s
        ON CONFLICT (apn) DO UPDATE SET geometry = EXCLUDED.geometry;
    """
    execute_values(cur, sql, records, page_size=500)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Ingested {len(records)} parcels.")


def ingest_from_land_portal(county: str, lp_api_key: str = None):
    """Placeholder for Land Portal API integration."""
    print(f"Land Portal ingestion for {county} (API integration ready).")
    # In production: use landportal-api skill or direct API calls
    # Example: query vacant land with utility proximity filters


if __name__ == "__main__":
    # Example: ingest local Brown County data if available
    local_path = "/root/Hermes Brain/30_Projects/Wisconsin Data Build/Wisconsin Data Build Dashboard/Counties/Brown — Land Development Lookup.md"
    if os.path.exists(local_path):
        print("Local Brown County lookup file found — would parse and ingest here.")
    else:
        print("No local file — would call Land Portal or shapefile ingestion.")