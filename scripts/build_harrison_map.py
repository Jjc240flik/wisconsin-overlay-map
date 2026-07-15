import json
from collections import defaultdict

# Load Harrison FLU data
with open('/root/.hermes/harrison_flu.geojson') as f:
    harrison_data = json.load(f)

# Load county PLU data
with open('/root/.hermes/calumet_county_plu.geojson') as f:
    county_data = json.load(f)

# Separate Village vs County parcels
village_parcels = []
town_parcels = []

for feat in harrison_data['features']:
    props = feat['properties']
    muni = str(props.get('muni','')).upper()
    if 'TOWN' in muni:
        town_parcels.append(feat)
    else:
        village_parcels.append(feat)

# Find Town of Harrison parcels in county PLU
town_plu = []
for feat in county_data['features']:
    props = feat['properties']
    muni = str(props.get('MUNI','')).upper()
    if 'HARRISON' in muni and 'TOWN' in muni:
        town_plu.append(feat)

print(f"Village parcels: {len(village_parcels)}")
print(f"Town parcels (from Harrison FLU): {len(town_parcels)}")
print(f"Town parcels (from County PLU): {len(town_plu)}")

# Calculate Village boundary for proximity check
import math

def get_centroid(feat):
    geom = feat.get('geometry',{})
    coords = []
    if geom.get('type') == 'Polygon':
        coords = geom['coordinates'][0]
    elif geom.get('type') == 'MultiPolygon':
        for ring in geom['coordinates']:
            coords.extend(ring[0])
    if not coords:
        return (0,0)
    x = sum(c[0] for c in coords) / len(coords)
    y = sum(c[1] for c in coords) / len(coords)
    return (x, y)

def distance_miles(p1, p2):
    # Simple lat/lon distance
    lat1, lon1 = p1[1], p1[0] if abs(p1[1]) < 90 else (p1[0], p1[1])
    lat2, lon2 = p2[1], p2[0] if abs(p2[1]) < 90 else (p2[0], p2[1])
    # WI is roughly at 44N, so 1 degree lat ≈ 69 miles, 1 degree lon ≈ 69*cos(44) ≈ 49.6 miles
    dlat = abs(lat2 - lat1) * 69.0
    dlon = abs(lon2 - lon1) * 49.6
    return math.sqrt(dlat**2 + dlon**2)

# Get all village geometry coordinates for boundary check
village_coords = []
for feat in village_parcels:
    geom = feat.get('geometry',{})
    if geom.get('type') == 'Polygon':
        village_coords.extend(geom['coordinates'][0])
    elif geom.get('type') == 'MultiPolygon':
        for ring in geom['coordinates']:
            village_coords.extend(ring[0])

# Find min/max of village boundary
vx = [c[0] for c in village_coords]
vy = [c[1] for c in village_coords]
print(f"\nVillage bounds: lon {min(vx):.4f} to {max(vx):.4f}, lat {min(vy):.4f} to {max(vy):.4f}")

# Now build the Leaflet map HTML
# Color mapping for FLU designations
colors = {
    'Low Density Residential': '#a6cee3',
    'Medium Density Residential': '#1f78b4',
    'High Density Residential': '#b2df8a',
    'Agriculture': '#33a02c',
    'Commercial': '#fb9a99',
    'Industrial': '#e31a1c',
    'Mixed Use': '#ff7f00',
    'Transitional Residential': '#ffff99',
    'Rural Residential': '#b15928',
    'Preservation and Open Space': '#6a3d9a',
    'Parks and Recreation': '#cab2d6',
    'Public and Institutional': '#fdb863',
    'A': '#33a02c',
    'LDR': '#a6cee3',
    'MDR': '#1f78b4',
    'C': '#fb9a99',
    'I': '#e31a1c',
    'MU': '#ff7f00',
    'TR': '#ffff99',
    'RR': '#b15928',
    'POS': '#6a3d9a',
    'PR': '#cab2d6',
    'PI': '#fdb863',
}

