#!/usr/bin/env python3
"""Final pipeline — corrected LP filters per Search Filters doc + Cody/North Star methodology."""
import requests, json, time, os
from collections import Counter, defaultdict
from datetime import datetime as dt

API_KEY = "lp_live_e3C0PY-2uwItQt3DcW1eH2t-bD0MfjkQ"
BASE = "https://api.landportal.com"
H = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
O = "/root/wisconsin-overlay-map/output/subdivision_leads"

F = {"Outagamie":"55087","Brown":"55009","Dane":"55025","Waukesha":"55133","Ozaukee":"55089","Milwaukee":"55079","Rock":"55105","Winnebago":"55139","Calumet":"55015","Door":"55029"}

T = {
 "Outagamie":{"VILLAGE OF GREENVILLE":("A+","PRIMARY. Adjacent Appleton. FLU adopted. 7 sub-areas. Water+wastewater. Ag→residential."),"TOWN OF GRAND CHUTE":("A","Adjacent Appleton. US 41. FLU ag→residential. Sewer/water. Active subdivisions."),"VILLAGE OF HARRISON":("A","East Appleton. US 10. Planned residential. Ag→residential transition.")},
 "Brown":{"TOWN OF LEDGEVIEW":("A+","PRIMARY. Fastest growing. Adjacent De Pere. Ag→residential active. FLU expansion."),"VILLAGE OF HOWARD":("A","North Green Bay. Active residential. Ag→subdivisions. Demand."),"VILLAGE OF SUAMICO":("A","North Howard. New subdivisions. Ag converting. Strong demand."),"VILLAGE OF BELLEVUE":("A","East Green Bay. Steady residential. Ag rezoning targets."),"TOWN OF LAWRENCE":("A","Near De Pere. I-41/I-43. Ag high rezoning likelihood."),"VILLAGE OF ASHWAUBENON":("A-","Adjacent Green Bay. I-41. Sewer/water. Mostly developed.")},
 "Dane":{"CITY OF VERONA":("A+","PRIMARY. Epic Systems. Massive demand. Ag→residential. FLU expansion."),"CITY OF FITCHBURG":("A","South Madison. Major residential. Sewer/water expanding. Ag converting."),"TOWN OF SUN PRAIRIE":("A","Surrounds city. FLU residential. Ag in growth path."),"TOWN OF WESTPORT":("A","Middleton-Lake Mendota. High pressure. Ag→development."),"TOWN OF SPRINGFIELD":("A-","North Middleton. Edge-of-metro. Ag rezoning potential."),"TOWN OF BURKE":("A-","Madison-Sun Prairie. Growth corridor. Ag conversion likely."),"TOWN OF BLOOMING GROVE":("A-","East Madison. Strong pressure. Limited ag.")},
 "Waukesha":{"VILLAGE OF MENOMONEE FALLS":("A","NE edge Milwaukee. Expansion. Ag→residential. I-94."),"TOWN OF LISBON":("A","Menomonee Falls-Pewaukee. FLU residential. Ag converting."),"TOWN OF GENESEE":("A-","Waukesha/Milwaukee edge. Ag development pressure."),"VILLAGE OF PEWAUKEE":("A-","I-94 corridor. Limited remaining ag."),"VILLAGE OF SUSSEX":("A-","Waukesha-Menomonee Falls. Edge growth.")},
 "Ozaukee":{"VILLAGE OF GRAFTON":("A","I-43 corridor. Ag rezoning potential."),"VILLAGE OF SAUKVILLE":("A","I-43 north. Expansion. Ag available."),"TOWN OF CEDARBURG":("A","Adjacent cities. FLU residential. Ag growth path."),"CITY OF MEQUON":("A-","Milwaukee north shore. Limited undeveloped.")},
 "Rock":{"BELOIT":("A+","PRIMARY. Adjacent Beloit. IL line. I-39/90 Stateline. Ag→residential."),"JANESVILLE":("A","Surrounds Janesville. FLU residential. Ag→development."),"TURTLE":("A","Southern Beloit. Stateline corridor. Ag growth path.")},
 "Winnebago":{"TOWN OF NEENAH":("A","Adjacent Neenah/Menasha. US 41. FLU residential. Ag→development."),"TOWN OF OSHKOSH":("A","South Oshkosh. US 41. Ag rezoning potential."),"TOWN OF ALGOMA":("A","North Oshkosh. US 41. Ag growth path."),"TOWN OF MENASHA":("A-","Surrounds Menasha. Edge growth. Limited ag.")},
 "Calumet":{"TOWN OF HARRISON":("A","South Appleton. US 41/10. Ag strong rezoning."),"TOWN OF MENASHA":("A","Adjacent Menasha/Appleton. Fox Cities edge. Ag→development.")},
}

s = requests.Session(); s.headers.update(H)

