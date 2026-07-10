import requests, json, re, sys, os
from urllib.parse import urlparse

headers = {'User-Agent': 'Mozilla/5.0'}

results = {}

# === DANE COUNTY ===
print("=== DANE COUNTY ===")
# Try the Open Data portal API
try:
    r = requests.get('https://danedata.countyofdane.com/api/v2/search?q=parcels', headers=headers, timeout=15)
    if r.status_code == 200:
        data = r.json()
        print(f"  Danedata portal: {len(data)} results")
        for item in data.get('results', [])[:5]:
            print(f"    {item.get('title', '')}")
except Exception as e:
    print(f"  Danedata: {e}")

# Try ArcGIS Online search for Dane County
search_url = 'https://www.arcgis.com/sharing/rest/search'
for query in ['Dane County WI parcels feature service', 'Dane County WI zoning feature service', 'Dane County WI land use feature service']:
    try:
        params = {'f': 'json', 'q': query, 'num': 5}
        r = requests.get(search_url, params=params, headers=headers, timeout=15)
        data = r.json()
        for res in data.get('results', []):
            url = res.get('url', '')
            title = res.get('title', '')
            owner = res.get('owner', '')
            if url and 'FeatureServer' in url:
                print(f"  {query[:30]}: {title} (owner: {owner})")
                print(f"    {url}")
    except:
        pass

# === WAUKESHA COUNTY ===
print("\n=== WAUKESHA COUNTY ===")
# Waukesha County has org ID: 5mNcDbMaBDRgBsIc
wc_url = 'https://services.arcgis.com/5mNcDbMaBDRgBsIc/arcgis/rest/services?f=json'
try:
    r = requests.get(wc_url, headers=headers, timeout=15)
    services = r.json().get('services', [])
    print(f"  Waukesha ArcGIS services: {len(services)}")
    for s in services:
        name = s.get('name', '')
        if any(kw in name.lower() for kw in ['parcel', 'zoning', 'land', 'municipal', 'future']):
            print(f"    {name} [{s.get('type')}]")
except Exception as e:
    print(f"  Error: {e}")

# === OZAUKEE COUNTY ===
print("\n=== OZAUKEE COUNTY ===")
# Search for Ozaukee on ArcGIS Online
for query in ['Ozaukee County WI parcel feature service', 'Ozaukee County WI zoning feature service']:
    try:
        params = {'f': 'json', 'q': query, 'num': 5}
        r = requests.get(search_url, params=params, headers=headers, timeout=15)
        data = r.json()
        for res in data.get('results', []):
            url = res.get('url', '')
            title = res.get('title', '')
            if url and 'FeatureServer' in url:
                print(f"  {title}: {url}")
    except:
        pass

# Try direct Ozaukee GIS
try:
    r = requests.get('https://gis.co.ozaukee.wi.us/arcgis/rest/services?f=json', headers=headers, timeout=10)
    if r.status_code == 200:
        services = r.json().get('services', [])
        print(f"  Ozaukee GIS server: {len(services)} services")
        for s in services[:15]:
            print(f"    {s.get('name')} [{s.get('type')}]")
except:
    print("  No direct GIS server found")

# === MILWAUKEE COUNTY ===
print("\n=== MILWAUKEE COUNTY ===")
# Milwaukee County - try their GIS
for url in ['https://county.milwaukee.gov/EN/Infrastructure/Technology-GIS',
            'https://milwaukee.maps.arcgis.com/arcgis/rest/services?f=json']:
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            print(f"  {url}: {r.status_code}")
    except:
        pass

for query in ['Milwaukee County WI land use feature service', 'Milwaukee County WI zoning feature service']:
    try:
        params = {'f': 'json', 'q': query, 'num': 5}
        r = requests.get(search_url, params=params, headers=headers, timeout=15)
        for res in r.json().get('results', []):
            url = res.get('url', '')
            title = res.get('title', '')
            if url and 'FeatureServer' in url:
                print(f"  {title}: {url}")
    except:
        pass

# === ROCK COUNTY ===
print("\n=== ROCK COUNTY ===")
# Rock County has a GIS server - try it
for url in ['https://rockgis.co.rock.wi.us:8443/rockpub/rest/services?f=json',
            'https://rockgis.co.rock.wi.us/arcgis/rest/services?f=json']:
    try:
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        if r.status_code == 200:
            services = r.json().get('services', [])
            print(f"  Rock GIS: {len(services)} services")
            for s in services:
                name = s.get('name', '')
                if any(kw in name.lower() for kw in ['parcel', 'zoning', 'land', 'municipal', 'future', 'general']):
                    print(f"    {name} [{s.get('type')}]")
    except Exception as e:
        print(f"  {url}: {e}")

# === WINNEBAGO COUNTY ===
print("\n=== WINNEBAGO COUNTY ===")
for query in ['Winnebago County WI parcel feature service', 'Winnebago County WI zoning']:
    try:
        params = {'f': 'json', 'q': query, 'num': 5}
        r = requests.get(search_url, params=params, headers=headers, timeout=15)
        for res in r.json().get('results', []):
            url = res.get('url', '')
            title = res.get('title', '')
            if url and ('FeatureServer' in url or 'MapServer' in url):
                print(f"  {title}: {url}")
    except:
        pass

# Try Winnebago County site
try:
    r = requests.get('https://www.winnebagocountywi.gov/Departments/GIS', headers=headers, timeout=10)
    print(f"  Winnebago GIS page: {r.status_code}")
except:
    pass

# === CALUMET COUNTY ===
print("\n=== CALUMET COUNTY ===")
# Calumet shares Land Use 2015 data with Winnebago
lu_url = 'https://services6.arcgis.com/gI7hlABYSIIozaRg/arcgis/rest/services/Land_Use_2015/FeatureServer/0/query'
try:
    params = {'where': '1=1', 'outFields': 'County', 'f': 'json', 'returnDistinctValues': 'true', 'returnGeometry': 'false'}
    r = requests.get(lu_url, params=params, headers=headers, timeout=15)
    for f in r.json().get('features', []):
        print(f"  Land Use 2015 covers: {f.get('attributes', {}).get('County', '')}")
except Exception as e:
    print(f"  Error: {e}")

# === DOOR COUNTY ===
print("\n=== DOOR COUNTY ===")
try:
    r = requests.get('https://www.co.door.wi.gov/193/GIS-Mapping', headers=headers, timeout=10)
    print(f"  Door GIS page: HTTP {r.status_code}")
except:
    pass

for query in ['Door County WI parcel feature service', 'Door County WI zoning']:
    try:
        params = {'f': 'json', 'q': query, 'num': 5}
        r = requests.get(search_url, params=params, headers=headers, timeout=15)
        for res in r.json().get('results', []):
            url = res.get('url', '')
            title = res.get('title', '')
            if url and 'FeatureServer' in url:
                print(f"  {title}: {url}")
    except:
        pass

print("\n=== RESEARCH COMPLETE ===")