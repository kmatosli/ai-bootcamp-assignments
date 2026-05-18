"""
sql_fundamentals.py

Module 3 — SQL Fundamentals: SELECT, INSERT, UPDATE, DELETE
Caduceus Healthcare Equity Platform | Rhenman & Partners

Domain: Phase 1 pharma universe — financial observations per ticker.
Demonstrates all four core SQL operations using raw sqlite3.

Rubric mapping:
  INSERT  → add new financial observations
  SELECT  → query revenue and R&D across tickers
  UPDATE  → revise a value after restatement
  DELETE  → remove an obsolete observation
"""
import sqlite3

# ── Connect ───────────────────────────────────────────────────────────────────
conn = sqlite3.connect("caduceus_fundamentals.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

# ── Create table ──────────────────────────────────────────────────────────────
cursor.execute("DROP TABLE IF EXISTS financial_observations")
cursor.execute("""
    CREATE TABLE financial_observations (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker       TEXT NOT NULL,
        company      TEXT NOT NULL,
        metric       TEXT NOT NULL,
        fiscal_year  INTEGER NOT NULL,
        value_usd_m  REAL NOT NULL
    )
""")

# ── INSERT ────────────────────────────────────────────────────────────────────
print("=" * 60)
print("  INSERT — Loading Phase 1 Universe FY2025 Data")
print("=" * 60)

observations = [
    ("PFE",  "Pfizer",       "revenue",    2025, 62579),
    ("MRK",  "Merck",        "revenue",    2025, 65011),
    ("JNJ",  "J&J",          "revenue",    2025, 94193),
    ("ABBV", "AbbVie",       "revenue",    2025, 61160),
    ("BMY",  "BMS",          "revenue",    2025, 48194),
    ("LLY",  "Eli Lilly",    "revenue",    2025, 65179),
    ("AMGN", "Amgen",        "revenue",    2025, 36751),
    ("GILD", "Gilead",       "revenue",    2025, 29443),
    ("PFE",  "Pfizer",       "rd_expense", 2025, 11400),
    ("MRK",  "Merck",        "rd_expense", 2025, 18300),
    ("LLY",  "Eli Lilly",    "rd_expense", 2025, 12600),
    ("ABBV", "AbbVie",       "rd_expense", 2025, 9800),
]

cursor.executemany("""
    INSERT INTO financial_observations (ticker, company, metric, fiscal_year, value_usd_m)
    VALUES (?, ?, ?, ?, ?)
""", observations)
conn.commit()
print(f"  Inserted {len(observations)} rows.\n")

# ── SELECT ────────────────────────────────────────────────────────────────────
print("=" * 60)
print("  SELECT — All FY2025 Revenue, Highest First")
print("=" * 60)
cursor.execute("""
    SELECT ticker, company, value_usd_m
    FROM financial_observations
    WHERE metric = 'revenue' AND fiscal_year = 2025
    ORDER BY value_usd_m DESC
""")
for ticker, company, value in cursor.fetchall():
    print(f"  [{ticker}] {company:<15} ${value:>10,.0f}M")

print()
print("=" * 60)
print("  SELECT — R&D Expense > $10,000M")
print("=" * 60)
cursor.execute("""
    SELECT ticker, company, value_usd_m
    FROM financial_observations
    WHERE metric = 'rd_expense' AND value_usd_m > 10000
    ORDER BY value_usd_m DESC
""")
for ticker, company, value in cursor.fetchall():
    print(f"  [{ticker}] {company:<15} ${value:>8,.0f}M R&D")

# ── UPDATE ────────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("  UPDATE — Revise PFE revenue after 10-K restatement")
print("=" * 60)
cursor.execute("""
    SELECT value_usd_m FROM financial_observations
    WHERE ticker = 'PFE' AND metric = 'revenue' AND fiscal_year = 2025
""")
before = cursor.fetchone()[0]
print(f"  Before: PFE revenue = ${before:,.0f}M")

cursor.execute("""
    UPDATE financial_observations
    SET value_usd_m = 62581
    WHERE ticker = 'PFE' AND metric = 'revenue' AND fiscal_year = 2025
""")
conn.commit()

cursor.execute("""
    SELECT value_usd_m FROM financial_observations
    WHERE ticker = 'PFE' AND metric = 'revenue' AND fiscal_year = 2025
""")
after = cursor.fetchone()[0]
print(f"  After:  PFE revenue = ${after:,.0f}M  (restated +$2M)")

# ── DELETE ────────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("  DELETE — Remove BMY R&D (not yet loaded)")
print("=" * 60)
cursor.execute("""
    SELECT COUNT(*) FROM financial_observations WHERE ticker = 'BMY' AND metric = 'rd_expense'
""")
print(f"  BMY R&D rows before delete: {cursor.fetchone()[0]}")

cursor.execute("""
    DELETE FROM financial_observations
    WHERE ticker = 'BMY' AND metric = 'rd_expense'
""")
conn.commit()

cursor.execute("""
    SELECT COUNT(*) FROM financial_observations WHERE ticker = 'BMY' AND metric = 'rd_expense'
""")
print(f"  BMY R&D rows after delete:  {cursor.fetchone()[0]}")

# ── Final SELECT ──────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("  SELECT — Final State of All Observations")
print("=" * 60)
cursor.execute("""
    SELECT ticker, metric, fiscal_year, value_usd_m
    FROM financial_observations
    ORDER BY metric, value_usd_m DESC
""")
for row in cursor.fetchall():
    print(f"  [{row[0]}] {row[1]:<12} FY{row[2]}  ${row[3]:>10,.0f}M")

# ── Close ─────────────────────────────────────────────────────────────────────
conn.close()
print("\n  Connection closed.\n")
