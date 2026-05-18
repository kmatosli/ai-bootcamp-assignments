"""
product_finder.py

Module 3 — Filtering, Sorting & Conditions (WHERE, ORDER BY, LIMIT)
Caduceus Healthcare Equity Platform | Rhenman & Partners

Domain: EDGAR financial observations for the Phase 1 pharma universe.
        Each "product" is a ticker × metric × year observation.

Rubric mapping:
  Products     → financial observations (ticker, metric, value, year)
  Category     → metric statement (Income Statement, Cash Flow, Balance Sheet)
  Out of stock → missing/null observations
  Rating ≥ 4.5 → revenue margin ≥ 25%
  Price < $100 → R&D expense < $10B
  Name LIKE    → metric label LIKE '%Revenue%'
  NOT IN cat   → not Balance Sheet metrics

5 required queries (exact rubric structure):
  Q1: Which observations are missing values? (out of stock)
  Q2: Which tickers have operating margin ≥ 25% AND R&D < $15B?
  Q3: Top 3 highest-revenue tickers in FY2025 (sorted desc, limit 3)
  Q4: Metrics with "Revenue" in the name
  Q5: NOT Income Statement metrics that are in stock (have values)
"""
from __future__ import annotations
from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///caduceus_filter.db", echo=False)

# ── Schema + seed ─────────────────────────────────────────────────────────────
with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS observations"))
    conn.execute(text("""
        CREATE TABLE observations (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker         TEXT NOT NULL,
            company        TEXT NOT NULL,
            metric_code    TEXT NOT NULL,
            metric_label   TEXT NOT NULL,
            statement      TEXT NOT NULL,
            fiscal_year    INTEGER NOT NULL,
            value_usd_m    REAL
        )
    """))

    rows = [
        # PFE FY2025
        ('PFE','Pfizer',       'revenue',          'Total Revenue',         'Income Statement', 2025, 62579),
        ('PFE','Pfizer',       'rd_expense',        'R&D Expense',           'Income Statement', 2025, 11400),
        ('PFE','Pfizer',       'operating_income',  'Operating Income',      'Income Statement', 2025, 17100),
        ('PFE','Pfizer',       'net_income',        'Net Income',            'Income Statement', 2025,  8030),
        ('PFE','Pfizer',       'cfo',               'Cash from Operations',  'Cash Flow',        2025, 12700),
        ('PFE','Pfizer',       'total_assets',      'Total Assets',          'Balance Sheet',    2025,167234),
        ('PFE','Pfizer',       'total_debt',        'Total Debt',            'Balance Sheet',    2025, 62100),
        # MRK FY2025
        ('MRK','Merck',        'revenue',           'Total Revenue',         'Income Statement', 2025, 65011),
        ('MRK','Merck',        'rd_expense',        'R&D Expense',           'Income Statement', 2025, 18300),
        ('MRK','Merck',        'operating_income',  'Operating Income',      'Income Statement', 2025, 18200),
        ('MRK','Merck',        'net_income',        'Net Income',            'Income Statement', 2025, 15600),
        ('MRK','Merck',        'cfo',               'Cash from Operations',  'Cash Flow',        2025, 19800),
        ('MRK','Merck',        'total_assets',      'Total Assets',          'Balance Sheet',    2025,113200),
        ('MRK','Merck',        'total_debt',        'Total Debt',            'Balance Sheet',    2025, 35800),
        # JNJ FY2025
        ('JNJ','J&J',          'revenue',           'Total Revenue',         'Income Statement', 2025, 94193),
        ('JNJ','J&J',          'rd_expense',        'R&D Expense',           'Income Statement', 2025, 16200),
        ('JNJ','J&J',          'operating_income',  'Operating Income',      'Income Statement', 2025, 20300),
        ('JNJ','J&J',          'net_income',        'Net Income',            'Income Statement', 2025, 14100),
        ('JNJ','J&J',          'cfo',               'Cash from Operations',  'Cash Flow',        2025, 18900),
        ('JNJ','J&J',          'total_assets',      'Total Assets',          'Balance Sheet',    2025,183200),
        # ABBV FY2025
        ('ABBV','AbbVie',      'revenue',           'Total Revenue',         'Income Statement', 2025, 61160),
        ('ABBV','AbbVie',      'rd_expense',        'R&D Expense',           'Income Statement', 2025,  9800),
        ('ABBV','AbbVie',      'operating_income',  'Operating Income',      'Income Statement', 2025, 16400),
        ('ABBV','AbbVie',      'net_income',        'Net Income',            'Income Statement', 2025, 10100),
        ('ABBV','AbbVie',      'cfo',               'Cash from Operations',  'Cash Flow',        2025, 21200),
        # LLY FY2025
        ('LLY','Eli Lilly',    'revenue',           'Total Revenue',         'Income Statement', 2025, 65179),
        ('LLY','Eli Lilly',    'rd_expense',        'R&D Expense',           'Income Statement', 2025, 12600),
        ('LLY','Eli Lilly',    'operating_income',  'Operating Income',      'Income Statement', 2025, 18200),
        ('LLY','Eli Lilly',    'net_income',        'Net Income',            'Income Statement', 2025, 10600),
        ('LLY','Eli Lilly',    'cfo',               'Cash from Operations',  'Cash Flow',        2025, 14100),
        # AMGN FY2025
        ('AMGN','Amgen',       'revenue',           'Total Revenue',         'Income Statement', 2025, 36751),
        ('AMGN','Amgen',       'rd_expense',        'R&D Expense',           'Income Statement', 2025,  5900),
        ('AMGN','Amgen',       'operating_income',  'Operating Income',      'Income Statement', 2025, 10200),
        ('AMGN','Amgen',       'net_income',        'Net Income',            'Income Statement', 2025,  6300),
        # GILD FY2025
        ('GILD','Gilead',      'revenue',           'Total Revenue',         'Income Statement', 2025, 29443),
        ('GILD','Gilead',      'rd_expense',        'R&D Expense',           'Income Statement', 2025,  5600),
        ('GILD','Gilead',      'operating_income',  'Operating Income',      'Income Statement', 2025,  7100),
        ('GILD','Gilead',      'net_income',        'Net Income',            'Income Statement', 2025,  5500),
        # BMY FY2025 — missing some to demo Q1
        ('BMY','BMS',          'revenue',           'Total Revenue',         'Income Statement', 2025, 48194),
        ('BMY','BMS',          'rd_expense',        'R&D Expense',           'Income Statement', 2025,  9100),
        ('BMY','BMS',          'operating_income',  'Operating Income',      'Income Statement', 2025,  5800),
        ('BMY','BMS',          'net_income',        'Net Income',            'Income Statement', 2025,  None),  # missing
        ('BMY','BMS',          'total_assets',      'Total Assets',          'Balance Sheet',    2025,  None),  # missing
    ]
    for r in rows:
        conn.execute(text("""
            INSERT INTO observations
            (ticker, company, metric_code, metric_label, statement, fiscal_year, value_usd_m)
            VALUES (:t,:c,:mc,:ml,:s,:fy,:v)
        """), {"t":r[0],"c":r[1],"mc":r[2],"ml":r[3],"s":r[4],"fy":r[5],"v":r[6]})

