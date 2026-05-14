"""
caduceus / data-foundation / extractors / edgar_executives_extractor.py
======================================================================

Extract Item 10 (Directors, Executive Officers and Corporate Governance) and
the "Information About Our Executive Officers" table from a SEC Form 10-K.

Why this exists
---------------
Item 10 is almost always incorporated by reference to the proxy statement, but
the **executive officers of the registrant** are listed directly in the 10-K
body — typically in Part I between Item 4 and Item 5 — under one of three
canonical headings:
    "Information About Our Executive Officers"
    "Executive Officers of the Registrant"
    "Executive Officers of the Company"

This extractor pulls that table, regex-parses (Name, Age, Current Title, Since
Date) tuples for each executive, and emits structured rows. It is the second
text-extraction stage in Caduceus's data foundation (the first being product
revenue from 10-K footnotes).

Design notes (Module 2 Regex deliverable)
-----------------------------------------
* **Pure regex on text** — no HTML table parsing. The (Name, Age, Position) row
  structure is a SEC convention; every filer uses it even when their HTML
  markup differs. Regex therefore generalizes better than DOM scraping.
* **Section locator anchors on heading + body opener** — anchoring on the
  heading alone matches the table-of-contents entry, not the actual section.
  The body always opens with "The executive officers..." or "The following...";
  using a lookahead on that prose distinguishes the body from the TOC.
* **NAME pattern handles particles** — Dutch/French/Italian particles ("de",
  "van", "von", "der", "della", "du", "le", "la") form part of the surname.
  Pattern uses an alternation: <First> <Middle?> [<particle> <Last> | <Last>].
* **Credentials are part of the name** — comma-separated suffixes like
  "DVM, Ph.D." or "MD, FRCP, FMedSci, Ph.D." are captured as part of the name
  field and split out post-match.
* **Page-break headers are stripped** — multi-page tables repeat
  "Pfizer Inc. / 2025 Form 10-K / 28 / Name / Age / Position" between rows.
  These break the entry pattern; we elide them before matching.
* **Encoding fix** — Workiva-generated 10-Ks declared as windows-1252 contain
  smart apostrophes that surface as U+FFFD when read as UTF-8. We
  replace U+FFFD with a single curly apostrophe.

Patterns are deliberately commented and named so the regex craft is legible.

Usage
-----
    # From a local file (override path)
    python edgar_executives_extractor.py --file pfe-20251231.htm

    # From EDGAR by ticker (resolves CIK → most-recent 10-K → primary doc)
    python edgar_executives_extractor.py --ticker PFE

    # From EDGAR by accession number
    python edgar_executives_extractor.py --cik 78003 --accession 0000078003-26-000026

    # As a library
    from edgar_executives_extractor import extract_executives, fetch_10k_html
    html = fetch_10k_html(ticker="PFE")
    rows = extract_executives(html, ticker="PFE")

Output schema
-------------
Each row dict contains:
    ticker            str   # passed in by caller
    name              str   # "Albert Bourla"
    credentials       str   # "DVM, Ph.D." or "" if none
    age               int
    current_title     str   # "Chairman of the Board and Chief Executive Officer"
    in_role_since     str   # "January 2019" or "2024" if no month given
    bio_text          str   # full position blob, whitespace-normalized
    source            str   # "sec_edgar/10-k/item10"
    source_url        str   # filing URL (if fetched from EDGAR)
    pulled_at         str   # ISO timestamp

Edge cases this extractor handles correctly
-------------------------------------------
* Item 10 fully incorporated by reference (returns empty list, sets reason)
* Credentialed names: "Albert Bourla, DVM, Ph.D."
* Multiple credentials: "Chris Boshoff, MD, FRCP, FMedSci, Ph.D."
* Particle names: "Alexandre de Germay"
* Multi-page tables with repeated header rows
* Bios that begin with semicolon-delimited role chains rather than "since"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests


# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────

HEADERS = {"User-Agent": "Caduceus Research caduceus@research.com"}
SOURCE_LABEL = "sec_edgar/10-k/item10"


# ──────────────────────────────────────────────────────────────────────────────
# REGEX PATTERNS — the heart of the extractor
# Each pattern is named, commented, and corresponds to one parsing stage.
# ──────────────────────────────────────────────────────────────────────────────

# --- Pattern 1: Section heading -----------------------------------------------
# Three canonical phrasings across SEC filers. Case-insensitive because filers
# render the heading in either Title Case or ALL CAPS.
SECTION_HEADING = re.compile(
    r"INFORMATION\s+ABOUT\s+(?:OUR\s+)?EXECUTIVE\s+OFFICERS"
    r"|EXECUTIVE\s+OFFICERS\s+OF\s+THE\s+(?:REGISTRANT|COMPANY|ISSUER)"
    r"|(?:^|\n)\s*Executive\s+Officers\s*(?:\n|$)",
    re.IGNORECASE | re.MULTILINE,
)

# --- Pattern 2: Section start (heading + body opener) -------------------------
# Anchoring on the heading alone matches the table-of-contents entry. The
# *actual* section body always opens with one of these prose phrases:
#     "The executive officers of the Company..."
#     "The following table sets forth..."
#     "The names, ages..."
# A lookahead on these distinguishes the body from the TOC entry.
SECTION_START = re.compile(
    r"(?:INFORMATION\s+ABOUT\s+(?:OUR\s+)?EXECUTIVE\s+OFFICERS"
    r"|EXECUTIVE\s+OFFICERS\s+OF\s+THE\s+(?:REGISTRANT|COMPANY|ISSUER)"
    r"|(?<=\n)\s*Executive\s+Officers\s*(?=\n))"
    # After the heading, accept either:
    #   (a) newline(s) directly (LLY/PFE/ABBV style), or
    #   (b) trailing context like " (ages as of...)" or " of the Company" then newline (MRK)
    r"(?:\s*\([^)\n]{0,100}\))?"   # optional parenthetical
    r"[ \t]*\.?[ \t]*\n+",          # optional period, then newline
    re.IGNORECASE,
)
# TOC signature detector: a candidate heading is in a TOC if, in the
# ~600 chars following it, we see multiple "Part II"/"Part III"/"Item N."
# entries each followed by a standalone page number. The actual body section
# does NOT have this pattern — it goes straight into the officer roster.
_TOC_NEXT_SECTIONS = re.compile(
    r"\b(?:Part\s+I{1,3}\b|Item\s+\d{1,2}[A-C]?\.?)\s",
    re.IGNORECASE,
)

# --- Pattern 3: Section terminator --------------------------------------------
# The next major heading. Position varies: when this section sits in Part I,
# it ends at "ITEM 1A." (Risk Factors) or "PART II" or "ITEM 5."
SECTION_END = re.compile(
    # Line-anchored to avoid matching "PART II" inside flowing bio text.
    # Real section terminators sit on their own line with whitespace context.
    r"(?m)^\s*(?:PART\s+II\b|ITEM\s+1A\.|ITEM\s+5\.)\s*(?:\n|$)"
    r"|\n\s*Directors\s*\n\s*Name\s*\n\s*Age",  # GILD: directors table follows
    re.IGNORECASE,
)

# --- Pattern 4: Page-break header repetition ---------------------------------
# Multi-page tables repeat "<Filer Name>\n<Year> Form 10-K\n<Page#>\nName\nAge
# \nPosition\n" between rows. These break the entry-matching pattern.
PAGE_HEADER = re.compile(
    r"\n\s*[A-Z][A-Za-z .,&\-]+?\s*\n\s*\d{4}\s+Form\s+10-K\s*\n\s*\d+\s*\n"
    r"\s*Name\s*\n\s*Age\s*\n\s*Position\s*\n",
)
TABLE_HEADER_ROW = re.compile(r"\n\s*Name\s*\n\s*Age\s*\n\s*Position\s*\n")
PAGE_NUMBER_LINE = re.compile(
    r"\n\s*[A-Z][A-Za-z .,&\-]+?\s*\n\s*\d{4}\s+Form\s+10-K\s*\n\s*\d+\s*\n"
)

# --- Pattern 5: Name (with optional credentials) ------------------------------
# Components, in order:
#   (a) First name: capitalized + letters/curly-apostrophe/hyphen
#   (b) Optional middle initials or middle names: "M." or "Marie"
#   (c) Last name, in two flavors:
#       - particle + capitalized last  ("de Germay", "von Trapp")
#       - plain capitalized last        ("Bourla")
#   (d) Optional credentials: ", DVM, Ph.D." or ", MD, FRCP"
# Credentials are restricted to a known list to avoid greedy over-matching.
_NAME = (
    r"[A-Z][A-Za-z\u2019'\-]+"                                       # First name
    r"(?:\s+[A-Z]\.?)*"                                              # Middle initials/names
    r"(?:"
        r"\s+(?:de|van|von|der|della|du|le|la)\s+[A-Z][A-Za-z\u2019'\-]+"  # particle + Last
    r"|"
        r"\s+[A-Z][A-Za-z\u2019'\-]+(?:\s+[A-Z][A-Za-z\u2019'\-]+)?"     # Last [+ 2nd Last]
    r")"
    r"(?:,\s*(?:"                                                     # 0+ credentials
        r"DVM|MD|MA|BM\s*ChB|FRCP|FMedSci|Ph\.?D\.?|D\.?Phil"
        r"|J\.?D\.?|M\.?B\.?A\.?|D\.?Sc\.?|Sc\.?D\.?"
        r"|FRSC|FACS|FRSE|FAANS|FACP|FAAS|FRS"
    r")\.?)*"
)

# --- Pattern 6: One executive entry -------------------------------------------
# An entry is "<Name>\n<Age>\n<Bio>" where <Age> is 2 digits and <Bio> runs
# until the next entry begins. The lookahead is critical: it terminates the
# lazy bio match at either (next entry's name+age) or end-of-section.
ENTRY = re.compile(
    r"^(?P<name>" + _NAME + r")\s*\n"
    r"\s*(?P<age>[2-9]\d)\s*\n"
    r"\s*(?P<bio>.+?)"
    r"(?="
    r"\n\s*" + _NAME + r"\s*\n\s*[2-9]\d\s*\n"   # next entry boundary
    r"|\Z"                                        # or end-of-string
    r")",
    re.MULTILINE | re.DOTALL,
)

# ENTRY variant: JNJ-style — "Name, Age\n<title>\n<bio>"
ENTRY_INLINE = re.compile(
    r"^(?P<name>" + _NAME + r")\s*,\s*(?P<age>[2-9]\d)\s*\n"
    r"\s*(?P<bio>.+?)"
    r"(?="
    r"\n\s*" + _NAME + r"\s*,\s*[2-9]\d\s*\n"   # next entry boundary
    r"|\Z"                                             # or end-of-string
    r")",
    re.MULTILINE | re.DOTALL,
)

# ENTRY variant: BMY-style — "Name\n<title lines>\n\n<Age>\n<employment history>"
# The title block is 1-4 short lines. The age sits on a line by itself after
# a blank-ish separator. The bio is a multi-line employment history.
ENTRY_DASHED = re.compile(
    r"^(?P<name>" + _NAME + r")\s*\n"
    r"(?P<title>(?:[A-Z][^\n]{0,150}\n){1,4})"
    r"\s*\n"                                          # blank separator
    r"\s*(?P<age>[2-9]\d)\s*\n"
    r"(?P<bio>.+?)"
    r"(?="
    r"\n\s*" + _NAME + r"\s*\n(?:[A-Z][^\n]{0,150}\n){1,4}\s*\n\s*[2-9]\d\s*\n"
    r"|\Z"
    r")",
    re.MULTILINE | re.DOTALL,
)

# ENTRY variant: AMGN-style — "Mr./Dr./Ms. <Name>, age N, <bio>"
# Single-line entry, honorific prefix, "age" keyword between name and number.
ENTRY_AGE_INLINE = re.compile(
    r"^(?:Mr|Mrs|Ms|Dr)\.\s+(?P<name>" + _NAME + r"),\s+age\s+(?P<age>[2-9]\d),\s*"
    r"(?P<bio>.+?)"
    r"(?="
    r"\n\s*(?:Mr|Mrs|Ms|Dr)\.\s+" + _NAME + r",\s+age\s+[2-9]\d,"  # next entry
    r"|\Z"
    r")",
    re.MULTILINE | re.DOTALL,
)


# --- Pattern 7: Current title and "since" date --------------------------------
# Bios universally begin with "<Title> since <Month?> <Year>." which means
# "currently holds <Title> as of <Date>". Older role history follows.
# We match lazily up to "since <Date>." Month is optional — some filers write
# "since 2024" without a month.
CURRENT_TITLE = re.compile(
    r"^(?P<title>.+?)"
    r"\s+since\s+"
    r"(?:(?P<month>January|February|March|April|May|June|July|"
    r"August|September|October|November|December)\s+)?"
    r"(?P<year>\d{4})"
    r"[\.\;]",
)

# --- Pattern 8: Name → (clean_name, credentials) split ------------------------
# After matching, split "Albert Bourla, DVM, Ph.D." into name + credentials.
NAME_CREDS_SPLIT = re.compile(
    r"^(?P<clean>[^,]+?)"
    r"(?:,\s*(?P<creds>(?:DVM|MD|MA|BM\s*ChB|FRCP|FMedSci|Ph\.?D\.?|D\.?Phil"
    r"|J\.?D\.?|M\.?B\.?A\.?|D\.?Sc\.?|Sc\.?D\.?|FRSC|FACS|FRSE|FAANS|FACP)"
    r"(?:,\s*[A-Za-z\.\s]+)*))?$",
)


# ──────────────────────────────────────────────────────────────────────────────
# DATA SHAPES
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ExecutiveRow:
    ticker: str
    name: str
    credentials: str
    age: int
    current_title: str
    in_role_since: str
    bio_text: str
    source: str
    source_url: str
    pulled_at: str


# ──────────────────────────────────────────────────────────────────────────────
# HTML → TEXT
# ──────────────────────────────────────────────────────────────────────────────

def html_to_text(html: str) -> str:
    """Strip HTML to plain text while preserving table-row line breaks.

    Closing tags for block elements become newlines; inline tags are dropped.
    HTML entities and Workiva windows-1252 artifacts are normalized.
    """
    s = html
    # Block-level closes → newline (so table rows survive as separate lines)
    s = re.sub(r"</(td|tr|p|div|li|h[1-6])>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", "", s)

    # Common entities
    s = s.replace("&nbsp;", " ").replace("&amp;", "&")
    s = re.sub(r"&#8217;|&rsquo;|&#x2019;", "’", s)
    s = re.sub(r"&#8212;|&mdash;|&#x2014;", "—", s)
    s = re.sub(r"&#8211;|&ndash;|&#x2013;", "–", s)
    s = re.sub(r"&#x[0-9a-fA-F]+;|&#\d+;", " ", s)

    # Workiva 10-Ks declared as windows-1252 use 0x92 (smart apostrophe);
    # when the file is read as UTF-8 these arrive as U+FFFD. Replace with the
    # contextually-most-likely glyph (curly apostrophe).
    s = s.replace("\uFFFD", "’")

    # Whitespace normalization (preserve paragraph breaks)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n[ \t]+", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


# ──────────────────────────────────────────────────────────────────────────────
# SECTION SLICING
# ──────────────────────────────────────────────────────────────────────────────

def _is_toc_context(text: str, offset: int) -> bool:
    """A candidate heading is in TOC if the following 600 chars contain
    several Part/Item markers (TOC entries) rather than officer entries.
    Threshold of 3 separate markers reliably distinguishes a TOC from
    actual body content where these terms appear sparsely or not at all.
    """
    window = text[offset:offset + 600]
    markers = list(_TOC_NEXT_SECTIONS.finditer(window))
    return len(markers) >= 3


def find_executives_section(text: str) -> Optional[str]:
    """Return the executive officers section as a single string, or None.

    Finds all candidate headings, classifies each as TOC vs body by
    structural context (TOC entries cluster Part/Item references densely
    after the heading; body sections don't), and selects the LAST non-TOC
    candidate. This handles filers whose TOC contains the same heading
    text as the body section (MRK/JNJ/ABBV/BMY/AMGN).
    """
    candidates = list(SECTION_START.finditer(text))
    if not candidates:
        return None

    body_candidates = [m for m in candidates if not _is_toc_context(text, m.start())]

    if not body_candidates:
        # All candidates are TOC-like; fall back to last candidate or only one
        chosen = candidates[-1] if len(candidates) >= 2 else candidates[0]
    else:
        # Score each non-TOC candidate by whether it has officer-like content
        # in the next 3000 chars. The candidate that scores highest wins.
        # This directly measures "is this the real body" without relying on
        # Part I/III structural assumptions that themselves have TOC ambiguity.
        def _score_candidate(text: str, offset: int) -> int:
            """Count officer-like patterns in next 3000 chars after offset.
            Patterns counted:
              - Honorific + Name + age N (AMGN-style)
              - Name\nAge\nBio (PFE-style, name + 2-digit-only line)
              - Name, Age inline (JNJ-style)
            """
            window = text[offset:offset + 3000]
            score = 0
            # AMGN-style: "Mr. <Name>, age N,"
            score += len(re.findall(r"(?:Mr|Mrs|Ms|Dr)\.\s+[A-Z][A-Za-z. ]+,\s+age\s+\d{2}", window))
            # JNJ-style: "<Name>, NN" (single line)
            score += len(re.findall(r"^[A-Z][A-Za-z. \-]+,\s+\d{2}\s*$", window, re.MULTILINE))
            # PFE-style: "<Name>\n<Age>" (two-line table entry)
            score += len(re.findall(r"^[A-Z][A-Za-z. \-]+\n\s*\d{2}\s*\n", window, re.MULTILINE))
            return score

        scored = [(m, _score_candidate(text, m.end())) for m in body_candidates]
        # Pick the highest-scoring candidate. Ties broken by later position.
        scored.sort(key=lambda x: (x[1], x[0].start()), reverse=False)
        # scored is ascending by score then position; we want max score, then max position among ties
        best_score = max(s for _, s in scored)
        if best_score > 0:
            # Highest score wins; among ties pick the LAST in document order
            chosen = [m for m, s in scored if s == best_score][-1]
        else:
            # No candidate has officer content; fall back to last non-TOC
            chosen = body_candidates[-1]
    section_start = chosen.end()  # everything AFTER the heading
    m_end = SECTION_END.search(text, section_start)
    section_end = m_end.start() if m_end else section_start + 30_000
    section = text[section_start:section_end]
    # Strip page-break header repetitions (3 patterns from most to least specific)
    section = PAGE_HEADER.sub("\n", section)
    section = PAGE_NUMBER_LINE.sub("\n", section)
    section = TABLE_HEADER_ROW.sub("\n", section)
    return section


def find_item10_section(text: str) -> Optional[str]:
    """Return the Item 10 (Part III) section as a single string, or None.

    Item 10 is usually a short paragraph that incorporates by reference. We
    return it for completeness; the *substance* lives in the executive officers
    section in Part I.
    """
    m = re.search(r"\n\s*ITEM\s+10\.\s*\n?\s*DIRECTORS,\s+EXECUTIVE\s+OFFICERS",
                  text, re.IGNORECASE)
    if not m:
        return None
    start = m.start()
    m_end = re.search(r"\n\s*ITEM\s+11\.\s", text[start:], re.IGNORECASE)
    end = start + (m_end.start() if m_end else 5000)
    return text[start:end].strip()


# ──────────────────────────────────────────────────────────────────────────────
# ENTRY EXTRACTION
# ──────────────────────────────────────────────────────────────────────────────

def parse_entry(match: re.Match, ticker: str, source_url: str,
                pulled_at: str) -> ExecutiveRow:
    """Convert a single matched entry into an ExecutiveRow."""
    raw_name = match.group("name").strip()
    age = int(match.group("age"))
    bio = re.sub(r"\s+", " ", match.group("bio")).strip()

    # Split name from credentials
    nc = NAME_CREDS_SPLIT.match(raw_name)
    if nc:
        clean_name = nc.group("clean").strip()
        credentials = (nc.group("creds") or "").strip()
    else:
        clean_name, credentials = raw_name, ""

    # Pull current title + since-date from bio
    tm = CURRENT_TITLE.search(bio)
    if tm:
        title = tm.group("title").strip().rstrip(",")
        month = tm.group("month") or ""
        year = tm.group("year")
        in_role_since = f"{month} {year}".strip()
    else:
        # Fallback: take everything before the first period as the title
        first_sentence = bio.split(".", 1)[0]
        title = first_sentence.strip()
        in_role_since = ""

    return ExecutiveRow(
        ticker=ticker,
        name=clean_name,
        credentials=credentials,
        age=age,
        current_title=title,
        in_role_since=in_role_since,
        bio_text=bio,
        source=SOURCE_LABEL,
        source_url=source_url,
        pulled_at=pulled_at,
    )


def extract_executives(html: str, ticker: str = "",
                       source_url: str = "") -> list[ExecutiveRow]:
    """Main entry point: HTML in → list of ExecutiveRow out.

    Returns an empty list if the section is not present (e.g. Item 10 is
    fully incorporated by reference and there is no Part I executive table).
    """
    pulled_at = datetime.now(timezone.utc).isoformat()
    text = html_to_text(html)
    section = find_executives_section(text)
    if section is None:
        return []
    # Try all 4 entry formats; use whichever matches the most rows.
    # Each Phase 1 filer uses a different layout convention.
    _pattern_results = [
        list(ENTRY.finditer(section)),
        list(ENTRY_INLINE.finditer(section)),
        list(ENTRY_DASHED.finditer(section)),
        list(ENTRY_AGE_INLINE.finditer(section)),
    ]
    matches = max(_pattern_results, key=len)
    return [
        parse_entry(m, ticker=ticker, source_url=source_url, pulled_at=pulled_at)
        for m in matches
    ]


# ──────────────────────────────────────────────────────────────────────────────
# EDGAR FETCH (for non-local invocations)
# ──────────────────────────────────────────────────────────────────────────────

def _ticker_to_cik(ticker: str) -> str:
    """Resolve a ticker to a 10-digit zero-padded CIK via SEC's ticker file."""
    r = requests.get("https://www.sec.gov/files/company_tickers.json",
                     headers=HEADERS, timeout=15)
    r.raise_for_status()
    for entry in r.json().values():
        if entry["ticker"].upper() == ticker.upper():
            return str(entry["cik_str"]).zfill(10)
    raise ValueError(f"Ticker not found in SEC ticker file: {ticker}")


def _latest_10k_accession(cik: str) -> tuple[str, str]:
    """Return (accession_number, primary_document_filename) for the most
    recent 10-K filing for a given CIK."""
    cik = cik.zfill(10)
    r = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json",
                     headers=HEADERS, timeout=15)
    r.raise_for_status()
    recent = r.json()["filings"]["recent"]
    for i, form in enumerate(recent["form"]):
        if form == "10-K":
            return recent["accessionNumber"][i], recent["primaryDocument"][i]
    raise ValueError(f"No 10-K found in recent filings for CIK {cik}")


