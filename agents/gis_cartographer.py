#!/usr/bin/env python3
"""
GIS Cartographer Agent (Improved)
- Better sample data
- Cleaner popup structure
- Ready for real parcel data
"""

import os
import folium
from folium import LayerControl
import geopandas as gpd
from dotenv import load_dotenv

load_dotenv()

def create_interactive_map(county_name: str, output_html: str = "brown_county_map.html"):
    print(f"Generating improved Folium map for {county_name}")

    m = folium.Map(location=[44.52, -88.0], zoom_start=11, tiles=None)

    # Base Layer - Satellite
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Satellite Imagery",
        overlay=False
    ).add_to(m)

    # Middle Layer - Sample Parcels (improved)
    parcels_fg = folium.FeatureGroup(name="Parcels & Current Zoning", show=True)

    sample_data = [
        {"apn": "B-45231", "owner": "Smith Family LLC", "acres": 47.2, "zoning": "AG-1", "future": "Future Residential Transition", "lat": 44.48, "lon": -88.05},
        {"apn": "B-45232", "owner": "Johnson Farms Inc", "acres": 89.5, "zoning": "AG-2", "future": "Urban Expansion Area", "lat": 44.51, "lon": -87.95},
        {"apn": "B-45233", "owner": "Green Acres Trust", "acres": 23.8, "zoning": "RR-1", "future": "Future Residential", "lat": 44.45, "lon": -88.12},
        {"apn": "B-45234", "owner": "North Star Holdings", "acres": 64.1, "zoning": "AG-1", "future": "Future Residential Transition", "lat": 44.49, "lon": -88.08},
    ]

    for p in sample_data:
        popup_html = f"""
        <b>APN:</b> {p['apn']}<br>
        <b>Owner:</b> {p['owner']}<br>
        <b>Acres:</b> {p['acres']}<br>
        <b>Current Zoning:</b> {p['zoning']}<br>
        <b>Future Designation:</b> {p['future']}<br>
        <b>Distance to Sewer:</b> ~1,800 ft<br>
        <b>Distance to Water:</b> ~2,400 ft
        """
        folium.CircleMarker(
            location=[p['lat'], p['lon']],
            radius=9,
            popup=folium.Popup(popup_html, max_width=320),
            color="#3388ff",
            fill=True,
            fill_opacity=0.75
        ).add_to(parcels_fg)

    parcels_fg.add_to(m)

    # Top Layer - Future Infrastructure (sample)
    future_fg = folium.FeatureGroup(name="Future Zoning & Utilities", show=True)
    folium.PolyLine(
        [[44.50, -88.10], [44.52, -88.05]],
        color="red",
        weight=3,
        popup="Proposed Water Main Extension (2040 Plan)"
    ).add_to(future_fg)
    future_fg.add_to(m)

    LayerControl(collapsed=False).add_to(m)
    m.save(output_html)
    print(f"Improved Folium map saved: {output_html}")


if __name__ == "__main__":
    create_interactive_map("Brown")