"""
universe_functional.py — Functional operations over Caduceus's Phase 1 universe.

Bootcamp Module 2 Functional Programming. The assignment ships a `products`
list and asks you to process it using filter / map / reduce / comprehensions
and lambdas only — no for-loop-with-append, no mutation of the original.

Caduceus mapping:
    products       -> pharma universe (8 Phase 1 large-cap pharma companies)
    name           -> ticker
    price          -> market_cap_usd_b   (market cap in $B)
    category       -> sub_industry       (Large Pharma / Biotech)
    in_stock       -> universe_active    (whether the name is in the active book)

All required functional patterns are exercised on real Caduceus universe data.

Run:
    python universe_functional.py
"""
from __future__ import annotations

from functools import reduce
from typing import Any, Callable, Dict, List


# ──────────────────────────────────────────────────────────────────────────────
# The data — Caduceus Phase 1 universe (real public data, snapshot)
# ──────────────────────────────────────────────────────────────────────────────

UNIVERSE: List[Dict[str, Any]] = [
    {"ticker": "LLY",  "market_cap_usd_b": 700.0, "sub_industry": "Large Pharma", "universe_active": True},
    {"ticker": "JNJ",  "market_cap_usd_b": 380.0, "sub_industry": "Large Pharma", "universe_active": True},
    {"ticker": "ABBV", "market_cap_usd_b": 320.0, "sub_industry": "Large Pharma", "universe_active": True},
    {"ticker": "MRK",  "market_cap_usd_b": 280.0, "sub_industry": "Large Pharma", "universe_active": False},
    {"ticker": "PFE",  "market_cap_usd_b": 170.0, "sub_industry": "Large Pharma", "universe_active": True},
    {"ticker": "AMGN", "market_cap_usd_b": 160.0, "sub_industry": "Biotech",      "universe_active": True},
    {"ticker": "BMY",  "market_cap_usd_b": 110.0, "sub_industry": "Large Pharma", "universe_active": False},
    {"ticker": "GILD", "market_cap_usd_b": 100.0, "sub_industry": "Biotech",      "universe_active": True},
]


# ──────────────────────────────────────────────────────────────────────────────
# Task 1 — filter: active universe members
# ──────────────────────────────────────────────────────────────────────────────

