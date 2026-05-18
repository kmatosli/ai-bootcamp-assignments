"""
crud.py

Module 3 Capstone — Drug Pipeline Tracker CRUD
Caduceus Healthcare Equity Platform | Rhenman & Partners

All data is converted to plain dicts INSIDE the session before returning.
No ORM objects ever leave the session context — eliminates all lazy load errors.
"""
from __future__ import annotations
from datetime import date
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload
from models import engine, Company, TherapeuticArea, Drug, Analyst, Coverage


# ── Internal helpers — called INSIDE open sessions only ───────────────────────

def _drug_to_dict(d: Drug) -> dict:
    return {
        "id":                   d.id,
        "brand_name":           d.brand_name,
        "generic_name":         d.generic_name,
        "ticker":               d.company.ticker if d.company else "?",
        "annual_revenue_usd_m": d.annual_revenue_usd_m,
        "areas":                [ta.name for ta in d.therapeutic_areas],
        "is_approved":          d.is_approved,
        "approval_date":        str(d.approval_date) if d.approval_date else None,
        "patent_expiry":        str(d.patent_expiry) if d.patent_expiry else None,
    }


def _analyst_to_dict(a: Analyst) -> dict:
    active = sum(1 for c in a.coverages if c.end_date is None)
    return {
        "id":          a.id,
        "full_name":   f"{a.first_name} {a.last_name}",
        "email":       a.email,
        "role":        a.role,
        "active_covs": active,
    }


def _coverage_to_dict(c: Coverage) -> dict:
    return {
        "drug_brand":    c.drug.brand_name if c.drug else "?",
        "drug_ticker":   c.drug.company.ticker if c.drug and c.drug.company else "?",
        "analyst_name":  f"{c.analyst.first_name} {c.analyst.last_name}" if c.analyst else "?",
        "assigned_date": str(c.assigned_date),
        "end_date":      str(c.end_date) if c.end_date else None,
        "is_active":     c.end_date is None,
        "notes":         c.coverage_notes,
    }


def _load_drug(s: Session, drug_id: int) -> Drug:
    return (s.query(Drug)
             .options(joinedload(Drug.company),
                      joinedload(Drug.therapeutic_areas))
             .filter(Drug.id == drug_id)
             .one())


# ── CREATE ────────────────────────────────────────────────────────────────────

def add_drug(brand_name: str, generic_name: str, ticker: str,
             therapeutic_area_names: list[str],
             annual_revenue_usd_m: float | None = None,
             approval_date: date | None = None,
             patent_expiry: date | None = None) -> dict:
    with Session(engine) as s:
        company = s.query(Company).filter(Company.ticker == ticker.upper()).first()
        if not company:
            raise ValueError(f"Company not found: {ticker}")
        areas = [s.query(TherapeuticArea)
                  .filter(TherapeuticArea.name.ilike(n)).first()
                  for n in therapeutic_area_names]
        areas = [a for a in areas if a]
        drug = Drug(
            brand_name=brand_name, generic_name=generic_name,
            company_id=company.id,
            annual_revenue_usd_m=annual_revenue_usd_m,
            approval_date=approval_date, patent_expiry=patent_expiry,
            therapeutic_areas=areas,
        )
        s.add(drug)
        s.commit()
        d = _load_drug(s, drug.id)
        return _drug_to_dict(d)


def add_analyst(first_name: str, last_name: str, email: str, role: str) -> dict:
    with Session(engine) as s:
        a = Analyst(first_name=first_name, last_name=last_name,
                    email=email, role=role)
        s.add(a)
        s.commit()
        return {"full_name": f"{first_name} {last_name}", "role": role}


def assign_coverage(analyst_email: str, drug_brand_name: str,
                    notes: str | None = None) -> dict:
    with Session(engine) as s:
        analyst = s.query(Analyst).filter(Analyst.email == analyst_email).first()
        if not analyst:
            raise ValueError(f"Analyst not found: {analyst_email}")
        drug = s.query(Drug).filter(Drug.brand_name.ilike(drug_brand_name)).first()
        if not drug:
            raise ValueError(f"Drug not found: {drug_brand_name}")
        existing = (s.query(Coverage)
                     .filter(Coverage.analyst_id == analyst.id,
                             Coverage.drug_id == drug.id,
                             Coverage.end_date == None)
                     .first())
        if existing:
            raise ValueError(
                f"{analyst.first_name} {analyst.last_name} already covers {drug.brand_name}")
        cov = Coverage(analyst_id=analyst.id, drug_id=drug.id,
                       assigned_date=date.today(), coverage_notes=notes)
        s.add(cov)
        s.commit()
        return {"analyst": analyst_email, "drug": drug.brand_name}


# ── READ ──────────────────────────────────────────────────────────────────────

