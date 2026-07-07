import os
from sqlalchemy import create_engine, text

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "wisconsin_spatial")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

def init_database():
    """Initializes the PostGIS database and required extensions."""
    engine = create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    
    with engine.begin() as conn:
        # Enable PostGIS extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        print("[+] PostGIS extension enabled.")

        # Create base tables if they don't exist (lightweight schema)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS brown_county_parcels (
                parcel_id TEXT,
                owner_name TEXT,
                owner_address TEXT,
                owner_city_state_zip TEXT,
                land_class_code TEXT,
                zoning_description TEXT,
                calculated_acres DOUBLE PRECISION,
                assessed_value DOUBLE PRECISION,
                geom GEOMETRY(MultiPolygon, 3071)
            );
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS future_land_use (
                planned_use TEXT,
                municipality TEXT,
                geom GEOMETRY(MultiPolygon, 3071)
            );
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sewer_service_area (
                district_name TEXT,
                is_serviceable BOOLEAN,
                geom GEOMETRY(MultiPolygon, 3071)
            );
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pipeline_targets (
                apn TEXT,
                owner_name TEXT,
                owner_address TEXT,
                owner_city_state_zip TEXT,
                acres DOUBLE PRECISION,
                assessed_value DOUBLE PRECISION,
                future_designation TEXT,
                geom_wgs84 GEOMETRY(Geometry, 4326)
            );
        """))
        
    print("[+] Database schema initialized successfully.")

if __name__ == "__main__":
    init_database()