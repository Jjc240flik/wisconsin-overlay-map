"""Species classifier — paper problem or capital problem?

This is the single most valuable decision in the pipeline. A parcel discounted
because of a PAPER problem is a Cody deal. A parcel discounted because of a
CAPITAL problem is someone else's deal.

Rule-based and auditable on purpose: every classification cites its trigger.
"""
from __future__ import annotations

from .schema import ScreenResult, Species, Severity, Verdict

# Codes that indicate a paper (entitlement) problem.
PAPER_CODES = {
    "FLU_MISMATCH", "FRONTAGE_SHORT", "CSM_ONLY", "SETBACK_VARIANCE",
    "EXPIRED_PLAT", "TITLE_SPLIT", "DEED_RESTRICTION", "MIN_LOT_VARIANCE",
    "ACCESS_EASEMENT",
}

# Codes that indicate a capital (money + contractor) problem.
CAPITAL_CODES = {
    "PUMP_REQUIRED", "WETLANDS_HIGH", "FLOOD_HIGH", "SLOPE_HIGH",
    "SOILS_POOR", "CAPACITY_UNVERIFIED", "ROCK", "OFFSITE_UTILITY",
    "FORCEMAIN", "ROAD_BUILD",
}


# Codes that mean "we do not know yet" — distinct from "no problem found".
UNKNOWN_CODES = {
    "ACRES_UNKNOWN", "ZONING_UNSET", "SSA_UNKNOWN", "FRONTAGE_UNKNOWN",
    "NO_COORDS", "SSA_ERROR", "CAPACITY_UNVERIFIED",
}


def classify(r: ScreenResult) -> dict:
    """Return {'species','paper':[...],'capital':[...],'verdict','reason'}"""
    codes = {f.code for f in r.flags}
    paper = sorted(codes & PAPER_CODES)
    capital = sorted(codes & CAPITAL_CODES)
    unknowns = sorted(codes & UNKNOWN_CODES)
    fatal_capital = [f.code for f in r.flags
                     if f.species == Species.CAPITAL and f.severity == Severity.FATAL]
    fatal_any = [f.code for f in r.fatal]

    # Any fatal flag ends it, regardless of species.
    if fatal_any:
        return {"species": Species.NONE.value, "paper": paper, "capital": capital,
                "unknowns": unknowns, "verdict": Verdict.KILL.value,
                "reason": f"Fatal constraint: {', '.join(sorted(set(fatal_any)))}"}

    if fatal_capital:
        return {"species": Species.CAPITAL.value, "paper": paper, "capital": capital,
                "unknowns": unknowns, "verdict": Verdict.KILL.value,
                "reason": f"Capital problem beyond financing ceiling: {', '.join(fatal_capital)}"}

    # Cannot classify what has not been measured.
    if unknowns:
        missing = ", ".join(unknowns)
        return {"species": Species.NONE.value, "paper": paper, "capital": capital,
                "unknowns": unknowns, "verdict": Verdict.HOLD.value,
                "reason": f"INSUFFICIENT DATA — enrich before judging. Missing: {missing}"}

    if capital and not paper:
        return {"species": Species.CAPITAL.value, "paper": paper, "capital": capital,
                "unknowns": unknowns, "verdict": Verdict.HOLD.value,
                "reason": "Discount is driven by capital cost (wetlands/flood/grade/utility), "
                          "not by entitlement. Not Jason's game unless the cost is small."}

    if paper:
        return {"species": Species.PAPER.value, "paper": paper, "capital": capital,
                "unknowns": unknowns, "verdict": Verdict.GO.value,
                "reason": "Discount is driven by an entitlement problem — solvable with time, "
                          "skill, and a planner relationship. This is the target profile."}

    return {"species": Species.NONE.value, "paper": paper, "capital": capital,
            "unknowns": unknowns, "verdict": Verdict.HOLD.value,
            "reason": "No problem identified — why is it discounted? If it isn't, there is no deal."}
