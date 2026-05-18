"""
translation_challenge.py

Module 3 — Bridge from DataFrames to SQL
Caduceus Healthcare Equity Platform | Rhenman & Partners

Domain: Phase 1 pharma universe — revenue and R&D across 8 tickers, FY2022-FY2025.
        The same 4 analytical questions answered in both SQL and pandas side-by-side.

Rubric mapping:
  sales_data     → edgar_facts (ticker, metric, value, year)
  product        → ticker
  category       → metric_code
  unit_price     → value_usd_m per unit
  quantity       → fiscal_year (time dimension)
  quarter        → fiscal_period

4 required questions (SQL + pandas):
  1. Total revenue per ticker across all years
  2. Which fiscal year had the highest total revenue across the universe?
  3. Average R&D expense per ticker
  4. Which tickers had total revenue > $200B across 4 years?
BONUS: pd.read_sql() round-trip
"""
from __future__ import annotations
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///caduceus_bridge.db", echo=False)

# ── Seed data — real Morningstar-validated EDGAR revenue ─────────────────────
EDGAR_FACTS = [
    # (ticker, metric,       fy,   value_usd_m)
    ("PFE",  "revenue",     2025, 62579),
    ("PFE",  "revenue",     2024, 63625),
    ("PFE",  "revenue",     2023, 58496),
    ("PFE",  "revenue",     2022, 100330),
    ("PFE",  "rd_expense",  2025, 11400),
    ("PFE",  "rd_expense",  2024, 10900),
    ("PFE",  "rd_expense",  2023, 11400),
    ("PFE",  "rd_expense",  2022, 11428),

    ("MRK",  "revenue",     2025, 65011),
    ("MRK",  "revenue",     2024, 64168),
    ("MRK",  "revenue",     2023, 60115),
    ("MRK",  "revenue",     2022, 59283),
    ("MRK",  "rd_expense",  2025, 18300),
    ("MRK",  "rd_expense",  2024, 17500),
    ("MRK",  "rd_expense",  2023, 17596),
    ("MRK",  "rd_expense",  2022, 13548),

    ("JNJ",  "revenue",     2025, 94193),
    ("JNJ",  "revenue",     2024, 88821),
    ("JNJ",  "revenue",     2023, 85159),
    ("JNJ",  "revenue",     2022, 94943),
    ("JNJ",  "rd_expense",  2025, 16200),
    ("JNJ",  "rd_expense",  2024, 15800),
    ("JNJ",  "rd_expense",  2023, 15101),
    ("JNJ",  "rd_expense",  2022, 14603),

    ("ABBV", "revenue",     2025, 61160),
    ("ABBV", "revenue",     2024, 56334),
    ("ABBV", "revenue",     2023, 54318),
    ("ABBV", "revenue",     2022, 58054),
    ("ABBV", "rd_expense",  2025, 9800),
    ("ABBV", "rd_expense",  2024, 9200),
    ("ABBV", "rd_expense",  2023, 6540),
    ("ABBV", "rd_expense",  2022, 6361),

    ("BMY",  "revenue",     2025, 48194),
    ("BMY",  "revenue",     2024, 48300),
    ("BMY",  "revenue",     2023, 45006),
    ("BMY",  "revenue",     2022, 46159),
    ("BMY",  "rd_expense",  2025, 9100),
    ("BMY",  "rd_expense",  2024, 9600),
    ("BMY",  "rd_expense",  2023, 9036),
    ("BMY",  "rd_expense",  2022, 7893),

    ("LLY",  "revenue",     2025, 65179),
    ("LLY",  "revenue",     2024, 45042),
    ("LLY",  "revenue",     2023, 34124),
    ("LLY",  "revenue",     2022, 28541),
    ("LLY",  "rd_expense",  2025, 12600),
    ("LLY",  "rd_expense",  2024, 11200),
    ("LLY",  "rd_expense",  2023, 9312),
    ("LLY",  "rd_expense",  2022, 7193),

    ("AMGN", "revenue",     2025, 36751),
    ("AMGN", "revenue",     2024, 33424),
    ("AMGN", "revenue",     2023, 28190),
    ("AMGN", "revenue",     2022, 26323),
    ("AMGN", "rd_expense",  2025, 5900),
    ("AMGN", "rd_expense",  2024, 5400),
    ("AMGN", "rd_expense",  2023, 4622),
    ("AMGN", "rd_expense",  2022, 3995),

    ("GILD", "revenue",     2025, 29443),
    ("GILD", "revenue",     2024, 28754),
    ("GILD", "revenue",     2023, 27116),
    ("GILD", "revenue",     2022, 27281),
    ("GILD", "rd_expense",  2025, 5600),
    ("GILD", "rd_expense",  2024, 5200),
    ("GILD", "rd_expense",  2023, 5020),
    ("GILD", "rd_expense",  2022, 4476),
]

with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS edgar_facts"))
    conn.execute(text("""
        CREATE TABLE edgar_facts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker       TEXT NOT NULL,
            metric       TEXT NOT NULL,
            fiscal_year  INTEGER NOT NULL,
            value_usd_m  REAL NOT NULL
        )
    """))
    for ticker, metric, fy, val in EDGAR_FACTS:
        conn.execute(text(
            "INSERT INTO edgar_facts (ticker, metric, fiscal_year, value_usd_m) "
            "VALUES (:t,:m,:fy,:v)"
        ), {"t": ticker, "m": metric, "fy": fy, "v": val})

