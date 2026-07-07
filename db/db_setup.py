import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "wisconsin_spatial")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

def init_database():
    """Initializes PostGIS and creates the target database if it doesn't exist."""
    
    # First connect to default 'postgres' database to create our target DB if needed
    default_engine = create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
    )

    try:
        with default_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'"))
            if not result.fetchone():
                conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
                print(f"[+] Created database: {DB_NAME}")
    except OperationalError as e:
        print(f"[-] Could not connect to PostgreSQL: {e}")
        return False

    # Now connect to our target database
    engine = create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        print("[+] PostGIS extension enabled.")

        # Create tables
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
    return True

if __name__ == "__main__":
    init_database()