html = '''<!DOCTYPE html>
<html>
<head>
<title>Harrison - Target Area Map</title>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
  body { margin:0; padding:0; }
  #map { width:100%; height:100vh; }
  .legend { background:white; padding:10px; border-radius:5px; line-height:1.5; }
  .legend i { width:18px; height:18px; float:left; margin-right:8px; opacity:0.8; border:1px solid #999; }
  .info { padding:6px 8px; background:white; border-radius:5px; box-shadow:0 0 15px rgba(0,0,0,0.2); }
</style>
</head>
<body>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('map').setView([44.19, -88.33], 13);
L.tileLayer('https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
  maxZoom: 20, subdomains: ['mt0','mt1','mt2','mt3'],
  attribution: '&copy; Google'
}).addTo(map);

var colorMap = ''' + json.dumps(colors) + ''';

// Village of Harrison FLU parcels
var villageData = ''' + json.dumps([{
    'type': 'Feature',
    'properties': f['properties'],
    'geometry': f['geometry']
} for f in village_parcels[:1000]]) + ''';

var villLayer = L.geoJSON(villageData, {
  style: function(f) {
    var plu = f.properties.PreferredLandUse || 'Agriculture';
    return {color: colorMap[plu] || '#ccc', weight: 1, fillOpacity: 0.5};
  },
  onEachFeature: function(f, layer) {
    var p = f.properties;
    layer.bindPopup('<b>' + (p.physadd || 'Parcel') + '</b><br>' +
      'FLU: ' + (p.PreferredLandUse || '?') + '<br>' +
      'Acres: ' + (p.totparacre || '?') + '<br>' +
      'Muni: ' + (p.muni || '?'));
  }
}).addTo(map);

// Town of Harrison parcels from County PLU
var townData = ''' + json.dumps([{
    'type': 'Feature',
    'properties': f['properties'],
    'geometry': f['geometry']
} for f in town_plu[:500]]) + ''';

var townLayer = L.geoJSON(townData, {
  style: function(f) {
    var cat = f.properties.PLU_CATEGORY || 'Agricultural';
    return {color: '#33a02c', weight: 2, fillOpacity: 0.3, dashArray: '5,5'};
  },
  onEachFeature: function(f, layer) {
    var p = f.properties;
    layer.bindPopup('<b>Town of Harrison</b><br>' +
      'PLU: ' + (p.PLU_CATEGORY || '?') + '<br>' +
      'Muni: ' + (p.MUNI || '?'));
  }
}).addTo(map);

// Legend
var legend = L.control({position: 'bottomright'});
legend.onAdd = function(map) {
  var div = L.DomUtil.create('div', 'legend');
  div.innerHTML = '<b>Village Harrison FLU (Adopted 7/2025)</b><br>';
  var items = [
    ['Low Density Residential', '#a6cee3'],
    ['Medium Density Residential', '#1f78b4'],
    ['Agriculture', '#33a02c'],
    ['Commercial', '#fb9a99'],
    ['Transitional Residential', '#ffff99'],
    ['Rural Residential', '#b15928'],
  ];
  for (var i=0; i<items.length; i++) {
    div.innerHTML += '<i style="background:' + items[i][1] + '"></i>' + items[i][0] + '<br>';
  }
  div.innerHTML += '<hr><i style="background:#33a02c;border:dashed"></i>Town Harrison (County PLU)<br>';
  return div;
};
legend.addTo(map);

// 0.5 mile buffer zone around Village (target area)
L.circle([44.19, -88.33], {radius: 804, color:'#ff0000', weight:2, fillOpacity:0, dashArray:'10,10'})
  .bindPopup('0.5 mile zone from Village center<br>AG→Residential eligible per County plan')
  .addTo(map);

L.control.scale({imperial:true}).addTo(map);

var title = L.control({position:'topleft'});
title.onAdd = function(map) {
  var div = L.DomUtil.create('div', 'info');
  div.innerHTML = '<h3 style="margin:0">🎯 Harrison Target Area</h3>Village FLU + Town AG parcels<br>Red: 0.5mi conversion zone';
  return div;
};
title.addTo(map);
</script>
</body>
</html>
'''

with open('/root/wisconsin-overlay-map/output/Harrison_Target_Area_Map.html', 'w') as f:
    f.write(html)

print("\nMap saved to: /root/wisconsin-overlay-map/output/Harrison_Target_Area_Map.html")
print(f"Map contains: {len(village_parcels[:1000])} village parcels + {len(town_plu[:500])} town parcels")