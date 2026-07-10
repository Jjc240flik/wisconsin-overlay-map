import json, os, warnings
warnings.filterwarnings('ignore')

# Build Door County map using MapServer image tiles
html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Door County Zoning & Parcel Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
        #map { height: 100vh; width: 100vw; }
        .toggle-container {
            position: absolute; top: 10px; left: 50%; transform: translateX(-50%);
            z-index: 1000; background: white; padding: 6px 4px;
            border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            display: flex; gap: 4px; font-size: 13px;
        }
        .toggle-btn { padding: 6px 16px; border: none; cursor: pointer; font-weight: bold; font-size: 13px; transition: 0.2s; border-radius: 6px; }
        .toggle-btn.active { background: #4CAF50; color: white; }
        .toggle-btn.inactive { background: transparent; color: #666; }
        .toggle-btn:hover:not(.active) { background: #f0f0f0; }
        .legend { background: white; padding: 10px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); font-size: 11px; line-height: 1.5; max-width: 240px; }
        .legend-item { display: flex; align-items: center; gap: 6px; }
        .legend-color { width: 12px; height: 12px; border-radius: 2px; flex-shrink: 0; }
        .note { position: absolute; bottom: 10px; right: 10px; z-index: 1000; background: rgba(255,255,255,0.85); padding: 4px 10px; border-radius: 4px; font-size: 11px; }
        .muni-label { background: none !important; border: none !important; }
        .muni-label div { box-shadow: 0 1px 4px rgba(0,0,0,0.3); }
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="toggle-container">
        <button class="toggle-btn active" id="btn-zoning" onclick="showZoning()">Zoning</button>
        <button class="toggle-btn inactive" id="btn-parcels" onclick="showParcels()">Parcels</button>
    </div>
    <div id="legend-container" class="legend" style="position:absolute;bottom:50px;left:10px;z-index:1000;">
        <b>Door County Zoning</b><br>
        <div class="legend-item"><div class="legend-color" style="background:#2196F3;opacity:0.4"></div>County Zoning Overlay</div>
        <br><i>Zoning map image from Door County GIS</i>
    </div>
    <div class="note">Door County, WI</div>

    <script>
    var map = L.map('map').setView([44.94, -87.22], 10);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {attribution: '©OSM'}).addTo(map);
    var satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {attribution: '©Esri'});
    L.control.layers({"Map": L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'), "Satellite": satellite}, null, {position:'topright'}).addTo(map);
    
    // Door County MapServer tile layers
    var zoningTile = L.tileLayer('https://gis.co.door.wi.us/arcgis/rest/services/Zoning_Map_Image/MapServer/tile/{z}/{y}/{x}', {
        opacity: 0.5, attribution: 'Door County'
    });
    var parcelTile = L.tileLayer('https://gis.co.door.wi.us/arcgis/rest/services/Parcel_Map_Image/MapServer/tile/{z}/{y}/{x}', {
        opacity: 0.6, attribution: 'Door County'
    });
    
    var currentView = 'zoning';
    zoningTile.addTo(map);
    
    function showZoning() {
        if (currentView === 'zoning') return;
        map.removeLayer(parcelTile);
        zoningTile.addTo(map);
        currentView = 'zoning';
        document.getElementById('btn-zoning').className = 'toggle-btn active';
        document.getElementById('btn-parcels').className = 'toggle-btn inactive';
        document.getElementById('legend-container').innerHTML = '<b>Door County Zoning</b><br><div class="legend-item"><div class="legend-color" style="background:#2196F3;opacity:0.4"></div>County Zoning Overlay</div><br><i>Zoning map image from Door County GIS</i>';
    }
    
    function showParcels() {
        if (currentView === 'parcels') return;
        map.removeLayer(zoningTile);
        parcelTile.addTo(map);
        currentView = 'parcels';
        document.getElementById('btn-parcels').className = 'toggle-btn active';
        document.getElementById('btn-zoning').className = 'toggle-btn inactive';
        document.getElementById('legend-container').innerHTML = '<b>Door County Parcels</b><br><div class="legend-item"><div class="legend-color" style="background:#FF9800;opacity:0.4"></div>Parcel Map Overlay</div><br><i>Parcel map image from Door County GIS</i>';
    }
    
    // Municipality Labels
    var muniData = [
        {"name":"Sturgeon Bay","rating":"Moderate","type":"City","lat":44.834,"lon":-87.377,"color":"#FFC107","size":15},
        {"name":"Sister Bay","rating":"Moderate to High","type":"Village","lat":45.188,"lon":-87.121,"color":"#8BC34A","size":14},
        {"name":"Egg Harbor","rating":"Moderate","type":"Village","lat":45.052,"lon":-87.290,"color":"#FFC107","size":13},
        {"name":"Ephraim","rating":"Low to Moderate","type":"Village","lat":45.156,"lon":-87.169,"color":"#FF9800","size":13},
        {"name":"Fish Creek","rating":"Low to Moderate","type":"Village","lat":45.128,"lon":-87.245,"color":"#FF9800","size":13},
        {"name":"Forestville","rating":"Low","type":"Village","lat":44.690,"lon":-87.470,"color":"#F44336","size":12},
        {"name":"Nasewaupee","rating":"Moderate","type":"Town","lat":44.778,"lon":-87.420,"color":"#FFC107","size":13}
    ];
    var muniLayer = L.layerGroup();
    muniData.forEach(function(m) {
        L.circleMarker([m.lat, m.lon], {radius: 5, fillColor: m.color, color: '#333', weight: 1.5, fillOpacity: 0.8}).bindPopup('<b>' + m.name + '</b><br>' + m.type + '<br>Growth: ' + m.rating).addTo(muniLayer);
        L.marker([m.lat, m.lon], {icon: L.divIcon({className: 'muni-label',
            html: '<div style="background:' + m.color + ';color:#fff;padding:2px 8px;border-radius:12px;font-size:' + m.size + 'px;font-weight:bold;text-shadow:0 1px 2px rgba(0,0,0,0.3);white-space:nowrap;border:1px solid #333;">' + m.name + '</div>',
            iconSize: [0,0], iconAnchor: [0,0]})}).addTo(muniLayer);
    });
    muniLayer.addTo(map);
    L.control.layers(null, {"Municipality Labels": muniLayer}, {position:'topright'}).addTo(map);
    </script>
</body>
</html>'''

with open('/root/wisconsin-overlay-map/output/Door_County_Zoning_Map.html', 'w') as f:
    f.write(html)
print(f"Door County map: {os.path.getsize('/root/wisconsin-overlay-map/output/Door_County_Zoning_Map.html'):,} bytes")