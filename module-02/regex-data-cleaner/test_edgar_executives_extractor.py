"""
Tests for edgar_executives_extractor.

Run:
    python -m pytest test_edgar_executives_extractor.py -v

These tests exercise each regex pattern against representative inputs from
real 10-K filings, and run an end-to-end check on the PFE 2025 10-K fixture.

The tests are deliberately written as named scenarios so that the regex
behavior is documented through examples — useful both as a unit-test suite
and as a reference for what the patterns are supposed to handle.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from edgar_executives_extractor import (
    SECTION_START,
    SECTION_END,
    ENTRY,
    CURRENT_TITLE,
    NAME_CREDS_SPLIT,
    html_to_text,
    find_executives_section,
    find_item10_section,
    extract_executives,
)


FIXTURE_HTML = Path(__file__).parent / "pfe-20251231.htm"


# ─── Pattern: name + credentials split ────────────────────────────────────────

class TestNameCredentialsSplit:
    """The NAME_CREDS_SPLIT pattern must cleanly separate the human name from
    its trailing comma-separated credentials."""

    @pytest.mark.parametrize("raw, expected_name, expected_creds", [
        ("Albert Bourla, DVM, Ph.D.",                 "Albert Bourla",        "DVM, Ph.D."),
        ("Andrew Baum, MA, BM ChB",                   "Andrew Baum",          "MA, BM ChB"),
        ("Chris Boshoff, MD, FRCP, FMedSci, Ph.D.",   "Chris Boshoff",        "MD, FRCP, FMedSci, Ph.D."),
        ("David M. Denton",                            "David M. Denton",     ""),
        ("Alexandre de Germay",                        "Alexandre de Germay", ""),
        ("Payal Sahni",                                "Payal Sahni",         ""),
    ])
    def test_split(self, raw, expected_name, expected_creds):
        m = NAME_CREDS_SPLIT.match(raw)
        assert m is not None, f"Failed to match: {raw!r}"
        assert m.group("clean").strip() == expected_name
        assert (m.group("creds") or "").strip() == expected_creds


# ─── Pattern: current title + since-date ──────────────────────────────────────

class TestCurrentTitle:
    """CURRENT_TITLE must extract <Title> and <Since-Date> from the opening
    sentence of an executive bio."""

    def test_with_full_date(self):
        bio = "Chief Financial Officer, Executive Vice President since May 2022. Prior roles..."
        m = CURRENT_TITLE.search(bio)
        assert m is not None
        assert m.group("title") == "Chief Financial Officer, Executive Vice President"
        assert m.group("month") == "May"
        assert m.group("year") == "2022"

    def test_year_only(self):
        bio = "Chief Strategy and Innovation Officer and Executive Vice President since 2024. Prior to..."
        m = CURRENT_TITLE.search(bio)
        assert m is not None
        assert m.group("title") == "Chief Strategy and Innovation Officer and Executive Vice President"
        assert m.group("month") is None
        assert m.group("year") == "2024"

    def test_semicolon_terminator(self):
        # Boshoff's bio uses a semicolon between his current role and his role history
        bio = "Chief Scientific Officer and President, Research & Development, since January 2025; Chief Oncology Officer, Executive Vice President from December 2023..."
        m = CURRENT_TITLE.search(bio)
        assert m is not None
        assert "Chief Scientific Officer" in m.group("title")
        assert m.group("year") == "2025"


# ─── HTML → text pipeline ─────────────────────────────────────────────────────

class TestHtmlToText:
    def test_strips_tags_preserves_breaks(self):
        html = "<table><tr><td>Name</td><td>Age</td></tr><tr><td>Bourla</td><td>64</td></tr></table>"
        text = html_to_text(html)
        # Each cell becomes its own line so regex can anchor on \n boundaries
        assert "Name" in text
        assert "Bourla" in text
        assert "\n" in text

    def test_replaces_workiva_smart_apostrophe(self):
        # When SEC files declared as windows-1252 are read as UTF-8, the
        # 0x92 smart apostrophe arrives as U+FFFD. We replace it with ’.
        html = "<p>Lowe\uFFFDs Companies</p>"
        text = html_to_text(html)
        assert "Lowe’s" in text
        assert "\uFFFD" not in text

    def test_html_entities(self):
        html = "<p>Research&nbsp;&amp;&nbsp;Development</p>"
        text = html_to_text(html)
        assert "Research & Development" in text


# ─── Section locator ──────────────────────────────────────────────────────────

class TestSectionLocator:
    """The section locator must distinguish the body section from the table
    of contents. The TOC contains the heading too, but it's followed by page
    numbers; the body is followed by descriptive prose."""

    def test_skips_toc_anchors_to_body(self):
        # Synthesized: a TOC entry, then the actual body
        text = (
            "Table of Contents\n"
            "INFORMATION ABOUT OUR EXECUTIVE OFFICERS\n"
            "27\n"
            "PART II\n"
            "29\n"
            "...lots of intervening text...\n"
            "INFORMATION ABOUT OUR EXECUTIVE OFFICERS\n"
            "The executive officers of the Company are set forth in this table.\n"
        )
        m = SECTION_START.search(text)
        assert m is not None
        # Should anchor to the SECOND occurrence (the body), not the first (TOC)
        assert text[m.start():m.start()+50].count("INFORMATION") == 1
        # And the next thing after the heading should be "The executive officers"
        assert text[m.end():m.end()+30].startswith("The executive")

    def test_handles_company_variant(self):
        text = (
            "EXECUTIVE OFFICERS OF THE COMPANY\n"
            "The executive officers of the Company are listed below.\n"
        )
        m = SECTION_START.search(text)
        assert m is not None

    def test_handles_registrant_variant(self):
        text = (
            "EXECUTIVE OFFICERS OF THE REGISTRANT\n"
            "The following table sets forth the names...\n"
        )
        m = SECTION_START.search(text)
        assert m is not None


# ─── End-to-end: PFE 10-K fixture ─────────────────────────────────────────────

@pytest.mark.skipif(not FIXTURE_HTML.exists(),
                    reason=f"PFE 10-K fixture not present at {FIXTURE_HTML}")
class TestPfizer2025EndToEnd:
    """End-to-end check against the Pfizer FY2025 10-K (filed Feb 2026).
    Verifies that all 10 executive officers are extracted with correct
    names, ages, and since-dates."""

    @pytest.fixture(scope="class")
    def rows(self):
        html = FIXTURE_HTML.read_text(encoding="utf-8", errors="replace")
        return extract_executives(html, ticker="PFE")

    def test_all_ten_officers_found(self, rows):
        assert len(rows) == 10

    def test_expected_officers_present(self, rows):
        names = {r.name for r in rows}
        expected = {
            "Albert Bourla", "Andrew Baum", "Chris Boshoff", "David M. Denton",
            "Alexandre de Germay", "Lidia Fonseca", "Douglas M. Lankler",
            "Aamir Malik", "Michael McDermott", "Payal Sahni",
        }
        assert names == expected

    def test_credentials_extracted(self, rows):
        bourla = next(r for r in rows if r.name == "Albert Bourla")
        assert bourla.credentials == "DVM, Ph.D."
        assert bourla.age == 64

        boshoff = next(r for r in rows if r.name == "Chris Boshoff")
        assert "MD" in boshoff.credentials
        assert "FRCP" in boshoff.credentials
        assert "Ph.D." in boshoff.credentials

    def test_particle_name_extracted(self, rows):
        # "Alexandre de Germay" is the particle-name test
        de_germay = next(r for r in rows if r.name == "Alexandre de Germay")
        assert de_germay.age == 58
        assert de_germay.in_role_since == "December 2023"

    def test_since_dates(self, rows):
        denton = next(r for r in rows if r.name == "David M. Denton")
        assert denton.in_role_since == "May 2022"

        baum = next(r for r in rows if r.name == "Andrew Baum")
        assert baum.in_role_since == "2024"  # year-only, no month

    def test_bio_text_preserved_intact(self, rows):
        # The full bio survives even though only the current title is parsed
        bourla = next(r for r in rows if r.name == "Albert Bourla")
        assert "Chief Operating Officer" in bourla.bio_text
        assert "Group President" in bourla.bio_text

    def test_no_workiva_artifacts_in_output(self, rows):
        # U+FFFD must be cleaned out everywhere
        for r in rows:
            assert "\uFFFD" not in r.bio_text, f"FFFD survived in {r.name}"
            assert "\uFFFD" not in r.current_title
