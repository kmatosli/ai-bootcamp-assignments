# Caduceus REST API Design Document
**Rhenman & Partners Healthcare Equity Platform**
Version 1.0 | May 2026

---

## Application Description

Caduceus is a healthcare equity decision-support platform built for institutional buy-side analysts at Rhenman & Partners. It centralizes financial data, drug pipeline intelligence, analyst coverage assignments, and investment thesis management across a covered universe of pharmaceutical companies. The API serves the Caduceus decision application — a multi-user web interface accessible via Bloomberg ID.

---

## Resources

The Caduceus API exposes six primary resources:

| Resource | Description |
|---|---|
| `companies` | Covered pharmaceutical companies (PFE, MRK, JNJ, etc.) |
| `financial-facts` | EDGAR-sourced financial observations per company per period |
| `drugs` | Drug products with revenue, approval status, patent expiry |
| `therapeutic-areas` | Disease categories grouping drugs and analyst coverage |
| `analysts` | Rhenman team members with coverage assignments |
| `coverage` | Assignment of an analyst to a drug (with dates and notes) |

---

## Relationships

```
companies          ──< financial-facts     (one-to-many: one company, many financial observations)
companies          ──< drugs               (one-to-many: one company markets many drugs)
therapeutic-areas  ──< drugs               (one-to-many: one area, many drugs)
analysts           ──< coverage            (one-to-many: one analyst, many assignments)
drugs              ──< coverage            (one-to-many: one drug, many coverage records)
companies         >──< drugs               (many-to-many: company co-markets drugs with partners)
analysts          >──< therapeutic-areas   (many-to-many: analyst covers multiple areas)
```

**One-to-many examples:**
- Merck has many financial observations (revenue, R&D, CFO — across 40+ periods)
- AbbVie markets many drugs (Humira, Skyrizi, Rinvoq, Venclexta)

**Many-to-many examples:**
- Eliquis is co-marketed by both BMY and PFE
- An analyst may cover drugs across Oncology and Immunology

---

## Endpoints

### Base URL
```
https://api.caduceus.rhenman.se/v1
```

### Authentication
All endpoints require a valid JWT bearer token except `/health` and `/auth/login`.
Bloomberg ID OAuth2 is the primary authentication provider.

---

### Companies

| Method | URI | Description |
|---|---|---|
| GET | `/companies` | List all companies in the covered universe |
| GET | `/companies/{ticker}` | Get a single company by ticker |
| POST | `/companies` | Add a company to the universe (admin only) |
| PUT | `/companies/{ticker}` | Update company metadata |
| DELETE | `/companies/{ticker}` | Remove a company (soft delete — sets effective_to) |
| GET | `/companies/{ticker}/financial-facts` | All financial facts for a company |
| GET | `/companies/{ticker}/drugs` | All drugs marketed by a company |
| GET | `/companies/{ticker}/coverage` | All analyst coverage for a company |

### Financial Facts

| Method | URI | Description |
|---|---|---|
| GET | `/financial-facts` | Query financial facts (filter by ticker, metric, year, period) |
| GET | `/financial-facts/{id}` | Get a single financial fact by ID |
| POST | `/financial-facts` | Insert a new financial observation |
| PUT | `/financial-facts/{id}` | Update a financial fact (restatement) |
| GET | `/financial-facts/metrics` | List all available metric codes |

### Drugs

| Method | URI | Description |
|---|---|---|
| GET | `/drugs` | List all drugs (filter by therapeutic area, ticker, approved) |
| GET | `/drugs/{id}` | Get a single drug |
| POST | `/drugs` | Add a new drug to the pipeline |
| PUT | `/drugs/{id}` | Update drug metadata (revenue, patent expiry, etc.) |
| DELETE | `/drugs/{id}` | Remove a drug (soft delete) |
| GET | `/drugs/{id}/coverage` | Get all analyst coverage for a drug |

### Therapeutic Areas

| Method | URI | Description |
|---|---|---|
| GET | `/therapeutic-areas` | List all therapeutic areas |
| GET | `/therapeutic-areas/{id}` | Get a single therapeutic area |
| GET | `/therapeutic-areas/{id}/drugs` | All drugs in this therapeutic area |
| GET | `/therapeutic-areas/{id}/analysts` | All analysts covering this area |

### Analysts

| Method | URI | Description |
|---|---|---|
| GET | `/analysts` | List all active analysts |
| GET | `/analysts/{id}` | Get a single analyst profile |
| POST | `/analysts` | Add a new analyst (admin only) |
| PUT | `/analysts/{id}` | Update analyst profile |
| GET | `/analysts/{id}/coverage` | Get all active coverage assignments for an analyst |

