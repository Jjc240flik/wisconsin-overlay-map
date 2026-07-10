#!/usr/bin/env python3
"""
North Star Subdivision Extraction Pipeline
Queries Land Portal API for all HIGH and Moderate-to-High municipalities
across the TOP 10 Wisconsin counties.
"""
import json
import requests
import time
import os
from collections import Counter
from datetime import datetime

API_KEY = "lp_live_z5k-VLjQn5gVOnb0NuTLG-rxJ1jtZy7G"
BASE_URL = "https://api.landportal.com"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
OUTPUT_DIR = "/root/wisconsin-overlay-map/output/subdivision_leads"

# County FIPS codes
COUNTY_FIPS = {
    "Outagamie": "55087",
    "Brown": "55009",
    "Dane": "55025",
    "Waukesha": "55133",
    "Ozaukee": "55089",
    "Milwaukee": "55079",
    "Rock": "55105",
    "Winnebago": "55139",
    "Calumet": "55015",
    "Door": "55029"
}

# Target municipalities: {county: {municipality: {zip, growth_rating, type, notes}}}
TARGETS = {
    "Outagamie": {
        "Greenville": {"zip": "54942", "rating": "High", "type": "Village", "notes": "PRIMARY GROWTH. Textbooks Cody Bjugan target. FLU map, water/wastewater master plans, 7 sub-area plans."},
        "Grand Chute": {"zip": "54913", "rating": "High", "type": "Town", "notes": "Surrounds Appleton. Fox River Mall corridor. US 41 growth spine."},
        "Harrison_Village": {"zip": "54956", "rating": "High", "type": "Village", "notes": "East of Appleton along US 10. Major planned residential expansion."},
        "Combined Locks": {"zip": "54113", "rating": "High", "type": "Village", "notes": "Adjacent to Kaukauna. Fox Cities metro core. Sewer/water infrastructure."},
        "Little Chute": {"zip": "54140", "rating": "High", "type": "Village", "notes": "Fox Cities metro core. Strong growth pressure from metro expansion."},
        "Buchanan": {"zip": "54130", "rating": "Moderate to High", "type": "Town", "notes": "Surrounds Kaukauna. In path of outward expansion."},
        "Freedom": {"zip": "54966", "rating": "Moderate to High", "type": "Town", "notes": "SW of Appleton. Adjacent to city limits. Check FLU + sewer."},
        "Kimberly": {"zip": "54136", "rating": "Moderate to High", "type": "Village", "notes": "Fox Cities core. Limited land but infill potential."},
    },
    "Brown": {
        "Ashwaubenon": {"zip": "54313", "rating": "High", "type": "Village", "notes": "Adjacent to Green Bay. I-41 corridor. Sports/entertainment. Sewer/water."},
        "Howard": {"zip": "54313", "rating": "High", "type": "Village", "notes": "North of Green Bay. Significant residential/commercial development ongoing."},
        "Suamico": {"zip": "54313", "rating": "High", "type": "Village", "notes": "North of Howard. New subdivisions actively built."},
        "Bellevue": {"zip": "54311", "rating": "High", "type": "Village", "notes": "East of Green Bay. Steady residential growth."},
        "Ledgeview": {"zip": "54115", "rating": "High", "type": "Town", "notes": "Fastest growing area. Near Green Bay and De Pere."},
        "Lawrence": {"zip": "54115", "rating": "High", "type": "Town", "notes": "Strong growth near De Pere. Good I-41/I-43 access."},
        "Allouez": {"zip": "54301", "rating": "Moderate to High", "type": "Village", "notes": "Adjacent to Green Bay. Mostly built out. Infill/redevelopment."},
        "Humboldt": {"zip": "54115", "rating": "Moderate to High", "type": "Town", "notes": "East of Green Bay. Edge-growth potential."},
        "Scott": {"zip": "54313", "rating": "Moderate to High", "type": "Town", "notes": "Near Howard. Growth along major roads."},
    },
    "Dane": {
        "Fitchburg": {"zip": "53711", "rating": "High", "type": "City", "notes": "South of Madison. Major residential development. Sewer/water expanding."},
        "Verona": {"zip": "53593", "rating": "High", "type": "City", "notes": "Epic Systems corridor. Massive residential demand."},
        "Sun Prairie Town": {"zip": "53590", "rating": "High", "type": "Town", "notes": "Surrounds City of Sun Prairie. FLU shows residential expansion."},
        "Westport": {"zip": "53562", "rating": "High", "type": "Town", "notes": "Between Middleton and Lake Mendota. High pressure for residential."},
        "Springfield": {"zip": "53562", "rating": "High", "type": "Town", "notes": "North of Middleton near Waunakee corridor."},
        "Burke": {"zip": "53590", "rating": "High", "type": "Town", "notes": "Between Madison and Sun Prairie. Directly in growth path."},
        "Blooming Grove": {"zip": "53716", "rating": "High", "type": "Town", "notes": "East of Madison. Strong development pressure."},
        "Pleasant Springs": {"zip": "53558", "rating": "Moderate to High", "type": "Town", "notes": "South of Madison near McFarland."},
        "Dunn": {"zip": "53593", "rating": "Moderate to High", "type": "Town", "notes": "SW of Madison. Edge growth near Fitchburg/Verona."},
        "Montrose": {"zip": "53575", "rating": "Moderate to High", "type": "Town", "notes": "SE of Oregon. Edge-growth potential."},
        "Oregon": {"zip": "53575", "rating": "Moderate to High", "type": "Village", "notes": "Growing SW metro community. FLU and sewer available."},
        "McFarland": {"zip": "53558", "rating": "Moderate to High", "type": "Village", "notes": "SE of Madison on Lake Waubesa."},
        "Waunakee": {"zip": "53597", "rating": "Moderate to High", "type": "Village", "notes": "NW metro. Strong growth pressure."},
        "DeForest": {"zip": "53532", "rating": "Moderate to High", "type": "Village", "notes": "North metro along I-39/90/94. Expanding rapidly."},
        "Windsor": {"zip": "53598", "rating": "Moderate to High", "type": "Village", "notes": "North metro. Growing with DeForest corridor."},
        "Bristol": {"zip": "53590", "rating": "Moderate to High", "type": "Town", "notes": "North of Sun Prairie. Edge growth."},
    },
    "Waukesha": {
        "Menomonee Falls": {"zip": "53051", "rating": "High", "type": "Village", "notes": "NE edge near Milwaukee. Strong residential/commercial expansion."},
        "Lisbon": {"zip": "53089", "rating": "High", "type": "Town", "notes": "Between Menomonee Falls and Pewaukee. FLU shows residential."},
        "Genesee": {"zip": "53186", "rating": "High", "type": "Town", "notes": "Near Waukesha/Milwaukee edge."},
        "Pewaukee Village": {"zip": "53072", "rating": "High", "type": "Village", "notes": "I-94 corridor. Growing rapidly."},
        "Sussex": {"zip": "53089", "rating": "High", "type": "Village", "notes": "Between Waukesha and Menomonee Falls."},
        "Waukesha Town": {"zip": "53186", "rating": "High", "type": "Town", "notes": "Directly adjacent to city."},
        "Brookfield Town": {"zip": "53005", "rating": "High", "type": "Town", "notes": "Adjacent to both cities."},
        "Lannon": {"zip": "53046", "rating": "Moderate to High", "type": "Village", "notes": "Near Menomonee Falls. Edge growth."},
    },
    "Ozaukee": {
        "Mequon": {"zip": "53092", "rating": "High", "type": "City", "notes": "Southern edge adjacent to Milwaukee County. High-value residential."},
        "Grafton Village": {"zip": "53024", "rating": "High", "type": "Village", "notes": "I-43 corridor. Growing commercial and residential."},
        "Saukville": {"zip": "53080", "rating": "High", "type": "Village", "notes": "I-43 north. Expansion potential."},
        "Cedarburg Town": {"zip": "53012", "rating": "High", "type": "Town", "notes": "Directly adjacent to cities. FLU likely shows residential."},
        "Cedarburg City": {"zip": "53012", "rating": "Moderate to High", "type": "City", "notes": "I-43 corridor. Growing bedroom community."},
        "Grafton Town": {"zip": "53024", "rating": "Moderate to High", "type": "Town", "notes": "I-43 corridor edge."},
    },
    "Milwaukee": {
        "Franklin": {"zip": "53132", "rating": "Moderate", "type": "City", "notes": "MOST GREENFIELD POTENTIAL in county. Southern edge with undeveloped land."},
        "Oak Creek": {"zip": "53154", "rating": "Moderate", "type": "City", "notes": "SECOND MOST GREENFIELD. SE edge near airport. Growth corridor."},
    },
    "Rock": {
        "Beloit Town": {"zip": "53511", "rating": "High", "type": "Town", "notes": "Adjacent to City of Beloit and Illinois line. Stateline corridor."},
        "Janesville Town": {"zip": "53545", "rating": "High", "type": "Town", "notes": "Surrounds Janesville. FLU shows residential."},
        "Turtle": {"zip": "53511", "rating": "High", "type": "Town", "notes": "Southern edge near Beloit. Stateline growth corridor."},
        "Harmony": {"zip": "53511", "rating": "Moderate to High", "type": "Town", "notes": "East of Janesville. Edge growth."},
        "Evansville": {"zip": "53536", "rating": "Moderate to High", "type": "Village", "notes": "North metro. Growing bedroom community."},
        "Milton Town": {"zip": "53563", "rating": "Moderate to High", "type": "Town", "notes": "Near City of Milton. Edge growth."},
        "Fulton": {"zip": "53534", "rating": "Moderate to High", "type": "Town", "notes": "NE of Janesville. Edge growth potential."},
    },
    "Winnebago": {
        "Neenah Town": {"zip": "54956", "rating": "High", "type": "Town", "notes": "Adjacent to Neenah/Menasha. FLU shows residential."},
        "Menasha Town": {"zip": "54952", "rating": "High", "type": "Town", "notes": "Surrounds Menasha. Edge growth."},
        "Oshkosh Town": {"zip": "54901", "rating": "High", "type": "Town", "notes": "South of Oshkosh. US 41 corridor."},
        "Algoma": {"zip": "54901", "rating": "High", "type": "Town", "notes": "North of Oshkosh. US 41 corridor."},
        "Vinland": {"zip": "54956", "rating": "Moderate to High", "type": "Town", "notes": "North of Neenah. Edge growth potential."},
        "Clayton": {"zip": "54956", "rating": "Moderate to High", "type": "Town", "notes": "SW of Neenah. Some growth."},
        "Fox Crossing": {"zip": "54956", "rating": "Moderate to High", "type": "Village", "notes": "Between Neenah and Menasha. Growing."},
    },
    "Calumet": {
        "Harrison Town": {"zip": "54956", "rating": "High", "type": "Town", "notes": "South of Appleton metro. US 41/10 corridor."},
        "Menasha Calumet": {"zip": "54952", "rating": "High", "type": "Town", "notes": "Adjacent to Menasha/Appleton. Fox Cities edge."},
        "Stockbridge": {"zip": "53088", "rating": "Moderate to High", "type": "Town", "notes": "Lake Winnebago shoreline. Growing."},
        "Brothertown": {"zip": "53014", "rating": "Moderate to High", "type": "Town", "notes": "Lakeshore. Seasonal and year-round."},
    },
    "Door": {
        "Sister Bay": {"zip": "54234", "rating": "Moderate to High", "type": "Village", "notes": "Key tourism corridor. Seasonal growth. Limited subdivision potential vs metro counties."},
    },
}


