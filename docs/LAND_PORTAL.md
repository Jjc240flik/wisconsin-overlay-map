# Land Portal — Complete Reference

**Last updated:** July 13, 2026
**Sources:** LP Help Center, OpenAPI spec (v2), observed API behavior, Land Portal Source Layer

---

## 1. API Authentication

### Key Format
- Prefix: `lp_live_…`
- Header: `Authorization: Bearer <key>`
- Generated at: landportal.com → Profile → API tab → Generate API Key

### Key States
| Docs (openapi.json) | Data endpoint | Meaning | Action |
|---|---|---|---|
| 200 OK | 200 OK | Key fully valid | Proceed |
| 200 OK | 401 Unauthorized | Key exists but data access revoked | Regenerate key |
| 401 Unauthorized | 401 Unauthorized | Key invalid/expired | Generate new key |

### Key Regeneration
1. Visit https://landportal.com and log in
2. Click **Profile** in left sidebar
3. Click **API tab** at top
4. Click **Generate API Key**
5. Confirm password
6. Copy new key (`lp_live_…` prefix)

**IMPORTANT:** landportal.com has Cloudflare bot protection — cannot be automated via browser tools. User must do this manually.

---

## 2. API Base URL

```
https://api.landportal.com
```

---

## 3. Endpoint Reference

### Filter Data (Bulk Queries) — **NO DAILY LIMIT**

| Method | Endpoint | Description |
|---|---|---|
| POST | `/v2/filter-data` | Bulk filtered property search with pagination |
| GET | `/v2/filter-data/filters` | List all available filter keys, operators, value sources |
| GET | `/v2/filter-data/filters/{key}/values` | Get selectable values for a filter key |

**Rate limit:** NONE — "Filter data requests are not subject to daily limits" (per OpenAPI spec).
**Page size:** 100 results per page. Use `?page_token=VALUE` for pagination.
**Results limit:** 50,000 total results per query.

### Properties (Read / Search) — **DAILY LIMIT**

| Method | Endpoint | Description |
|---|---|---|
| GET | `/v2/properties` | Search by owner, APN, or address (max 10 results) |
| GET | `/v2/properties/{propertyId}` | Full detail for one property (GeoJSON Feature) |
| GET | `/v2/properties/point` | Resolve parcel at lat/lon coordinates |

**Rate limit:** Daily `single_property_limit` quota. When exhausted, consumes subscription export row balance. When both exhausted, returns 429.

### Exports — **SUBSCRIPTION TOKENS**

| Method | Endpoint | Description |
|---|---|---|
| POST | `/v2/exports` | Queue CSV export by property IDs (max 100,000 IDs) |
| GET | `/v2/exports` | List export tasks, poll status, download completed CSVs |

**Rate limit:** Uses subscription export token balance. Pro plan: 20,000 free exports/month. Enterprise: unlimited.

### Comps / Reports

| Method | Endpoint | Description |
|---|---|---|
| POST | `/v2/reports/comps` | Queue a comp report for a property |
| GET | `/v2/reports/comps` | List existing comp reports |
| GET | `/v2/reports/comps/{reportId}` | Fetch completed comp report data |

---

## 4. Rate Limits — Summary

| Endpoint | Limit Type | Observed Behavior |
|---|---|---|
| `POST /v2/filter-data` | **No daily limit** | Unlimited queries. Use for all discovery. |
| `GET /v2/properties/{id}` | **Daily quota** | ~200-300 calls/day before 429. Pacing: 1 req per 2-5 seconds. |
| `POST /v2/exports` | **Subscription tokens** | Pro: 20,000/month. Enterprise: unlimited. |

**429 error messages:**
- Detail endpoint: `"You have reached your daily single property limit and your subscription export tokens are exhausted."`
- Export endpoint: `"Your subscription export token balance is exhausted."`

**Best practice:** Use filter-data for all discovery. Use detail endpoint only for properties needing acreage/prices/coordinates. Pace at 1 req per 2-5 seconds with 30-60s pauses every 20-50 requests.

---

## 5. Category 1 — Subdivision / Bulk Land Filters

From the North Star / Cody Bjugan methodology and the Search Filters doc:

