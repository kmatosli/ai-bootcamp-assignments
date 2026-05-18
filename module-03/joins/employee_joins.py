"""
employee_joins.py

Module 3 — Joins: Connecting Tables Together
Caduceus Healthcare Equity Platform | Rhenman & Partners

Domain: Rhenman analysts (employees), therapeutic areas (departments),
        and drug coverage assignments (projects).

Rubric mapping:
  departments → therapeutic_areas (Oncology, Immunology, etc.)
  employees   → analysts (Rhenman team members)
  projects    → drug_coverage (which analyst covers which drug)

5 required queries:
  Q1: INNER JOIN  — analysts with their therapeutic area
  Q2: LEFT JOIN   — all areas, even uncovered ones
  Q3: LEFT JOIN   — all analysts and drugs they cover (including uncovered analysts)
  Q4: LEFT JOIN + IS NULL — analysts covering no drugs
  Q5: 3-table JOIN — drug + analyst name + their therapeutic area
"""
from __future__ import annotations
from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///caduceus_joins.db", echo=False)

# ── Schema ────────────────────────────────────────────────────────────────────
with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS drug_coverage"))
    conn.execute(text("DROP TABLE IF EXISTS analysts"))
    conn.execute(text("DROP TABLE IF EXISTS therapeutic_areas"))

    conn.execute(text("""
        CREATE TABLE therapeutic_areas (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT NOT NULL UNIQUE,
            focus    TEXT NOT NULL
        )
    """))

    conn.execute(text("""
        CREATE TABLE analysts (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            name                 TEXT NOT NULL,
            role                 TEXT NOT NULL,
            years_experience     INTEGER,
            therapeutic_area_id  INTEGER REFERENCES therapeutic_areas(id)
        )
    """))

    conn.execute(text("""
        CREATE TABLE drug_coverage (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            drug_name   TEXT NOT NULL,
            ticker      TEXT NOT NULL,
            analyst_id  INTEGER REFERENCES analysts(id)
        )
    """))

# ── Seed ─────────────────────────────────────────────────────────────────────
with engine.begin() as conn:
    conn.execute(text("""
        INSERT INTO therapeutic_areas (name, focus) VALUES
        ('Oncology',        'Solid tumors and hematologic malignancies'),
        ('Immunology',      'Autoimmune and inflammatory diseases'),
        ('Cardiometabolic', 'Cardiovascular and metabolic disorders'),
        ('Rare Disease',    'Orphan and rare genetic conditions'),
        ('Vaccines',        'Infectious disease prevention')
    """))

    conn.execute(text("""
        INSERT INTO analysts (name, role, years_experience, therapeutic_area_id) VALUES
        ('Henrik Rhenman',       'CIO / Founder',                    30, 1),
        ('Kaspar Hållsten',      'Analyst — MedTech',                12, NULL),
        ('Hugo Schmidt',         'Analyst — Healthcare Services',    10, NULL),
        ('Amennai Beyeen',       'Analyst — Biopharma',              8,  2),
        ('Camilla Oxhamre Cruse','PM — Biopharma',                   15, 2),
        ('Kathy Matosli',        'Quant Developer',                  5,  NULL),
        ('Lars Eriksson',        'Junior Analyst — Oncology',        3,  1),
        ('Anna Lindberg',        'Junior Analyst — Cardiometabolic', 2,  3)
    """))

    conn.execute(text("""
        INSERT INTO drug_coverage (drug_name, ticker, analyst_id) VALUES
        ('Keytruda',  'MRK',  1),
        ('Opdivo',    'BMY',  7),
        ('Humira',    'ABBV', 4),
        ('Skyrizi',   'ABBV', 5),
        ('Rinvoq',    'ABBV', 4),
        ('Mounjaro',  'LLY',  8),
        ('Eliquis',   'BMY',  8),
        ('Vyndaqel',  'PFE',  NULL)
    """))

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
    # Q1: All analysts with their therapeutic area (INNER JOIN — only matched)
    run(conn, "Q1: Analysts with Therapeutic Area (INNER JOIN)", """
        SELECT a.name, a.role, t.name AS therapeutic_area
        FROM analysts a
        INNER JOIN therapeutic_areas t ON a.therapeutic_area_id = t.id
        ORDER BY t.name, a.name
    """)

    # Q2: All therapeutic areas even if no analyst assigned (LEFT JOIN)
    run(conn, "Q2: All Therapeutic Areas — Including Unassigned (LEFT JOIN)", """
        SELECT t.name AS therapeutic_area, t.focus,
               COUNT(a.id) AS analyst_count
        FROM therapeutic_areas t
        LEFT JOIN analysts a ON a.therapeutic_area_id = t.id
        GROUP BY t.id, t.name, t.focus
        ORDER BY t.name
    """)

    # Q3: All analysts and drugs they cover, including those with no coverage
    run(conn, "Q3: Analysts and Drug Coverage — Including Uncovered (LEFT JOIN)", """
        SELECT a.name AS analyst, a.role,
               d.drug_name, d.ticker
        FROM analysts a
        LEFT JOIN drug_coverage d ON d.analyst_id = a.id
        ORDER BY a.name, d.drug_name
    """)

    # Q4: Analysts covering NO drugs (LEFT JOIN + IS NULL)
    run(conn, "Q4: Analysts With No Drug Coverage (LEFT JOIN + IS NULL)", """
        SELECT a.name, a.role, a.years_experience
        FROM analysts a
        LEFT JOIN drug_coverage d ON d.analyst_id = a.id
        WHERE d.id IS NULL
        ORDER BY a.name
    """)

    # Q5: Drug + analyst name + analyst's therapeutic area (3-table JOIN)
    run(conn, "Q5: Drug Coverage with Analyst and Their Area (3-Table JOIN)", """
        SELECT d.drug_name, d.ticker,
               a.name AS analyst,
               COALESCE(t.name, 'Cross-coverage') AS analyst_area
        FROM drug_coverage d
        LEFT JOIN analysts a ON d.analyst_id = a.id
        LEFT JOIN therapeutic_areas t ON a.therapeutic_area_id = t.id
        ORDER BY d.drug_name
    """)

    # BONUS: Self-join — analyst hierarchy (who reports to Henrik)
    run(conn, "BONUS Self-Join: Analyst Reporting Lines", """
        SELECT a.name AS analyst, a.role,
               m.name AS reports_to
        FROM analysts a
        LEFT JOIN analysts m ON a.id != m.id AND m.role LIKE '%CIO%'
        WHERE a.role NOT LIKE '%CIO%'
        ORDER BY a.name
    """)