def should_keep_owner(owner_name):
    """Filter owners: keep individuals and Farm LLCs, exclude trusts, LLCs, INC, govt."""
    if not owner_name:
        return False
    
    upper = owner_name.upper().strip()
    
    # EXCLUDE: Government/tribal
    exclude_patterns = [
        "COUNTY", "TOWNSHIP", "CITY OF", "STATE OF", "UNITED STATES",
        "NATION ", "TRIBE", "TOWN OF", "VILLAGE OF", "DEPT OF",
        "DEPARTMENT", "DNR", "DOT", "SCHOOL DISTRICT", "SANITARY DISTRICT",
    ]
    for p in exclude_patterns:
        if p in upper:
            return False
    
    # EXCLUDE: Trusts
    if "TRUST" in upper:
        return False
    
    # EXCLUDE: INC/INCORPORATED (unless it's just part of a name like "INC")
    if " INC" in upper or " INC." in upper or "INCORPORATED" in upper or " CORP" in upper or " CORPORATION" in upper:
        return False
    
    # LLC handling: KEEP if "FARM" in name, otherwise EXCLUDE
    if "LLC" in upper or "L L C" in upper or "LIMITED LIABILITY" in upper:
        if "FARM" in upper:
            return True  # Farm LLCs are OK
        return False  # All other LLCs excluded
    
    # EXCLUDE: Industrial holders
    industrial_patterns = ["ASPHALT", "QUARRY", "GRAVEL", "CONCRETE", "MINING", "SAND &"]
    for p in industrial_patterns:
        if p in upper:
            return False
    
    # EXCLUDE: Banks, lenders, churches
    bank_patterns = ["BANK", "CREDIT UNION", "CHURCH", "DIOCESE", "ARCHDIOCESE"]
    for p in bank_patterns:
        if p in upper:
            return False
    
    # KEEP: Individual names
    return True