```
20-200 acres, road frontage ≥300ft, wetlands ≤25%, FEMA ≤50%, slope sum_up_to_15 ≥50%, vacant land
```

### Off-Market Payload
```json
{
  "fips": ["55009"],
  "filters": [
    {"key": "municipality", "operator": "condition", "value": "TOWN OF LEDGEVIEW"},
    {"key": "lotsizeacres", "operator": "range", "value": {"min": 20, "max": 200}},
    {"key": "vacant", "operator": "boolean", "value": true},
    {"key": "road_frontage", "operator": "range", "value": {"min": 300}},
    {"key": "wetlands_cover_percentage", "operator": "range", "value": {"max": 25}},
    {"key": "fema_cover_percentage", "operator": "range", "value": {"max": 50}},
    {"key": "sum_up_to_15", "operator": "range", "value": {"min": 50}}
  ]
}
```

### For-Sale Payload (all 5 land codes)
```json
{
  "fips": ["55009"],
  "filters": [
    {"key": "municipality", "operator": "condition", "value": "TOWN OF LEDGEVIEW"},
    {"key": "landusecode", "operator": "condition", "value": "8000"},
    {"key": "active_listing_toggle", "operator": "active_listing_toggle", "value": true}
  ]
}
```
Land codes: 8000 (Vacant General), 8001 (Residential Vacant), 8008 (Rural/Ag Vacant), 7000 (Agricultural), 7001 (Farm Land)

---

## 6. Filter Reference

### Available Filter Keys (partial — most used)

| Key | Type | Description |
|---|---|---|
| `municipality` | condition | Exact town name (varies by county!) |
| `situszip5` | condition | 5-digit ZIP code |
| `fips` | condition | 5-digit county FIPS |
| `lotsizeacres` | range | Lot size in acres |
| `vacant` | boolean | Vacant lots only |
| `road_frontage` | range | Road frontage in feet |
| `wetlands_cover_percentage` | range | Wetlands coverage % |
| `fema_cover_percentage` | range | FEMA flood zone coverage % |
| `sum_up_to_15` | range | % of land under 15% slope |
| `landusecode` | condition | ATTOM land use code (single value only) |
| `land_locked` | boolean | Land-locked parcels |
| `city_limits` | boolean | Outside city limits |
| `active_listing_toggle` | toggle | Include active MLS listings |
| `owneroccupied` | condition | Owner occupied status |
| `out_of_state` | boolean | Out of state owner |
| `corporate_owned` | boolean | Corporate owned |
| `zoning` | condition | Zoning code (varies by county) |

### Municipality Names — CRITICAL PITFALL
Municipality names are NOT consistent across counties. Always query values first:
```
GET /v2/filter-data/filters/municipality/values?fips=55009
```

| County | Town format | Village format | City format |
|---|---|---|---|
| Brown | `TOWN OF LEDGEVIEW` | `VILLAGE OF ASHWAUBENON` | `CITY OF GREEN BAY` |
| Outagamie | `TOWN OF GRAND CHUTE` | `VILLAGE OF GREENVILLE` | `CITY OF APPLETON` |
| Rock | `BELOIT` (bare!) | `VILLAGE OF CLINTON` | `CITY OF BELOIT` |
| Milwaukee | `FRANKLIN` (bare!) | — | `MILWAUKEE` (bare) |

---

## 7. Filter-Data Response Fields

The response includes: `fips`, `apn`, `street_address`, `owner_full_name`, `lot_size_acres`, `property_id`

**PITFALL:** `lot_size_acres` is NOT returned for these counties in filter-data results:
- Outagamie, Calumet, Milwaukee, Waukesha, Winnebago

Use `GET /v2/properties/{id}` for these counties. The detail endpoint returns `calc_acres` as an alternative field.

---

## 8. Owner Filtering Rules

