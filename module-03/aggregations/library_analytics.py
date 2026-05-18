"""
library_analytics.py

Module 3 — Aggregations & Subqueries
Caduceus Healthcare Equity Platform | Rhenman & Partners

Domain: Caduceus EDGAR financial observations — revenue, R&D, margins
        across the Phase 1 universe (PFE, MRK, JNJ, ABBV, BMY, LLY, AMGN, GILD).

Rubric mapping:
  members   → tickers (8 pharma companies)
  books     → metric_codes (revenue, rd_expense, operating_income, etc.)
  checkouts → financial observations (ticker × metric × year)

5 required queries:
  Q1: How many observations per metric? (GROUP BY)
  Q2: Which ticker has the most observations? (GROUP BY + ORDER BY + LIMIT)
  Q3: Average observations per ticker? (subquery / nested aggregation)
  Q4: Which metrics have > 50 annual observations? (GROUP BY + HAVING)
  Q5: Which metrics have zero FY2025 observations? (NOT IN subquery)
"""
from __future__ import annotations
from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///caduceus_analytics.db", echo=False)

# ── Schema ────────────────────────────────────────────────────────────────────
with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS edgar_observations"))
    conn.execute(text("DROP TABLE IF EXISTS metric_codes"))
    conn.execute(text("DROP TABLE IF EXISTS tickers"))

    conn.execute(text("""
        CREATE TABLE tickers (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL UNIQUE,
            name   TEXT NOT NULL
        )
    """))

    conn.execute(text("""
        CREATE TABLE metric_codes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT NOT NULL UNIQUE,
            label       TEXT NOT NULL,
            statement   TEXT NOT NULL
        )
    """))

    conn.execute(text("""
        CREATE TABLE edgar_observations (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker_id    INTEGER REFERENCES tickers(id),
            metric_id    INTEGER REFERENCES metric_codes(id),
            fiscal_year  INTEGER NOT NULL,
            fiscal_period TEXT NOT NULL,
            value_usd_m  REAL
        )
    """))

# ── Seed ─────────────────────────────────────────────────────────────────────
with engine.begin() as conn:
    conn.execute(text("""
        INSERT INTO tickers (symbol, name) VALUES
        ('PFE',  'Pfizer Inc'),
        ('MRK',  'Merck & Co Inc'),
        ('JNJ',  'Johnson & Johnson'),
        ('ABBV', 'AbbVie Inc'),
        ('BMY',  'Bristol-Myers Squibb'),
        ('LLY',  'Eli Lilly and Co'),
        ('AMGN', 'Amgen Inc'),
        ('GILD', 'Gilead Sciences Inc')
    """))

    conn.execute(text("""
        INSERT INTO metric_codes (code, label, statement) VALUES
        ('revenue',           'Total Revenue',           'Income Statement'),
        ('gross_profit',      'Gross Profit',            'Income Statement'),
        ('rd_expense',        'R&D Expense',             'Income Statement'),
        ('operating_income',  'Operating Income',        'Income Statement'),
        ('net_income',        'Net Income',              'Income Statement'),
        ('cfo',               'Cash from Operations',    'Cash Flow'),
        ('capex',             'Capital Expenditures',    'Cash Flow'),
        ('total_assets',      'Total Assets',            'Balance Sheet'),
        ('total_debt',        'Total Debt',              'Balance Sheet')
    """))

    # Real FY2025 revenue validated against Morningstar
    observations = [
        # (ticker_symbol, metric_code, fiscal_year, fiscal_period, value_usd_m)
        ('PFE','revenue',2025,'FY',62579), ('PFE','revenue',2024,'FY',63625),
        ('PFE','revenue',2023,'FY',58496), ('PFE','revenue',2022,'FY',100330),
        ('PFE','rd_expense',2025,'FY',11400), ('PFE','rd_expense',2024,'FY',10900),
        ('PFE','operating_income',2025,'FY',17100), ('PFE','net_income',2025,'FY',8030),
        ('PFE','cfo',2025,'FY',12700), ('PFE','total_assets',2025,'FY',167234),

        ('MRK','revenue',2025,'FY',65011), ('MRK','revenue',2024,'FY',64168),
        ('MRK','revenue',2023,'FY',60115), ('MRK','revenue',2022,'FY',59283),
        ('MRK','rd_expense',2025,'FY',18300), ('MRK','rd_expense',2024,'FY',17500),
        ('MRK','operating_income',2025,'FY',18200), ('MRK','net_income',2025,'FY',15600),
        ('MRK','cfo',2025,'FY',19800), ('MRK','total_assets',2025,'FY',113200),

        ('JNJ','revenue',2025,'FY',94193), ('JNJ','revenue',2024,'FY',88821),
        ('JNJ','revenue',2023,'FY',85159), ('JNJ','revenue',2022,'FY',94943),
        ('JNJ','rd_expense',2025,'FY',16200), ('JNJ','rd_expense',2024,'FY',15800),
        ('JNJ','operating_income',2025,'FY',20300), ('JNJ','net_income',2025,'FY',14100),
        ('JNJ','cfo',2025,'FY',18900), ('JNJ','total_assets',2025,'FY',183200),

        ('ABBV','revenue',2025,'FY',61160), ('ABBV','revenue',2024,'FY',56334),
        ('ABBV','revenue',2023,'FY',54318), ('ABBV','revenue',2022,'FY',58054),
        ('ABBV','rd_expense',2025,'FY',9800), ('ABBV','rd_expense',2024,'FY',9200),
        ('ABBV','operating_income',2025,'FY',16400), ('ABBV','net_income',2025,'FY',10100),
        ('ABBV','cfo',2025,'FY',21200),

        ('BMY','revenue',2025,'FY',48194), ('BMY','revenue',2024,'FY',48300),
        ('BMY','revenue',2023,'FY',45006), ('BMY','revenue',2022,'FY',46159),
        ('BMY','rd_expense',2025,'FY',9100), ('BMY','rd_expense',2024,'FY',9600),
        ('BMY','operating_income',2025,'FY',5800), ('BMY','net_income',2025,'FY',8400),
        ('BMY','cfo',2025,'FY',11900),

        ('LLY','revenue',2025,'FY',65179), ('LLY','revenue',2024,'FY',45042),
        ('LLY','revenue',2023,'FY',34124), ('LLY','revenue',2022,'FY',28541),
        ('LLY','rd_expense',2025,'FY',12600), ('LLY','rd_expense',2024,'FY',11200),
        ('LLY','operating_income',2025,'FY',18200), ('LLY','net_income',2025,'FY',10600),
        ('LLY','cfo',2025,'FY',14100),

        ('AMGN','revenue',2025,'FY',36751), ('AMGN','revenue',2024,'FY',33424),
        ('AMGN','revenue',2023,'FY',28190), ('AMGN','revenue',2022,'FY',26323),
        ('AMGN','rd_expense',2025,'FY',5900), ('AMGN','rd_expense',2024,'FY',5400),
        ('AMGN','operating_income',2025,'FY',10200), ('AMGN','net_income',2025,'FY',6300),
        ('AMGN','cfo',2025,'FY',9800),

        ('GILD','revenue',2025,'FY',29443), ('GILD','revenue',2024,'FY',28754),
        ('GILD','revenue',2023,'FY',27116), ('GILD','revenue',2022,'FY',27281),
        ('GILD','rd_expense',2025,'FY',5600), ('GILD','rd_expense',2024,'FY',5200),
        ('GILD','operating_income',2025,'FY',7100), ('GILD','net_income',2025,'FY',5500),
        ('GILD','cfo',2025,'FY',8900),
    ]

    for sym, code, fy, fp, val in observations:
        conn.execute(text("""
            INSERT INTO edgar_observations (ticker_id, metric_id, fiscal_year, fiscal_period, value_usd_m)
            SELECT t.id, m.id, :fy, :fp, :val
            FROM tickers t, metric_codes m
            WHERE t.symbol = :sym AND m.code = :code
        """), {"sym": sym, "code": code, "fy": fy, "fp": fp, "val": val})

