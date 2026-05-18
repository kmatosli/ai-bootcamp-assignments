"""
school_enrollment.py

Module 3 — Relationships: One-to-Many and Many-to-Many
Caduceus Healthcare Equity Platform | Rhenman & Partners

Rubric mapping (Caduceus domain):
  Department  → TherapeuticArea  (Oncology, Immunology, etc.)  — one-to-many with analysts
  Teacher     → Analyst          (Rhenman team)               — one-to-many with drugs
  Course      → Drug             (Keytruda, Humira, etc.)     — many-to-many with companies
  Student     → Company          (PFE, MRK, LLY, etc.)       — enrolled in many drugs
  student_courses → company_drug_coverage                     — association table

Relationships:
  TherapeuticArea  →  Analyst     (one-to-many)
  Analyst          →  Drug        (one-to-many: analyst leads coverage)
  Drug           ↔   Company      (many-to-many via company_drug_coverage)
"""
from __future__ import annotations
from typing import List, Optional
from sqlalchemy import (
    create_engine, String, Integer, ForeignKey, Table, Column,
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, Session,
)

engine = create_engine("sqlite:///school_enrollment.db", echo=False)


class Base(DeclarativeBase):
    pass


# ── Many-to-many association: Drug ↔ Company ─────────────────────────────────
company_drug_coverage = Table(
    "company_drug_coverage",
    Base.metadata,
    Column("company_id", Integer, ForeignKey("companies.id"), primary_key=True),
    Column("drug_id",    Integer, ForeignKey("drugs.id"),    primary_key=True),
)


# ── Department → TherapeuticArea (one-to-many with Analyst) ──────────────────
class TherapeuticArea(Base):
    __tablename__ = "therapeutic_areas"

    id:          Mapped[int]         = mapped_column(Integer, primary_key=True, autoincrement=True)
    name:        Mapped[str]         = mapped_column(String(64), nullable=False, unique=True)

    analysts: Mapped[List["Analyst"]] = relationship("Analyst", back_populates="area")

    def __repr__(self) -> str:
        return f"TherapeuticArea({self.name!r})"


# ── Teacher → Analyst (belongs to one area, leads many drugs) ────────────────
class Analyst(Base):
    __tablename__ = "analysts"

    id:      Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name:    Mapped[str] = mapped_column(String(128), nullable=False)
    area_id: Mapped[int] = mapped_column(ForeignKey("therapeutic_areas.id"), nullable=False)

    area:  Mapped["TherapeuticArea"]  = relationship("TherapeuticArea", back_populates="analysts")
    drugs: Mapped[List["Drug"]]       = relationship("Drug", back_populates="lead_analyst")

    def __repr__(self) -> str:
        return f"Analyst({self.name!r})"


# ── Course → Drug (led by one analyst, covered by many companies) ─────────────
class Drug(Base):
    __tablename__ = "drugs"

    id:              Mapped[int]         = mapped_column(Integer, primary_key=True, autoincrement=True)
    title:           Mapped[str]         = mapped_column(String(128), nullable=False)
    analyst_id:      Mapped[int]         = mapped_column(ForeignKey("analysts.id"), nullable=False)

    lead_analyst: Mapped["Analyst"]        = relationship("Analyst", back_populates="drugs")
    companies:    Mapped[List["Company"]]  = relationship(
        "Company", secondary=company_drug_coverage, back_populates="drugs"
    )

    def __repr__(self) -> str:
        return f"Drug({self.title!r})"


# ── Student → Company (enrolled in many drugs via many-to-many) ───────────────
class Company(Base):
    __tablename__ = "companies"

    id:    Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name:  Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

    drugs: Mapped[List["Drug"]] = relationship(
        "Drug", secondary=company_drug_coverage, back_populates="companies"
    )

    def __repr__(self) -> str:
        return f"Company({self.name!r})"


Base.metadata.create_all(engine)

