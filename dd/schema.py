"""Canonical parcel schema and result types for the due-diligence engine.

Design rule: everything here is deterministic and JSON-serialisable so that
every screen result is reproducible and auditable. No LLM calls in this layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional

ACRE_SQFT = 43560.0


class Status(str, Enum):
    FOR_SALE = "for_sale"
    OFF_MARKET = "off_market"
    UNKNOWN = "unknown"


class Verdict(str, Enum):
    GO = "GO"        # passes screens, economics work
    HOLD = "HOLD"    # missing information, do not spend yet
    KILL = "KILL"    # fatal constraint


class Species(str, Enum):
    """Two species of discount. This distinction drives the whole engine."""
    PAPER = "paper"      # solvable with time + entitlement skill
    CAPITAL = "capital"  # requires money + contractors (NOT Jason's game)
    NONE = "none"


class Severity(str, Enum):
    INFO = "info"
    WARN = "warn"
    FATAL = "fatal"


@dataclass
class Flag:
    code: str
    severity: Severity
    species: Species
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "severity": self.severity.value,
                "species": self.species.value, "message": self.message}


@dataclass
class Parcel:
    apn: str
    county: str
    muni: str = ""
    owner: str = ""
    acres: Optional[float] = None
    acre_low: Optional[float] = None   # when source gives a range e.g. 20-200
    acre_high: Optional[float] = None
    status: Status = Status.UNKNOWN
    grade: str = ""                    # source growth grade (A+/A/...)
    zoning: str = ""
    flu_code: str = ""
    min_lot_sqft: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    road_frontage_ft: Optional[float] = None
    wetlands_pct: Optional[float] = None
    flood_pct: Optional[float] = None
    slope_over_15_pct: Optional[float] = None
    soils_group: str = ""
    in_sewer_service_area: Optional[bool] = None
    sewer_capacity: str = "unknown"     # gravity | pump | unknown
    attrs: dict = field(default_factory=dict)

    # ---- derived helpers -------------------------------------------------
    @property
    def acres_known(self) -> bool:
        return self.acres is not None

    @property
    def acres_effective(self) -> Optional[float]:
        """Best available acreage. Midpoint of a range when only a range exists."""
        if self.acres is not None:
            return self.acres
        if self.acre_low is not None and self.acre_high is not None:
            return (self.acre_low + self.acre_high) / 2.0
        return None

    def max_lots_by_zoning(self) -> Optional[int]:
        """Gross lot yield from acreage and minimum lot size. Not a site plan."""
        a = self.acres_effective
        if a is None or not self.min_lot_sqft:
            return None
        return int((a * ACRE_SQFT) // self.min_lot_sqft)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        d["acres_effective"] = self.acres_effective
        d["acres_known"] = self.acres_known
        d["max_lots_by_zoning"] = self.max_lots_by_zoning()
        return d


@dataclass
class ScreenResult:
    parcel: Parcel
    flags: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    def add(self, code, severity, species, message) -> None:
        self.flags.append(Flag(code, severity, species, message))

    @property
    def fatal(self) -> list:
        return [f for f in self.flags if f.severity == Severity.FATAL]

    @property
    def verdict(self) -> Verdict:
        if self.fatal:
            return Verdict.KILL
        warns = [f for f in self.flags if f.severity == Severity.WARN]
        if warns or not self.parcel.acres_known:
            return Verdict.HOLD
        return Verdict.GO

    def to_dict(self) -> dict:
        return {
            "apn": self.parcel.apn,
            "county": self.parcel.county,
            "muni": self.parcel.muni,
            "owner": self.parcel.owner,
            "acres": self.parcel.acres_effective,
            "status": self.parcel.status.value,
            "grade": self.parcel.grade,
            "verdict": self.verdict.value,
            "fatal": [f.to_dict() for f in self.fatal],
            "flags": [f.to_dict() for f in self.flags],
            "notes": self.notes,
        }