### Coverage

| Method | URI | Description |
|---|---|---|
| GET | `/coverage` | List all active coverage assignments |
| POST | `/coverage` | Assign an analyst to cover a drug |
| PUT | `/coverage/{id}` | Update a coverage assignment (add notes) |
| DELETE | `/coverage/{id}` | End a coverage assignment (sets end_date) |

### Universe & Health

| Method | URI | Description |
|---|---|---|
| GET | `/universe` | Summary of the full covered universe with counts |
| GET | `/health` | API health check (public, no auth) |

---

## Request & Response Schemas

### POST `/companies` — Add a company to the universe

**Request body:**
```json
{
  "ticker":   "string, required, 1-10 chars, uppercase",
  "name":     "string, required, full legal name",
  "cik":      "string, optional, SEC CIK with leading zeros",
  "sector":   "string, optional, default='Healthcare'",
  "phase":    "integer, optional, default=1"
}
```

**Response — 201 Created:**
```json
{
  "caduceus_uuid": "uuid",
  "ticker":        "PFE",
  "name":          "Pfizer Inc",
  "cik":           "0000078003",
  "sector":        "Healthcare",
  "phase":         1,
  "effective_from": "2026-05-18",
  "effective_to":   null,
  "created_at":    "2026-05-18T19:00:00Z"
}
```

---

### POST `/coverage` — Assign analyst to drug

**Request body:**
```json
{
  "analyst_id":     "integer, required",
  "drug_id":        "integer, required",
  "assigned_date":  "string, required, ISO date YYYY-MM-DD",
  "coverage_notes": "string, optional"
}
```

**Response — 201 Created:**
```json
{
  "id":             1,
  "analyst_id":     3,
  "analyst_name":   "Amennai Beyeen",
  "drug_id":        7,
  "drug_name":      "Humira",
  "ticker":         "ABBV",
  "assigned_date":  "2026-05-18",
  "end_date":       null,
  "is_active":      true,
  "coverage_notes": "Primary Immunology coverage"
}
```

---

### GET `/companies/{ticker}/financial-facts` — Financial facts for a company

**Query parameters:**
```
metric      string   optional   Filter by metric code (e.g. revenue, rd_expense)
fiscal_year integer  optional   Filter by fiscal year (e.g. 2025)
period      string   optional   FY | Q1 | Q2 | Q3 | Q4
flag        string   optional   as_reported | restated | canonical (default: canonical)
```

**Response — 200 OK:**
```json
{
  "ticker":  "PFE",
  "count":   12,
  "facts": [
    {
      "id":             1001,
      "metric_code":    "revenue",
      "metric_label":   "Total Revenue",
      "fiscal_year":    2025,
      "fiscal_period":  "FY",
      "value":          62579.0,
      "unit":           "USD_millions",
      "flag":           "canonical",
      "accession_no":   "0000078003-26-000013",
      "filing_date":    "2026-02-19",
      "period_end":     "2025-12-31"
    }
  ]
}
```

---

### GET `/drugs` — List drugs with filters

**Query parameters:**
```
therapeutic_area  string   optional   Filter by area name (e.g. Oncology)
ticker            string   optional   Filter by company ticker
approved          boolean  optional   true | false
min_revenue       number   optional   Minimum annual revenue in $M
sort              string   optional   revenue | approval_date | patent_expiry
order             string   optional   asc | desc (default: desc)
page              integer  optional   default: 1
per_page          integer  optional   default: 20, max: 100
```

**Response — 200 OK:**
```json
{
  "count":    10,
  "page":     1,
  "per_page": 20,
  "drugs": [
    {
      "id":                   1,
      "brand_name":           "Keytruda",
      "generic_name":         "pembrolizumab",
      "ticker":               "MRK",
      "therapeutic_area":     "Oncology",
      "annual_revenue_usd_m": 29516.0,
      "is_approved":          true,
      "approval_date":        "2014-09-04",
      "patent_expiry":        "2028-12-31"
    }
  ]
}
```

---

## Authentication Plan

### Method: JWT Bearer Token via Bloomberg OAuth2

```
Authorization: Bearer <jwt_token>
```

All tokens expire after 8 hours (one trading day). Refresh tokens are valid for 30 days.

### Endpoint Access Matrix

