# main.py — Macro Regime Narrator
# Applied to Premia: displays a random macro regime narrative each run
# Demonstrates: lists of tuples, random module, formatted output

import random

# --- 10 macro regime narratives stored as (quote, author) tuples ---
narratives = [
    ("Markets are in late-cycle expansion. Earnings growth is decelerating but credit spreads remain tight. Position defensively.", "Premia Macro Engine"),
    ("A regime shift is underway. The yield curve has uninverted and historically this precedes a growth slowdown within 12 months.", "Premia Macro Engine"),
    ("Risk-on conditions prevail. Breadth is expanding, volatility is compressed, and momentum favors cyclicals over defensives.", "Premia Macro Engine"),
    ("Stagflationary pressures are building. Input costs remain elevated while demand indicators are softening. Margins are at risk.", "Premia Macro Engine"),
    ("Early-cycle recovery signals are emerging. Credit is expanding, PMIs are inflecting, and small-caps are outperforming.", "Premia Macro Engine"),
    ("The Fed is in a holding pattern. Real rates are positive and the policy transmission lag is still working through the system.", "Premia Macro Engine"),
    ("Global growth is diverging. US data remains resilient while European and Chinese indicators continue to disappoint.", "Premia Macro Engine"),
    ("Liquidity conditions are tightening. Money supply growth is negative in real terms and asset correlations are rising.", "Premia Macro Engine"),
    ("Sentiment has reached an extreme. Positioning data and options skew suggest the next move is more likely to surprise to the upside.", "Premia Macro Engine"),
    ("Volatility regime has shifted. Realized vol is exceeding implied vol — the market is underpricing near-term risk.", "Premia Macro Engine"),
]

# --- Select and display a random narrative ---
quote, author = random.choice(narratives)

print()
print("=" * 60)
print(f"{'PREMIA — MACRO REGIME SIGNAL':^60}")
print("=" * 60)
print()
print(f'  "{quote}"')
print()
print(f"  — {author}")
print()
print("=" * 60)
print()
