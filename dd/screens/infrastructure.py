"""Screen C — infrastructure. The screen that would have killed Estler in 10 seconds.

Live against the ECWRPC sewer-service-area feature service. Deterministic query,
on-disk cache so a re-run costs nothing.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import requests

from ..schema import ScreenResult, Severity, Species

SSA_URL = ("https://services1.arcgis.com/Osi6nedbad6tbPn5/arcgis/rest/services/"
           "SSA/FeatureServer/0/query")
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "output", "dd", "_cache")
TIMEOUT = 25


def _cache_path(lat: float, lon: float) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"ssa_{lat:.5f}_{lon:.5f}.json")


def query_ssa(lat: float, lon: float, use_cache: bool = True) -> dict:
    """Point-in-polygon against the ECWRPC Sewer Service Area layer.

    Returns {"in_ssa": bool|None, "ssa_name": str, "features": n, "error": str|None}
    """
    cp = _cache_path(lat, lon)
    if use_cache and os.path.exists(cp):
        with open(cp) as f:
            return json.load(f)

    params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "SSA,SSABnd_Name",
        "returnGeometry": "false",
        "f": "json",
    }
    out = {"in_ssa": None, "ssa_name": "", "features": 0, "error": None}
    try:
        resp = requests.get(SSA_URL, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        feats = data.get("features") or []
        out["features"] = len(feats)
        out["in_ssa"] = len(feats) > 0
        if feats:
            a = feats[0].get("attributes", {})
            out["ssa_name"] = a.get("SSABnd_Name") or str(a.get("SSA", ""))
    except Exception as e:                      # network, JSON, service change
        out["error"] = f"{type(e).__name__}: {e}"

    if use_cache and out["error"] is None:
        with open(cp, "w") as f:
            json.dump(out, f)
    return out


def screen_infrastructure(r: ScreenResult, use_cache: bool = True) -> ScreenResult:
    p = r.parcel

    if p.lat is None or p.lon is None:
        r.add("NO_COORDS", Severity.WARN, Species.NONE,
              "No coordinates — cannot run sewer service area test. Geocode the APN first.")
        return r

    res = query_ssa(p.lat, p.lon, use_cache=use_cache)
    if res["error"]:
        r.add("SSA_ERROR", Severity.WARN, Species.NONE,
              f"Sewer service area lookup failed ({res['error']}) — treat as unknown, not as clear")
        return r

    p.in_sewer_service_area = res["in_ssa"]
    if res["in_ssa"]:
        r.notes.append(f"Inside SSA boundary '{res['ssa_name']}' — sewer/water mandatory.")
    else:
        r.add("OUTSIDE_SSA", Severity.FATAL, Species.NONE,
              "Outside the ECWRPC sewer service area — plat prohibited, CSM-limited. Kill.")

    # --- capacity: honestly unknown without a human ----------------------
    # No public dataset publishes available sewer CAPACITY or connection grade.
    # That is exactly the gap that killed the Estler parcel, and it is the one
    # thing software cannot answer. It requires a written answer from the utility.
    if p.sewer_capacity == "unknown":
        r.add("CAPACITY_UNVERIFIED", Severity.WARN, Species.CAPITAL,
              "Sewer CAPACITY/connection grade unverified. No public dataset publishes this. "
              "Send the utility the capacity question and get a written answer BEFORE any offer.")
    elif p.sewer_capacity == "pump":
        r.add("PUMP_REQUIRED", Severity.FATAL, Species.CAPITAL,
              "Connection requires pumping (lift station) — a capital problem. "
              "Estimate the station cost before proceeding; if > ceiling, pass.")
    elif p.sewer_capacity == "gravity":
        r.notes.append("Gravity connection reported — lowest-cost path, verify in writing.")

    return r
