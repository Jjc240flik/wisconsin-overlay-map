#!/usr/bin/env python3
"""
Wisconsin Overlay Map - Database Setup Script
PRD v1.1 compliant - MultiPolygon geometry + PostGIS extensions
"""

import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "dbname": os.getenv("POSTGRES_DB", "wisconsin_overlay"),
}

def create_database():
    """Create database if it doesn't exist."""
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        dbname="postgres"
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG["dbname"],))
    if not cur.fetchone():
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_CONFIG["dbname"])))
        print(f"Database '{DB_CONFIG['dbname']}' created.")
    else:
        print(f"Database '{DB_CONFIG['dbname']}' already exists.")

    cur.close()
    conn.close()

def setup_extensions_and_schema():
    """Connect to target DB and create PostGIS extensions + tables."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Enable PostGIS extensions
    print("Enabling PostGIS extensions...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    cur.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology;")

    # Counties tracker
    cur.execute("""
        CREATE TABLE IF NOT EXISTS counties (
            county_id SERIAL PRIMARY KEY,
            county_name TEXT NOT NULL,
            state TEXT DEFAULT 'WI',
            status TEXT DEFAULT 'pending',
            last_updated TIMESTAMP DEFAULT NOW(),
            source_files TEXT[]
        );
    """)

    # Parcels (MultiPolygon geometry - CRITICAL FIX)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parcels (
            parcel_id SERIAL PRIMARY KEY,
            apn TEXT UNIQUE NOT NULL,
            county_id INTEGER REFERENCES counties(county_id),
            owner_name TEXT,
            mailing_address TEXT,
            acreage NUMERIC,
            current_zoning TEXT,
            land_use TEXT,
            geometry GEOMETRY(MultiPolygon, 4326),
            within_city_limits BOOLEAN,
            tier INTEGER,
            distance_to_sewer NUMERIC,
            distance_to_water NUMERIC,
            distance_to_electric NUMERIC,
            future_designation TEXT,
            rationale TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # Growth infrastructure
    cur.execute("""
        CREATE TABLE IF NOT EXISTS growth_infrastructure (
            infra_id SERIAL PRIMARY KEY,
            county_id INTEGER REFERENCES counties(county_id),
            infra_type TEXT,
            geometry GEOMETRY(MultiLineString, 4326),
            description TEXT,
            source TEXT,
            effective_year INTEGER
        );
    """)

    # Spatial indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_parcels_geom ON parcels USING GIST (geometry);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_infra_geom ON growth_infrastructure USING GIST (geometry);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_parcels_apn ON parcels (apn);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_parcels_tier ON parcels (tier);")

    conn.commit()
    print("PostGIS extensions and schema created successfully.")
    print("Geometry type: MultiPolygon (4326) – ready for county shapefiles.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    print("=== Wisconsin Overlay Map Database Setup ===")
    create_database()
    setup_extensions_and_schema()
    print("Database setup complete.")