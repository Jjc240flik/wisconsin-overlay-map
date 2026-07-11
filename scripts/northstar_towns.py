#!/usr/bin/env python3
"""Town-Level Pipeline — queries by municipality, not ZIP."""
import requests, json, time, os
from collections import Counter, defaultdict
from datetime import datetime

API_KEY = "lp_live_z5k-VLjQn5gVOnb0NuTLG-rxJ1jtZy7G"
BASE_URL = "https://api.landportal.com"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
OUTPUT_DIR = "/root/wisconsin-overlay-map/output/subdivision_leads"

COUNTY_FIPS = {
    "Outagamie": "55087", "Brown": "55009", "Dane": "55025",
    "Waukesha": "55133", "Ozaukee": "55089", "Milwaukee": "55079",
    "Rock": "55105", "Winnebago": "55139", "Calumet": "55015", "Door": "55029"
}

# Municipality names as they appear in LP
TOWNS = {
    "Outagamie": {
        "TOWN OF GRAND CHUTE": ("High", "Surrounds Appleton. US 41 corridor."),
        "VILLAGE OF GREENVILLE": ("High", "PRIMARY. FLU + water/wastewater. 7 sub-areas."),
        "VILLAGE OF HARRISON": ("High", "East Appleton. US 10 corridor."),
        "VILLAGE OF COMBINED LOCKS": ("High", "Adjacent Kaukauna. Fox Cities."),
        "VILLAGE OF LITTLE CHUTE": ("High", "Fox Cities metro core."),
        "TOWN OF BUCHANAN": ("Moderate to High", "Surrounds Kaukauna."),
        "TOWN OF FREEDOM": ("Moderate to High", "SW Appleton. Adjacent."),
        "VILLAGE OF KIMBERLY": ("Moderate to High", "Fox Cities. Limited land."),
    },
    "Brown": {
        "VILLAGE OF ASHWAUBENON": ("High", "Adjacent Green Bay. I-41. Sewer/water."),
        "VILLAGE OF HOWARD": ("High", "North Green Bay. Residential."),
        "VILLAGE OF SUAMICO": ("High", "North Howard. New subdivisions."),
        "VILLAGE OF BELLEVUE": ("High", "East Green Bay. Steady growth."),
        "TOWN OF LEDGEVIEW": ("High", "Fastest growing. Near De Pere."),
        "TOWN OF LAWRENCE": ("High", "Strong growth. I-41/I-43."),
        "VILLAGE OF ALLOUEZ": ("Moderate to High", "Adjacent Green Bay. Built out."),
        "TOWN OF HUMBOLDT": ("Moderate to High", "East Green Bay. Edge."),
        "TOWN OF SCOTT": ("Moderate to High", "Near Howard. Growth."),
    },
    "Dane": {
        "CITY OF FITCHBURG": ("High", "South Madison. Major residential."),
        "CITY OF VERONA": ("High", "Epic Systems corridor."),
        "TOWN OF SUN PRAIRIE": ("High", "Surrounds city. FLU residential."),
        "TOWN OF WESTPORT": ("High", "Between Middleton & Lake Mendota."),
        "TOWN OF SPRINGFIELD": ("High", "North Middleton."),
        "TOWN OF BURKE": ("High", "Madison-Sun Prairie path."),
        "TOWN OF BLOOMING GROVE": ("High", "East Madison."),
        "TOWN OF PLEASANT SPRINGS": ("Moderate to High", "South Madison."),
        "TOWN OF DUNN": ("Moderate to High", "SW Madison edge."),
        "TOWN OF MONTROSE": ("Moderate to High", "SE Oregon."),
        "VILLAGE OF OREGON": ("Moderate to High", "SW metro. FLU."),
        "VILLAGE OF MCFARLAND": ("Moderate to High", "SE Madison. Waubesa."),
        "VILLAGE OF WAUNAKEE": ("Moderate to High", "NW metro."),
        "VILLAGE OF DEFOREST": ("Moderate to High", "North metro. I-39/90."),
        "VILLAGE OF WINDSOR": ("Moderate to High", "North metro."),
        "TOWN OF BRISTOL": ("Moderate to High", "North Sun Prairie."),
    },
    "Waukesha": {
        "VILLAGE OF MENOMONEE FALLS": ("High", "NE edge. Milwaukee fringe."),
        "TOWN OF LISBON": ("High", "Menomonee Falls-Pewaukee."),
        "TOWN OF GENESEE": ("High", "Waukesha/Milwaukee edge."),
        "VILLAGE OF PEWAUKEE": ("High", "I-94 corridor."),
        "VILLAGE OF SUSSEX": ("High", "Waukesha-Menomonee Falls."),
        "TOWN OF WAUKESHA": ("High", "Adjacent city."),
        "TOWN OF BROOKFIELD": ("High", "Adjacent cities."),
        "VILLAGE OF LANNON": ("Moderate to High", "Near Menomonee Falls."),
    },
    "Ozaukee": {
        "CITY OF MEQUON": ("High", "Milwaukee north shore."),
        "VILLAGE OF GRAFTON": ("High", "I-43 corridor."),
        "VILLAGE OF SAUKVILLE": ("High", "I-43 north."),
        "TOWN OF CEDARBURG": ("High", "Adjacent cities. FLU."),
        "CITY OF CEDARBURG": ("Moderate to High", "I-43. Bedroom."),
        "TOWN OF GRAFTON": ("Moderate to High", "I-43 edge."),
    },
    "Milwaukee": {
        "CITY OF FRANKLIN": ("Moderate", "MOST greenfield."),
        "CITY OF OAK CREEK": ("Moderate", "SE edge corridor."),
    },
    "Rock": {
        "TOWN OF BELOIT": ("High", "Stateline. Illinois line."),
        "TOWN OF JANESVILLE": ("High", "Surrounds city."),
        "TOWN OF TURTLE": ("High", "Stateline corridor."),
        "TOWN OF HARMONY": ("Moderate to High", "East Janesville."),
        "VILLAGE OF EVANSVILLE": ("Moderate to High", "North metro."),
        "TOWN OF MILTON": ("Moderate to High", "Near Milton City."),
        "TOWN OF FULTON": ("Moderate to High", "NE Janesville."),
    },
    "Winnebago": {
        "TOWN OF NEENAH": ("High", "Adjacent Neenah/Menasha. US 41."),
        "TOWN OF MENASHA": ("High", "Surrounds Menasha."),
        "TOWN OF OSHKOSH": ("High", "South Oshkosh. US 41."),
        "TOWN OF ALGOMA": ("High", "North Oshkosh. US 41."),
        "TOWN OF VINLAND": ("Moderate to High", "North Neenah."),
        "TOWN OF CLAYTON": ("Moderate to High", "SW Neenah."),
        "VILLAGE OF FOX CROSSING": ("Moderate to High", "Neenah-Menasha."),
    },
    "Calumet": {
        "TOWN OF HARRISON": ("High", "South Appleton. US 41/10."),
        "TOWN OF MENASHA": ("High", "Adjacent Menasha/Appleton."),
        "TOWN OF STOCKBRIDGE": ("Moderate to High", "Lake Winnebago."),
        "TOWN OF BROTHERTOWN": ("Moderate to High", "Lakeshore."),
    },
    "Door": {
        "VILLAGE OF SISTER BAY": ("Moderate to High", "Tourism corridor."),
    },
}

