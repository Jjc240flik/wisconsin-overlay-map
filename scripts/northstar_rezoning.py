#!/usr/bin/env python3
"""Final pipeline with rezoning/subdivision grading."""
import requests, json, time, os
from collections import Counter, defaultdict
from datetime import datetime

API_KEY = "lp_live_z5k-VLjQn5gVOnb0NuTLG-rxJ1jtZy7G"
BASE_URL = "https://api.landportal.com"
H = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
OUT = "/root/wisconsin-overlay-map/output/subdivision_leads"

FIPS = {"Outagamie":"55087","Brown":"55009","Dane":"55025","Waukesha":"55133","Ozaukee":"55089","Milwaukee":"55079","Rock":"55105","Winnebago":"55139","Calumet":"55015","Door":"55029"}

# Town → (rezoning_grade, description focused on ag→subdivision potential)
TOWNS = {
    "Outagamie": {
        "VILLAGE OF GREENVILLE": ("A+", "PRIMARY. Adjacent Appleton. FLU adopted. 7 sub-area plans. Water+wastewater plans. Ag→residential active."),
        "TOWN OF GRAND CHUTE": ("A", "Adjacent Appleton. US 41. FLU shows ag→residential. Sewer/water. Active subdivisions."),
        "VILLAGE OF HARRISON": ("A", "East Appleton. US 10 corridor. Planned residential. Ag→residential transition."),
        "VILLAGE OF COMBINED LOCKS": ("A-", "Adjacent Kaukauna. Fox Cities. Sewer/water. Limited remaining ag."),
        "VILLAGE OF LITTLE CHUTE": ("A-", "Fox Cities core. Limited undeveloped land. Infill potential."),
        "TOWN OF BUCHANAN": ("B+", "Surrounds Kaukauna. Expansion path. Check FLU for ag→residential zones."),
        "TOWN OF FREEDOM": ("B+", "SW Appleton. Adjacent city. Ag land with rezoning potential. Check sewer."),
        "VILLAGE OF KIMBERLY": ("B", "Fox Cities core. Mostly built out. Limited ag land."),
    },
    "Brown": {
        "TOWN OF LEDGEVIEW": ("A+", "PRIMARY. Fastest growing. Adjacent De Pere. Ag→residential active. FLU expansion."),
        "VILLAGE OF HOWARD": ("A", "North Green Bay. Active residential. Ag→subdivisions. Strong demand."),
        "VILLAGE OF SUAMICO": ("A", "North Howard. New subdivisions. Ag land converting. Strong demand."),
        "VILLAGE OF BELLEVUE": ("A", "East Green Bay. Steady residential. Ag parcels are rezoning targets."),
        "TOWN OF LAWRENCE": ("A", "Near De Pere. I-41/I-43. Ag land with high rezoning likelihood."),
        "VILLAGE OF ASHWAUBENON": ("A-", "Adjacent Green Bay. I-41. Sewer/water. Mostly developed — infill."),
        "TOWN OF SCOTT": ("B+", "Near Howard. Growth along roads. Ag parcels with development pressure."),
        "TOWN OF HUMBOLDT": ("B+", "East Green Bay. Edge growth. Ag land near metro boundary. Check FLU."),
        "VILLAGE OF ALLOUEZ": ("B", "Adjacent Green Bay. Mostly built out. Infill, not ag conversion."),
    },
    "Dane": {
        "CITY OF VERONA": ("A+", "PRIMARY. Epic Systems corridor. Massive demand. Ag→residential. FLU expansion."),
        "CITY OF FITCHBURG": ("A", "South Madison. Major residential. Sewer/water expanding. Ag converting rapidly."),
        "TOWN OF SUN PRAIRIE": ("A", "Surrounds city. FLU residential expansion. Ag land in growth path."),
        "TOWN OF WESTPORT": ("A", "Middleton-Lake Mendota. High pressure residential. Ag→development."),
        "TOWN OF SPRINGFIELD": ("A-", "North Middleton. Edge-of-metro. Ag land with rezoning potential."),
        "TOWN OF BURKE": ("A-", "Madison-Sun Prairie path. Growth corridor. Ag conversion likely."),
        "TOWN OF BLOOMING GROVE": ("A-", "East Madison. Strong pressure. Limited remaining ag."),
        "TOWN OF PLEASANT SPRINGS": ("B+", "South Madison near McFarland. Edge growth. Check FLU."),
        "TOWN OF DUNN": ("B+", "SW edge near Fitchburg/Verona. Ag land. Check growth boundaries."),
        "TOWN OF MONTROSE": ("B+", "SE Oregon edge. Ag land — verify FLU."),
        "VILLAGE OF OREGON": ("B+", "SW metro. FLU+sewer. Some ag parcels remain."),
        "VILLAGE OF MCFARLAND": ("B+", "SE Madison. Bedroom. Limited ag land."),
        "VILLAGE OF WAUNAKEE": ("B+", "NW metro. Strong growth. Check FLU ag→residential."),
        "VILLAGE OF DEFOREST": ("B+", "North metro I-39/90. Expanding. Ag in growth corridor."),
        "VILLAGE OF WINDSOR": ("B+", "North metro. Ag land — verify expansion plans."),
        "TOWN OF BRISTOL": ("B+", "North Sun Prairie. Edge growth. Check comp plan."),
    },
    "Waukesha": {
        "VILLAGE OF MENOMONEE FALLS": ("A", "NE edge Milwaukee. Strong expansion. Ag→residential. I-94."),
        "TOWN OF LISBON": ("A", "Menomonee Falls-Pewaukee. FLU residential. Ag land converting."),
        "TOWN OF GENESEE": ("A-", "Waukesha/Milwaukee edge. Ag land with development pressure."),
        "VILLAGE OF PEWAUKEE": ("A-", "I-94 corridor. Growing. Limited remaining ag."),
        "VILLAGE OF SUSSEX": ("A-", "Waukesha-Menomonee Falls. Edge growth."),
        "TOWN OF WAUKESHA": ("B+", "Adjacent city. Some ag — check FLU."),
        "TOWN OF BROOKFIELD": ("B", "Adjacent cities. Mostly developed. Limited ag."),
        "VILLAGE OF LANNON": ("B", "Near Menomonee Falls. Small. Limited ag."),
    },
    "Ozaukee": {
        "VILLAGE OF GRAFTON": ("A", "I-43 corridor. Growing. Ag parcels with rezoning potential."),
        "VILLAGE OF SAUKVILLE": ("A", "I-43 north. Expansion potential. Ag land available."),
        "TOWN OF CEDARBURG": ("A", "Adjacent cities. FLU residential. Ag in growth path."),
        "CITY OF MEQUON": ("A-", "Milwaukee north shore. High-value. Limited undeveloped. Infill."),
        "CITY OF CEDARBURG": ("B+", "I-43 corridor. Bedroom. Limited ag."),
        "TOWN OF GRAFTON": ("B+", "I-43 edge. Ag parcels — check FLU."),
    },
    "Milwaukee": {
        "FRANKLIN": ("B+", "Most greenfield in county. Undeveloped land with potential."),
        "OAK CREEK": ("B+", "SE edge corridor. Undeveloped land."),
    },
    "Rock": {
        "BELOIT": ("A+", "PRIMARY. Adjacent Beloit. Illinois line. I-39/90 Stateline. Ag→residential pressure."),
        "JANESVILLE": ("A", "Surrounds Janesville. FLU residential. Ag→development active."),
        "TURTLE": ("A", "Southern edge Beloit. Stateline corridor. Ag in growth path."),
        "HARMONY": ("B+", "East Janesville. Edge growth. Ag — check FLU."),
        "CITY OF EVANSVILLE": ("B+", "North metro. Bedroom. Some ag."),
        "MILTON": ("B+", "Near Milton City. Edge growth. Ag parcels."),
        "FULTON": ("B+", "NE Janesville. Ag with edge potential."),
    },
    "Winnebago": {
        "TOWN OF NEENAH": ("A", "Adjacent Neenah/Menasha. US 41. FLU residential. Ag→development."),
        "TOWN OF OSHKOSH": ("A", "South Oshkosh. US 41. Ag land with rezoning potential."),
        "TOWN OF ALGOMA": ("A", "North Oshkosh. US 41. Ag in growth path."),
        "TOWN OF MENASHA": ("A-", "Surrounds Menasha. Edge growth. Limited ag."),
        "TOWN OF VINLAND": ("B+", "North Neenah. Edge growth. Ag — verify FLU."),
        "TOWN OF CLAYTON": ("B+", "SW Neenah. Some growth. Ag land."),
        "VILLAGE OF FOX CROSSING": ("B", "Neenah-Menasha. Growing. Limited ag."),
    },
    "Calumet": {
        "TOWN OF HARRISON": ("A", "South Appleton. US 41/10. Ag with strong rezoning potential."),
        "TOWN OF MENASHA": ("A", "Adjacent Menasha/Appleton. Fox Cities edge. Ag→development."),
        "TOWN OF STOCKBRIDGE": ("B+", "Lake Winnebago. Growing. Ag parcels. Seasonal+year-round."),
        "TOWN OF BROTHERTOWN": ("B+", "Lakeshore. Ag land. Seasonal+year-round demand."),
    },
    "Door": {
        "VILLAGE OF SISTER BAY": ("B", "Tourism corridor. Seasonal. Limited ag→subdivision play."),
    },
}

