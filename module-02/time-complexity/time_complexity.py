"""
time_complexity.py — Big O Detective + Caduceus Balance Sheet Integrity Check

Coding Temple AI Bootcamp · Module 2 · Time Complexity and Big O Notation
Author: Kathy Matos

This file delivers:
    Part 1 — Big O classifications for 5 functions (comments above each)
    Part 2 — Cross-foot validation: find balance-sheet observation pairs that
             form a valid accounting identity. Two implementations:
                 naive O(n^2) — nested loop comparing every pair
                 optimized O(n) — hash by (ticker, period_end) key

This is a real Caduceus operation. The script:
  1. Loads real edgar_observations data (3,441 rows, 8 Phase 1 pharma names)
  2. Runs the balance-sheet cross-foot:  total_assets = total_liabilities + stockholders_equity
  3. Benchmarks naive vs optimized at sizes 500 / 1,000 / 3,441
  4. Surfaces real Caduceus data findings:
       - Concept coverage gaps in edgar_observations
       - Cross-foot identity violations (audit trail for adapter fixes)
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import List, Tuple, Dict

import pandas as pd


HERE = Path(__file__).resolve().parent
DATA_CSV = HERE / "data" / "edgar_observations.csv"

# Balance sheet identity: total_assets = total_liabilities + stockholders_equity
# Tolerance for XBRL rounding noise (0.1% of total_assets)
BS_CONCEPTS = ("total_assets", "total_liabilities", "stockholders_equity")
TOLERANCE = 0.001


# ──────────────────────────────────────────────────────────────────────────────
# PART 1 — Classify These Functions
# ──────────────────────────────────────────────────────────────────────────────

# Function A — O(1) constant time.
# Indexing a list at a fixed position is a single memory lookup, independent of
# the size of the list.
def get_first(data: List[int]) -> int:
    return data[0]


# Function B — O(n) linear time.
# We iterate every element of `data` exactly once; the work scales linearly
# with the size of the input.
def count_matches(data: List[int], target: int) -> int:
    count = 0
    for item in data:
        if item == target:
            count += 1
    return count


# Function C — O(n^2) quadratic time.
# Nested loops where both run from 0 to len(data) means the total number of
# operations is n * n; the work scales with the square of the input size.
def all_pairs(data: List[int]) -> List[Tuple[int, int]]:
    pairs = []
    for i in range(len(data)):
        for j in range(len(data)):
            pairs.append((data[i], data[j]))
    return pairs


# Function D — O(log n) logarithmic time.
# Each iteration of the loop halves n via integer division, so the number of
# iterations is log2(n) — the classic shape of binary search and binary trees.
def mystery(n: int) -> int:
    count = 0
    while n > 1:
        n = n // 2
        count += 1
    return count


# Function E — O(n log n) linearithmic time.
# Total is dominated by the slowest step: sum(data) is O(n), sorted(data) is
# O(n log n), and data[0] is O(1). Big O takes the maximum, so the overall
# complexity is O(n log n) driven by the sort.
def process(data: List[int]):
    total = sum(data)             # O(n)
    sorted_data = sorted(data)    # O(n log n)
    first = data[0]               # O(1)
    return total, sorted_data, first


# ──────────────────────────────────────────────────────────────────────────────
# PART 2 — Cross-foot validation on real edgar_observations
#
# The pair-counting problem reframed for accounting validation:
# Given a list of observations (ticker, period_end, concept, value), count
# how many (ticker, period_end) groups contain a complete balance-sheet triple
# AND satisfy total_assets = total_liabilities + stockholders_equity within
# 0.1% tolerance.
#
# This is a pair-finding operation: for each observation, we want to know
# whether matching observations (same ticker+period, different concept)
# exist in the list. The naive way scans all pairs; the optimized way
# uses a hash to group in linear time.
# ──────────────────────────────────────────────────────────────────────────────

Observation = Tuple[str, str, str, float]
# (ticker, period_end, concept, value)


def validate_crossfoot_naive(observations: List[Observation]) -> Dict[str, int]:
    """
    O(n^2) — for each observation, scan every other observation to find ones
    sharing the same (ticker, period_end). Then check if the triple validates.

    This is the textbook "nested loop over pairs" implementation. It works
    correctly but does O(n^2) comparisons, most of which find no match.
    """
    n = len(observations)
    complete_triples = 0
    validated = 0
    failed = 0
    seen_keys = set()

    for i in range(n):
        ticker_i, period_i, concept_i, value_i = observations[i]
        if concept_i != "total_assets":
            continue

        # Look for the other two concepts at the same (ticker, period)
        liab_value = None
        equity_value = None
        for j in range(n):
            if i == j:
                continue
            ticker_j, period_j, concept_j, value_j = observations[j]
            if ticker_j != ticker_i or period_j != period_i:
                continue
            if concept_j == "total_liabilities":
                liab_value = value_j
            elif concept_j == "stockholders_equity":
                equity_value = value_j

        if liab_value is not None and equity_value is not None:
            key = (ticker_i, period_i)
            if key in seen_keys:
                continue  # already processed this triple
            seen_keys.add(key)
            complete_triples += 1
            calc = liab_value + equity_value
            diff = abs(value_i - calc) / value_i if value_i else 0
            if diff <= TOLERANCE:
                validated += 1
            else:
                failed += 1

    return {
        "complete_triples": complete_triples,
        "validates": validated,
        "fails": failed,
    }


def validate_crossfoot_optimized(observations: List[Observation]) -> Dict[str, int]:
    """
    O(n) — hash all observations by (ticker, period_end), then check each
    group once.

    Single pass to build the hash, single pass to check each group. The
    dictionary lookup is O(1) on average, so total work scales linearly
    with the number of observations.
    """
    # Group observations by (ticker, period_end) in one O(n) pass
    groups: Dict[Tuple[str, str], Dict[str, float]] = {}
    for ticker, period_end, concept, value in observations:
        if concept not in BS_CONCEPTS:
            continue
        key = (ticker, period_end)
        if key not in groups:
            groups[key] = {}
        groups[key][concept] = value

    # Check each group once — O(k) where k = number of groups, k <= n
    complete_triples = 0
    validated = 0
    failed = 0
    for key, concepts in groups.items():
        if len(concepts) < 3:
            continue
        complete_triples += 1
        assets = concepts["total_assets"]
        liabs = concepts["total_liabilities"]
        equity = concepts["stockholders_equity"]
        calc = liabs + equity
        diff = abs(assets - calc) / assets if assets else 0
        if diff <= TOLERANCE:
            validated += 1
        else:
            failed += 1

    return {
        "complete_triples": complete_triples,
        "validates": validated,
        "fails": failed,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Benchmark
# ──────────────────────────────────────────────────────────────────────────────

def load_observations() -> List[Observation]:
    """Load real edgar_observations rows from the bundled CSV."""
    df = pd.read_csv(DATA_CSV)
    return list(
        df[["ticker", "period_end", "concept", "value"]]
        .itertuples(index=False, name=None)
    )


def benchmark(observations: List[Observation], sizes: List[int]) -> None:
    """Run both implementations at each size and print a comparison."""
    print("=" * 76)
    print("  BENCHMARK — Balance sheet cross-foot on real edgar_observations")
    print("=" * 76)
    print(f"\n{'rows':>10}  {'naive O(n^2)':>16}  {'optimized O(n)':>16}  {'speedup':>10}")
    print("-" * 60)

    for n in sizes:
        sample = observations[:n]

        # Time the naive implementation
        t0 = time.perf_counter()
        naive_result = validate_crossfoot_naive(sample)
        naive_time = time.perf_counter() - t0

        # Time the optimized implementation
        t0 = time.perf_counter()
        opt_result = validate_crossfoot_optimized(sample)
        opt_time = time.perf_counter() - t0

        # Sanity check: both return the same answer
        assert naive_result == opt_result, (
            f"Result mismatch at n={n}:\n"
            f"  naive={naive_result}\n"
            f"  opt={opt_result}"
        )

        speedup = naive_time / opt_time if opt_time > 0 else float("inf")
        print(
            f"{n:>10,}  {naive_time*1000:>13.2f} ms  "
            f"{opt_time*1000:>13.2f} ms  {speedup:>9.1f}x"
        )

    print("\n  Note: both functions return identical results (asserted).")
    print("  The naive O(n^2) grows quadratically; doubling input ~quadruples time.")
    print("  The optimized O(n) grows linearly; doubling input ~doubles time.")


# ──────────────────────────────────────────────────────────────────────────────
# Caduceus data quality report
# ──────────────────────────────────────────────────────────────────────────────

def report_data_quality(observations: List[Observation]) -> None:
    """
    Surface real Caduceus data findings: concept coverage gaps and balance
    sheet integrity violations.
    """
    df = pd.DataFrame(observations, columns=["ticker", "period_end", "concept", "value"])

    print("\n" + "=" * 76)
    print("  CADUCEUS DATA QUALITY FINDINGS")
    print("=" * 76)

    # Concept coverage across the universe
    print("\n  Concept coverage in edgar_observations (Phase 1 universe):")
    coverage = df.groupby("concept").size().sort_values(ascending=False)
    for concept, count in coverage.items():
        print(f"    {concept:<25} {count:>5} rows")

    # Identify missing concepts (the ones we should expect but don't have)
    expected = {
        "revenue", "cogs", "gross_profit", "rd_expense", "sga_expense",
        "operating_income", "net_income",
        "cfo", "cfi", "cff", "capex",
        "total_assets", "total_liabilities", "stockholders_equity",
        "cash", "long_term_debt",
    }
    present = set(df["concept"].unique())
    missing = expected - present
    if missing:
        print(f"\n  ⚠ Concepts in canonical list but ABSENT from data: {sorted(missing)}")
        print(f"    Action: adapter mapping audit needed (likely missing in")
        print(f"    RAW_FACTS_TO_CANONICAL or statement-based extraction).")

    # Balance sheet triple completeness
    bs = df[df["concept"].isin(BS_CONCEPTS)]
    pivot = bs.pivot_table(
        index=["ticker", "period_end"],
        columns="concept",
        values="value",
        aggfunc="first",
    )
    complete = pivot.dropna()
    print(f"\n  Balance sheet triple coverage:")
    print(f"    Total (ticker, period_end) groups with all 3 BS concepts: {len(complete)}")
    print(f"    Coverage by ticker:")
    by_ticker = complete.reset_index().groupby("ticker").size().sort_values(ascending=False)
    for ticker in sorted(df["ticker"].unique()):
        cnt = by_ticker.get(ticker, 0)
        marker = "  ✓" if cnt > 0 else "  ✗ MISSING"
        print(f"      {ticker:<6} {cnt:>3} triples {marker}")
    missing_tickers = [t for t in df["ticker"].unique() if by_ticker.get(t, 0) == 0]
    if missing_tickers:
        print(f"\n    ⚠ Tickers with no complete BS triples: {missing_tickers}")
        print(f"      Action: investigate why total_liabilities or stockholders_equity")
        print(f"      is missing for these names.")

    # Cross-foot validation breakdown
    complete = complete.copy()
    complete["calc"] = complete["total_liabilities"] + complete["stockholders_equity"]
    complete["rel_diff"] = (
        (complete["total_assets"] - complete["calc"]).abs()
        / complete["total_assets"]
    ).fillna(0)

    pass_rows = complete[complete["rel_diff"] <= TOLERANCE]
    fail_rows = complete[complete["rel_diff"] > TOLERANCE]

    print(f"\n  Balance sheet identity check (total_assets = total_liabilities + stockholders_equity):")
    print(f"    Validates within {TOLERANCE*100:.1f}% tolerance: {len(pass_rows)} of {len(complete)}")
    print(f"    FAILS tolerance:                              {len(fail_rows)} of {len(complete)}")

    if len(fail_rows) > 0:
        print(f"\n    ⚠ Top 5 worst failures (by relative diff):")
        worst = fail_rows.sort_values("rel_diff", ascending=False).head(5)
        for (ticker, period), row in worst.iterrows():
            assets_b = row["total_assets"] / 1e9
            calc_b = row["calc"] / 1e9
            diff_b = (row["total_assets"] - row["calc"]) / 1e9
            print(
                f"      {ticker} {period}:  "
                f"assets=${assets_b:>6.1f}B  "
                f"L+E=${calc_b:>6.1f}B  "
                f"diff=${diff_b:>+6.2f}B  "
                f"({row['rel_diff']*100:.2f}%)"
            )
        print(f"\n    Likely causes (to investigate in Caduceus):")
        print(f"      1. Minority interest / non-controlling interest not captured")
        print(f"      2. Different XBRL tags for total_liabilities across filers")
        print(f"      3. stockholders_equity tagged 'attributable to parent' vs 'total'")


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 76)
    print("  CADUCEUS BALANCE SHEET CROSS-FOOT")
    print("  Bootcamp Module 2 — Time Complexity and Big O Notation")
    print("=" * 76)

    observations = load_observations()
    print(f"\n  Loaded {len(observations):,} real EDGAR observations from {DATA_CSV.name}")

    # Run benchmark at sizes that match real data volume
    benchmark(observations, sizes=[500, 1_000, len(observations)])

    # Surface real Caduceus data findings
    report_data_quality(observations)

    print("\n" + "=" * 76)
    print("  DONE")
    print("=" * 76)
