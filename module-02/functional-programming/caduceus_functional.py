"""
Module 2 — Functional Programming
Caduceus equivalent of "Functional Data Processor"

Rubric: Process a dataset using only functional patterns (filter, map, lambda,
sorted, comprehensions). No for-loops with append. Don't mutate the input.
Time target: 20 minutes.

Original exercise asks 6 operations on a list of 8 product dicts.
This version asks the same 6 operations on 8 large-cap pharma securities
from the Caduceus Phase 1 universe, using real FY2024 financial data.

The "products" list becomes "securities" — Phase 1 pharma companies with
revenue, sub-industry, profitability, and active-status flags. The 6
operations map to actual buy-side workflow primitives: portfolio screening,
margin computation, sector filtering, ranking, exposure summing, and
classification grouping.

All transformations use functional patterns only.
"""
from functools import reduce

# ----------------------------------------------------------------------
# The Data
# ----------------------------------------------------------------------
# 8 pharma securities, Phase 1 Caduceus universe. FY2024 figures from SEC
# 10-K filings, extracted via edgartools adapter. The dict shape mirrors
# how a portfolio screening tool would receive each candidate:
#   ticker          — symbol
#   name            — issuer legal name
#   revenue_usd_b   — FY2024 total revenue, $B
#   sub_industry    — buy-side coverage subcategory
#   profitable      — GAAP net income > 0 in FY2024
#   active          — currently in the analyst's working coverage set
securities = [
    {"ticker": "PFE",  "name": "Pfizer",                "revenue_usd_b": 63.627, "sub_industry": "diversified_pharma", "profitable": True,  "active": True},
    {"ticker": "MRK",  "name": "Merck",                 "revenue_usd_b": 64.168, "sub_industry": "diversified_pharma", "profitable": True,  "active": True},
    {"ticker": "JNJ",  "name": "Johnson & Johnson",     "revenue_usd_b": 88.821, "sub_industry": "diversified_pharma", "profitable": True,  "active": False},
    {"ticker": "ABBV", "name": "AbbVie",                "revenue_usd_b": 56.334, "sub_industry": "diversified_pharma", "profitable": True,  "active": True},
    {"ticker": "BMY",  "name": "Bristol-Myers Squibb",  "revenue_usd_b": 48.300, "sub_industry": "biopharma",          "profitable": False, "active": True},
    {"ticker": "LLY",  "name": "Eli Lilly",             "revenue_usd_b": 45.043, "sub_industry": "biopharma",          "profitable": True,  "active": True},
    {"ticker": "AMGN", "name": "Amgen",                 "revenue_usd_b": 33.424, "sub_industry": "biopharma",          "profitable": True,  "active": False},
    {"ticker": "GILD", "name": "Gilead",                "revenue_usd_b": 28.754, "sub_industry": "biopharma",          "profitable": True,  "active": True},
]

print("=" * 75)
print("CADUCEUS — FUNCTIONAL PROCESSING ACROSS PHASE 1 PHARMA UNIVERSE")
print("Source: SEC 10-K filings via edgartools adapter")
print("=" * 75)
print(f"Starting set: {len(securities)} securities\n")


# ----------------------------------------------------------------------
# Op 1: Get all ACTIVE securities (filter)
# Rubric equivalent: "Get all in-stock products (filter)"
# ----------------------------------------------------------------------
print("─" * 75)
print("Op 1: Filter to active coverage securities")
print("─" * 75)
active = [s for s in securities if s["active"]]
for s in active:
    print(f"  {s['ticker']:<6} {s['name']}")
print(f"  → {len(active)} active securities")


# ----------------------------------------------------------------------
# Op 2: Add a "stressed_revenue" field that's 15% off the original (map)
# Rubric equivalent: "Add a 'discounted_price' field 10% off original
#                     (map — create new dicts, don't mutate)"
# Use case: a recession stress scenario for portfolio valuation
# ----------------------------------------------------------------------
print("\n" + "─" * 75)
print("Op 2: Map — apply 15% recession-scenario haircut to revenue (new dicts)")
print("─" * 75)
stressed = [
    {**s, "stressed_revenue": round(s["revenue_usd_b"] * 0.85, 3)}
    for s in securities
]
for s in stressed[:4]:  # show first 4 for brevity
    print(f"  {s['ticker']:<6} base ${s['revenue_usd_b']:>6.2f}B → stressed ${s['stressed_revenue']:>6.2f}B")
