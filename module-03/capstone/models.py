"""
models.py

Module 3 Capstone — Drug Pipeline Tracker
Caduceus Healthcare Equity Platform | Rhenman & Partners

The Caduceus drug pipeline tracker manages the Phase 1 covered universe
of pharmaceutical companies, their drug portfolios, and analyst coverage
assignments. This is the institutional-grade equivalent of the Library
Management System — drugs are books, companies are publishers, analysts
are members, and coverage assignments are borrowings.

Tables:
  companies          — 8 Phase 1 pharma names (PFE, MRK, JNJ, etc.)
  therapeutic_areas  — disease categories (Oncology, Immunology, etc.)
  drugs              — drug products with M:M to therapeutic_areas
  drug_areas         — many-to-many association table
  analysts           — Rhenman team members
  coverage           — which analyst covers which drug (with dates)

SQLAlchemy 2.0 Mapped/mapped_column syntax throughout.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import (
    create_engine, String, Integer, Boolean, Float, Date, DateTime,
    ForeignKey, Table, Column, Text, UniqueConstraint,
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, Session,
)

engine = create_engine("sqlite:///caduceus_pipeline.db", echo=False)


class Base(DeclarativeBase):
    pass


# ── Many-to-many association: drugs ↔ therapeutic_areas ──────────────────────
drug_areas = Table(
    "drug_areas",
    Base.metadata,
    Column("drug_id",  Integer, ForeignKey("drugs.id"),              primary_key=True),
    Column("area_id",  Integer, ForeignKey("therapeutic_areas.id"),  primary_key=True),
)


# ── Model: Company ────────────────────────────────────────────────────────────
class Company(Base):
    __tablename__ = "companies"

    id:        Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker:    Mapped[str]           = mapped_column(String(10), nullable=False, unique=True)
    name:      Mapped[str]           = mapped_column(String(128), nullable=False)
    cik:       Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sector:    Mapped[str]           = mapped_column(String(64),  nullable=False, default="Healthcare")

    drugs: Mapped[List["Drug"]] = relationship("Drug", back_populates="company")

    def __repr__(self) -> str:
        return f"Company(ticker={self.ticker!r}, name={self.name!r})"


# ── Model: TherapeuticArea ────────────────────────────────────────────────────
class TherapeuticArea(Base):
    __tablename__ = "therapeutic_areas"

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    name:        Mapped[str]           = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    drugs: Mapped[List["Drug"]] = relationship("Drug", secondary=drug_areas, back_populates="therapeutic_areas")

    def __repr__(self) -> str:
        return f"TherapeuticArea(name={self.name!r})"


# ── Model: Drug ───────────────────────────────────────────────────────────────
class Drug(Base):
    __tablename__ = "drugs"

    id:                   Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_name:           Mapped[str]            = mapped_column(String(128), nullable=False)
    generic_name:         Mapped[str]            = mapped_column(String(128), nullable=False)
    company_id:           Mapped[int]            = mapped_column(ForeignKey("companies.id"), nullable=False)
    annual_revenue_usd_m: Mapped[Optional[float]]= mapped_column(Float, nullable=True)
    is_approved:          Mapped[bool]           = mapped_column(Boolean, default=True)
    approval_date:        Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    patent_expiry:        Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes:                Mapped[Optional[str]]  = mapped_column(Text, nullable=True)

    company:            Mapped["Company"]               = relationship("Company", back_populates="drugs")
    therapeutic_areas:  Mapped[List["TherapeuticArea"]] = relationship(
        "TherapeuticArea", secondary=drug_areas, back_populates="drugs"
    )
    coverages: Mapped[List["Coverage"]] = relationship("Coverage", back_populates="drug")

    def __repr__(self) -> str:
        return f"Drug(brand={self.brand_name!r}, ticker={self.company.ticker if self.company else '?'!r})"


# ── Model: Analyst ────────────────────────────────────────────────────────────
class Analyst(Base):
    __tablename__ = "analysts"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str]           = mapped_column(String(64), nullable=False)
    last_name:  Mapped[str]           = mapped_column(String(64), nullable=False)
    email:      Mapped[str]           = mapped_column(String(128), nullable=False, unique=True)
    role:       Mapped[str]           = mapped_column(String(128), nullable=False)
    is_active:  Mapped[bool]          = mapped_column(Boolean, default=True)

    coverages: Mapped[List["Coverage"]] = relationship("Coverage", back_populates="analyst")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"Analyst(name={self.full_name!r}, role={self.role!r})"


# ── Model: Coverage (association with extra columns) ──────────────────────────
class Coverage(Base):
    """
    Which analyst covers which drug — with assignment date and notes.
    Equivalent to 'borrowings' in the Library Management System.
    """
    __tablename__ = "coverage"

    id:            Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    analyst_id:    Mapped[int]            = mapped_column(ForeignKey("analysts.id"), nullable=False)
    drug_id:       Mapped[int]            = mapped_column(ForeignKey("drugs.id"), nullable=False)
    assigned_date: Mapped[date]           = mapped_column(Date, nullable=False, default=date.today)
    end_date:      Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    coverage_notes:Mapped[Optional[str]]  = mapped_column(Text, nullable=True)

    analyst: Mapped["Analyst"] = relationship("Analyst", back_populates="coverages")
    drug:    Mapped["Drug"]    = relationship("Drug", back_populates="coverages")

    @property
    def is_active(self) -> bool:
        return self.end_date is None

    def __repr__(self) -> str:
        return f"Coverage(analyst={self.analyst_id}, drug={self.drug_id}, active={self.is_active})"


# ── Create all tables ─────────────────────────────────────────────────────────
Base.metadata.create_all(engine)