def fetch_10k_html(ticker: Optional[str] = None,
                   cik: Optional[str] = None,
                   accession: Optional[str] = None) -> tuple[str, str]:
    """Fetch a 10-K's primary HTML document from EDGAR.

    Provide one of:
      - ticker (resolves to CIK, fetches latest 10-K)
      - cik (fetches latest 10-K for that CIK)
      - cik + accession (fetches that specific 10-K)

    Returns (html_text, source_url).
    """
    if ticker and not cik:
        cik = _ticker_to_cik(ticker)
    if not cik:
        raise ValueError("Must provide ticker or cik")
    cik = cik.zfill(10)

    if not accession:
        accession, primary_doc = _latest_10k_accession(cik)
    else:
        # Caller-supplied accession; we still need the primary doc filename
        _, primary_doc = _latest_10k_accession(cik)
        # Override only if accession matches; otherwise look up the filing
        # (full implementation would query the accession's index.json — we
        # accept the latest primary doc as a reasonable default for now)

    # EDGAR archive URL convention
    accession_nodash = accession.replace("-", "")
    cik_int = int(cik)
    url = (f"https://www.sec.gov/Archives/edgar/data/{cik_int}/"
           f"{accession_nodash}/{primary_doc}")
    time.sleep(0.12)  # SEC rate limit courtesy
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    # SEC serves 10-Ks as windows-1252 in the headers; honor that to preserve
    # smart apostrophes and avoid the U+FFFD substitution.
    r.encoding = r.apparent_encoding or "windows-1252"
    return r.text, url


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def _cli():
    p = argparse.ArgumentParser(
        description="Extract Item 10 / executive officers from a SEC Form 10-K.")
    p.add_argument("--file", help="Local path to a 10-K HTML file (overrides EDGAR fetch)")
    p.add_argument("--ticker", help="Ticker symbol (resolves to CIK; tags output rows)")
    p.add_argument("--cik", help="CIK (resolves latest 10-K when no --file)")
    p.add_argument("--accession", help="Accession number (with or without dashes)")
    p.add_argument("--out", default=None,
                   help="Output path for JSON (default: stdout)")
    args = p.parse_args()

    if not (args.file or args.ticker or args.cik):
        p.error("Provide --file, --ticker, or --cik")

    if args.file:
        html = Path(args.file).read_text(encoding="utf-8", errors="replace")
        ticker = args.ticker or ""
        source_url = f"file://{Path(args.file).resolve()}"
    else:
        html, source_url = fetch_10k_html(ticker=args.ticker, cik=args.cik,
                                          accession=args.accession)
        ticker = args.ticker or ""

    rows = extract_executives(html, ticker=ticker, source_url=source_url)
    payload = [asdict(r) for r in rows]

    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {len(rows)} rows → {args.out}", file=sys.stderr)
    else:
        print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    _cli()
