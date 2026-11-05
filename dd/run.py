"""Orchestrator: county pipeline file in, screened shortlist out.

Usage:
    python -m dd.run --county Outagamie
    python -m dd.run --county Outagamie --limit 40 --no-network
    python -m dd.run --county Outagamie --coords coords.json --lot-price 55000

Emits:
    output/dd/<County>_screened.json
    output/dd/<County>_screened.md
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter

from . import config
from .classify import classify
from .schema import Parcel, ScreenResult, Status
from .screens import screen_physical, screen_regulatory, screen_infrastructure
from .underwrite import underwrite, sensitivity

BASE = "output/subdivision_leads/by_county"
OUTDIR = "output/dd"

ROW_RE = re.compile(
    r'\|\s*\*\*(A\+|A|A-|B\+|B)\*\*\s*\|\s*([A-Za-z ]+?)\s*\|\s*([\d.]+|[\d.]+-[\d.]+†?|20-200†)\s*\|'
    r'\s*([^|]+?)\s*\|\s*([\w-]+)\s*\|\s*(\S+)')


def parse_range(tok: str):
    """'37.5' -> (37.5, None, None); '20-200†' -> (None, 20, 200)"""
    tok = tok.replace("†", "").strip()
    m = re.fullmatch(r'([\d.]+)-([\d.]+)', tok)
    if m:
        return None, float(m.group(1)), float(m.group(2))
    try:
        return float(tok), None, None
    except ValueError:
        return None, None, None


def load_pipeline(county: str, limit: int | None = None):
    path = os.path.join(BASE, f"{county}_pipeline.md")
    if not os.path.exists(path):
        sys.exit(f"pipeline file not found: {path}")
    parcels = []
    for line in open(path, encoding="utf-8"):
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        grade, town, ac_tok, owner, apn, status_icon = m.groups()
        acres, lo, hi = parse_range(ac_tok)
        parcels.append(Parcel(
            apn=apn.strip(),
            county=county,
            muni=town.strip().title(),
            owner=owner.replace("🔗", "").strip(),
            acres=acres, acre_low=lo, acre_high=hi,
            grade=grade,
            status=Status.OFF_MARKET if "📬" in status_icon else Status.FOR_SALE,
        ))
        if limit and len(parcels) >= limit:
            break
    return parcels


def run(county: str, limit=None, use_network=True, coords=None,
        lot_price=None, land_per_acre=None, min_acres=None):
    parcels = load_pipeline(county, limit)
    if min_acres:
        keep = [p for p in parcels if (p.acres_effective or 0) >= min_acres]
        print(f"acreage filter >= {min_acres}: {len(keep)} of {len(parcels)}")
        parcels = keep

    results = []
    for p in parcels:
        if coords and p.apn in coords:
            p.lat, p.lon = coords[p.apn]["lat"], coords[p.apn]["lon"]
        r = ScreenResult(parcel=p)
        screen_physical(r)
        if use_network and p.lat is not None:
            screen_infrastructure(r)
        screen_regulatory(r)
        cls = classify(r)
        eco = None
        lots = p.max_lots_by_zoning()
        if lots and lot_price:
            land = (p.acres_effective or 0) * land_per_acre if land_per_acre else None
            eco = underwrite(lots, lot_price, land)
            eco["sensitivity"] = sensitivity(lots, lot_price, land)
        results.append({**r.to_dict(), "classification": cls, "economics": eco})

    verdicts = Counter(x["verdict"] for x in results)
    species = Counter(x["classification"]["species"] for x in results)

    os.makedirs(OUTDIR, exist_ok=True)
    jpath = os.path.join(OUTDIR, f"{county}_screened.json")
    with open(jpath, "w") as f:
        json.dump({"county": county, "count": len(results),
                   "verdicts": dict(verdicts), "species": dict(species),
                   "results": results}, f, indent=2)

    mpath = os.path.join(OUTDIR, f"{county}_screened.md")
    with open(mpath, "w") as f:
        f.write(f"# {county} County — Screened Shortlist\n\n")
        f.write(f"**{len(results)} parcels screened** · verdicts: {dict(verdicts)} · "
                f"species: {dict(species)}\n\n")
        f.write("| Verdict | APN | Munis | Owner | Acres | Species | Reason |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for x in sorted(results, key=lambda y: (y["verdict"] != "GO", y["verdict"])):
            f.write(f"| **{x['verdict']}** | `{x['apn']}` | {x['muni']} | {x['owner'][:26]} | "
                    f"{x['acres'] if x['acres'] is not None else '?'} | "
                    f"{x['classification']['species']} | {x['classification']['reason'][:90]} |\n")
        f.write("\n## Fatal flags\n\n")
        for x in results:
            if x["fatal"]:
                f.write(f"- `{x['apn']}` ({x['muni']}): "
                        f"{'; '.join(fl['message'] for fl in x['fatal'])}\n")
    return jpath, mpath, dict(verdicts), dict(species)


def main():
    ap = argparse.ArgumentParser(description="Land due-diligence screen")
    ap.add_argument("--county", required=True)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--no-network", action="store_true")
    ap.add_argument("--coords", help="JSON file: {APN: {lat, lon}}")
    ap.add_argument("--lot-price", type=float)
    ap.add_argument("--land-per-acre", type=float)
    ap.add_argument("--min-acres", type=float)
    a = ap.parse_args()
    coords = json.load(open(a.coords)) if a.coords else None
    j, m, v, s = run(a.county, a.limit, not a.no_network, coords,
                     a.lot_price, a.land_per_acre, a.min_acres)
    print(f"wrote {j}\nwrote {m}\nverdicts={v}\nspecies={s}")


if __name__ == "__main__":
    main()