print(f"  ...and 4 more.")
# Verify input wasn't mutated
assert "stressed_revenue" not in securities[0], "Mutated input!"
print(f"  ✓ Original list unchanged: 'stressed_revenue' not in input dicts")


# ----------------------------------------------------------------------
# Op 3: Get only biopharma securities under $50B revenue (filter, 2 conditions)
# Rubric equivalent: "Get only electronics under $200 (filter with two conditions)"
# Use case: small/mid-cap biopharma screening
# ----------------------------------------------------------------------
print("\n" + "─" * 75)
print("Op 3: Filter — biopharma under $50B revenue (mid-cap biopharma screen)")
print("─" * 75)
small_biopharma = [
    s for s in securities
    if s["sub_industry"] == "biopharma" and s["revenue_usd_b"] < 50
]
for s in small_biopharma:
    print(f"  {s['ticker']:<6} {s['name']:<25} ${s['revenue_usd_b']:>6.2f}B")
print(f"  → {len(small_biopharma)} matches")


# ----------------------------------------------------------------------
# Op 4: Sort all securities by revenue, lowest first (sorted + key lambda)
# Rubric equivalent: "Sort by price, lowest first"
# Use case: ranking universe for portfolio construction
# ----------------------------------------------------------------------
print("\n" + "─" * 75)
print("Op 4: Sort by FY2024 revenue, ascending (universe ranking)")
print("─" * 75)
by_revenue = sorted(securities, key=lambda s: s["revenue_usd_b"])
for s in by_revenue:
    print(f"  ${s['revenue_usd_b']:>6.2f}B  {s['ticker']:<6} {s['name']}")


# ----------------------------------------------------------------------
# Op 5: Total revenue across all ACTIVE securities (reduce or sum-with-comp)
# Rubric equivalent: "Calculate total value of all in-stock products"
# Use case: total revenue exposure in the active coverage set
# ----------------------------------------------------------------------
print("\n" + "─" * 75)
print("Op 5: Sum — total revenue across active coverage set")
print("─" * 75)

# Two equivalent functional patterns; both shown for completeness
total_via_sum = sum(s["revenue_usd_b"] for s in securities if s["active"])
total_via_reduce = reduce(
    lambda acc, s: acc + s["revenue_usd_b"] if s["active"] else acc,
    securities,
    0.0,
)
print(f"  via sum + generator expression: ${total_via_sum:>7.2f}B")
print(f"  via functools.reduce:           ${total_via_reduce:>7.2f}B")
assert abs(total_via_sum - total_via_reduce) < 1e-9
print(f"  ✓ Both functional patterns agree")


# ----------------------------------------------------------------------
# Op 6: Group securities by sub-industry → dict
# Rubric equivalent: "Group products by category, return a dictionary
#                     like {'electronics': [...], 'books': [...]}"
# Use case: sector-bucket exposure breakdown
# ----------------------------------------------------------------------
print("\n" + "─" * 75)
print("Op 6: Group by sub-industry → dict of {sub_industry: [securities]}")
print("─" * 75)

# Functional grouping with reduce (no for-append loop)
by_sub_industry = reduce(
    lambda acc, s: {**acc, s["sub_industry"]: acc.get(s["sub_industry"], []) + [s]},
    securities,
    {},
)

for sub_industry, members in by_sub_industry.items():
    tickers = ", ".join(s["ticker"] for s in members)
    total_rev = sum(s["revenue_usd_b"] for s in members)
    print(f"  {sub_industry:<22} ({len(members)} names, ${total_rev:>6.2f}B): {tickers}")


# ----------------------------------------------------------------------
# Buy-side analyst takeaway
# ----------------------------------------------------------------------
print("\n" + "=" * 75)
print("BUY-SIDE ANALYST TAKEAWAY")
print("=" * 75)
print("""
The functional pipeline produces a working portfolio screening workflow:
  Op 1: Identify which names are in the active coverage set (6 of 8)
  Op 2: Apply a recession-scenario stress haircut without mutating positions
  Op 3: Surface the sub-$50B biopharma opportunity set (4 names)
  Op 4: Rank by scale for portfolio construction (smallest → largest)
  Op 5: Quantify total active-coverage revenue exposure (~$306B)
  Op 6: Bucket into sub-industries for sector-tilt analysis

Functional patterns are non-negotiable in production quant code because they
make data transformations auditable and composable. Each operation returns a
new collection; no operation mutates input. The same six primitives — filter,
map, sort, sum, reduce, group — underpin every screen and backtest at the
desk.
""")
