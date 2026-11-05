# DD — Land Due-Diligence Decision Engine

The **decision layer** that sits on top of the existing collection layer
(`agents/`, `scripts/`, `db/`). Collection answers *"what data exists?"*
This engine answers ***"does this parcel work, and why?"***

## Why it is mostly Python and only lightly agentic

| Layer | Technology | Reason |
|---|---|---|
| Screens, scoring, arithmetic | **Deterministic Python** | A right answer exists. Reproducible, instant, free, auditable |
| Ordinance/PDF field extraction | **Narrow LLM agent** | Language task — min lot sizes buried in code text |
| Municipal reply classification | **Narrow LLM agent** | Language task — is this reply "gravity denied" or "maybe"? |
| Letter + Act 68 request drafting | **Narrow LLM agent** | Language task, always human-approved |
| Anything leaving the building | **Human gate** | No outbound mail, no offers, ever automatic |

A "team of bots" that reasons about geometry and acreage is slower, costlier,
non-reproducible and impossible to audit. Bots are used only where language
judgment is genuinely required.

## Modules

```
dd/
  schema.py           Parcel, ScreenResult, Flag, Verdict, Species
  config.py           every threshold and assumption in one place
  screens/
    physical.py       acreage, frontage, wetlands, flood, slope, soils
    regulatory.py     zoning/FLU mismatch, min lot size, SSA -> plat eligibility
    infrastructure.py LIVE ECWRPC sewer-service-area lookup + capacity gap
  classify.py         PAPER problem vs CAPITAL problem (the key decision)
  underwrite.py       yield, revenue, all-in, margin, ±5/10% sensitivity
  run.py              county pipeline file -> screened JSON + markdown
  demo_estler.py      regression test: engine must reproduce a known KILL
  tests/test_dd.py    19 unit tests, no network
```

## The core distinction

> **A parcel discounted by a PAPER problem is a Cody deal.
> A parcel discounted by a CAPITAL problem is someone else's deal.**

Paper problems — zoning/FLU mismatch, missing plat, short frontage, expired CSM,
split title, lot-size variance — are solved with time, skill and a planner
relationship. Capital problems — lift stations, force mains, wetland mitigation,
rock, road builds — are solved with money. `classify.py` enforces this.

## Usage

```bash
cd /root/wisconsin-overlay-map
./venv/bin/python -m dd.run --county Outagamie          # online, if coords exist
./venv/bin/python -m dd.run --county Outagamie --no-network
./venv/bin/python -m dd.run --county Outagamie --coords coords.json \
        --lot-price 55000 --land-per-acre 15400
./venv/bin/python -m pytest dd/tests/test_dd.py -q       # 19 tests
./venv/bin/python -m dd.demo_estler                      # live regression check
```

Outputs: `output/dd/<County>_screened.{json,md}`

## Verified behaviour

Run against live data on 2026-10-27:

- **19/19 unit tests pass.**
- **Estler (111041000/111041200)** — engine returns `KILL` / `DEAD`, margin
  **−$930,000**, reason `PUMP_REQUIRED`, with the ECWRPC query confirming
  *inside* the sewer service area. This reproduces, in ~1 second, a conclusion
  that took two weeks of board transcripts and email. That is the regression
  test that matters: if the engine ever blesses Estler, it is broken.
- **Outagamie county-wide**: 200 parsed, **11 KILL** (all sub-20-acre parcels —
  correctly rejected as noise), **189 HOLD**, 0 GO.

## Known limitation — the honest one

The county-wide run returns **zero GO** because the collected data is missing
everything the screens need:

| Missing field | Parcels affected |
|---|---|
| Road frontage | 200 / 200 |
| Zoning / min lot size | 200 / 200 |
| Sewer service area | 200 / 200 |
| Verified acreage | 188 / 200 |

The collection layer captured APN, owner, growth grade and listing status — and
stopped. **Enrichment is the binding task**, not more screening:

1. **Geocode** each APN (needed for the SSA screen)
2. **Verified acreage** per APN
3. **Zoning district** + min lot size from the county code
4. **Road frontage** from the parcel geometry

`scripts/lp_slow_detail.py` was written for step 1–3 and appears incomplete.
Until enrichment runs, every parcel is honestly `HOLD`.

## No public dataset answers "is there sewer capacity"

`infrastructure.py` can tell you *inside vs outside* the service area (live, free,
accurate). It **cannot** tell you whether a connection is gravity or pumped, or
what capacity exists — nobody publishes that. This is precisely the gap that
killed Estler. The engine therefore emits `CAPACITY_UNVERIFIED` and refuses to
guess. Closing it requires a written answer from the utility:

> one template email per corridor to the county/village utilities department,
> citing Wisconsin Act 68 pre-submission conceptual review.

That is the human step the engine routes to rather than fakes.