s = requests.Session()
s.headers.update(H)

def query(fips, muni, fs=False):
    if fs:
        flt = [{"key":"municipality","operator":"condition","value":muni},{"key":"landusecode","operator":"condition","value":"8001"},{"key":"active_listing_toggle","operator":"active_listing_toggle","value":True}]
    else:
        flt = [{"key":"municipality","operator":"condition","value":muni},{"key":"lotsizeacres","operator":"range","value":{"min":20,"max":300}},{"key":"vacant","operator":"boolean","value":True},{"key":"road_frontage","operator":"range","value":{"min":400}},{"key":"wetlands_cover_percentage","operator":"range","value":{"max":30}},{"key":"fema_cover_percentage","operator":"range","value":{"max":50}}]
    all_p, pt = [], None
    while True:
        url = f"{BASE_URL}/v2/filter-data"
        if pt: url += f"?page_token={pt}"
        try:
            r = s.post(url, json={"fips":[fips],"filters":flt}, timeout=30)
            if r.status_code!=200: break
            d = r.json()
            all_p.extend(d.get("data",{}).get("properties",[]))
            pt = d.get("data",{}).get("next_page_token","")
            if not pt: break
            time.sleep(0.1)
        except: break
    return all_p

def ok(name):
    if not name: return False
    u = name.upper().strip()
    if any(t in u for t in ["TRUST","TRST","REVOCABLE","REVOCABL","IRREVOCABLE","IRREVOCABL","REV TR","LIV TR","IRREV TR"," REVO"]): return False
    if u.endswith(" TRST") or u.endswith(" TR"): return False
    if any(p in u for p in ["COUNTY","TOWNSHIP","CITY OF","STATE OF","NATION ","TRIBE","VILLAGE OF","TOWN OF","HOUSING AUTHORITY","DEPT OF","DEPARTMENT OF","DOT","DNR","ELECTRIC POWER","SCHOOL DISTRICT","SANITARY DISTRICT","UNIFIED SCHOOL"]): return False
    if any(p in u for p in ["OWNERS OF LOTS","LOT OWNERS OF","HOMEOWNERS ASSOC"]): return False
    if u in ("AVAILABLE NOT","AVAILABLE NAME NOT","AVAILABLE","NOT AVAILABLE","UNKNOWN","N/A"): return False
    if " INC" in u or " CORP" in u: return False
    if ("LLC" in u or "L L C" in u) and "FARM" not in u: return False
    return True