# Load into pandas too
df = pd.read_sql("SELECT * FROM edgar_facts", engine)

print("=" * 70)
print("  CADUCEUS — SQL vs Pandas Translation Challenge")
print("  Phase 1 Universe: PFE MRK JNJ ABBV BMY LLY AMGN GILD | FY2022-2025")
print("=" * 70)

# ── Q1: Total revenue per ticker ──────────────────────────────────────────────
print("\n" + "─" * 70)
print("Q1: Total Revenue per Ticker (FY2022–2025, $M)")
print("─" * 70)

print("\n  [SQL]")
with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT ticker, SUM(value_usd_m) AS total_revenue_usd_m
        FROM edgar_facts
        WHERE metric = 'revenue'
        GROUP BY ticker
        ORDER BY total_revenue_usd_m DESC
    """)).fetchall()
    for r in rows:
        print(f"    {r[0]:<6}  ${r[1]:>10,.0f}M")

print("\n  [Pandas]")
q1 = (df[df["metric"] == "revenue"]
      .groupby("ticker")["value_usd_m"]
      .sum()
      .sort_values(ascending=False)
      .reset_index()
      .rename(columns={"value_usd_m": "total_revenue_usd_m"}))
for _, row in q1.iterrows():
    print(f"    {row['ticker']:<6}  ${row['total_revenue_usd_m']:>10,.0f}M")

# ── Q2: Which year had the highest total universe revenue? ────────────────────
print("\n" + "─" * 70)
print("Q2: Fiscal Year with Highest Total Universe Revenue")
print("─" * 70)

print("\n  [SQL]")
with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT fiscal_year, SUM(value_usd_m) AS universe_revenue_usd_m
        FROM edgar_facts
        WHERE metric = 'revenue'
        GROUP BY fiscal_year
        ORDER BY universe_revenue_usd_m DESC
        LIMIT 1
    """)).fetchall()
    for r in rows:
        print(f"    FY{r[0]}  ${r[1]:>10,.0f}M")

print("\n  [Pandas]")
q2 = (df[df["metric"] == "revenue"]
      .groupby("fiscal_year")["value_usd_m"]
      .sum()
      .sort_values(ascending=False))
print(f"    FY{q2.index[0]}  ${q2.iloc[0]:>10,.0f}M")

# ── Q3: Average R&D expense per ticker ───────────────────────────────────────
print("\n" + "─" * 70)
print("Q3: Average Annual R&D Expense per Ticker ($M)")
print("─" * 70)

print("\n  [SQL]")
with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT ticker, ROUND(AVG(value_usd_m), 0) AS avg_rd_usd_m
        FROM edgar_facts
        WHERE metric = 'rd_expense'
        GROUP BY ticker
        ORDER BY avg_rd_usd_m DESC
    """)).fetchall()
    for r in rows:
        print(f"    {r[0]:<6}  ${r[1]:>8,.0f}M")

print("\n  [Pandas]")
q3 = (df[df["metric"] == "rd_expense"]
      .groupby("ticker")["value_usd_m"]
      .mean()
      .round(0)
      .sort_values(ascending=False)
      .reset_index()
      .rename(columns={"value_usd_m": "avg_rd_usd_m"}))
for _, row in q3.iterrows():
    print(f"    {row['ticker']:<6}  ${row['avg_rd_usd_m']:>8,.0f}M")

# ── Q4: Tickers with total 4-year revenue > $200B ────────────────────────────
print("\n" + "─" * 70)
print("Q4: Tickers with 4-Year Total Revenue > $200,000M")
print("─" * 70)

print("\n  [SQL]")
with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT ticker, SUM(value_usd_m) AS total_rev
        FROM edgar_facts
        WHERE metric = 'revenue'
        GROUP BY ticker
        HAVING SUM(value_usd_m) > 200000
        ORDER BY total_rev DESC
    """)).fetchall()
    for r in rows:
        print(f"    {r[0]:<6}  ${r[1]:>10,.0f}M")

print("\n  [Pandas]")
q4 = (df[df["metric"] == "revenue"]
      .groupby("ticker")["value_usd_m"]
      .sum()
      .reset_index()
      .rename(columns={"value_usd_m": "total_rev"}))
q4 = q4[q4["total_rev"] > 200_000].sort_values("total_rev", ascending=False)
for _, row in q4.iterrows():
    print(f"    {row['ticker']:<6}  ${row['total_rev']:>10,.0f}M")

# ── BONUS: pd.read_sql() round-trip ──────────────────────────────────────────
print("\n" + "─" * 70)
print("BONUS: pd.read_sql() — SQL query result loaded directly as DataFrame")
print("─" * 70)
bonus_df = pd.read_sql("""
    SELECT ticker,
           SUM(CASE WHEN metric='revenue'    THEN value_usd_m END) AS revenue,
           SUM(CASE WHEN metric='rd_expense' THEN value_usd_m END) AS rd_expense,
           ROUND(
               SUM(CASE WHEN metric='rd_expense' THEN value_usd_m END) /
               SUM(CASE WHEN metric='revenue'    THEN value_usd_m END) * 100, 1
           ) AS rd_intensity_pct
    FROM edgar_facts
    WHERE fiscal_year = 2025
    GROUP BY ticker
    ORDER BY rd_intensity_pct DESC
""", engine)
print(f"\n  R&D Intensity FY2025 (via pd.read_sql):\n")
print(bonus_df.to_string(index=False))
