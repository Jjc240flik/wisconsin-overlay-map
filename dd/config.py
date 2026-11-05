"""Tunable assumptions for the DD engine. Everything in one place, no magic numbers.

Change these and every downstream verdict moves — that is deliberate, so that a
sensitivity run is one edit instead of a code hunt.
"""
from __future__ import annotations

# ---- Category 1 physical filter (Cody / North Star) ----------------------
MIN_ACRES = 20.0
MAX_ACRES = 200.0
MIN_ROAD_FRONTAGE_FT = 300.0
MAX_WETLANDS_PCT = 25.0
MAX_FLOOD_PCT = 50.0
MAX_STEEP_SLOPE_PCT = 50.0     # % of site with slope > 15%

# ---- Regulatory ----------------------------------------------------------
# Wisconsin: outside a sewer service area a subdivision PLAT is prohibited and
# only 10 CSM lots per calendar year are allowed (Greenville 270-8.1 pattern).
CSM_LOTS_PER_YEAR = 10

# ---- Economics (defaults — override per deal) ---------------------------
DEFAULTS = {
    "lot_price": 55_000.0,          # finished lot, validated $50-75K band
    "soft_cost_per_lot": 6_250.0,   # engineering, legal, rezoning, contingency
    "land_basis_per_acre": None,    # None => derive from list price if known
    "target_margin_pct": 20.0,      # minimum acceptable margin on revenue
    "sales_absorption_months": 24,
}

# ---- Capital-problem ceiling --------------------------------------------
# Anything above this, per lot, converts the discount from a paper problem
# into a capital problem. Jason cannot finance capital problems.
MAX_CAPITAL_COST_PER_LOT = 8_000.0
MAX_CAPITAL_COST_TOTAL = 350_000.0

# ---- Jurisdiction knowledge base ----------------------------------------
# Extend as corridors are learned. Keyed by lower-case municipality.
JURISDICTIONS = {
    "greenville": {
        "sewer_rule": "Plats prohibited outside sewer service area; public sewer+water "
                      "mandatory inside it (Ord. 270-8.1)",
        "csm_cap_per_year": 10,
        "lift_station": "Lift Station No. 4 ~$2.0-2.3M; area north of Everglade Road "
                        "must be pumped; Village requires developer to install + recapture",
        "planner": "Mark Mommaerts, AICP",
        "notes": "Act 68 pre-submission conceptual review available by right",
    },
}
