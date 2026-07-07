import os
import folium
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine

# Fallback defaults if Docker/environment variables aren't set
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "wisconsin_spatial")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

class GISCartographer:
    """Agent 3: Exports the off-market mailing list and generates the interactive Folium map."""
    
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        # Establish database engine connection
        self.engine = create_engine(
            f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    def export_mailing_list(self):
        """Extracts spatial targets to an optimized, acreage-sorted CSV mailing list."""
        print("[*] Generating off-market CSV mailing list...")
        query = """
            SELECT apn, owner_name, owner_address, owner_city_state_zip, acres, assessed_value, future_designation
            FROM pipeline_targets
            ORDER BY acres DESC;
        """
        df = pd.read_sql(query, self.engine)
        
        # Clean string formats to eliminate database trailing white spaces
        for col in ['apn', 'owner_name', 'owner_address', 'owner_city_state_zip']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        csv_path = os.path.join(self.output_dir, "mailing_list.csv")
        df.to_csv(csv_path, index=False)
        print(f"[+] Mailing list successfully exported to {csv_path} ({len(df)} records generated).")
        return df

    def generate_interactive_map(self):
        """Queries spatial vectors and builds a multi-layered Folium HTML product."""
        print("[*] Building interactive Folium map...")
        
        # Pull targets directly as a GeoDataFrame using the WGS84 geometry column
        query = "SELECT apn, owner_name, owner_address, acres, assessed_value, future_designation, geom_wgs84 AS geometry FROM pipeline_targets;"
        gdf_targets = gpd.read_postgis(query, self.engine, geom_col="geometry", crs="EPSG:4326")
        
        # Pull Sewer Service Area (SSA) geometries for the boundary reference overlay
        ssa_query = "SELECT district_name, ST_Transform(geom, 4326) AS geometry FROM sewer_service_area;"
        gdf_ssa = gpd.read_postgis(ssa_query, self.engine, geom_col="geometry", crs="EPSG:4326")

        # Fallback coordinate positioning to central Brown County if no targets exist
        center_lat, center_lon = 44.45, -88.05
        if not gdf_targets.empty:
            center_lat = gdf_targets.geometry.centroid.y.mean()
            center_lon = gdf_targets.geometry.centroid.x.mean()

        # Initialize Base Leaflet Map canvas
        m = folium.Map(location=[center_lat, center_lon], zoom_start=11, control_scale=True)

        # Layer 1 Toggle Component: Satellite Hybrid Imagery (Esri Endpoint)
        folium.TileLayer(
            tiles='https://arcgisonline.com{z}/{y}/{x}',
            attr='Esri',
            name='Satellite Hybrid',
            overlay=False,
            control=True
        ).add_to(m)

        # Layer 2 Toggle Component: Sewer Service Area (SSA) Boundary Limits
        if not gdf_ssa.empty:
            ssa_layer = folium.FeatureGroup(name="Sewer Service Area Boundary", show=True)
            folium.GeoJson(
                gdf_ssa.__geo_interface__,
                style_function=lambda x: {
                    'fillColor': 'transparent',
                    'color': '#d9534f', # Solid red boundary tracking utility limits
                    'weight': 2.5,
                    'dashArray': '5, 5'
                },
                tooltip=folium.GeoJsonTooltip(fields=['district_name'], aliases=['Sanitary District:'])
            ).add_to(ssa_layer)
            ssa_layer.add_to(m)

        # Layer 3 Toggle Component: High-Value Pipeline Acquisition Targets
        if not gdf_targets.empty:
            target_layer = folium.FeatureGroup(name="Development Targets (Ag + Utilities + Future Res)", show=True)
            
            # Intercept feature properties and bind custom formatting to target polygons
            for _, row in gdf_targets.iterrows():
                # Formulate structural tooltip popup formatting blocks
                popup_html = f"""
                <div style="font-family: Arial, sans-serif; min-width: 220px; font-size: 12px;">
                    <h4 style="margin: 0 0 8px 0; color: #2c3e50; border-bottom: 1px solid #ccc; padding-bottom: 4px;">Target Parcel</h4>
                    <b>APN:</b> {row['apn']}<br>
                    <b>Owner:</b> {row['owner_name']}<br>
                    <b>Address:</b> {row['owner_address']}<br>
                    <b>Size:</b> {float(row['acres']):.2f} Acres<br>
                    <b>Assessed Value:</b> ${float(row['assessed_value']):,.2f}<br>
                    <b style="color: #27ae60;">Future Comp Plan:</b> {row['future_designation']}
                </div>
                """
                
                folium.GeoJson(
                    row['geometry'].__geo_interface__,
                    style_function=lambda x: {
                        'fillColor': '#2ecc71', # Neon Green highlight indicator fill
                        'color': '#27ae60',
                        'weight': 1.5,
                        'fillOpacity': 0.6
                    },
                    highlight_function=lambda x: {'fillOpacity': 0.85, 'weight': 3.0},
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(target_layer)
                
            target_layer.add_to(m)

        # Tie complete interface layer collection back into standard Layer Control toggle button
        folium.LayerControl(position='topright').add_to(m)

        map_path = os.path.join(self.output_dir, "map.html")
        m.save(map_path)
        print(f"[+] Interactive UI Cartography map generated at: {map_path}")
        return map_path

    def run_all(self):
        """Executes full workflow sequence sequentially."""
        self.export_mailing_list()
        self.generate_interactive_map()
        print("[+] GIS Cartographer execution sequence completed.")

if __name__ == "__main__":
    cartographer = GISCartographer()
    cartographer.run_all()