# Module 2 — Functional Programming

## Submission

This is the Module 2 Functional Programming exercise, completed using real-world Caduceus pharma securities data instead of the sample products dataset. The same six functional operations the rubric asks for are demonstrated on a buy-side equity analyst's portfolio screening workflow.

**Primary file:** `caduceus_functional.py`

The script applies all six functional patterns the rubric requires — `filter`, `map`, multi-condition `filter`, `sorted` with `key=lambda`, `reduce`/`sum`, and grouping by key — using only list comprehensions, lambdas, and functional tools. No `for` loops with `append`. No mutation of input.

---

## Rubric Coverage

| Rubric Task | Caduceus Equivalent | Pattern Used |
|---|---|---|
| 1. Get all in-stock products | Get all active coverage securities | `[s for s in securities if s["active"]]` |
| 2. Add `discounted_price` (10% off, map → new dicts, no mutation) | Add `stressed_revenue` (15% recession haircut, map → new dicts) | `[{**s, "stressed_revenue": ...} for s in securities]` |
| 3. Get electronics under $200 (filter, 2 conditions) | Get biopharma under $50B revenue (filter, 2 conditions) | `[s for s in securities if s["sub_industry"]=="biopharma" and s["revenue_usd_b"]<50]` |
| 4. Sort by price ascending | Sort by revenue ascending | `sorted(securities, key=lambda s: s["revenue_usd_b"])` |
| 5. Total value of in-stock products (reduce or sum-comp) | Total revenue of active coverage (BOTH patterns shown) | `sum(...)` AND `reduce(...)` — verified equal |
| 6. Group products by category → dict | Group securities by sub-industry → dict | `reduce` with dict-spread |

The script includes both `sum`-with-comprehension and `functools.reduce` implementations for Op 5 to demonstrate fluency with both patterns. Both produce the same answer ($306.23B) — verified with an `assert`.

Op 6 uses `reduce` with dict-spread (`{**acc, ...}`) instead of a for-loop with append — strictly functional, no mutation.

---

## The Data

8 rows representing the Caduceus Phase 1 pharmaceutical universe. Each row is a dict with:

| Key | Description | Source |
|---|---|---|
| `ticker` | Stock ticker symbol | Identity |
| `name` | Issuer legal name | SEC entity name |
| `revenue_usd_b` | FY2024 total revenue in $B | SEC 10-K, extracted via Caduceus edgartools adapter |
| `sub_industry` | Buy-side coverage subcategory (`diversified_pharma` or `biopharma`) | Analyst-assigned, mirrors Rhenman coverage convention |
| `profitable` | GAAP net income > 0 in FY2024 | SEC 10-K |
| `active` | Currently in the analyst's working coverage set | Workflow state |

Revenue and profitability are spot-checked to 0.00% delta vs SEC-filed values from the Caduceus universe load (15,279 financial observations across these 8 filers). The `active` flag is a workflow state used to demonstrate the filter pattern.

---

## Why This Mapping Works

The rubric's original `products` list is pedagogically clean — 8 dicts with categorical/numeric/boolean attributes, plus an in-stock flag. The pharma securities equivalent has the same shape with buy-side analytical meaning:

- **8 products → 8 securities** (same row count, mirror structure)
- **price → revenue_usd_b** (continuous numeric, sortable, summable)
- **category → sub_industry** (string, used for grouping)
- **in_stock → active** (boolean, used for filtering)
- **+ profitable** (extra boolean attribute for richer filtering scenarios)
- **+ name** (display field)

Every rubric operation maps to a real question a quant developer at Rhenman would ask. The "stressed_revenue" map (Op 2) is a recession-scenario stress test. The "sub-$50B biopharma" filter (Op 3) is a mid-cap opportunity screen. The grouping (Op 6) is sector-tilt exposure analysis.

---

## How to Run

```bash
python caduceus_functional.py
```

No external dependencies — only `functools.reduce` from the standard library. The script prints all six operations with section headers and an analyst takeaway.

---

## Sample Output Highlights

```
Op 1: 6 active securities (PFE, MRK, ABBV, BMY, LLY, GILD)
Op 2: 8 new dicts with stressed_revenue field (input unchanged — verified)
Op 3: 4 biopharma names under $50B (BMY $48.3B, LLY $45.0B, AMGN $33.4B, GILD $28.8B)
Op 4: 8 securities sorted by revenue ($28.75B GILD → $88.82B JNJ)
Op 5: $306.23B total active-coverage revenue (sum and reduce both agree)
Op 6: 2 groups — diversified_pharma ($272.95B, 4 names), biopharma ($155.52B, 4 names)
```

---

## Constraints Followed

- ✓ No `for` loops with `append` — only list comprehensions, `sorted`, `sum`, `reduce`
- ✓ Input `securities` list never mutated (verified with `assert`)
- ✓ All transformations produce new collections
- ✓ Lambdas used in `sorted(key=...)` and `reduce(...)`
- ✓ Multi-condition filter uses `and` inside the comprehension
