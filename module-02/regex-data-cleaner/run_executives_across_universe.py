"""
caduceus / data-foundation / extractors / run_executives_across_universe.py
==========================================================================

Driver: run the Item 10 / executive officers extractor across the full
Phase 1 universe of 8 large-cap pharma names. Aggregates results to CSV
and JSON; logs per-filer success and any extraction failures so we know
which 10-K phrasings need hardening.

Output files (written to data-foundation/raw/):
    executives_all_phase1.csv    — one row per executive, all 8 filers
    executives_all_phase1.json   — same data as JSON (cleaner for bios)
    executives_run_log.txt       — per-filer success/failure summary

Usage:
    cd <caduceus repo root>
    python data-foundation/extractors/run_executives_across_universe.py

The script is rate-limited to ~2 req/sec against SEC EDGAR (well under the
10 req/sec ceiling) and uses the same User-Agent the rest of Caduceus uses.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

# Allow importing the extractor module when this driver is run directly
sys.path.insert(0, str(Path(__file__).parent))

from edgar_executives_extractor import (
    fetch_10k_html,
    extract_executives,
    find_executives_section,
    html_to_text,
)


# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────

# Phase 1 universe: 8 large-cap pharma names (matches caduceus_remaining_pullers.py)
PHASE1 = {
    "PFE":  {"cik": "0000078003", "name": "Pfizer Inc"},
    "MRK":  {"cik": "0000310158", "name": "Merck & Co Inc"},
    "JNJ":  {"cik": "0000200406", "name": "Johnson & Johnson"},
    "ABBV": {"cik": "0001551152", "name": "AbbVie Inc"},
    "BMY":  {"cik": "0000014272", "name": "Bristol-Myers Squibb Co"},
    "LLY":  {"cik": "0000059478", "name": "Eli Lilly and Co"},
    "AMGN": {"cik": "0000318154", "name": "Amgen Inc"},
    "GILD": {"cik": "0000882095", "name": "Gilead Sciences Inc"},
}

OUT_DIR = Path("data-foundation/raw")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH  = OUT_DIR / "executives_all_phase1.csv"
JSON_PATH = OUT_DIR / "executives_all_phase1.json"
LOG_PATH  = OUT_DIR / "executives_run_log.txt"

REQUEST_DELAY_SECONDS = 0.5  # ~2 req/sec — well under SEC's 10 req/sec ceiling


# ──────────────────────────────────────────────────────────────────────────────
# DRIVER
# ──────────────────────────────────────────────────────────────────────────────

def diagnose_extraction_failure(html: str) -> str:
    """When extract_executives returns 0 rows, try to figure out why so the
    log entry is actually useful for hardening. Returns a short diagnosis
    string."""
    text = html_to_text(html)

    # Did we even find the section heading?
    import re
    if re.search(r"INFORMATION\s+ABOUT\s+OUR\s+EXECUTIVE\s+OFFICERS"
                 r"|EXECUTIVE\s+OFFICERS\s+OF\s+THE\s+(?:REGISTRANT|COMPANY)",
                 text, re.IGNORECASE):
        section = find_executives_section(text)
        if section is None:
            return "heading present but body opener didn't match (TOC-only or unusual prose)"
        if len(section) < 500:
            return f"section found but only {len(section)} chars — likely incorporated by reference"
        # Section exists and has content but no entries matched — phrasing variant
        return f"section found ({len(section):,} chars) but ENTRY regex matched 0 rows — likely phrasing variant"
    else:
        return "no executive officers section heading found anywhere"


def run() -> None:
    started = datetime.now(timezone.utc)
    print(f"╔══════════════════════════════════════════════════════════════════════╗")
    print(f"║  Caduceus — Item 10 / Executive Officers across Phase 1 Universe     ║")
    print(f"║  Started: {started.isoformat()}                          ║")
    print(f"╚══════════════════════════════════════════════════════════════════════╝\n")

    all_rows = []
    log_lines = [f"Run started: {started.isoformat()}", ""]

    for ticker, meta in PHASE1.items():
        print(f"── {ticker:5s} {meta['name']:30s} ", end="", flush=True)
        try:
            html, source_url = fetch_10k_html(ticker=ticker)
            rows = extract_executives(html, ticker=ticker, source_url=source_url)
            if rows:
                all_rows.extend(rows)
                msg = f"{len(rows):>3d} executives  ({source_url.split('/')[-1]})"
                print(f"✓  {msg}")
                log_lines.append(f"{ticker}: SUCCESS — {len(rows)} executives extracted")
                log_lines.append(f"        {source_url}")
            else:
                diagnosis = diagnose_extraction_failure(html)
                print(f"⚠   0 executives — {diagnosis}")
                log_lines.append(f"{ticker}: NO ROWS — {diagnosis}")
                log_lines.append(f"        {source_url}")
        except Exception as e:
            print(f"✗   FETCH/PARSE ERROR: {type(e).__name__}: {e}")
            log_lines.append(f"{ticker}: ERROR — {type(e).__name__}: {e}")

        log_lines.append("")
        time.sleep(REQUEST_DELAY_SECONDS)

    # ── Summary ────────────────────────────────────────────────────────────
    print(f"\n{'═'*72}")
    successes = sum(1 for line in log_lines if "SUCCESS" in line)
    no_rows   = sum(1 for line in log_lines if "NO ROWS" in line)
    errors    = sum(1 for line in log_lines if line.startswith(tuple(PHASE1)) and "ERROR" in line)
    print(f"  Filers processed:  {len(PHASE1)}")
    print(f"  Successes:         {successes}/{len(PHASE1)}")
    print(f"  No rows extracted: {no_rows}")
    print(f"  Errors:            {errors}")
    print(f"  Total executives:  {len(all_rows)}")
    print(f"{'═'*72}\n")

    if not all_rows:
        print("No data extracted — aborting writes.")
        LOG_PATH.write_text("\n".join(log_lines), encoding="utf-8")
        return

    # ── Write CSV ──────────────────────────────────────────────────────────
    rows_dict = [asdict(r) for r in all_rows]
    with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        # utf-8-sig because Excel on Windows mishandles plain UTF-8 (per spec)
        writer = csv.DictWriter(f, fieldnames=list(rows_dict[0].keys()))
        writer.writeheader()
        writer.writerows(rows_dict)
    print(f"Wrote CSV:  {CSV_PATH}  ({len(rows_dict)} rows)")

    # ── Write JSON ─────────────────────────────────────────────────────────
    JSON_PATH.write_text(
        json.dumps(rows_dict, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote JSON: {JSON_PATH}  ({len(rows_dict)} rows)")

    # ── Write log ──────────────────────────────────────────────────────────
    finished = datetime.now(timezone.utc)
    log_lines.append("")
    log_lines.append(f"Run finished: {finished.isoformat()}")
    log_lines.append(f"Duration: {(finished - started).total_seconds():.1f}s")
    log_lines.append(f"Total rows written: {len(rows_dict)}")
    LOG_PATH.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote log:  {LOG_PATH}")

    # ── Per-filer breakdown ────────────────────────────────────────────────
    print(f"\nPer-filer breakdown:")
    counts = {}
    for r in all_rows:
        counts[r.ticker] = counts.get(r.ticker, 0) + 1
    for ticker in PHASE1:
        n = counts.get(ticker, 0)
        marker = "✓" if n > 0 else "⚠"
        print(f"  {marker}  {ticker:5s} {n:>3d} executives")


if __name__ == "__main__":
    run()