def list_drugs(approved_only: bool = False) -> list[dict]:
    with Session(engine) as s:
        q = (s.query(Drug)
              .options(joinedload(Drug.company),
                       joinedload(Drug.therapeutic_areas)))
        if approved_only:
            q = q.filter(Drug.is_approved == True)
        drugs = q.order_by(Drug.brand_name).all()
        return [_drug_to_dict(d) for d in drugs]


def search_drugs(query: str) -> list[dict]:
    with Session(engine) as s:
        drugs = (s.query(Drug)
                  .options(joinedload(Drug.company),
                           joinedload(Drug.therapeutic_areas))
                  .filter(Drug.brand_name.ilike(f"%{query}%"))
                  .order_by(Drug.brand_name).all())
        return [_drug_to_dict(d) for d in drugs]


def find_drugs_by_area(area_name: str) -> list[dict]:
    with Session(engine) as s:
        # Case-insensitive match on therapeutic area name
        ta = (s.query(TherapeuticArea)
               .filter(TherapeuticArea.name.ilike(area_name))
               .first())
        if not ta:
            return []
        # Load drugs for this area with eager loading
        drugs = (s.query(Drug)
                  .options(joinedload(Drug.company),
                           joinedload(Drug.therapeutic_areas))
                  .filter(Drug.therapeutic_areas.any(TherapeuticArea.id == ta.id))
                  .all())
        return [_drug_to_dict(d) for d in drugs]


def list_analyst_coverage(analyst_email: str, active_only: bool = True) -> list[dict]:
    with Session(engine) as s:
        analyst = s.query(Analyst).filter(Analyst.email == analyst_email).first()
        if not analyst:
            return []
        q = (s.query(Coverage)
              .options(
                  joinedload(Coverage.drug).joinedload(Drug.company),
                  joinedload(Coverage.drug).joinedload(Drug.therapeutic_areas),
                  joinedload(Coverage.analyst),
              )
              .filter(Coverage.analyst_id == analyst.id))
        if active_only:
            q = q.filter(Coverage.end_date == None)
        return [_coverage_to_dict(c) for c in q.all()]


def list_uncovered_drugs() -> list[dict]:
    with Session(engine) as s:
        covered_rows = s.query(Coverage.drug_id).filter(Coverage.end_date == None).all()
        covered_ids  = {r[0] for r in covered_rows}
        q = (s.query(Drug)
              .options(joinedload(Drug.company),
                       joinedload(Drug.therapeutic_areas)))
        if covered_ids:
            q = q.filter(Drug.id.notin_(covered_ids))
        return [_drug_to_dict(d) for d in q.all()]


def list_all_analysts() -> list[dict]:
    with Session(engine) as s:
        analysts = (s.query(Analyst)
                     .options(joinedload(Analyst.coverages))
                     .filter(Analyst.is_active == True)
                     .order_by(Analyst.last_name).all())
        return [_analyst_to_dict(a) for a in analysts]


# ── UPDATE ────────────────────────────────────────────────────────────────────

def end_coverage(analyst_email: str, drug_brand_name: str) -> bool:
    with Session(engine) as s:
        analyst = s.query(Analyst).filter(Analyst.email == analyst_email).first()
        drug    = s.query(Drug).filter(Drug.brand_name.ilike(drug_brand_name)).first()
        if not analyst or not drug:
            return False
        cov = (s.query(Coverage)
                .filter(Coverage.analyst_id == analyst.id,
                        Coverage.drug_id == drug.id,
                        Coverage.end_date == None)
                .first())
        if not cov:
            return False
        cov.end_date = date.today()
        s.commit()
        return True


def update_analyst_email(old_email: str, new_email: str) -> bool:
    with Session(engine) as s:
        a = s.query(Analyst).filter(Analyst.email == old_email).first()
        if not a:
            return False
        a.email = new_email
        s.commit()
        return True


# ── DELETE ────────────────────────────────────────────────────────────────────

def remove_drug(brand_name: str) -> bool:
    with Session(engine) as s:
        drug = s.query(Drug).filter(Drug.brand_name.ilike(brand_name)).first()
        if not drug:
            return False
        active = (s.query(Coverage)
                   .filter(Coverage.drug_id == drug.id,
                           Coverage.end_date == None).count())
        if active > 0:
            raise ValueError(f"Cannot remove {drug.brand_name}: {active} active coverage(s)")
        s.delete(drug)
        s.commit()
        return True


def remove_analyst(email: str) -> bool:
    with Session(engine) as s:
        a = s.query(Analyst).filter(Analyst.email == email).first()
        if not a:
            return False
        active = (s.query(Coverage)
                   .filter(Coverage.analyst_id == a.id,
                           Coverage.end_date == None).count())
        if active > 0:
            raise ValueError(
                f"Cannot remove {a.first_name} {a.last_name}: "
                f"{active} active coverage(s). End coverage first.")
        s.delete(a)
        s.commit()
        return True