Exclude:
- Trusts: `TRUST`, `TRST`, `REVOCABLE`, `REVOCABL`, `IRREVOCABLE`, `IRREVOCABL`, `REV TR`, `LIV TR`, `IRREV TR`, `REVO`
- Government: `COUNTY`, `TOWNSHIP`, `CITY OF`, `STATE OF`, `NATION`, `TRIBE`, `VILLAGE OF`, `TOWN OF`, `HOUSING AUTHORITY`, `DEPT OF`, `DEPARTMENT OF`, `DOT`, `DNR`
- Utilities: `ELECTRIC POWER`, `SCHOOL DISTRICT`, `SANITARY DISTRICT`, `UNIFIED SCHOOL`
- HOAs: `OWNERS OF LOTS`, `LOT OWNERS OF`, `HOMEOWNERS ASSOC`
- Data artifacts: `AVAILABLE NOT`, `AVAILABLE`, `NOT AVAILABLE`, `UNKNOWN`, `N/A`
- Corporate: `INC`, `CORP`, `INCORPORATED`
- Non-Farm LLCs: `LLC` or `L L C` without `FARM` in name

Keep: Individual names, Farm LLCs, Farm LLPs, Limited Partnerships, Sole Proprietorships

---

## 9. County FIPS Reference

| County | FIPS | Primary Growth Node |
|---|---|---|
| Outagamie | 55087 | Appleton → Greenville, Grand Chute |
| Brown | 55009 | Green Bay → Ledgeview, Lawrence |
| Dane | 55025 | Madison → Verona, Fitchburg |
| Waukesha | 55133 | Milwaukee → Menomonee Falls, Lisbon |
| Ozaukee | 55089 | Milwaukee → Grafton, Cedarburg |
| Milwaukee | 55079 | Franklin, Oak Creek |
| Rock | 55105 | Janesville/Beloit → Stateline |
| Winnebago | 55139 | Oshkosh/Neenah → US 41 |
| Calumet | 55015 | Appleton → Harrison |
| Door | 55029 | Sturgeon Bay → Sister Bay |

---

## 10. LP Help Center — Key Articles

### Subdivide Lead List
- 20-100 acres (LP recommends)
- Outside city limits
- Landlocked: No
- Min road frontage: 1,000 ft (LP recommends)
- Buildability: ≥30%
- Min buildable acres: 8
- Max FEMA: 50%
- Max wetlands: 50%
- Source: https://help.landportal.com/article/60-build-profitable-subdivide-lead-lists-on-land-portal

### API Key
- Generated at Profile → API tab
- "Each key is tied to your account usage limits and may consume export/skip trace tokens"
- Source: https://help.landportal.com/article/74-how-to-find-your-api-key-in-land-portal

### Export / Duplicate Removal
- Remove duplicates: keeps largest-acreage parcel per unique address
- Remove empty mailing addresses: excludes non-deliverable records
- Pro plan: 20,000 free exports per month
- Enterprise: unlimited exports
- Source: https://help.landportal.com/article/41-removing-duplicates-exported-data

### Bulk Skip Trace
- 10¢ per record default
- Bulk tokens: as low as 5¢ per record
- Up to 6 phone numbers per contact
- Source: https://help.landportal.com/article/28-how-to-bulk-skip-trace

---

## 11. Common Errors

| HTTP | Meaning | Action |
|---|---|---|
| 200 | OK | Proceed |
| 400 | Bad request / unsupported filter | Check filter key and operator |
| 401 | Invalid/expired key | Regenerate key |
| 429 | Rate limited | Daily quota exhausted — wait for reset |
| 404 | Endpoint not found | Check URL |
| 422 | Invalid input | Check parameter values |
| 500 | Server error | Retry |

---

## 12. Pagination

Filter-data returns 100 results per page. Pass `?page_token=VALUE` as query parameter on the POST URL (NOT in the request body):

```
POST /v2/filter-data?page_token=MTAw
```

Empty `next_page_token` means all results returned.

---

## 13. Data Quality Notes

- Some counties don't return `lot_size_acres` in filter-data (Outagamie, Calumet, Milwaukee, Waukesha, Winnebago)
- Detail endpoint returns `calc_acres` as alternative to `lot_size_acres`
- Municipality names are inconsistent across counties — always discover first
- For-sale listings require querying ALL 5 land codes (8000, 8001, 8008, 7000, 7001) — code 8001 alone misses most listings
- Filter-data for-sale results do NOT include sale prices — need detail endpoint for prices
- The `mls_propertytype` filter requires MLS data access (may not be included in all plans)