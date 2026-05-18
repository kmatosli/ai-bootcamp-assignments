# Caduceus Balance Sheet Cross-Foot Validation

**Submitted as:** Coding Temple AI Bootcamp · Module 2 · Time Complexity and Big O Notation
**Author:** Kathy Matos

## What this is

A balance-sheet integrity check for the Caduceus EDGAR observations pipeline. It validates that the fundamental accounting identity holds across all observations in the database:

> `total_assets = total_liabilities + stockholders_equity`

The script runs two implementations of the validation algorithm:
- **Naive O(n²)** — nested loops, pairwise comparison
- **Optimized O(n)** — single-pass hash-by-key grouping

It benchmarks both at sizes 500 / 1,000 / 3,441 (the full Phase 1 universe of real observations) and surfaces real Caduceus data findings: concept coverage gaps and accounting identity violations that warrant adapter investigation.

The bootcamp deliverables (Part 1 function classifications, Part 2 pair-counting benchmark, Part 3 n log n essay) all map to this work — the rubric is satisfied by doing legitimate Caduceus integrity work, not by writing throwaway algorithm code.

## What the script does

### Part 1 — Function classifications

Five reference functions (A through E) are annotated with their Big O complexity and a one-sentence explanation each. Classifications:

| Function | Complexity | Why |
|---|---|---|
| `get_first` | O(1) | Indexed access is one memory lookup |
| `count_matches` | O(n) | Single pass over the list |
| `all_pairs` | O(n²) | Nested loops each going to `len(data)` |
| `mystery` | O(log n) | Each iteration halves `n` |
| `process` | O(n log n) | Dominated by the `sorted()` call |

### Part 2 — Cross-foot validation (pair-counting on real data)

Two implementations of the same accounting identity check:

```python
def validate_crossfoot_naive(observations):
    # O(n²) — for each total_assets observation, scan all others
    # looking for matching total_liabilities and stockholders_equity
    # at the same (ticker, period_end)
    ...

def validate_crossfoot_optimized(observations):
    # O(n) — hash all observations by (ticker, period_end) in one
    # pass, then check each group's identity in O(1) per group
    ...
```

Both functions return identical results (asserted in the benchmark). Both are run against real `edgar_observations` data from the Caduceus pipeline — 3,441 observations across 8 Phase 1 pharma names.

### Part 3 — O(n log n) barrier essay

See `nlogn_barrier.md` for the explanation of why comparison-based sorts can't beat O(n log n), plus a bonus on counting sort and radix sort.

## How to run

```bash
pip install -r requirements.txt
python time_complexity.py
```

No external services required — runs against the bundled CSV snapshot.

## Real Caduceus findings (what the script surfaces when it runs)

This is the part that makes the script useful beyond the bootcamp rubric. Running against real data uncovered three concrete adapter issues:

### Finding 1 — Two canonical income statement concepts are MISSING entirely

`gross_profit` and `operating_income` returned zero rows. These are standard XBRL tags (`us-gaap:GrossProfit`, `us-gaap:OperatingIncomeLoss`) present in every 10-K and 10-Q. Action: audit `RAW_FACTS_TO_CANONICAL` in `edgartools_adapter.py` for these mappings.

### Finding 2 — 5 of 8 Phase 1 tickers have NO complete balance sheet triples

```
ABBV     0 triples   ✗ MISSING
AMGN     0 triples   ✗ MISSING
BMY     35 triples   ✓
GILD     0 triples   ✗ MISSING
JNJ     13 triples   ✓
LLY      0 triples   ✗ MISSING
MRK      0 triples   ✓
PFE     35 triples   ✓
```

Only BMY, JNJ, and PFE have all three balance sheet concepts (`total_assets`, `total_liabilities`, `stockholders_equity`) populated for any (ticker, period) pair. The missing concept is almost always `total_liabilities`, which has only 106 rows out of an expected ~280. Action: investigate why `total_liabilities` extraction is failing for the other 5 names — likely tag variation across filers.

### Finding 3 — Of the 83 complete triples, 45 fail the accounting identity

The identity `total_assets = total_liabilities + stockholders_equity` should hold exactly, but 45 of 83 cases fail outside a 0.1% tolerance. Top failures:

```
JNJ 2023-07-02:  assets=$191.7B  L+E=$190.4B  diff=+$1.26B  (0.66%)
BMY 2016-12-31:  assets=$ 33.7B  L+E=$ 33.5B  diff=+$0.17B  (0.50%)
BMY 2018-03-31:  assets=$ 33.1B  L+E=$ 33.0B  diff=+$0.11B  (0.34%)
```

The pattern (small consistent positive differences) points to **minority interest / non-controlling interest** being captured in `total_assets` but not in the L+E sum. Action: add `MinorityInterest` (or equivalent NCI concept) to the adapter so the identity can be checked as `total_assets = total_liabilities + stockholders_equity + minority_interest`.

## Why this design

The bootcamp rubric describes a pair-counting problem on synthetic integer lists. Rather than generate random data, this implementation applies the same algorithmic pattern (two-sum / pair-by-key) to a real Caduceus operation. The pedagogical content is identical — the hash-set trick that converts O(n²) into O(n) — but the work produced is useful to Caduceus instead of throwaway.

## Expected benchmark output

```
============================================================================
  BENCHMARK — Balance sheet cross-foot on real edgar_observations
============================================================================

      rows      naive O(n^2)    optimized O(n)     speedup
------------------------------------------------------------
       500           0.87 ms           0.05 ms       16.3x
     1,000           3.06 ms           0.07 ms       42.6x
     3,441          39.16 ms           0.25 ms      154.5x
```

The naive implementation roughly quadruples when input doubles (signature of O(n²)). The optimized implementation stays nearly flat below 1ms — measurement noise dominates real work at this size. Speedup widens from 16× at n=500 to 154× at n=3,441; the gap would continue to widen with larger inputs.

## File manifest

```
time-complexity/
├── README.md                  (this file)
├── requirements.txt           (pandas only)
├── time_complexity.py         (the script)
├── nlogn_barrier.md           (Part 3 essay)
└── data/
    └── edgar_observations.csv (3,441 real EDGAR observations, 16 concepts)
```

## Honest scope notes

- The benchmark sizes (500 / 1,000 / 3,441) are smaller than the rubric's example (1,000 / 5,000 / 10,000) because they match the real volume of Phase 1 data
- The data findings are real and warrant immediate Caduceus follow-up work; they are not constructed for the assignment
- Part 3 essay (`nlogn_barrier.md`) is theoretical and doesn't require real data
