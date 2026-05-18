"""
seed.py

Module 3 Capstone — Drug Pipeline Tracker Seed Data
Caduceus Healthcare Equity Platform | Rhenman & Partners

Seeds the database with:
  8 Phase 1 companies (validated CIKs)
  5 therapeutic areas
  10 key drugs across the universe
  6 Rhenman analysts
  8 coverage assignments (some active, some ended)
"""
from __future__ import annotations
from datetime import date
from sqlalchemy.orm import Session
from models import engine, Company, TherapeuticArea, Drug, Analyst, Coverage, drug_areas, Base


def seed():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with Session(engine) as s:
        # ── Companies ─────────────────────────────────────────────────────────
        companies = [
            Company(ticker="PFE",  name="Pfizer Inc",             cik="0000078003"),
            Company(ticker="MRK",  name="Merck & Co Inc",          cik="0000310158"),
            Company(ticker="JNJ",  name="Johnson & Johnson",        cik="0000200406"),
            Company(ticker="ABBV", name="AbbVie Inc",               cik="0001551152"),
            Company(ticker="BMY",  name="Bristol-Myers Squibb Co",  cik="0000014272"),
            Company(ticker="LLY",  name="Eli Lilly and Co",         cik="0000059478"),
            Company(ticker="AMGN", name="Amgen Inc",                cik="0000318154"),
            Company(ticker="GILD", name="Gilead Sciences Inc",      cik="0000882095"),
        ]
        s.add_all(companies)
        s.flush()

        # ── Therapeutic areas ─────────────────────────────────────────────────
        areas = {
            "Oncology":        TherapeuticArea(name="Oncology",        description="Cancer treatment and immunotherapy"),
            "Immunology":      TherapeuticArea(name="Immunology",      description="Autoimmune and inflammatory diseases"),
            "Cardiometabolic": TherapeuticArea(name="Cardiometabolic", description="Cardiovascular and metabolic disorders"),
            "Rare Disease":    TherapeuticArea(name="Rare Disease",    description="Orphan and rare genetic conditions"),
            "Virology":        TherapeuticArea(name="Virology",        description="Antiviral and infectious disease drugs"),
        }
        s.add_all(areas.values())
        s.flush()

        # ── Drugs ─────────────────────────────────────────────────────────────
        co = {c.ticker: c for c in companies}
        drugs = [
            Drug(brand_name="Keytruda",  generic_name="pembrolizumab", company=co["MRK"],
                 annual_revenue_usd_m=29516, approval_date=date(2014,9,4),
                 patent_expiry=date(2028,12,31),
                 therapeutic_areas=[areas["Oncology"]]),
            Drug(brand_name="Humira",    generic_name="adalimumab",    company=co["ABBV"],
                 annual_revenue_usd_m=8940,  approval_date=date(2002,12,31),
                 patent_expiry=date(2023,6,30),
                 therapeutic_areas=[areas["Immunology"]]),
            Drug(brand_name="Skyrizi",   generic_name="risankizumab",  company=co["ABBV"],
                 annual_revenue_usd_m=12162, approval_date=date(2019,4,23),
                 patent_expiry=date(2033,4,30),
                 therapeutic_areas=[areas["Immunology"]]),
            Drug(brand_name="Mounjaro",  generic_name="tirzepatide",   company=co["LLY"],
                 annual_revenue_usd_m=13900, approval_date=date(2022,5,13),
                 patent_expiry=date(2036,5,31),
                 therapeutic_areas=[areas["Cardiometabolic"]]),
            Drug(brand_name="Zepbound",  generic_name="tirzepatide",   company=co["LLY"],
                 annual_revenue_usd_m=5167,  approval_date=date(2023,11,8),
                 patent_expiry=date(2036,5,31),
                 therapeutic_areas=[areas["Cardiometabolic"]]),
            Drug(brand_name="Eliquis",   generic_name="apixaban",      company=co["BMY"],
                 annual_revenue_usd_m=12225, approval_date=date(2012,12,28),
                 patent_expiry=date(2026,12,31),
                 therapeutic_areas=[areas["Cardiometabolic"]]),
            Drug(brand_name="Opdivo",    generic_name="nivolumab",     company=co["BMY"],
                 annual_revenue_usd_m=9235,  approval_date=date(2014,12,22),
                 patent_expiry=date(2030,6,30),
                 therapeutic_areas=[areas["Oncology"]]),
            Drug(brand_name="Vyndaqel",  generic_name="tafamidis",     company=co["PFE"],
                 annual_revenue_usd_m=4000,  approval_date=date(2019,5,3),
                 patent_expiry=date(2027,5,31),
                 therapeutic_areas=[areas["Rare Disease"]]),
            Drug(brand_name="Veklury",   generic_name="remdesivir",    company=co["GILD"],
                 annual_revenue_usd_m=1100,  approval_date=date(2020,10,22),
                 patent_expiry=date(2031,1,31),
                 therapeutic_areas=[areas["Virology"]]),
            Drug(brand_name="Repatha",   generic_name="evolocumab",    company=co["AMGN"],
                 annual_revenue_usd_m=1800,  approval_date=date(2015,8,27),
                 patent_expiry=date(2026,8,31),
                 therapeutic_areas=[areas["Cardiometabolic"]]),
        ]
        s.add_all(drugs)
        s.flush()

        # ── Analysts ──────────────────────────────────────────────────────────
        analysts = [
            Analyst(first_name="Henrik",   last_name="Rhenman",       email="h.rhenman@rhenman.se",  role="CIO / Founder"),
            Analyst(first_name="Amennai",  last_name="Beyeen",        email="a.beyeen@rhenman.se",   role="Analyst — Biopharma"),
            Analyst(first_name="Camilla",  last_name="Oxhamre Cruse", email="c.oxhamre@rhenman.se",  role="PM — Biopharma"),
            Analyst(first_name="Hugo",     last_name="Schmidt",       email="h.schmidt@rhenman.se",  role="Analyst — Healthcare Services"),
            Analyst(first_name="Kaspar",   last_name="Hållsten",      email="k.hallsten@rhenman.se", role="Analyst — MedTech"),
            Analyst(first_name="Kathy",    last_name="Matosli",       email="k.matosli@rhenman.se",  role="Quant Developer"),
        ]
        s.add_all(analysts)
        s.flush()

        # ── Coverage assignments ───────────────────────────────────────────────
        drug_map     = {d.brand_name: d for d in drugs}
        analyst_map  = {a.email: a for a in analysts}

        coverages = [
            # Active
            Coverage(analyst=analyst_map["a.beyeen@rhenman.se"],   drug=drug_map["Humira"],   assigned_date=date(2024,1,15)),
            Coverage(analyst=analyst_map["a.beyeen@rhenman.se"],   drug=drug_map["Skyrizi"],  assigned_date=date(2024,1,15)),
            Coverage(analyst=analyst_map["c.oxhamre@rhenman.se"],  drug=drug_map["Keytruda"], assigned_date=date(2024,3,1)),
            Coverage(analyst=analyst_map["c.oxhamre@rhenman.se"],  drug=drug_map["Opdivo"],   assigned_date=date(2024,3,1)),
            Coverage(analyst=analyst_map["h.rhenman@rhenman.se"],  drug=drug_map["Mounjaro"], assigned_date=date(2024,6,1)),
            Coverage(analyst=analyst_map["h.rhenman@rhenman.se"],  drug=drug_map["Eliquis"],  assigned_date=date(2024,6,1)),
            # Ended (hand-off)
            Coverage(analyst=analyst_map["k.matosli@rhenman.se"],  drug=drug_map["Repatha"],
                     assigned_date=date(2024,1,1), end_date=date(2024,12,31),
                     coverage_notes="Handed off to Amennai after quant rotation"),
            Coverage(analyst=analyst_map["h.schmidt@rhenman.se"],  drug=drug_map["Veklury"],
                     assigned_date=date(2024,1,1), end_date=date(2024,9,30),
                     coverage_notes="Dropped — revenue declining post-COVID"),
        ]
        s.add_all(coverages)
        s.commit()

    print("Seed complete:")
    print(f"  {len(companies)} companies | {len(areas)} therapeutic areas | {len(drugs)} drugs")
    print(f"  {len(analysts)} analysts | {len(coverages)} coverage records")


if __name__ == "__main__":
    seed()