om_a, fs_a = [], []
for county, towns in TOWNS.items():
    fips = FIPS[county]
    print(f"\n{county}:")
    for muni, (grade, notes) in towns.items():
        om = query(fips, muni, fs=False)
        for p in om: p["_C"]=county; p["_T"]=muni; p["_G"]=grade; p["_N"]=notes; p["_S"]="off-market"
        om_a.extend(om)
        time.sleep(0.12)
        fs = query(fips, muni, fs=True)
        for p in fs: p["_C"]=county; p["_T"]=muni; p["_G"]=grade; p["_N"]=notes; p["_S"]="for-sale"
        fs_a.extend(fs)
        time.sleep(0.12)
        print(f"  {muni}: {len(om)} OM + {len(fs)} FS")

# Filter
so, sf = set(), set()
om_f, fs_f = [], []
for p in om_a:
    pid=p.get("property_id")
    if pid and pid not in so and ok(p.get("owner_full_name","")):
        so.add(pid); om_f.append(p)
for p in fs_a:
    pid=p.get("property_id")
    if pid and pid not in sf and ok(p.get("owner_full_name","")):
        sf.add(pid); fs_f.append(p)
        if pid in so: om_f=[x for x in om_f if x.get("property_id")!=pid]; so.discard(pid)

# Build entries
E=[]
for p in om_f:
    E.append({"apn":p.get("apn",""),"owner":p.get("owner_full_name",""),"acres":p.get("lot_size_acres",0)or 0,"county":p["_C"],"town":p["_T"],"rezoning":p["_G"],"notes":p["_N"],"source":"off-market"})
for p in fs_f:
    E.append({"apn":p.get("apn",""),"owner":p.get("owner_full_name",""),"acres":p.get("lot_size_acres",0)or 0,"county":p["_C"],"town":p["_T"],"rezoning":p["_G"],"notes":p["_N"],"source":"for-sale"})

oc=Counter(e["owner"] for e in E if e["owner"])
multi={o:c for o,c in oc.items() if c>=2}
for e in E: e["multi"]=e["owner"] in multi

gr={"A+":0,"A":1,"A-":2,"B+":3,"B":4,"C":5}
E.sort(key=lambda e:(gr.get(e["rezoning"],6),-e["acres"]))

