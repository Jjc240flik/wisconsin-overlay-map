# ESTLER PARCEL DEED & OWNERSHIP FORENSICS — N Mayflower Dr, Greenville, WI 54942
**Research date: Aug 18, 2026**

## 1. APNs (CONFIRMED)
| APN (PINLINK/TAXKEY) | PINDISPLAY | Legal | Deed Ac | GIS Ac | LP APN |
|---|---|---|---|---|---|
| **111041000** | 041000 | NE NE (less N483') Sec 12, T21N R16E | 23.40 | 22.18 | 11-1-0410-00 |
| **111041200** | 0412 | NW NE Sec 12, T21N R16E | 40.00 | 40.45 | 11-1-0412-00 |
| **Combined** | | | **63.40** | **62.62** | |
- Sources: Outagamie ArcGIS `County_Tax_Parcel_OpenData` (services.arcgis.com/VJeP6MUQzbTKwSpv); Land Portal API detail.
- MLS/Zillow confirm listing covers exactly these two parcels ("Parcel number: 111041000 and 111041200"). Listing acreage = 63.4 (deed acres). Our file's "±62" = GIS acres (62.6).
- Third related Essler holding, **NOT** in the MLS: PIN **101024400** (Town of Grand Chute, N Mayflower Dr, 13.71 deed / 11.46 GIS ac) — same family ownership cluster.

## 2. Recorded Owner (CONFIRMED)
- **ESSLER, BARBARA J** (note spelling: **ESSLER**, not Estler) — mailing 1924 N Elinor St, Appleton WI 54914.
- Co-owners: **REINKE, BARBARA J** (111041000) and **REINKE, DARLENE** (111041200). Grand Chute parcel: STARFELDT, DIANE R.
- School: Hortonville; Voc: FVTC. Zoning: Ag (AGD per concept plan; Zillow "Agricultural").

## 3. Ownership History (CONFIRMED: held 20+ yrs; PRICE: NO RELIABLE DATA)
- Deed **#1437530 recorded 11/21/2001** (cited in both parcels' chain) → held **>20 years** (matches our files).
- Later chain: #1587114 (11/14/2003, Ht-110/TOD), **#2021202 Deed 7/30/2014** (likely intra-family transfer to Reinke co-owners — unverified), #2221584 (1/25/2021 map/boundaries).
- Outagamie `SalesHistoryData_View` (39,883 records, back to 1997) returns **zero** rows for these PINs or ESSLER as buyer/seller → **no acquisition price available** (2001 transfer not in assessor's sales window). Land Portal has no sale history for either parcel.
- LandShark (landshark.outagamie.gov) timed out from sandbox; Ascent (ascent.outagamie.org) returned 403 — direct deed-imaged verification not possible here.

## 4. MLS Listing (CONFIRMED — STILL ACTIVE)
- **MLS #50280408** (RANW / WIREX via MLS GRID). Price **$1,280,000** (~$20,200/deed ac).
- **Status: ACTIVE / "Active-no offer"** as of Aug 18, 2026. Listed by **Kevin R Evers, Real Broker LLC** (920-277-6523).
- **DOM: 1,084+** (realtor.com/Zillow). Price history: Listed 8/30/2023 $1.28M → Contingent 5/23/2024 → Relisted 8/12/2024 $1.28M → still active. No price changes in 2.5 years.
- Description confirms our files: "POTENTIAL SELLER FINANCING… At almost 64 acres, these 2 parcels… majority tillable, small wooded areas; some preliminary wetland work done."

## 5. WHO IS "NINE TWENTY REALTY" — the 78-lot concept plan entity (CONFIRMED registry; RELATIONSHIP TO SELLER LIKELY)
- **WI DFI (apps.dfi.wi.gov) Entity N046495 — NINE TWENTY REALTY, LLC**; Domestic LLC; **organized 12/09/2016**; status **Restored to Good Standing 12/17/2022** (delinquent 10/1/2022 → restored). Annual reports filed 2017–2025 (2021 gap). No old names. Registered agent + principal office: **KEVIN EVERS, W4971 Natures Way Dr, Sherwood, WI 54169** (agent changes 1/6/2024 and 11/9/2025).
- **Same Kevin Evers = the MLS listing agent** for the Essler parcels (Real Broker LLC). Nine Twenty Realty is a Fox Valley brokerage (historically Little Chute/Appleton; per One Key Collective/Facebook, "Nine Twenty Realty is now brokered by Real Broker, LLC"; cf. Craig Harvey, One Key Collective).
- **Owns ZERO Outagamie parcels** (ArcGIS owner search) → NOT the recorded owner, and no deed of trust/option appears in parcel-level records.
- Our 2024 Greenville archive (`wisconsin-overlay-map/docs/Greenville_2024_Archive.md`): concept first discussed **3/12/2024** at Ad Hoc Village Development Committee ("55 Acres – Subdivision Mayflower Everglade.pdf"); **Davel Engineering finalized the 78-lot concept plan 6/25/2024 for Nine Twenty Realty**; prior analysis concluded Nine Twenty is "a separate entity from the current seller (the Barbara/Estler family)."
- **Interpretation (LIKELY):** Nine Twenty Realty (Kevin Evers) is the **developer/agent driving the concept plan — acting as contracted buyer/option-holder or development partner with seller financing in mind** (the MLS's seller-financing hook + Evers as both LLC principal and listing agent strongly suggest he controls a purchase path). **NO RELIABLE DATA** on an actual recorded option/PSA; not found in county sales/deed data as owner.

## 6. Assessed Values 2025–26
- **Land Portal (ATTOM, 2025 assessment):** 111041000 = **$7,300** (land $7,300; tax $81.81); 111041200 = **$11,700** (land $11,700; tax $131.60). Combined **$19,000**; Zillow shows annual tax $194. These are **Ag use-value** assessments, not market value (ag land locked in farmland-preservation use-value — important for the $900K–$1M target: assessed value is NOT a comp anchor).
- 2026 assessment: **NO RELIABLE DATA** (county snapshot layer is parcel-only; Ascent/LandShark inaccessible from sandbox). Note for diligence: tlp_estimate values are meaningless here ($351K/$396K ATTOM automated for ag land).

## Key takeaways for the deal file
1. Seller name is spelled **ESSLER** — use that for deed search/LOI paperwork.
2. MLS is stale (DOM 1,084, zero price cuts, once contingent 2024) → leverage for the $900K–$1M seller-financed target.
3. Nine Twenty Realty = Kevin Evers' vehicle; Evers is both the concept-plan entity and the listing agent → negotiate with Evers directly; confirm whether Nine Twenty holds an option (ASK the agent; not on record).
4. 63.4 acreage figure = deed acres; GIS = 62.6 — cite both.

**Sources:** Outagamie ArcGIS (County_Tax_Parcel_OpenData, OwnerViewParcel_test, SalesHistoryData_View), Land Portal API v2 (property IDs 170397030/170397486), Zillow/realtor.com listing #50280408, apps.dfi.wi.gov CorpSearch (N046495), wisconsin-overlay-map/docs/Greenville_2024_Archive.md.