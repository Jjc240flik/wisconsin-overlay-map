import os
import json
import requests
from typing import Optional

class DataHarvester:
    """Agent 1: Pulls raw spatial vector data layers for Brown County, WI."""

    def __init__(self, data_dir="data/raw"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        # Real public endpoints (examples - will need real Brown County open data URLs)
        self.endpoints = {
            "base_parcels": "https://services.arcgis.com/REPLACE_WITH_BROWN_COUNTY/arcgis/rest/services/Parcels/FeatureServer/0",
            "future_land_use": "https://services.arcgis.com/REPLACE_WITH_BROWN_COUNTY/arcgis/rest/services/FutureLandUse_2040/FeatureServer/0",
            "sewer_service_area": "https://services.arcgis.com/REPLACE_WITH_BROWN_COUNTY/arcgis/rest/services/SewerServiceArea/FeatureServer/0"
        }

    def fetch_layer(self, layer_key: str, where_clause: str = "1=1") -> Optional[str]:
        base_url = self.endpoints.get(layer_key)
        if not base_url:
            raise ValueError(f"Unknown layer key: {layer_key}")

        print(f"[*] Harvesting layer: {layer_key}")

        all_features = []
        result_offset = 0
        result_record_count = 1000

        while True:
            params = {
                "where": where_clause,
                "outFields": "*",
                "f": "geojson",
                "resultOffset": result_offset,
                "resultRecordCount": result_record_count,
                "outSR": "3071"
            }

            try:
                response = requests.get(f"{base_url}/query", params=params, timeout=60)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                print(f"[-] Error fetching {layer_key}: {e}")
                return None

            features = data.get("features", [])
            if not features:
                break

            all_features.extend(features)
            print(f"    -> Collected {len(all_features)} records...")

            if len(features) < result_record_count:
                break

            result_offset += result_record_count

        if not all_features:
            print(f"[-] No features returned for {layer_key}")
            return None

        geojson_out = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::3071"}},
            "features": all_features
        }

        output_path = os.path.join(self.data_dir, f"{layer_key}.geojson")
        with open(output_path, "w") as f:
            json.dump(geojson_out, f)

        print(f"[+] Saved {layer_key} → {output_path}\n")
        return output_path

    def run_all(self):
        # Brown County FIPS filter (55009)
        self.fetch_layer("base_parcels", where_clause="COUNTY_FIPS = '55009'")
        self.fetch_layer("future_land_use")
        self.fetch_layer("sewer_service_area")
        print("[+] Harvester completed.")