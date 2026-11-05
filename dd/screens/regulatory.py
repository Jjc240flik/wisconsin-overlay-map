"""Screen B — regulatory / entitlement. Answers 'what does the code actually allow'."""
from __future__ import annotations

from .. import config
from ..schema import ScreenResult, Severity, Species


def screen_regulatory(r: ScreenResult) -> ScreenResult:
    p = r.parcel

    # --- zoning -> min lot size -------------------------------------------
    if p.min_lot_sqft is None:
        r.add("ZONING_UNSET", Severity.WARN, Species.NONE,
              "Minimum lot size not established — pull the zoning code before underwriting")
    else:
        lots = p.max_lots_by_zoning()
        if lots is not None:
            r.notes.append(f"Gross yield by zoning: {lots} lots "
                           f"({p.acres_effective:.1f} ac / {p.min_lot_sqft:,.0f} sq ft)")

    # --- FLU vs zoning mismatch = classic paper problem -------------------
    if p.flu_code and p.zoning and p.flu_code.upper() != p.zoning.upper():
        r.add("FLU_MISMATCH", Severity.INFO, Species.PAPER,
              f"FLU '{p.flu_code}' vs zoning '{p.zoning}' — rezoning required. "
              "This is the discount AND the value-add")

    # --- sewer service area -> plat eligibility ---------------------------
    # This is the single most expensive mistake in the whole pipeline.
    if p.in_sewer_service_area is False:
        r.add("OUTSIDE_SSA", Severity.FATAL, Species.NONE,
              "Parcel is OUTSIDE the sewer service area: subdivision plat is prohibited and "
              f"only {config.CSM_LOTS_PER_YEAR} CSM lots/year are allowed. No 40-lot play exists here.")
    elif p.in_sewer_service_area is True:
        r.notes.append("Inside sewer service area — public sewer/water is mandatory; "
                       "connection feasibility now governs.")
    else:
        r.add("SSA_UNKNOWN", Severity.WARN, Species.NONE,
              "Sewer service area status unverified — run the infrastructure screen")

    # --- jurisdiction knowledge ------------------------------------------
    j = config.JURISDICTIONS.get(p.muni.lower().strip())
    if j:
        r.notes.append(f"Jurisdiction note ({p.muni}): {j.get('notes','')}")
        if j.get("lift_station"):
            r.notes.append(f"Known infrastructure issue: {j['lift_station']}")

    return r