s = requests.Session()
s.headers.update(HEADERS)

def ok(name):
    if not name: return False
    u = name.upper().strip()
    if any(t in u for t in ["TRUST","TRST","REVOCABLE","REVOCABL","IRREVOCABLE","IRREVOCABL","REV TR","LIV TR","IRREV TR"," REVO"]):
        return False
    if u.endswith(" TRST") or u.endswith(" TR"): return False
    if any(p in u for p in ["COUNTY","TOWNSHIP","CITY OF","STATE OF","NATION ","TRIBE","VILLAGE OF","TOWN OF","HOUSING AUTHORITY","DEPT OF","DEPARTMENT OF","DOT","DNR","ELECTRIC POWER","SCHOOL DISTRICT","SANITARY DISTRICT","UNIFIED SCHOOL"]):
        return False
    if any(p in u for p in ["OWNERS OF LOTS","LOT OWNERS OF","HOMEOWNERS ASSOC"]): return False
    if u in ("AVAILABLE NOT","AVAILABLE NAME NOT","AVAILABLE","NOT AVAILABLE","UNKNOWN","N/A"): return False
    if " INC" in u or " CORP" in u: return False
    if ("LLC" in u or "L L C" in u) and "FARM" not in u: return False
    return True

def query(fips, muni, fs=False):
    if fs:
        flt = [
            {"key":"municipality","operator":"condition","value":muni},
            {"key":"landusecode","operator":"condition","value":"8001"},
            {"key":"active_listing_toggle","operator":"active_listing_toggle","value":True},
        ]
    else:
        flt = [
            {"key":"municipality","operator":"condition","value":muni},
            {"key":"lotsizeacres","operator":"range","value":{"min":20,"max":300}},
            {"key":"vacant","operator":"boolean","value":True},
            {"key":"road_frontage","operator":"range","value":{"min":400}},
            {"key":"wetlands_cover_percentage","operator":"range","value":{"max":30}},
            {"key":"fema_cover_percentage","operator":"range","value":{"max":50}},
        ]
    try:
        r = s.post(f"{BASE_URL}/v2/filter-data", json={"fips":[fips],"filters":flt}, timeout=30)
        return r.json() if r.status_code==200 else None
    except:
        return None