| Endpoint | Public | Analyst | Admin |
|---|---|---|---|
| `GET /health` | ✓ | ✓ | ✓ |
| `GET /companies` | ✗ | ✓ | ✓ |
| `GET /companies/{ticker}` | ✗ | ✓ | ✓ |
| `POST /companies` | ✗ | ✗ | ✓ |
| `DELETE /companies/{ticker}` | ✗ | ✗ | ✓ |
| `GET /financial-facts` | ✗ | ✓ | ✓ |
| `POST /financial-facts` | ✗ | ✗ | ✓ |
| `GET /drugs` | ✗ | ✓ | ✓ |
| `POST /drugs` | ✗ | ✗ | ✓ |
| `GET /analysts` | ✗ | ✓ | ✓ |
| `POST /analysts` | ✗ | ✗ | ✓ |
| `GET /coverage` | ✗ | ✓ | ✓ |
| `POST /coverage` | ✗ | ✓ | ✓ |
| `DELETE /coverage/{id}` | ✗ | ✓ (own) | ✓ |

**Rules:**
- Analysts can assign and end their own coverage but not others'
- Only admins can add/remove companies, drugs, or analysts
- All financial data is read-only for analysts — writes go through the EDGAR pipeline

---

## Error Responses

### Most important endpoint: `GET /companies/{ticker}/financial-facts`

| Status Code | Reason | Response body |
|---|---|---|
| 200 OK | Success — facts returned | `{ "ticker": "PFE", "count": 12, "facts": [...] }` |
| 400 Bad Request | Invalid query parameter | `{ "error": "invalid_param", "message": "fiscal_year must be an integer" }` |
| 401 Unauthorized | Missing or expired token | `{ "error": "unauthorized", "message": "Bearer token required" }` |
| 403 Forbidden | Valid token but insufficient role | `{ "error": "forbidden", "message": "Analyst role required" }` |
| 404 Not Found | Ticker not in covered universe | `{ "error": "not_found", "message": "Ticker XYZ not found in universe" }` |
| 422 Unprocessable | Valid params but no data found | `{ "error": "no_data", "message": "No facts for PFE FY2030" }` |
| 429 Too Many Requests | Rate limit exceeded | `{ "error": "rate_limited", "message": "60 requests/minute limit exceeded" }` |
| 500 Internal Server Error | Unexpected server failure | `{ "error": "server_error", "message": "Contact support" }` |

---

## URI Design Evaluation

### Bad URIs from the rubric — corrected:

| Original | Problem | Corrected |
|---|---|---|
| `GET /getAllUsers` | Verb in URI, not RESTful | `GET /analysts` |
| `GET /user/5` | Singular noun | `GET /analysts/5` |
| `DELETE /removeProduct?id=12` | Verb in URI, ID in query string | `DELETE /drugs/12` |
| `PUT /updateUser/5` | Verb in URI | `PUT /analysts/5` |
| `GET /users/5/orders/10/items/3/reviews/1/replies` | Over-nested (4+ levels) | `GET /reviews/1/replies` — flatten it |

### Good URIs (already correct):
- `POST /users` — correct verb + plural noun
- `GET /products?category=electronics&sort=price` — filtering via query params, correct
- `GET /users/5/orders` — nested resource, 2 levels deep, acceptable

### Caduceus URI design decisions:

**Why `/companies/{ticker}` not `/companies/{id}`?**
Analysts think in tickers (PFE, MRK, LLY) — never in database IDs. The ticker is the natural key for this domain. Internal UUID is used as the database primary key but never exposed in the API.

**Why `/financial-facts` as a top-level resource?**
Financial facts are queried across multiple companies simultaneously (sector aggregates, peer comparisons). A nested-only design `/companies/{ticker}/financial-facts` would force N calls for an N-company comparison. The top-level endpoint supports `?ticker=PFE,MRK,LLY` multi-ticker queries.

**Why soft deletes everywhere?**
`DELETE /companies/{ticker}` sets `effective_to = today` — it never destroys data. Caduceus is a point-in-time system. Historical data must be reproducible exactly as it appeared on any given date.

---

## Rate Limiting

- 60 requests per minute per authenticated user
- 1,000 requests per hour per authenticated user
- Rate limit headers returned on every response:
  ```
  X-RateLimit-Limit: 60
  X-RateLimit-Remaining: 47
  X-RateLimit-Reset: 1716912000
  ```

---

## Versioning

API version is included in the URL path: `/v1/`. Breaking changes increment to `/v2/`. Non-breaking additions (new fields, new endpoints) are added to the current version without a version bump.
