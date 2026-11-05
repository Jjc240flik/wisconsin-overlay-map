"""Screen A — physical constraints. Pure functions, no network."""
from __future__ import annotations

from .. import config
from ..schema import ScreenResult, Severity, Species


def screen_physical(r: ScreenResult) -> ScreenResult:
    p = r.parcel

    # --- acreage -----------------------------------------------------------
    if not p.acres_known:
        r.add("ACRES_UNKNOWN", Severity.WARN, Species.NONE,
              "Acreage not verified in source data — confirm with county before any offer")
    else:
        a = p.acres
        assert a is not None
        if a < config.MIN_ACRES:
            r.add("ACRES_TOO_SMALL", Severity.FATAL, Species.NONE,
                  f"{a:.1f} ac is below the {config.MIN_ACRES:.0f} ac floor for a subdivision play")
        elif a > config.MAX_ACRES:
            r.add("ACRES_TOO_LARGE", Severity.WARN, Species.NONE,
                  f"{a:.1f} ac exceeds {config.MAX_ACRES:.0f} ac — may be an assembly, price per acre will govern")

    # --- road frontage -----------------------------------------------------
    rf = p.road_frontage_ft
    if rf is None:
        r.add("FRONTAGE_UNKNOWN", Severity.WARN, Species.NONE,
              "Road frontage unverified — access is a fatal issue if absent")
    elif rf < config.MIN_ROAD_FRONTAGE_FT:
        r.add("FRONTAGE_SHORT", Severity.WARN, Species.PAPER,
              f"{rf:.0f} ft frontage < {config.MIN_ROAD_FRONTAGE_FT:.0f} ft — may need a shared "
              "driveway, easement, or a variance (paper problem, solvable)")

    # --- wetlands ----------------------------------------------------------
    w = p.wetlands_pct
    if w is not None and w > config.MAX_WETLANDS_PCT:
        r.add("WETLANDS_HIGH", Severity.WARN, Species.CAPITAL,
              f"{w:.0f}% wetlands exceeds {config.MAX_WETLANDS_PCT:.0f}% — mitigation is a "
              "capital cost, not an entitlement exercise")

    # --- floodplain --------------------------------------------------------
    f = p.flood_pct
    if f is not None and f > config.MAX_FLOOD_PCT:
        r.add("FLOOD_HIGH", Severity.WARN, Species.CAPITAL,
              f"{f:.0f}% in floodplain exceeds {config.MAX_FLOOD_PCT:.0f}% — fill/grade cost")

    # --- slope -------------------------------------------------------------
    s = p.slope_over_15_pct
    if s is not None and s > config.MAX_STEEP_SLOPE_PCT:
        r.add("SLOPE_HIGH", Severity.WARN, Species.CAPITAL,
              f"{s:.0f}% of site steeper than 15% — grading/retaining cost")

    # --- soils -------------------------------------------------------------
    if p.soils_group in ("D",) or str(p.soils_group).upper().startswith("D"):
        r.add("SOILS_POOR", Severity.WARN, Species.CAPITAL,
              "Hydrologic soil group D (slow infiltration) — stormwater and septic both cost more")

    return r