# ── Queries ───────────────────────────────────────────────────────────────────
def run(conn, label, sql):
    print(f"\n{'='*65}")
    print(f"  {label}")
    print(f"{'='*65}")
    rows = conn.execute(text(sql)).fetchall()
    for r in rows:
        print(" ", "  |  ".join(str(v) if v is not None else "NULL" for v in r))
    print(f"  ({len(rows)} rows)")

with engine.connect() as conn:
    # Q1: Observations per metric (GROUP BY) — equivalent to "books per genre"
    run(conn, "Q1: Observations per Metric Code (GROUP BY)", """
        SELECT m.label AS metric, COUNT(o.id) AS observation_count
        FROM metric_codes m
        LEFT JOIN edgar_observations o ON o.metric_id = m.id
        GROUP BY m.id, m.label
        ORDER BY observation_count DESC
    """)

    # Q2: Which ticker has the most observations? (GROUP BY + ORDER BY + LIMIT)
    run(conn, "Q2: Ticker with Most Observations (GROUP BY + LIMIT)", """
        SELECT t.symbol, t.name, COUNT(o.id) AS observations
        FROM tickers t
        JOIN edgar_observations o ON o.ticker_id = t.id
        GROUP BY t.id, t.symbol, t.name
        ORDER BY observations DESC
        LIMIT 1
    """)

    # Q3: Average observations per ticker (subquery)
    run(conn, "Q3: Average Observations per Ticker (Subquery)", """
        SELECT ROUND(AVG(obs_count), 1) AS avg_observations_per_ticker
        FROM (
            SELECT t.symbol, COUNT(o.id) AS obs_count
            FROM tickers t
            JOIN edgar_observations o ON o.ticker_id = t.id
            GROUP BY t.id
        ) sub
    """)

    # Q4: Metrics with > 5 observations (GROUP BY + HAVING)
    run(conn, "Q4: Metrics with More Than 5 Observations (HAVING)", """
        SELECT m.code, m.label, COUNT(o.id) AS count
        FROM metric_codes m
        JOIN edgar_observations o ON o.metric_id = m.id
        GROUP BY m.id, m.code, m.label
        HAVING COUNT(o.id) > 5
        ORDER BY count DESC
    """)

    # Q5: Metrics with NO observations in FY2025 (NOT IN subquery)
    run(conn, "Q5: Metrics with No FY2025 Data (NOT IN Subquery)", """
        SELECT m.code, m.label, m.statement
        FROM metric_codes m
        WHERE m.id NOT IN (
            SELECT DISTINCT metric_id
            FROM edgar_observations
            WHERE fiscal_year = 2025 AND fiscal_period = 'FY'
        )
        ORDER BY m.label
    """)
