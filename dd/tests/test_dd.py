"""Tests for the DD decision engine. No network calls."""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from dd.schema import Parcel, ScreenResult, Severity, Species, Status  # noqa: E402
from dd.screens.physical import screen_physical  # noqa: E402
from dd.screens.regulatory import screen_regulatory  # noqa: E402
from dd.classify import classify  # noqa: E402
from dd.underwrite import underwrite, sensitivity  # noqa: E402
from dd.run import parse_range  # noqa: E402


# ---------- schema ---------------------------------------------------------
def test_acres_effective_midpoint():
    p = Parcel(apn="X", county="Test", acre_low=20, acre_high=200)
    assert p.acres_effective == 110.0
    assert p.acres_known is False


def test_acres_known_wins():
    p = Parcel(apn="X", county="Test", acres=37.5, acre_low=20, acre_high=200)
    assert p.acres_effective == 37.5
    assert p.acres_known is True


def test_max_lots_by_zoning():
    # 10 ac at 10,000 sq ft min lot => 435,600/10,000 = 43 lots
    p = Parcel(apn="X", county="Test", acres=10.0, min_lot_sqft=10_000)
    assert p.max_lots_by_zoning() == 43


def test_max_lots_none_without_zoning():
    p = Parcel(apn="X", county="Test", acres=10.0)
    assert p.max_lots_by_zoning() is None


# ---------- physical -------------------------------------------------------
def test_small_acreage_is_fatal():
    r = ScreenResult(Parcel(apn="X", county="Test", acres=3.0))
    screen_physical(r)
    assert any(f.code == "ACRES_TOO_SMALL" and f.severity == Severity.FATAL for f in r.flags)


def test_unknown_acres_is_warn_not_fatal():
    r = ScreenResult(Parcel(apn="X", county="Test"))
    screen_physical(r)
    codes = {f.code for f in r.flags}
    assert "ACRES_UNKNOWN" in codes
    assert not r.fatal


def test_wetlands_high_is_capital():
    r = ScreenResult(Parcel(apn="X", county="Test", acres=40, wetlands_pct=40))
    screen_physical(r)
    f = [x for x in r.flags if x.code == "WETLANDS_HIGH"][0]
    assert f.species == Species.CAPITAL


def test_short_frontage_is_paper():
    r = ScreenResult(Parcel(apn="X", county="Test", acres=40, road_frontage_ft=120))
    screen_physical(r)
    f = [x for x in r.flags if x.code == "FRONTAGE_SHORT"][0]
    assert f.species == Species.PAPER


# ---------- regulatory -----------------------------------------------------
def test_outside_ssa_is_fatal():
    r = ScreenResult(Parcel(apn="X", county="Test", acres=40, in_sewer_service_area=False))
    screen_regulatory(r)
    assert any(f.code == "OUTSIDE_SSA" and f.severity == Severity.FATAL for f in r.flags)
    assert r.verdict.value == "KILL"


# ---------- classifier -----------------------------------------------------
def test_paper_problem_classified_paper():
    # complete data required: unknowns force HOLD regardless of species
    r = ScreenResult(Parcel(apn="X", county="Test", acres=40,
                            road_frontage_ft=100, flu_code="AG", zoning="R-1",
                            min_lot_sqft=43_560, in_sewer_service_area=True))
    screen_physical(r); screen_regulatory(r)
    c = classify(r)
    assert c["species"] == "paper"
    assert c["verdict"] == "GO"


def test_capital_problem_classified_capital():
    r = ScreenResult(Parcel(apn="X", county="Test", acres=40,
                            wetlands_pct=45, road_frontage_ft=1_000,
                            min_lot_sqft=43_560, in_sewer_service_area=True))
    screen_physical(r); screen_regulatory(r)
    c = classify(r)
    assert c["species"] == "capital"
    assert c["verdict"] == "HOLD"


def test_unknowns_force_hold():
    r = ScreenResult(Parcel(apn="X", county="Test", acres=40, road_frontage_ft=100,
                            flu_code="AG", zoning="R-1"))
    screen_physical(r); screen_regulatory(r)
    c = classify(r)
    assert c["verdict"] == "HOLD"
    assert "INSUFFICIENT DATA" in c["reason"]


def test_fatal_beats_species():
    r = ScreenResult(Parcel(apn="X", county="Test", acres=5,
                            in_sewer_service_area=False))
    screen_physical(r); screen_regulatory(r)
    c = classify(r)
    assert c["verdict"] == "KILL"


# ---------- underwriting ---------------------------------------------------
def test_underwrite_basic():
    e = underwrite(40, 55_000, land_cost=600_000)
    assert e["revenue"] == 2_200_000
    assert e["soft_costs"] == 40 * 6_250
    assert e["all_in"] == 600_000 + 250_000
    assert e["margin"] == 2_200_000 - 850_000


def test_underwrite_dead_when_capital_exceeds():
    e = underwrite(44, 55_000, land_cost=975_000, capital_cost=2_100_000)
    assert e["margin"] < 0
    assert e["verdict"] == "DEAD"


def test_underwrite_no_lots():
    e = underwrite(None)
    assert "error" in e


def test_sensitivity_has_five_cases():
    s = sensitivity(44, 55_000, 975_000)
    assert len(s) == 5
    assert s["-10%"] < s["+0%"] < s["+10%"]


# ---------- parsing --------------------------------------------------------
def test_parse_range_scalar():
    assert parse_range("37.5") == (37.5, None, None)


def test_parse_range_range_with_dagger():
    assert parse_range("20-200†") == (None, 20.0, 200.0)


def test_parse_range_bad():
    assert parse_range("?") == (None, None, None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
