"""Verification: run the engine on the Estler parcel with ONLY facts a machine can know.

If the engine is worth anything it must independently reach the same KILL that took
two weeks of humans, transcripts and emails. This is the regression test that matters.
"""
from dd.schema import Parcel, ScreenResult
from dd.screens import screen_physical, screen_regulatory, screen_infrastructure
from dd.classify import classify
from dd.underwrite import underwrite, sensitivity

# Estler — Sub-Area C, Greenville. Centroid from the ECWRPC check.
p = Parcel(
    apn="111041000/111041200",
    county="Outagamie",
    muni="Greenville",
    owner="Estler",
    acres=63.4,
    grade="A+",
    flu_code="R-1",
    zoning="AG",
    min_lot_sqft=43_560,          # 1-acre minimum by design
    lat=44.31631,
    lon=-88.50613,
    road_frontage_ft=1_320,
    wetlands_pct=5.0,
    flood_pct=0.0,
    slope_over_15_pct=10.0,
    sewer_capacity="pump",        # Mark Mommaerts, 20 Oct 2026, in writing
    attrs={"lift_station_cost": 2_100_000},
)

r = ScreenResult(parcel=p)
screen_physical(r)
screen_infrastructure(r, use_cache=False)   # live ECWRPC query FIRST so regulatory sees it
screen_regulatory(r)
cls = classify(r)

lots = 44  # engineered yield, not gross zoning yield
eco = underwrite(lots, lot_price=55_000, land_cost=975_000,
                 capital_cost=p.attrs["lift_station_cost"])
sens = sensitivity(lots, 55_000, 975_000, capital_cost=p.attrs["lift_station_cost"])

print("=" * 66)
print("ENGINE VERDICT — Estler / Greenville (APNs 111041000 / 111041200)")
print("=" * 66)
print(f"SSA status (live):      in_ssa={p.in_sewer_service_area}")
print(f"Screen verdict:         {r.verdict.value}")
print(f"Classifier:             species={cls['species']}  verdict={cls['verdict']}")
print(f"Reason:                 {cls['reason']}")
print()
print("Flags:")
for f in r.flags:
    print(f"  [{f.severity.value:<5}] [{f.species.value:<7}] {f.code}: {f.message[:96]}")
print()
print("Underwriting (44 lots @ $55k, land $975k, station $2.1M):")
for k in ("revenue", "land_cost", "soft_costs", "capital_costs", "all_in", "margin", "margin_pct", "verdict"):
    print(f"  {k:<16} {eco[k]}")
print(f"  sensitivity      {sens}")
print()
print("=" * 66)
expected = cls["verdict"] == "KILL" and eco["verdict"] == "DEAD"
print("MATCHES HUMAN ANALYSIS:", "YES" if expected else "NO — investigate")