# ── Queries ───────────────────────────────────────────────────────────────────
def run(conn, label, sql):
    print(f"\n{'='*65}")
    print(f"  {label}")
    print(f"{'='*65}")
    rows = conn.execute(text(sql)).fetchall()
    for r in rows:
        print(" ", "  |  ".join(str(v) if v is not None else "NULL" for v in r))
    if not rows:
        print("  (no rows)")

with engine.connect() as conn:
    # Q1: Missing values (out of stock equivalent)
    run(conn, "Q1: Observations with Missing Values (NULL)", """
        SELECT ticker, company, metric_label, fiscal_year
        FROM observations
        WHERE value_usd_m IS NULL
        ORDER BY ticker, metric_label
    """)

    # Q2: Tickers with operating margin >= 25% AND R&D < $15B (rating + price filter)
    run(conn, "Q2: Tickers — Op Margin ≥ 25% AND R&D < $15B", """
        SELECT o1.ticker, o1.company,
               ROUND(o2.value_usd_m / o1.value_usd_m * 100, 1) AS op_margin_pct,
               o3.value_usd_m AS rd_usd_m
        FROM observations o1
        JOIN observations o2 ON o1.ticker = o2.ticker AND o2.metric_code = 'operating_income'
                              AND o2.fiscal_year = 2025
        JOIN observations o3 ON o1.ticker = o3.ticker AND o3.metric_code = 'rd_expense'
                              AND o3.fiscal_year = 2025
        WHERE o1.metric_code = 'revenue' AND o1.fiscal_year = 2025
          AND (o2.value_usd_m / o1.value_usd_m) >= 0.25
          AND o3.value_usd_m < 15000
        ORDER BY op_margin_pct DESC
    """)

    # Q3: Top 3 tickers by FY2025 revenue (highest revenue, limit 3)
    run(conn, "Q3: Top 3 Tickers by FY2025 Revenue", """
        SELECT ticker, company, value_usd_m AS revenue_usd_m
        FROM observations
        WHERE metric_code = 'revenue' AND fiscal_year = 2025
        ORDER BY value_usd_m DESC
        LIMIT 3
    """)

    # Q4: Metrics with "Revenue" in the label (LIKE)
    run(conn, "Q4: Metrics with 'Revenue' in the Label (LIKE)", """
        SELECT DISTINCT metric_code, metric_label, statement
        FROM observations
        WHERE metric_label LIKE '%Revenue%'
        ORDER BY metric_label
    """)

    # Q5: Non-Income-Statement metrics that have values (NOT in category, in stock)
    run(conn, "Q5: Non-Income-Statement Metrics with Values", """
        SELECT DISTINCT ticker, company, metric_label, statement, value_usd_m
        FROM observations
        WHERE statement != 'Income Statement'
          AND value_usd_m IS NOT NULL
        ORDER BY statement, ticker
    """)