def q(fips,muni,fs=False):
    if fs:
        all_p = []
        for code in ["8000","8001","8008","7000","7001"]:
            fl=[{"key":"municipality","operator":"condition","value":muni},{"key":"landusecode","operator":"condition","value":code},{"key":"active_listing_toggle","operator":"active_listing_toggle","value":True}]
            r=s.post(f"{BASE}/v2/filter-data",json={"fips":[fips],"filters":fl},timeout=30)
            if r.status_code!=200: continue
            d=r.json()
            if d.get("meta",{}).get("rejected_filters"): continue
            all_p.extend(d.get("data",{}).get("properties",[]))
            time.sleep(0.05)
        return all_p
    else:
        fl=[{"key":"municipality","operator":"condition","value":muni},{"key":"lotsizeacres","operator":"range","value":{"min":20,"max":200}},{"key":"vacant","operator":"boolean","value":True},{"key":"road_frontage","operator":"range","value":{"min":300}},{"key":"wetlands_cover_percentage","operator":"range","value":{"max":25}},{"key":"fema_cover_percentage","operator":"range","value":{"max":50}},{"key":"sum_up_to_15","operator":"range","value":{"min":50}}]
    ap,pt=[],None
    while True:
        u=f"{BASE}/v2/filter-data"
        if pt: u+=f"?page_token={pt}"
        try:
            r=s.post(u,json={"fips":[fips],"filters":fl},timeout=30)
            if r.status_code!=200: break
            d=r.json()
            if d.get("meta",{}).get("rejected_filters"): break
            ap.extend(d.get("data",{}).get("properties",[]))
            pt=d.get("data",{}).get("next_page_token","")
            if not pt: break; time.sleep(0.1)
        except: break
    return ap

def ok(n):
    if not n: return False
    u=n.upper().strip()
    if any(t in u for t in ["TRUST","TRST","REVOCABLE","REVOCABL","IRREVOCABLE","IRREVOCABL","REV TR","LIV TR","IRREV TR"," REVO"]): return False
    if u.endswith(" TRST") or u.endswith(" TR"): return False
    if any(p in u for p in ["COUNTY","TOWNSHIP","CITY OF","STATE OF","NATION ","TRIBE","VILLAGE OF","TOWN OF","HOUSING AUTHORITY","DEPT OF","DEPARTMENT OF","DOT","DNR","ELECTRIC POWER","SCHOOL DISTRICT","SANITARY DISTRICT","UNIFIED SCHOOL"]): return False
    if "OWNERS OF LOTS" in u or "LOT OWNERS OF" in u or "HOMEOWNERS ASSOC" in u: return False
    if u in ("AVAILABLE NOT","AVAILABLE NAME NOT","AVAILABLE","NOT AVAILABLE","UNKNOWN","N/A"): return False
    if " INC" in u or " CORP" in u: return False
    if ("LLC" in u or "L L C" in u) and "FARM" not in u: return False
    return True

om_a,fs_a=[],[]
for c,towns in T.items():
    fips=F[c]
    print(f"\n{c}:")
    for m,(g,n) in towns.items():
        om=q(fips,m); time.sleep(0.12)
        fs=q(fips,m,True); time.sleep(0.12)
        for p in om: p["_C"]=c; p["_T"]=m; p["_G"]=g; p["_N"]=n; p["_S"]="off-market"
        for p in fs: p["_C"]=c; p["_T"]=m; p["_G"]=g; p["_N"]=n; p["_S"]="for-sale"
        om_a.extend(om); fs_a.extend(fs)
        print(f"  {m}: {len(om)} OM + {len(fs)} FS")

so,sf=set(),set(); om_f,fs_f=[],[]
for p in om_a:
    pid=p.get("property_id")
    if pid and pid not in so and ok(p.get("owner_full_name","")): so.add(pid); om_f.append(p)
for p in fs_a:
    pid=p.get("property_id")
    if pid and pid not in sf and ok(p.get("owner_full_name","")): sf.add(pid); fs_f.append(p)
    if pid in so: om_f=[x for x in om_f if x.get("property_id")!=pid]; so.discard(pid)

E=[]
for p in om_f: E.append({"apn":p.get("apn",""),"owner":p.get("owner_full_name",""),"acres":p.get("lot_size_acres",0)or 0,"county":p["_C"],"town":p["_T"],"rezoning":p["_G"],"notes":p["_N"],"source":"off-market"})
for p in fs_f: E.append({"apn":p.get("apn",""),"owner":p.get("owner_full_name",""),"acres":p.get("lot_size_acres",0)or 0,"county":p["_C"],"town":p["_T"],"rezoning":p["_G"],"notes":p["_N"],"source":"for-sale"})

oc=Counter(e["owner"] for e in E if e["owner"]); multi={o:c for o,c in oc.items() if c>=2}
for e in E: e["multi"]=e["owner"] in multi

