"""Module 2 - Space Complexity (real Caduceus edgar_observations data)."""
from __future__ import annotations
import sys, time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CADUCEUS = REPO_ROOT / "caduceus"
sys.path.insert(0, str(CADUCEUS / "data-foundation"))

from dotenv import load_dotenv
load_dotenv(CADUCEUS / ".env")

from sqlalchemy import text
from security_master.database import SessionLocal


# Function A: O(n) - slicing creates new string of same length
def reverse_string(s):
    return s[::-1]


# Function B: O(k) distinct chars, bounded by O(n) worst case
def count_letters(text):
    counts = {}
    for char in text:
        counts[char] = counts.get(char, 0) + 1
    return counts


# Function C: O(n^2) - n-by-n matrix
def matrix_identity(n):
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]


# Function D: O(1) - only scalar accumulators
def running_sum(numbers):
    total = 0
    for num in numbers:
        total += num
        print(total)


def find_duplicates_set_approach(session):
    """O(n) time, O(n) space - in-memory set."""
    seen = set()
    duplicates = []
    rows = session.execute(text(
        "SELECT caduceus_uuid, concept_id, period_end, accession_number "
        "FROM edgar_observations "
        "WHERE accession_number NOT LIKE 'DERIVED%'"
    ))
    for row in rows:
        identity = tuple(row)
        if identity in seen:
            duplicates.append(identity)
        else:
            seen.add(identity)
    return duplicates


def find_duplicates_sort_approach(session):
    """O(n log n) time, O(1) Python-side space - DB sorts on disk."""
    duplicates = []
    previous = None
    rows = session.execute(text(
        "SELECT caduceus_uuid, concept_id, period_end, accession_number "
        "FROM edgar_observations "
        "WHERE accession_number NOT LIKE 'DERIVED%' "
        "ORDER BY caduceus_uuid, concept_id, period_end, accession_number"
    ))
    for row in rows:
        current = tuple(row)
        if previous is not None and current == previous:
            duplicates.append(current)
        previous = current
    return duplicates


def main():
    print("Module 2 - Space Complexity: duplicate detection on real edgar_observations")
    session = SessionLocal()

    n_rows = session.execute(text(
        "SELECT COUNT(*) FROM edgar_observations WHERE accession_number NOT LIKE 'DERIVED%'"
    )).scalar()
    print(f"Rows to scan: {n_rows:,}")

    print("\nApproach 1: in-memory set (O(n) time, O(n) space)")
    t0 = time.perf_counter()
    dupes_set = find_duplicates_set_approach(session)
    print(f"  Elapsed: {time.perf_counter() - t0:.3f}s, duplicates found: {len(dupes_set)}")

    print("\nApproach 2: sort and scan (O(n log n) time, O(1) space)")
    t0 = time.perf_counter()
    dupes_sort = find_duplicates_sort_approach(session)
    print(f"  Elapsed: {time.perf_counter() - t0:.3f}s, duplicates found: {len(dupes_sort)}")

    if set(dupes_set) == set(dupes_sort):
        print(f"\nCross-check: both approaches agree on {len(dupes_set)} duplicates")
    else:
        print(f"\nDISAGREEMENT: set={len(dupes_set)}, sort={len(dupes_sort)}")

    if dupes_set:
        print("\nSample duplicates (first 5):")
        for d in dupes_set[:5]:
            print(f"  {d}")
    else:
        print("\nNo duplicates found - edgar_observations identity tuple is clean.")

    session.close()


if __name__ == "__main__":
    main()