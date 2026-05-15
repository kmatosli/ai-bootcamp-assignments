# Data Cleaning + Visualization — Caduceus EDGAR Observations

**Coding Temple AI Bootcamp · Module 2 · Data Cleaning and Visualization**
Author: Kathy Matos

A real-data implementation of the Module 2 Data Cleaning + matplotlib deliverable, applied to live SEC EDGAR financial observations from the Caduceus healthcare equity decision-support platform.

The data layer covers 8 large-cap healthcare names (Caduceus Phase 1 universe). The chart layer presents a **7-name pure-pharma comparison** — JNJ is excluded from the analytical visualizations because its MedTech segment and ~$94B scale distort comparability with pure-pharma peers. JNJ remains in the underlying data for cross-checks.

## What this submission does

1. **Loads** real EDGAR observations from a bundled CSV snapshot (or live Supabase if `DATABASE_URL` is set)
2. **Cleans** the data: type coercion, null-handling, fiscal-period normalization, period-length classification, restatement-aware deduplication
3. **Validates** coverage (every ticker × concept), period coverage per ticker, and revenue magnitude sanity
4. **Visualizes** three branded analytical panels: FY revenue ranking, quarterly trend, and R&D intensity

## Data source — real, not synthetic

The dataset is **2,105 real SEC EDGAR XBRL observations** sourced from official 10-K and 10-Q filings of 8 large-cap pharmaceutical companies:

| Ticker | Company | CIK |
|---|---|---|
| PFE | Pfizer Inc. | 0000078003 |
| MRK | Merck & Co. Inc. | 0000310158 |
| JNJ | Johnson & Johnson | 0000200406 |
| ABBV | AbbVie Inc. | 0001551152 |
| BMY | Bristol-Myers Squibb Co. | 0000014272 |
| LLY | Eli Lilly and Co. | 0000059478 |
| AMGN | Amgen Inc. | 0000318154 |
| GILD | Gilead Sciences Inc. | 0000882184 |