om_all, fs_all = [], []
for county, towns in TOWNS.items():
    fips = COUNTY_FIPS[county]
    for muni, (rating, notes) in towns.items():
        if rating not in ("High","Moderate to High"): continue
        # Off-market
        r = query(fips, muni)
        if r:
            for p in r.get("data",{}).get("properties",[]):
                p["_C"]=county; p["_T"]=muni; p["_R"]=rating; p["_N"]=notes; p["_S"]="off-market"
            om_all.extend(r["data"]["properties"])
        time.sleep(0.15)
        # For-sale
        r = query(fips, muni, fs=True)
        if r:
            for p in r.get("data",{}).get("properties",[]):
                p["_C"]=county; p["_T"]=muni; p["_R"]=rating; p["_N"]=notes; p["_S"]="for-sale"
            fs_all.extend(r["data"]["properties"])
        time.sleep(0.15)
    print(f"  {county} done")

print(f"\nRaw: {len(om_all)} OM + {len(fs_all)} FS = {len(om_all)+len(fs_all)}")

# Filter
seen_o, seen_f = set(), set()
om_f, fs_f = [], []
for p in om_all:
    pid=p.get("property_id")
    if pid and pid not in seen_o and ok(p.get("owner_full_name","")):
        seen_o.add(pid); om_f.append(p)
for p in fs_all:
    pid=p.get("property_id")
    if pid and pid not in seen_f and ok(p.get("owner_full_name","")):
        seen_f.add(pid); fs_f.append(p)
        if pid in seen_o: om_f=[x for x in om_f if x.get("property_id")!=pid]; seen_o.discard(pid)

print(f"Filtered: {len(om_f)} OM + {len(fs_f)} FS = {len(om_f)+len(fs_f)}")

# Build entries
entries=[]
for p in om_f:
    entries.append({"apn":p.get("apn",""),"owner":p.get("owner_full_name",""),"acres":p.get("lot_size_acres",0)or 0,"county":p["_C"],"town":p["_T"],"growth":p["_R"],"notes":p["_N"],"source":"off-market","pid":p.get("property_id")})
for p in fs_f:
    entries.append({"apn":p.get("apn",""),"owner":p.get("owner_full_name",""),"acres":p.get("lot_size_acres",0)or 0,"county":p["_C"],"town":p["_T"],"growth":p["_R"],"notes":p["_N"],"source":"for-sale","pid":p.get("property_id")})

oc=Counter(e["owner"] for e in entries if e["owner"])
multi={o:c for o,c in oc.items() if c>=2}
for e in entries: e["multi"]=e["owner"] in multi; e["owner_count"]=multi.get(e["owner"],1)

def grade(g,n):
    if g=="High": return "A" if any(w in n.lower() for w in ["flu","sewer","water","primary","master plan"]) else "A-"
    if g=="Moderate to High": return "B+"
    return "B"
for e in entries: e["grade"]=grade(e["growth"],e["notes"])