def query_filter_data(fips, zip_code, page_token=None):
    """Query Land Portal filter-data endpoint."""
    filters = [
        {"key": "situszip5", "operator": "condition", "value": zip_code},
        {"key": "lotsizeacres", "operator": "range", "value": {"min": 20, "max": 300}},
        {"key": "vacant", "operator": "boolean", "value": True},
        {"key": "road_frontage", "operator": "range", "value": {"min": 400}},
        {"key": "wetlands_cover_percentage", "operator": "range", "value": {"max": 30}},
        {"key": "fema_cover_percentage", "operator": "range", "value": {"max": 50}},
    ]
    
    payload = {
        "fips": [fips],
        "filters": filters,
    }
    
    url = f"{BASE_URL}/v2/filter-data"
    if page_token:
        url += f"?page_token={page_token}"
    
    try:
        resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"  ERROR {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"  EXCEPTION: {e}")
        return None


def get_property_detail(property_id):
    """Get full property detail."""
    try:
        resp = requests.get(f"{BASE_URL}/v2/properties/{property_id}", headers=HEADERS, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        return None


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    all_results = {}  # county -> list of properties
    total_queried = 0
    total_filtered = 0
    
    # Deduplicate ZIPs per county
    for county, municipalities in TARGETS.items():
        fips = COUNTY_FIPS[county]
        print(f"\n{'='*60}")
        print(f"COUNTY: {county} (FIPS: {fips})")
        print(f"{'='*60}")
        
        # Get unique ZIPs for this county
        zip_muni_map = {}  # zip -> [muni_names]
        for muni_name, info in municipalities.items():
            z = info["zip"]
            if z not in zip_muni_map:
                zip_muni_map[z] = []
            zip_muni_map[z].append((muni_name, info))
        
        county_results = []
        
        for zip_code, muni_list in zip_muni_map.items():
            muni_names = [m[0] for m in muni_list]
            muni_ratings = {m[0]: m[1]["rating"] for m in muni_list}
            muni_notes = {m[0]: m[1]["notes"] for m in muni_list}
            best_rating = "High" if any(r == "High" for r in muni_ratings.values()) else \
                          "Moderate to High" if any(r == "Moderate to High" for r in muni_ratings.values()) else \
                          "Moderate"
            
            print(f"\n  ZIP: {zip_code} -> {', '.join(muni_names)} (Best: {best_rating})")
            
            # Query first page
            result = query_filter_data(fips, zip_code)
            if not result:
                continue
            
            data = result.get("data", {})
            properties = data.get("properties", [])
            count = data.get("count", 0)
            next_token = data.get("next_page_token", "")
            
            print(f"    Total: {count}, Page: {len(properties)}")
            
            # Paginate if needed
            all_properties = list(properties)
            page_num = 1
            while next_token:
                page_num += 1
                result = query_filter_data(fips, zip_code, next_token)
                if not result:
                    break
                data = result.get("data", {})
                more_props = data.get("properties", [])
                next_token = data.get("next_page_token", "")
                all_properties.extend(more_props)
                print(f"    Page {page_num}: +{len(more_props)} (total: {len(all_properties)})")
                time.sleep(0.5)  # Rate limit respect
            
            total_queried += len(all_properties)
            
            # Filter owners
            kept = []
            for p in all_properties:
                owner = p.get("owner_full_name", "")
                if should_keep_owner(owner):
                    # Determine which municipality this parcel is in
                    # For now, assign to the first matching municipality
                    p["_municipality"] = muni_names[0]  # Best guess; would need geocoding for precision
                    p["_rating"] = best_rating
                    p["_county"] = county
                    p["_zip"] = zip_code
                    p["_muni_notes"] = muni_notes.get(muni_names[0], "")
                    kept.append(p)
            
            filtered = len(all_properties) - len(kept)
            total_filtered += len(kept)
            print(f"    Kept: {len(kept)} (filtered out: {filtered})")
            
            county_results.extend(kept)
            time.sleep(1)  # Rate limit between ZIPs
        
        all_results[county] = county_results
    
    print(f"\n{'='*60}")
    print(f"TOTAL QUERIED: {total_queried}")
    print(f"TOTAL FILTERED (kept): {total_filtered}")
    print(f"{'='*60}")
    
    # Now separate into for-sale vs off-market
    # For now, we don't have MLS data embedded in filter-data results directly
    # We'll need to check each property for MLS listing status
    # For the initial run, separate by examining property details and MLS indicators
    
    # Save raw data
    raw_path = os.path.join(OUTPUT_DIR, "raw_filtered_results.json")
    with open(raw_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nRaw results saved to: {raw_path}")
    
    # Build the two lists
    off_market = []
    for_sale = []
    
    # Check each property for MLS status via detail endpoint
    print("\nChecking MLS status for filtered properties...")
    for county, props in all_results.items():
        print(f"\n  {county}: {len(props)} properties")
        for i, p in enumerate(props):
            pid = p.get("property_id")
            if not pid:
                continue
            
            detail = get_property_detail(pid)
            if not detail:
                continue
            
            dprops = detail.get("data", {}).get("properties", {})
            
            # Check for MLS listing indicators
            mls_status = dprops.get("mls_status", "")
            current_sale_price = dprops.get("current_sale_price", 0)
            listing_status = dprops.get("listing_status", "")
            land_use = dprops.get("land_use_description", "")
            zoning = dprops.get("zoning", "")
            legal = dprops.get("legal_description", "")
            assessed_value = dprops.get("assessed_total_value", 0)
            latitude = dprops.get("latitude", 0)
            longitude = dprops.get("longitude", 0)
            
            entry = {
                "property_id": pid,
                "apn": p.get("apn", ""),
                "address": p.get("street_address", ""),
                "owner": p.get("owner_full_name", ""),
                "acres": p.get("lot_size_acres", 0),
                "county": county,
                "municipality": p.get("_municipality", ""),
                "zip": p.get("_zip", ""),
                "growth_rating": p.get("_rating", ""),
                "muni_notes": p.get("_muni_notes", ""),
                "land_use": land_use,
                "zoning": zoning,
                "assessed_value": assessed_value,
                "latitude": latitude,
                "longitude": longitude,
                "mls_status": mls_status,
                "sale_price": current_sale_price,
                "listing_status": listing_status,
            }
            
            if mls_status and mls_status.lower() in ("active", "for sale", "pending"):
                for_sale.append(entry)
            elif listing_status and listing_status.lower() in ("active", "for sale", "pending"):
                for_sale.append(entry)
            elif current_sale_price and current_sale_price > 0:
                for_sale.append(entry)
            else:
                off_market.append(entry)
            
            if (i + 1) % 20 == 0:
                print(f"    Processed {i+1}/{len(props)}...")
                time.sleep(0.5)
            
            time.sleep(0.3)  # Rate limit for detail calls
    
    # Find multi-property owners in off-market
    owner_counts = Counter(e["owner"] for e in off_market if e["owner"])
    multi_owners = {owner: count for owner, count in owner_counts.items() if count >= 2}
    
    # Tag multi-property owners
    for entry in off_market:
        if entry["owner"] in multi_owners:
            entry["multi_property"] = True
            entry["owner_parcel_count"] = multi_owners[entry["owner"]]
        else:
            entry["multi_property"] = False
            entry["owner_parcel_count"] = 1
    
    for entry in for_sale:
        if entry["owner"] in multi_owners:
            entry["multi_property"] = True
            entry["owner_parcel_count"] = multi_owners[entry["owner"]]
        else:
            entry["multi_property"] = False
            entry["owner_parcel_count"] = 1
    
    # Save final results
    final = {
        "generated": datetime.now().isoformat(),
        "summary": {
            "total_queried": total_queried,
            "total_filtered": total_filtered,
            "off_market_count": len(off_market),
            "for_sale_count": len(for_sale),
            "multi_property_owners": len(multi_owners),
        },
        "off_market": off_market,
        "for_sale": for_sale,
        "multi_property_owners": {owner: count for owner, count in multi_owners.items()},
    }
    
    final_path = os.path.join(OUTPUT_DIR, "subdivision_leads.json")
    with open(final_path, "w") as f:
        json.dump(final, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"  Off-Market: {len(off_market)}")
    print(f"  For Sale: {len(for_sale)}")
    print(f"  Multi-Property Owners: {len(multi_owners)}")
    print(f"  Saved to: {final_path}")
    print(f"{'='*60}")
    
    # Print county breakdown
    print("\nCounty Breakdown:")
    for county in COUNTY_FIPS:
        om = len([e for e in off_market if e["county"] == county])
        fs = len([e for e in for_sale if e["county"] == county])
        print(f"  {county}: {om} off-market, {fs} for-sale = {om+fs} total")

if __name__ == "__main__":
    main()