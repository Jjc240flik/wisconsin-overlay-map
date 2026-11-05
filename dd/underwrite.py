"""Underwriting — the arithmetic, with sensitivity. No opinions, only spreadsheets."""
from __future__ import annotations

from . import config


def underwrite(lots: int | None,
               lot_price: float | None = None,
               land_cost: float | None = None,
               soft_per_lot: float | None = None,
               capital_cost: float = 0.0,
               target_margin_pct: float | None = None) -> dict:
    """Return a full economics block. All values are gross of financing unless noted."""
    lot_price = lot_price if lot_price is not None else config.DEFAULTS["lot_price"]
    soft_per_lot = (soft_per_lot if soft_per_lot is not None
                    else config.DEFAULTS["soft_cost_per_lot"])
    target = (target_margin_pct if target_margin_pct is not None
              else config.DEFAULTS["target_margin_pct"])

    if not lots:
        return {"error": "no lot yield — cannot underwrite", "lots": lots}

    revenue = lots * lot_price
    soft = lots * soft_per_lot
    land = land_cost or 0.0
    all_in = land + soft + capital_cost
    margin = revenue - all_in
    margin_pct = (margin / revenue * 100.0) if revenue else 0.0

    verdict = "GO" if margin_pct >= target else ("THIN" if margin > 0 else "DEAD")

    return {
        "lots": lots,
        "lot_price": lot_price,
        "revenue": round(revenue, 2),
        "land_cost": round(land, 2),
        "soft_costs": round(soft, 2),
        "capital_costs": round(capital_cost, 2),
        "all_in": round(all_in, 2),
        "margin": round(margin, 2),
        "margin_pct": round(margin_pct, 2),
        "margin_per_lot": round(margin / lots, 2),
        "target_margin_pct": target,
        "verdict": verdict,
    }


def sensitivity(lots: int,
                lot_price: float | None = None,
                land_cost: float | None = None,
                capital_cost: float = 0.0) -> dict:
    """How much a 5% / 10% yield miss costs. Guards against pricing on a soft estimate."""
    out = {}
    for err in (0.0, -0.05, 0.05, -0.10, 0.10):
        adj = int(round(lots * (1 + err)))
        out[f"{err*100:+.0f}%"] = underwrite(adj, lot_price, land_cost,
                                             capital_cost=capital_cost)["margin"]
    return out