go={"High":0,"Moderate to High":1,"Moderate":2}
gro={"A":0,"A-":1,"B+":2,"B":3}
entries.sort(key=lambda e:(go.get(e["growth"],5),gro.get(e["grade"],5),-e["acres"]))

# Write files
os.makedirs(os.path.join(OUTPUT_DIR,"by_county"),exist_ok=True)
for county in COUNTY_FIPS:
    ee=[e for e in entries if e["county"]==county]
    if not ee: continue
    bt=defaultdict(list)
    for e in ee:
        ts=e["town"].replace("TOWN OF ","").replace("VILLAGE OF ","").replace("CITY OF ","")
        bt[ts].append(e)
    omc=len([e for e in ee if e["source"]=="off-market"])
    fsc=len([e for e in ee if e["source"]=="for-sale"])
    L=[f"# {county} County — North Star Subdivision Pipeline",""]
    L.append(f"**{len(ee)} parcels** | {omc} off-market | {fsc} for-sale | HIGH & Moderate-to-High towns")
    L.extend(["","## Parcels Ranked by Growth Potential",""])
    L.append("| Growth | Town | Acres | Owner | APN | Status |")
    L.append("|---|---|---|---|---|---|")
    for e in ee:
        st="📞 MLS" if e["source"]=="for-sale" else "📬 Mail"
        mp=" 🔗" if e["multi"] else ""
        ac=f"{e['acres']:.1f}" if e.get("acres") else "?"
        ts=e["town"].replace("TOWN OF ","").replace("VILLAGE OF ","").replace("CITY OF ","")
        L.append(f"| {e['growth']} | {ts} | {ac} | {e['owner']}{mp} | {e['apn']} | {st} |")
    L.append("")
    L.extend(["## North Star Takeaway",""])
    cl={t:p for t,p in bt.items() if len(p)>=3}
    for t,p in sorted(cl.items(),key=lambda x:-len(x[1])):
        ta=sum(e["acres"] for e in p)
        g=p[0]["growth"]
        mo=set(e["owner"] for e in p if e["multi"])
        fsct=len([e for e in p if e["source"]=="for-sale"])
        L.append(f"### {t} — {len(p)} parcels, ~{ta:.0f} acres ({g})")
        L.append(f"- **{len(p)} parcels** in {t}, a {g}-growth town.")
        if fsct: L.append(f"- **{fsct} MLS-listed** — call first.")
        if mo: L.append(f"- **{len(mo)} multi-property owners** — one conversation, multiple deals.")
        L.append("")
    fst=defaultdict(list)
    for e in ee:
        if e["source"]=="for-sale":
            ts=e["town"].replace("TOWN OF ","").replace("VILLAGE OF ","").replace("CITY OF ","")
            fst[ts].append(e)
    if fst:
        L.append("### 📞 For-Sale Priority Targets")
        for t,p in sorted(fst.items(),key=lambda x:-len(x[1])):
            L.append(f"- **{t}** ({p[0]['growth']}): {len(p)} MLS-listed")
    omt=defaultdict(list)
    for e in ee:
        if e["source"]=="off-market":
            ts=e["town"].replace("TOWN OF ","").replace("VILLAGE OF ","").replace("CITY OF ","")
            omt[ts].append(e)
    if omt:
        L.append(""); L.append("### 📬 Off-Market Priority Targets")
        for t,p in sorted(omt.items(),key=lambda x:-len(x[1])):
            mc=len(set(e["owner"] for e in p if e["multi"]))
            sf=f" — {mc} multi-owners" if mc else ""
            L.append(f"- **{t}** ({p[0]['growth']}): {len(p)} parcels{sf}")
    L.extend(["","---",f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Queried by exact town/municipality name. Graded from county 2040 comprehensive plans.*",""])
    with open(os.path.join(OUTPUT_DIR,"by_county",f"{county}_pipeline.md"),"w") as f:
        f.write("\n".join(L))
    print(f"  {county}: {len(ee)} parcels")

print(f"\n===== DONE =====")
for county in COUNTY_FIPS:
    om=len([e for e in entries if e["county"]==county and e["source"]=="off-market"])
    fs=len([e for e in entries if e["county"]==county and e["source"]=="for-sale"])
    print(f"  {county}: {om} OM + {fs} FS = {om+fs}")
print(f"  TOTAL: {len(entries)}")