def get_active_names(universe: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter to names currently in the active book (universe_active == True)."""
    return list(filter(lambda c: c["universe_active"], universe))


# ──────────────────────────────────────────────────────────────────────────────
# Task 2 — map: add a stress-tested market cap (10% drawdown), no mutation
# ──────────────────────────────────────────────────────────────────────────────

def with_stress_test(universe: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add a 'stress_market_cap_usd_b' field = 90% of current (10% drawdown).

    Mirrors the assignment's 'discounted_price' but framed as a portfolio
    stress test, which is what Rhenman would actually use this for.

    Critically: returns NEW dicts; the original is never mutated.
    """
    return list(map(
        lambda c: {**c, "stress_market_cap_usd_b": round(c["market_cap_usd_b"] * 0.90, 2)},
        universe,
    ))


# ──────────────────────────────────────────────────────────────────────────────
# Task 3 — filter with two conditions: large pharma under $200B
# ──────────────────────────────────────────────────────────────────────────────

def small_large_pharma(universe: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Large Pharma names with market cap under $200B — the 'mid-cap pharma'
    bucket where Caduceus tends to find dispersion in conviction."""
    return [
        c for c in universe
        if c["sub_industry"] == "Large Pharma" and c["market_cap_usd_b"] < 200
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Task 4 — sorted with key lambda: ascending by market cap
# ──────────────────────────────────────────────────────────────────────────────

def sorted_by_market_cap(universe: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(universe, key=lambda c: c["market_cap_usd_b"])


# ──────────────────────────────────────────────────────────────────────────────
# Task 5 — reduce/sum: total active market cap in the book
# ──────────────────────────────────────────────────────────────────────────────

def total_active_market_cap(universe: List[Dict[str, Any]]) -> float:
    """Total market cap across the active book. Use reduce() to satisfy the
    assignment's 'reduce or sum with comprehension' requirement — both are
    shown below; we return the reduce() version."""
    active = filter(lambda c: c["universe_active"], universe)
    return reduce(lambda acc, c: acc + c["market_cap_usd_b"], active, 0.0)


def total_active_market_cap_via_sum(universe: List[Dict[str, Any]]) -> float:
    """Same calculation via sum + generator expression — for comparison."""
    return sum(c["market_cap_usd_b"] for c in universe if c["universe_active"])


# ──────────────────────────────────────────────────────────────────────────────
# Task 6 — group by sub-industry
# ──────────────────────────────────────────────────────────────────────────────

def group_by_sub_industry(universe: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group the universe by sub-industry into {sub_industry: [members]}."""
    sub_industries = {c["sub_industry"] for c in universe}
    return {
        si: [c for c in universe if c["sub_industry"] == si]
        for si in sub_industries
    }


# ──────────────────────────────────────────────────────────────────────────────
# Caduceus-specific bonus: a small functional pipeline
# ──────────────────────────────────────────────────────────────────────────────

def compose(*fns: Callable) -> Callable:
    """Right-to-left function composition: compose(f, g)(x) == f(g(x))."""
    return reduce(lambda f, g: lambda x: f(g(x)), fns)


def active_large_pharma_tickers(universe: List[Dict[str, Any]]) -> List[str]:
    """Composed pipeline: active -> large pharma -> sorted by market cap -> tickers."""
    pipeline = compose(
        lambda xs: [c["ticker"] for c in xs],
        lambda xs: sorted(xs, key=lambda c: -c["market_cap_usd_b"]),  # descending
        lambda xs: list(filter(lambda c: c["sub_industry"] == "Large Pharma", xs)),
        lambda xs: list(filter(lambda c: c["universe_active"], xs)),
    )
    return pipeline(universe)


# ──────────────────────────────────────────────────────────────────────────────
# Demo — prints results for all six tasks
# ──────────────────────────────────────────────────────────────────────────────

def _demo() -> None:
    print("=" * 70)
    print("  CADUCEUS PHASE 1 UNIVERSE — functional operations demo")
    print("=" * 70)

    # ── Task 1 ──────────────────────────────────────────────────────────────
    active = get_active_names(UNIVERSE)
    print(f"\n[1] Active universe members ({len(active)} of {len(UNIVERSE)}):")
    for c in active:
        print(f"      {c['ticker']:5s}  ${c['market_cap_usd_b']:>6.1f}B  {c['sub_industry']}")

    # ── Task 2 ──────────────────────────────────────────────────────────────
    stressed = with_stress_test(UNIVERSE)
    print(f"\n[2] After 10% stress test (new dicts, original preserved):")
    for c in stressed[:3]:
        print(f"      {c['ticker']:5s}  base=${c['market_cap_usd_b']:>6.1f}B  "
              f"stress=${c['stress_market_cap_usd_b']:>6.1f}B")
    print(f"    ... (showing 3 of {len(stressed)})")

    # Prove non-mutation
    assert "stress_market_cap_usd_b" not in UNIVERSE[0], "ORIGINAL WAS MUTATED!"
    print(f"    ✓ Original UNIVERSE unchanged — 'stress_market_cap_usd_b' "
          f"not present in original")

    # ── Task 3 ──────────────────────────────────────────────────────────────
    mids = small_large_pharma(UNIVERSE)
    print(f"\n[3] Large Pharma under $200B (the dispersion bucket):")
    for c in mids:
        print(f"      {c['ticker']:5s}  ${c['market_cap_usd_b']:>6.1f}B")

    # ── Task 4 ──────────────────────────────────────────────────────────────
    by_cap = sorted_by_market_cap(UNIVERSE)
    print(f"\n[4] Sorted ascending by market cap:")
    for c in by_cap:
        print(f"      {c['ticker']:5s}  ${c['market_cap_usd_b']:>6.1f}B")

    # ── Task 5 ──────────────────────────────────────────────────────────────
    total_reduce = total_active_market_cap(UNIVERSE)
    total_sum    = total_active_market_cap_via_sum(UNIVERSE)
    print(f"\n[5] Total active book market cap:")
    print(f"      via reduce(): ${total_reduce:>8.1f}B")
    print(f"      via sum():    ${total_sum:>8.1f}B")
    assert total_reduce == total_sum, "reduce and sum disagree — bug"

    # ── Task 6 ──────────────────────────────────────────────────────────────
    grouped = group_by_sub_industry(UNIVERSE)
    print(f"\n[6] Grouped by sub-industry:")
    for si, members in grouped.items():
        tickers = [c["ticker"] for c in members]
        print(f"      {si:14s}  ({len(members)})  {tickers}")

    # ── Bonus: composed pipeline ────────────────────────────────────────────
    print(f"\n[bonus] Composed pipeline (active large pharma, sorted desc by cap):")
    print(f"      {active_large_pharma_tickers(UNIVERSE)}")

    print()


if __name__ == "__main__":
    _demo()
