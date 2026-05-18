"""
music_db.py

Module 3 — Build Your Own Database
Caduceus Healthcare Equity Platform | Rhenman & Partners

Rubric mapping (Caduceus domain substitution):
  artists → pharmaceutical companies  (PFE, MRK, LLY, ABBV, BMY)
  albums  → drug portfolio releases   (drug franchises grouped by approval era)

Uses raw sqlite3 (standard library) — no SQLAlchemy.
"""
import sqlite3

# ── Connect ───────────────────────────────────────────────────────────────────
conn = sqlite3.connect("music.db")
cursor = conn.cursor()

# Enable foreign key enforcement (SQLite off by default)
cursor.execute("PRAGMA foreign_keys = ON")

# ── Create tables ─────────────────────────────────────────────────────────────
cursor.execute("""
    CREATE TABLE IF NOT EXISTS artists (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        name  TEXT NOT NULL,
        genre TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS albums (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        title     TEXT NOT NULL,
        year      INTEGER,
        artist_id INTEGER,
        FOREIGN KEY (artist_id) REFERENCES artists(id)
    )
""")

# ── Insert artists (pharmaceutical companies) ─────────────────────────────────
artists = [
    ("Pfizer Inc",             "Large-Cap Pharma"),
    ("Merck & Co Inc",         "Large-Cap Pharma"),
    ("Eli Lilly and Co",       "Large-Cap Pharma"),
    ("AbbVie Inc",             "Large-Cap Pharma"),
    ("Bristol-Myers Squibb",   "Large-Cap Pharma"),
]
cursor.executemany("INSERT INTO artists (name, genre) VALUES (?, ?)", artists)

# ── Insert albums (drug portfolio releases by era) ────────────────────────────
albums = [
    # Pfizer (artist_id=1)
    ("Pfizer Oncology Portfolio",       2019, 1),
    ("Pfizer Rare Disease Franchise",   2021, 1),
    ("Pfizer Vaccine & Antiviral Era",  2022, 1),
    # Merck (artist_id=2)
    ("Merck Keytruda Expansion",        2018, 2),
    ("Merck Cardiovascular Portfolio",  2023, 2),
    # Eli Lilly (artist_id=3)
    ("Lilly GLP-1 Franchise",           2022, 3),
    ("Lilly Oncology Pipeline",         2024, 3),
    # AbbVie (artist_id=4)
    ("AbbVie Immunology Franchise",     2020, 4),
    ("AbbVie Neuroscience Portfolio",   2023, 4),
    # Bristol-Myers Squibb (artist_id=5)
    ("BMS Immuno-Oncology Duo",         2015, 5),
]
cursor.executemany(
    "INSERT INTO albums (title, year, artist_id) VALUES (?, ?, ?)", albums
)

conn.commit()

# ── Query: all albums with their artist ──────────────────────────────────────
print("\n" + "=" * 65)
print("  Caduceus — Pharma Portfolio Database")
print("=" * 65)
print(f"  {'Album / Portfolio':<40} {'Year':<6} {'Company'}")
print(f"  {'─'*40} {'─'*6} {'─'*25}")

cursor.execute("""
    SELECT albums.title, albums.year, artists.name
    FROM albums
    JOIN artists ON albums.artist_id = artists.id
    ORDER BY artists.name, albums.year
""")

for title, year, artist in cursor.fetchall():
    print(f"  {title:<40} {year:<6} {artist}")

print()

# ── Close ─────────────────────────────────────────────────────────────────────
conn.close()
print("  Database closed.\n")