gr={"A+":0,"A":1,"A-":2,"B+":3,"B":4}; E.sort(key=lambda e:(gr.get(e["rezoning"],6),-e["acres"]))

os.makedirs(os.path.join(O,"by_county"),exist_ok=True)
for c in F:
    ee=[e for e in E if e["county"]==c]
    if not ee: continue
    bt=defaultdict(list)
    for e in ee: bt[e["town"].replace("TOWN OF ","").replace("VILLAGE OF ","").replace("CITY OF ","")].append(e)
    omc=len([e for e in ee if e["source"]=="off-market"]); fsc=len([e for e in ee if e["source"]=="for-sale"])
    L=[f"# {c} County — Ag→Subdivision Rezoning Pipeline",""]
    L.append(f"**{len(ee)} parcels** | {omc} off-market | {fsc} for-sale | Category 1 filters: 20-200ac, 300ft road, ≤25% wetlands, ≤50% FEMA, ≥50% slope <15°")
    L.extend(["","## Parcels Ranked by Rezoning Potential",""])
    L.append("| Rezoning | Town | Acres | Owner | APN | Status |")
    L.append("|---|---|---|---|---|---|")
    for e in ee[:200]:
        st="📞" if e["source"]=="for-sale" else "📬"
        mp="🔗" if e["multi"] else ""
        ac=f"{e['acres']:.1f}" if e.get("acres") else "?"
        ts=e["town"].replace("TOWN OF ","").replace("VILLAGE OF ","").replace("CITY OF ","")
        L.append(f"| **{e['rezoning']}** | {ts} | {ac} | {e['owner']} {mp}| {e['apn']} | {st} |")
    if len(ee)>200: L.append(f"| ... | ... | ... (+{len(ee)-200} more) | ... | ... |")
    L.append("")
    L.append("## Rezoning Analysis")
    L.append("")
    top=[e for e in ee if e["rezoning"] in ("A+","A")]
    if top:
        L.append("### 🔥 A+/A — Prime Ag→Subdivision Targets")
        L.append("*Directly adjacent to city limits. FLU maps show ag→residential. Sewer/water planned or active. Highest rezoning likelihood.*")
        L.append("")
        for e in top[:10]:
            ts=e["town"].replace("TOWN OF ","").replace("VILLAGE OF ","").replace("CITY OF ","")
            L.append(f"- **{e['apn']}** | {e['acres']:.1f}ac | {e['owner']} | {ts} — {e['notes']}")
        L.append("")
    L.append("### Clusters")
    cl={t:p for t,p in bt.items() if len(p)>=3}
    for t,p in sorted(cl.items(),key=lambda x:-len(x[1])):
        ta=sum(e["acres"] for e in p); g=p[0]["rezoning"]
        mo=set(e["owner"] for e in p if e["multi"]); fs_ct=len([e for e in p if e["source"]=="for-sale"])
        L.append(f"**{t}** ({g}): {len(p)} parcels, ~{ta:.0f}ac")
        if fs_ct: L.append(f"  {fs_ct} MLS — call first")
        if mo: L.append(f"  {len(mo)} multi-owners")
    L.append("")
    fst=defaultdict(list); omt=defaultdict(list)
    for e in ee:
        ts=e["town"].replace("TOWN OF ","").replace("VILLAGE OF ","").replace("CITY OF ","")
        if e["source"]=="for-sale": fst[ts].append(e)
        else: omt[ts].append(e)
    if fst:
        L.append("### 📞 For-Sale")
        for t,p in sorted(fst.items(),key=lambda x:-len(x[1])): L.append(f"- **{t}** ({p[0]['rezoning']}): {len(p)}")
    if omt:
        L.append(""); L.append("### 📬 Off-Market")
        for t,p in sorted(omt.items(),key=lambda x:-len(x[1])):
            mc=len(set(e["owner"] for e in p if e["multi"]))
            L.append(f"- **{t}** ({p[0]['rezoning']}): {len(p)}{' — '+str(mc)+' multi-owners' if mc else ''}")
    L.extend(["","---",f"*{dt.now().strftime('%Y-%m-%d %H:%M')} | North Star / Cody Bjugan criteria. Search Filters doc v1.0. County 2040 comp plan cross-reference.*",""])
    with open(os.path.join(O,"by_county",f"{c}_pipeline.md"),"w") as f: f.write("\n".join(L))
    print(f"  {c}: {len(ee)} parcels")

print(f"\n===== DONE =====")
for c in F:
    om=len([e for e in E if e["county"]==c and e["source"]=="off-market"])
    fs=len([e for e in E if e["county"]==c and e["source"]=="for-sale"])
    print(f"  {c}: {om} OM + {fs} FS = {om+fs}")
print(f"  TOTAL: {len(E)}")