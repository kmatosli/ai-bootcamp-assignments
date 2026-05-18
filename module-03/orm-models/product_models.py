"""
product_models.py

Module 3 — SQLAlchemy ORM Models & Engine Setup
Caduceus Healthcare Equity Platform | Rhenman & Partners

Domain: Therapeutic areas (categories) and pharmaceutical drugs (products).

Rubric mapping:
  Category model  → TherapeuticArea (name, description)
  Product model   → Drug (name, price/revenue, in_stock/is_covered, category_name FK)
  Engine echo=True, Base.metadata.create_all, 3 queries, bonus inspect()
"""
from __future__ import annotations
from datetime import date
from sqlalchemy import (
    create_engine, String, Integer, Boolean, Float, Text, Date,
    UniqueConstraint, ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_engine("sqlite:///caduceus_drugs.db", echo=True)


class Base(DeclarativeBase):
    pass


# ── Model 1: TherapeuticArea (= Category) ────────────────────────────────────
class TherapeuticArea(Base):
    """Disease category a drug targets. Maps to 'Category' in the rubric."""
    __tablename__ = "therapeutic_areas"

    id:          Mapped[int]       = mapped_column(Integer, primary_key=True, autoincrement=True)
    name:        Mapped[str]       = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[str|None]  = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"TherapeuticArea(id={self.id}, name={self.name!r})"


# ── Model 2: Drug (= Product) ─────────────────────────────────────────────────
class Drug(Base):
    """Pharma drug in the Caduceus covered universe. Maps to 'Product' in the rubric."""
    __tablename__ = "drug_products"

    id:                    Mapped[int]       = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_name:            Mapped[str]       = mapped_column(String(128), nullable=False)
    generic_name:          Mapped[str]       = mapped_column(String(128), nullable=False)
    ticker:                Mapped[str]       = mapped_column(String(10),  nullable=False)
    annual_revenue_usd_m:  Mapped[float]     = mapped_column(Float, nullable=False)
    is_covered:            Mapped[bool]      = mapped_column(Boolean, default=True)
    therapeutic_area_name: Mapped[str]       = mapped_column(
        String(64), ForeignKey("therapeutic_areas.name"), nullable=False
    )
    approval_date:         Mapped[date|None] = mapped_column(Date, nullable=True)

    def __repr__(self) -> str:
        return f"Drug(brand={self.brand_name!r}, ticker={self.ticker!r}, revenue=${self.annual_revenue_usd_m:,.0f}M)"


# ── Create tables ─────────────────────────────────────────────────────────────
Base.metadata.create_all(engine)

# ── Seed ──────────────────────────────────────────────────────────────────────
AREAS = [
    TherapeuticArea(name="Oncology",        description="Cancer treatment and immunotherapy"),
    TherapeuticArea(name="Immunology",      description="Autoimmune and inflammatory diseases"),
    TherapeuticArea(name="Cardiometabolic", description="Cardiovascular and metabolic disorders"),
    TherapeuticArea(name="Vaccines",        description="Infectious disease prevention"),
    TherapeuticArea(name="Rare Disease",    description="Orphan and rare genetic conditions"),
]

DRUGS = [
    Drug(brand_name="Keytruda",  generic_name="pembrolizumab", ticker="MRK",  annual_revenue_usd_m=29516, therapeutic_area_name="Oncology",        approval_date=date(2014, 9,  4)),
    Drug(brand_name="Humira",    generic_name="adalimumab",    ticker="ABBV", annual_revenue_usd_m=8940,  therapeutic_area_name="Immunology",      approval_date=date(2002, 12,31)),
    Drug(brand_name="Skyrizi",   generic_name="risankizumab",  ticker="ABBV", annual_revenue_usd_m=12162, therapeutic_area_name="Immunology",      approval_date=date(2019, 4, 23)),
    Drug(brand_name="Mounjaro",  generic_name="tirzepatide",   ticker="LLY",  annual_revenue_usd_m=13900, therapeutic_area_name="Cardiometabolic", approval_date=date(2022, 5, 13)),
    Drug(brand_name="Zepbound",  generic_name="tirzepatide",   ticker="LLY",  annual_revenue_usd_m=5167,  therapeutic_area_name="Cardiometabolic", approval_date=date(2023, 11, 8)),
    Drug(brand_name="Eliquis",   generic_name="apixaban",      ticker="BMY",  annual_revenue_usd_m=12225, therapeutic_area_name="Cardiometabolic", approval_date=date(2012, 12,28)),
    Drug(brand_name="Opdivo",    generic_name="nivolumab",     ticker="BMY",  annual_revenue_usd_m=9235,  therapeutic_area_name="Oncology",        approval_date=date(2014, 12,22)),
    Drug(brand_name="Vyndaqel",  generic_name="tafamidis",     ticker="PFE",  annual_revenue_usd_m=4000,  therapeutic_area_name="Rare Disease",    approval_date=date(2019, 5,  3)),
    Drug(brand_name="Comirnaty", generic_name="BNT162b2",      ticker="PFE",  annual_revenue_usd_m=6808,  therapeutic_area_name="Vaccines",        approval_date=date(2021, 8, 23)),
]

with Session(engine) as s:
    s.add_all(AREAS)
    s.commit()
    s.add_all(DRUGS)
    s.commit()
    print(f"\nSeeded {len(AREAS)} therapeutic areas and {len(DRUGS)} drugs.\n")

# ── Query 1: All categories (therapeutic areas) ───────────────────────────────
print("=" * 60)
print("Query 1: All Therapeutic Areas")
print("=" * 60)
with Session(engine) as s:
    for a in s.query(TherapeuticArea).order_by(TherapeuticArea.name).all():
        print(f"  {a.name:<20} {a.description}")

# ── Query 2: All covered drugs (in_stock equivalent) ─────────────────────────
print("\n" + "=" * 60)
print("Query 2: All Covered Drugs (is_covered=True)")
print("=" * 60)
with Session(engine) as s:
    for d in s.query(Drug).filter(Drug.is_covered == True).order_by(Drug.ticker).all():
        print(f"  [{d.ticker}] {d.brand_name:<15} ${d.annual_revenue_usd_m:>8,.0f}M  ({d.therapeutic_area_name})")

# ── Query 3: Drugs with revenue > $10B (price < $50 equivalent) ──────────────
print("\n" + "=" * 60)
print("Query 3: Blockbuster Drugs — Revenue > $10,000M")
print("=" * 60)
with Session(engine) as s:
    for d in (s.query(Drug)
                .filter(Drug.annual_revenue_usd_m > 10_000)
                .order_by(Drug.annual_revenue_usd_m.desc()).all()):
        print(f"  {d.brand_name:<15} [{d.ticker}]  ${d.annual_revenue_usd_m:>8,.0f}M")

# ── BONUS: Schema inspection ──────────────────────────────────────────────────
print("\n" + "=" * 60)
print("BONUS: inspect() — Schema Verification")
print("=" * 60)
from sqlalchemy import inspect as sa_inspect
inspector = sa_inspect(engine)
print(f"Tables: {inspector.get_table_names()}")
for tbl in ["therapeutic_areas", "drug_products"]:
    print(f"\n  {tbl}:")
    for col in inspector.get_columns(tbl):
        print(f"    {col['name']:<30} {str(col['type']):<15} nullable={col['nullable']}")