Data path: **SEC EDGAR XBRL API → `edgartools` Python library → Caduceus Supabase Postgres → bundled CSV**. The full pipeline lives in the [Caduceus](https://github.com/kmatosli/Caduceus) repo at `data-foundation/adapters/edgartools_adapter.py`.

Spot-check (FY 2024 revenue, USD):

| Ticker | Reported (10-K) | This dataset |
|---|---|---|
| JNJ | $88.8B | $88,821,000,000 |
| MRK | $64.2B | $64,168,000,000 |
| PFE | $63.6B | $63,627,000,000 |
| ABBV | $56.3B | $56,334,000,000 |
| BMY | $48.3B | $48,300,000,000 |
| LLY | $45.0B | $45,042,700,000 |
| AMGN | $33.4B | $33,424,000,000 |
| GILD | $28.8B | $28,754,000,000 |

All values match audited financial filings within rounding.

## How to run

```bash
# Install dependencies
pip install -r requirements.txt

# Run against the bundled CSV (default — no setup required)
python sec_observations_cleaning.py
```

Output:
- Cleaned data summary printed to stdout
- Validation report (coverage gaps, period coverage, magnitude flags)
- Chart written to `output/sec_observations_charts.png`

### Optional — live Supabase mode

If `DATABASE_URL` is set in the environment (or in a `.env` file), the script pulls fresh data from the live Caduceus Supabase Postgres instance instead of reading the bundled CSV. This refreshes the snapshot. Most graders will use the bundled CSV path.

## Architecture

```
SEC EDGAR XBRL API
       ↓ (edgartools Python library)
   edgartools_adapter.py            ← Caduceus pipeline (separate repo)
       ↓ (rolled-up financial facts)
   edgartools_loader.py             ← writes to Postgres
       ↓
   Supabase Postgres
   edgar_observations table
       ↓ (snapshot export)
   data/edgar_observations.csv      ← bundled in this submission
       ↓ (this script)
   sec_observations_cleaning.py
       ↓
   - clean_observations()           ← Module 2 cleaning logic
   - validate()                     ← coverage + magnitude QA
   - make_charts()                  ← Module 2 visualization
       ↓
   output/sec_observations_charts.png
```

## Cleaning steps

Implemented in `clean_observations()`:

1. **Type coercion** — `period_start`, `period_end` to datetime; `value` to numeric (errors coerced to NaN)
2. **Null-handling** — drop rows where `value` failed numeric conversion
3. **Fiscal-period normalization** — uppercase, strip whitespace
4. **Period-length classification** — compute `(period_end - period_start).days`, classify as:
   - `quarterly` (80-100 days)
   - `annual` (350-380 days)
   - `other` (everything else)
5. **Period labeling** — build a stable `period_label` like `2024-FY` or `2024-Q3` for deduplication
6. **Restatement-aware deduplication** — sort by `period_end` descending, keep first per `(ticker, concept, period_label)`. This handles SEC restatements (see "Data nuances" below)

## Data nuances surfaced

**JNJ FY 2023 revenue restatement**

The raw EDGAR data contains two distinct values for JNJ's FY 2023 revenue:

| Reported in | Value | Reason |
|---|---|---|
| 2024 10-K (FY 2023 filing) | $94,943M | Total revenue as originally filed |
| 2025 10-K (FY 2024 filing) | $85,159M | Restated to exclude Kenvue (divested August 2023) |

This is a classic post-divestiture restatement — Johnson & Johnson spun off its consumer health business (Kenvue) in August 2023, and the 2024 10-K reclassifies Kenvue revenue as discontinued operations.

The script's deduplication keeps the **most recently filed** value (the restated $85.2B figure), which is the correct treatment for current period comparisons. The original $94.9B value is preserved in the raw CSV with its accession number so the audit trail is intact.

**Quarterly classification**

Some 10-Q filings have period lengths slightly outside 80-100 days due to JNJ's 53-week fiscal calendar. These end up in the `other` bucket and are excluded from quarterly trend visualization. A more sophisticated approach would adjust the boundary by ticker — left as a known limitation.

## What the chart shows

Three branded analytical panels (left to right):

1. **FY{latest} revenue by ticker** — descending bar chart. Annotation: universe total, leader's share, top-to-bottom spread.
2. **Quarterly revenue — last 8 quarters** — line chart per ticker. Annotation: strongest mover and weakest mover over the window.
3. **FY{latest} R&D intensity** — descending bar chart with universe-mean reference line. Annotation: heaviest investor, most efficient.

Color palette is the Caduceus brand system (Inter for sans, IBM Plex Serif for headings — falls back to system defaults if the fonts aren't installed).

## What the chart shows

### Panel 1 — FY 2025 revenue ranking

The pharma universe ex-JNJ runs ~$369B. Four names (LLY, MRK, PFE, ABBV) cluster tightly at $61-65B and account for about 69% of total revenue. Below that cluster, BMY/AMGN/GILD operate at a smaller scale at $29-48B each.

### Panel 2 — Quarterly trajectory

LLY's revenue has approximately doubled over the eight-quarter window — the only name in the universe with that growth profile. PFE is the only name down over the same window. The other five trade in a roughly $11-17B range with quarter-to-quarter noise from product seasonality and one-time revenue events (e.g., Paxlovid lump-sum recognition, Gardasil seasonality). The chart is intentionally not annotated — quarterly revenue movement attribution belongs in fundamental research, not a data-cleaning deliverable.

### Panel 3 — FY 2025 R&D intensity

MRK leads at 24% R&D-to-revenue, followed by a cluster (BMY/LLY/AMGN/GILD) at 20-21%. PFE and ABBV are the only two names below the universe average of 19%. The MRK figure stands out as patent-cliff defense (Keytruda loses exclusivity around 2028).

## File manifest

```
data-cleaning-viz/
├── README.md                          (this file)
├── requirements.txt                   (pandas, matplotlib)
├── sec_observations_cleaning.py       (main script)
├── branding/
│   ├── __init__.py
│   └── branding.py                    (brand colors and matplotlib styling)
├── data/
│   └── edgar_observations.csv         (2,105 real EDGAR observations)
└── output/
    └── sec_observations_charts.png    (generated by the script)
```

## Honest scope notes

- This is the Data Cleaning + matplotlib assignment, not a full Caduceus deliverable
- The pipeline that produced this data is real and committed at https://github.com/kmatosli/Caduceus
- The bundled CSV is a point-in-time snapshot, not refreshed nightly
- The script intentionally trusts the upstream pipeline's cleanliness — the "messy data" treatment lives in the Module 2 Capstone deliverable, not here