# ── Seed ──────────────────────────────────────────────────────────────────────
with Session(engine) as s:
    # Therapeutic areas (departments) — 2+
    oncology   = TherapeuticArea(name="Oncology")
    immunology = TherapeuticArea(name="Immunology")
    cardio     = TherapeuticArea(name="Cardiometabolic")
    s.add_all([oncology, immunology, cardio])
    s.flush()

    # Analysts (teachers) — 4+, each belongs to one area
    amennai = Analyst(name="Amennai Beyeen",        area=immunology)
    camilla = Analyst(name="Camilla Oxhamre Cruse", area=oncology)
    henrik  = Analyst(name="Henrik Rhenman",        area=cardio)
    hugo    = Analyst(name="Hugo Schmidt",          area=oncology)
    s.add_all([amennai, camilla, henrik, hugo])
    s.flush()

    # Drugs (courses) — 5+, each led by one analyst
    humira   = Drug(title="Humira (adalimumab)",      lead_analyst=amennai)
    skyrizi  = Drug(title="Skyrizi (risankizumab)",   lead_analyst=amennai)
    keytruda = Drug(title="Keytruda (pembrolizumab)", lead_analyst=camilla)
    opdivo   = Drug(title="Opdivo (nivolumab)",       lead_analyst=hugo)
    eliquis  = Drug(title="Eliquis (apixaban)",       lead_analyst=henrik)
    mounjaro = Drug(title="Mounjaro (tirzepatide)",   lead_analyst=henrik)
    s.add_all([humira, skyrizi, keytruda, opdivo, eliquis, mounjaro])
    s.flush()

    # Companies (students) — 6+, enrolled in various drugs (many-to-many)
    abbv = Company(name="AbbVie Inc",           email="ir@abbvie.com",   drugs=[humira, skyrizi])
    mrk  = Company(name="Merck & Co Inc",       email="ir@merck.com",    drugs=[keytruda])
    bmy  = Company(name="Bristol-Myers Squibb", email="ir@bms.com",      drugs=[opdivo, eliquis])
    lly  = Company(name="Eli Lilly and Co",     email="ir@lilly.com",    drugs=[mounjaro])
    pfe  = Company(name="Pfizer Inc",           email="ir@pfizer.com",   drugs=[eliquis])
    jnj  = Company(name="Johnson & Johnson",    email="ir@jnj.com",      drugs=[keytruda, humira])
    s.add_all([abbv, mrk, bmy, lly, pfe, jnj])
    s.commit()

print("=" * 65)
print("  Caduceus School Enrollment — Relationship Demonstrations")
print("=" * 65)

# ── Demo 1: Each department (area) and its teachers (analysts) ────────────────
print("\n1. Each Therapeutic Area and its Analysts:")
with Session(engine) as s:
    areas = s.query(TherapeuticArea).all()
    for area in areas:
        print(f"\n   {area.name}:")
        for analyst in area.analysts:
            print(f"     → {analyst.name}")

# ── Demo 2: Each teacher (analyst) and courses (drugs) they lead ──────────────
print("\n\n2. Each Analyst and the Drugs They Lead:")
with Session(engine) as s:
    analysts = s.query(Analyst).all()
    for analyst in analysts:
        drugs = ", ".join(d.title.split(" (")[0] for d in analyst.drugs)
        print(f"   {analyst.name:<28} → {drugs or 'none'}")

# ── Demo 3: Each course (drug) with its enrolled students (companies) ─────────
print("\n\n3. Each Drug and its Covered Companies:")
with Session(engine) as s:
    drugs = s.query(Drug).all()
    for drug in drugs:
        cos = ", ".join(c.name for c in drug.companies)
        print(f"   {drug.title.split(' (')[0]:<25} → {cos or 'none'}")

# ── Demo 4: Each student (company) and courses they're enrolled in ────────────
print("\n\n4. Each Company and the Drugs They're Enrolled In:")
with Session(engine) as s:
    companies = s.query(Company).all()
    for co in companies:
        drugs = ", ".join(d.title.split(" (")[0] for d in co.drugs)
        print(f"   {co.name:<28} → {drugs or 'none'}")

# ── Demo 5: Find drugs with more than 1 company enrolled ─────────────────────
print("\n\n5. Drugs Covered by More Than 1 Company:")
with Session(engine) as s:
    drugs = s.query(Drug).all()
    for drug in drugs:
        if len(drug.companies) > 1:
            cos = ", ".join(c.name for c in drug.companies)
            print(f"   {drug.title.split(' (')[0]:<25} ({len(drug.companies)} companies) → {cos}")

print()