# Write
os.makedirs(os.path.join(OUT,"by_county"),exist_ok=True)
for county in FIPS:
    ee=[e for e in E if e["county"]==county]
    if not ee: continue
    bt=defaultdict(list)
    for e in ee:
        ts=e["town"].replace("TOWN OF ","").replace("VILLAGE OF ","").replace("CITY OF ","")
        bt[ts].append(e)
    omc=len([e for e in ee if e["source"]=="off-market"])
    fsc=len([e for e in ee if e["source"]=="for-sale"])
    L=[f"# {county} County — Subdivision Rezoning Pipeline",""]
    L.append(f"**{len(ee)} parcels** | {omc} off-market | {fsc} for-sale | Ag→Subdivision targets")
    L.extend(["","## Parcels Ranked by Rezoning / Subdivision Potential",""])
    L.append("| Rezoning | Town | Acres | Owner | APN | Status |")
    L.append("|---|---|---|---|---|---|")
    for e in ee[:200]:
        st="📞 MLS" if e["source"]=="for-sale" else "📬 Mail"
        mp=" 🔗" if e["multi"] else ""
        ac=f"{e['acres']:.1f}" if e.get("acres") else "?"
        ts=e["town"].replace("TOWN OF ","").replace("VILLAGE OF ","").replace("CITY OF ","")
        L.append(f"| **{e['rezoning']}** | {ts} | {ac} | {e['owner']}{mp} | {e['apn']} | {st} |")
    if len(ee)>200: L.append(f"| ... | ... | ... | ... (+{len(ee)-200} more) | ... | ... |")
    L.append("")
    L.extend(["## Rezoning / Subdivision Analysis",""])
    
    # A+/A tier
    top=[e for e in ee if e["rezoning"] in ("A+","A")]
    if top:
        L.append("### 🔥 A+/A — Prime Ag→Subdivision Targets")
        L.append("*These towns are directly adjacent to city limits with FLU maps showing ag→residential transition. Water/sewer infrastructure planned or active. Highest rezoning likelihood.*")
        L.append("")
        for e in top[:10]:
            ts=e["town"].replace("TOWN OF ","").replace("VILLAGE OF ","").replace("CITY OF ","")
            L.append(f"- **{e['apn']}** | {e['acres']:.1f}ac | {e['owner']} | {ts} — {e['notes']}")
        L.append("")
    
    # Clusters
    L.append("### Cluster Analysis")
    cl={t:p for t,p in bt.items() if len(p)>=3}
    for t,p in sorted(cl.items(),key=lambda x:-len(x[1])):
        ta=sum(e["acres"] for e in p)
        g=p[0]["rezoning"]
        mo=set(e["owner"] for e in p if e["multi"])
        fs_ct=len([e for e in p if e["source"]=="for-sale"])
        L.append(f"**{t}** ({g}): {len(p)} parcels, ~{ta:.0f} acres")
        if fs_ct: L.append(f"  - {fs_ct} MLS-listed — call first")
        if mo: L.append(f"  - {len(mo)} multi-property owners")
    L.append("")
    
    fst=defaultdict(list)
    for e in ee:
        if e["source"]=="for-sale":
            ts=e["town"].replace("TOWN OF ","").replace("VILLAGE OF ","").replace("CITY OF ","")
            fst[ts].append(e)
    if fst:
        L.append("### 📞 For-Sale — Call First")
        for t,p in sorted(fst.items(),key=lambda x:-len(x[1])):
            L.append(f"- **{t}** ({p[0]['rezoning']}): {len(p)} MLS-listed")
    
    omt=defaultdict(list)
    for e in ee:
        if e["source"]=="off-market":
            ts=e["town"].replace("TOWN OF ","").replace("VILLAGE OF ","").replace("CITY OF ","")
            omt[ts].append(e)
    if omt:
        L.append(""); L.append("### 📬 Off-Market — Mail Campaign")
        for t,p in sorted(omt.items(),key=lambda x:-len(x[1])):
            mc=len(set(e["owner"] for e in p if e["multi"]))
            sf=f" — {mc} multi-owners" if mc else ""
            L.append(f"- **{t}** ({p[0]['rezoning']}): {len(p)} parcels{sf}")
    
    L.extend(["","---",f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Queried by exact municipality. Grading reflects ag→subdivision rezoning potential from county 2040 comprehensive plans and FLU maps.*",""])
    with open(os.path.join(OUT,"by_county",f"{county}_pipeline.md"),"w") as f:
        f.write("\n".join(L))
    print(f"  {county}: {len(ee)} parcels")

print(f"\n===== DONE =====")
print(f"Off-market: {len(om_f)}, For-sale: {len(fs_f)}, Total: {len(E)}")
for county in FIPS:
    om=len([e for e in E if e["county"]==county and e["source"]=="off-market"])
    fs=len([e for e in E if e["county"]==county and e["source"]=="for-sale"])
    print(f"  {county}: {om} OM + {fs} FS = {om+fs}")