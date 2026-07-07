import os
import geopandas as gpd
from sqlalchemy import create_engine, text

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "wisconsin_spatial")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

class DataIngester:
    """Agent 2: Ingests raw GeoJSON layers, loads PostGIS, and runs spatial intersections."""

    def __init__(self, data_dir="data/raw"):
        self.data_dir = data_dir
        self.engine = create_engine(
            f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    def _reproject_and_cast(self, gdf):
        """Reprojects to EPSG:3071 and ensures MultiPolygon geometry."""
        if gdf.crs is None or gdf.crs.to_epsg() != 3071:
            print("   -> Reprojecting to EPSG:3071...")
            gdf = gdf.to_crs(epsg=3071)

        # Convert Polygons to MultiPolygons
        gdf["geometry"] = gdf["geometry"].apply(
            lambda geom: geom if geom.geom_type == "MultiPolygon" else gpd.GeoSeries([geom]).unary_union
        )
        return gdf

    def ingest_base_parcels(self):
        path = os.path.join(self.data_dir, "base_parcels.geojson")
        print(f"[*] Ingesting Base Parcels from: {path}")

        gdf = gpd.read_file(path)
        gdf = self._reproject_and_cast(gdf)

        df_to_load = gpd.GeoDataFrame({
            "parcel_id": gdf.get("PARCELID", gdf.get("parcel_id")),
            "owner_name": gdf.get("OWNERNME1", gdf.get("owner_name")),
            "owner_address": gdf.get("PSTADR", gdf.get("owner_address")),
            "owner_city_state_zip": gdf.get("SITEADRESS", gdf.get("owner_city_state_zip")),
            "land_class_code": gdf.get("CLASS", gdf.get("land_class_code")),
            "zoning_description": gdf.get("ZONING", gdf.get("zoning_description")),
            "calculated_acres": gdf.get("GISACRES", gdf.get("calculated_acres")),
            "assessed_value": gdf.get("TOTALASSESSEDVALUE", gdf.get("assessed_value")),
            "geometry": gdf.geometry
        }, crs="EPSG:3071")

        df_to_load["calculated_acres"] = df_to_load["calculated_acres"].fillna(0.0)
        df_to_load["assessed_value"] = df_to_load["assessed_value"].fillna(0.0)

        df_to_load.to_postgis("brown_county_parcels", con=self.engine, if_exists="replace", index=False)
        print("[+] Base parcels uploaded.")

    def ingest_future_land_use(self):
        path = os.path.join(self.data_dir, "future_land_use.geojson")
        print(f"[*] Ingesting Future Land Use from: {path}")

        gdf = gpd.read_file(path)
        gdf = self._reproject_and_cast(gdf)

        df_to_load = gpd.GeoDataFrame({
            "planned_use": gdf.get("Future_Land_Use", gdf.get("planned_use", "Unassigned")),
            "municipality": gdf.get("MUNICIPALITY", gdf.get("municipality", "Unknown")),
            "geometry": gdf.geometry
        }, crs="EPSG:3071")

        df_to_load.to_postgis("future_land_use", con=self.engine, if_exists="replace", index=False)
        print("[+] Future Land Use uploaded.")

    def ingest_sewer_service_area(self):
        path = os.path.join(self.data_dir, "sewer_service_area.geojson")
        print(f"[*] Ingesting Sewer Service Area from: {path}")

        gdf = gpd.read_file(path)
        gdf = self._reproject_and_cast(gdf)

        df_to_load = gpd.GeoDataFrame({
            "district_name": gdf.get("SSA_Name", gdf.get("district_name", "Primary District")),
            "is_serviceable": True,
            "geometry": gdf.geometry
        }, crs="EPSG:3071")

        df_to_load.to_postgis("sewer_service_area", con=self.engine, if_exists="replace", index=False)
        print("[+] Sewer Service Area uploaded.")

    def execute_spatial_intersection(self):
        print("[*] Running PostGIS intersection query...")

        query = """
        DROP TABLE IF EXISTS pipeline_targets;

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
            (p.land_class_code ILIKE '%AG%' 
             OR p.zoning_description ILIKE '%agri%'
             OR p.land_class_code IN ('4', '5', '5M'))
            AND (f.planned_use ILIKE '%Res%' 
                 OR f.planned_use ILIKE '%Comm%' 
                 OR f.planned_use ILIKE '%Mixed%' 
                 OR f.planned_use ILIKE '%Ind%')
            AND s.is_serviceable = TRUE
            AND p.calculated_acres >= 5.0;
        """

        with self.engine.begin() as conn:
            conn.execute(text(query))

        with self.engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM pipeline_targets;")).fetchone()[0]

        print(f"[+] Found {count} target parcels.")

    def run_all(self):
        self.ingest_base_parcels()
        self.ingest_future_land_use()
        self.ingest_sewer_service_area()
        self.execute_spatial_intersection()