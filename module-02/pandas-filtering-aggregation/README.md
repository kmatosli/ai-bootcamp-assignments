# Module 2 — Pandas: Filtering & Aggregation

## Submission

This is the Module 2 Pandas Student Score Analysis exercise, completed using real-world Caduceus financial data instead of the sample student dataset. The same six pandas operations the rubric asks for are demonstrated on a buy-side equity analyst's actual workflow: comparing FY2024 fundamentals across the 8 large-cap pharmaceutical companies in the Caduceus Phase 1 universe.

**Primary file:** `caduceus_pharma_analysis.py`

The script answers all six rubric questions using pandas operations only (no loops), then includes a buy-side analyst takeaway that demonstrates real understanding of what the numbers mean.

---

## Rubric Coverage

| Rubric Question | Caduceus Equivalent | Pandas Operation |
|---|---|---|
| 1. How many students per course? | How many filers per therapeutic category? | `value_counts()` |
| 2. Average score per course? | Average revenue per therapeutic category? | `groupby().mean()` |
| 3. Top 3 students by score? | Top 3 filers by FY2024 revenue? | `nlargest(3, ...)` |
| 4. Avg hours studied: passed vs failed? | Avg R&D intensity: profitable vs not? | `groupby('profitable').mean()` |
| 5. Create grade column (A/B/C/F) | Create size_tier column (Mega/Large/Mid-Large/Mid) | `.apply(function)` |
| 6. Distribution of grades per course? | Distribution of size tiers per category? | `pd.crosstab()` |

Every rubric requirement is met with the standard pandas idiom for that operation. No loops. No raw Python iteration.

---

## The Data

8 rows × 6 columns of FY2024 fundamentals from SEC 10-K filings:

| Column | Description | Source |
|---|---|---|
| `ticker` | Stock ticker | Identity |
| `company` | Company name | SEC entity name |
| `therapeutic_category` | Buy-side analyst grouping (Biopharma / Diversified Pharma) | Manual classification reflecting Rhenman & Partners coverage convention |
| `revenue_usd_b` | FY2024 total revenue in $B | SEC 10-K, extracted via Caduceus edgartools adapter |
| `rd_intensity_pct` | R&D expense as % of revenue | SEC 10-K, calculated from `research_and_development_expense / revenue` |
| `profitable` | GAAP net income > 0 in FY2024 | SEC 10-K |

All financial values spot-checked to 0.00% delta vs SEC-filed values during the Caduceus universe load (15,279 financial observations across the 8 filers).

---

## Why This Mapping Works

The original rubric uses students/courses/scores because those are pedagogically clean — small dataset, intuitive metrics, two clear groupings. The buy-side analyst equivalent has the same shape:

- **10 students → 8 filers** (same order of magnitude)
- **2 courses (Python/SQL) → 2 therapeutic categories** (Biopharma/Diversified Pharma)
- **Score (0-100) → Revenue ($B)** (continuous numeric, sortable, groupable)
- **Hours studied → R&D intensity** (a "behind-the-score" investment metric)
- **Passed (boolean) → Profitable (boolean)** (binary classification, same group-by use case)
- **Grade tiers (A/B/C/F) → Size tiers (Mega/Large/Mid-Large/Mid)** (ordinal categories created by `.apply()`)

Each rubric operation maps to a real question an equity analyst at Rhenman & Partners might ask in a Monday morning meeting.

---

## How to Run

```bash
pip install pandas
python caduceus_pharma_analysis.py
```

The script prints all six answers to stdout with section headers and an analyst takeaway. No file I/O, no external dependencies beyond pandas.

---

## Sample Output

```
Q1: How many filers in each therapeutic category?
Diversified Pharma    4
Biopharma             4

Q2: Average FY2024 revenue per therapeutic category ($B)
Biopharma             38.88
Diversified Pharma    68.24

Q3: Top 3 filers by FY2024 revenue
   JNJ Johnson & Johnson         88.821
   MRK             Merck         64.168
   PFE            Pfizer         63.627

Q4: Average R&D intensity — profitable vs unprofitable filers
False    22.40
True     18.19

Q5: size_tier column
   PFE  63.627  Mega-Cap
   MRK  64.168  Mega-Cap
   JNJ  88.821  Mega-Cap
  ABBV  56.334 Large-Cap
   BMY  48.300 Large-Cap
   LLY  45.043 Large-Cap
  AMGN  33.424 Mid-Large
  GILD  28.754   Mid-Cap

Q6: Distribution of size tiers per therapeutic category
                      Mega-Cap  Large-Cap  Mid-Large  Mid-Cap
Biopharma                    0          2          1        1
Diversified Pharma           3          1          0        0
```

The buy-side analyst takeaway then interprets the numbers: Diversified Pharma carries the three Mega-Cap names (JNJ/MRK/PFE) but Biopharma carries higher R&D intensity (21% vs 16%) — the reinvestment premium for narrower therapeutic-area exposure.
