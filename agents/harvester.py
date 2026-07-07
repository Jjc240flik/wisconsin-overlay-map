import os
import json
import requests
from typing import Optional

class DataHarvester:
    """
    Agent 1: Data Harvester
    Pulls raw GIS vector layers for Brown County, WI from official sources.
    """

    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        # Official Brown County ArcGIS REST endpoints
        self.endpoints = {
            "base_parcels": "https://bcgis.browncountywi.gov/arcgis/rest/services/Parcels/ParcelFeatures/FeatureServer/0",
            "future_land_use": "https://bcgis.browncountywi.gov/arcgis/rest/services/Planning/FutureLandUse_2040/FeatureServer/0",  # May need adjustment
            "sewer_service_area": "https://bcgis.browncountywi.gov/arcgis/rest/services/Planning/SewerServiceArea/FeatureServer/0"   # May need adjustment
        }

    def fetch_layer(self, layer_key: str, where_clause: str = "1=1") -> Optional[str]:
        """Fetches a layer as GeoJSON with pagination support."""
        base_url = self.endpoints.get(layer_key)
        if not base_url:
            raise ValueError(f"Unknown layer: {layer_key}")

        print(f"[Harvester] Fetching: {layer_key}")

        all_features = []
        offset = 0
        page_size = 1000

        while True:
            params = {
                "where": where_clause,
                "outFields": "*",
                "f": "geojson",
                "resultOffset": offset,
                "resultRecordCount": page_size,
                "outSR": "3071"
            }

            try:
                resp = requests.get(f"{base_url}/query", params=params, timeout=90)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[-] Failed to fetch {layer_key}: {e}")
                return None

            features = data.get("features", [])
            if not features:
                break

            all_features.extend(features)
            print(f"    -> {len(all_features)} records collected")

            if len(features) < page_size:
                break

            offset += page_size

        if not all_features:
            print(f"[-] No data returned for {layer_key}")
            return None

        geojson = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::3071"}},
            "features": all_features
        }

        output_path = os.path.join(self.data_dir, f"{layer_key}.geojson")
        with open(output_path, "w") as f:
            json.dump(geojson, f)

        print(f"[+] Saved: {output_path}\n")
        return output_path

    def run_all(self):
        """Run full harvest for all three required layers."""
        # Brown County parcels (FIPS 55009)
        self.fetch_layer("base_parcels", where_clause="COUNTY = 'Brown'")
        self.fetch_layer("future_land_use")
        self.fetch_layer("sewer_service_area")
        print("[Harvester] All layers harvested.\n")