"""
contact_manager.py

Module 3 — CRUD Operations with SQLAlchemy
Caduceus Healthcare Equity Platform | Rhenman & Partners

Domain: Internal contacts — the Rhenman team, data vendors, and service providers.
These are the same contacts seeded in Caduceus production (internal_contacts table).

Rubric mapping:
  Contact model  → AnalystContact (first_name, last_name, email, phone, favorite)
  add_contact()      create
  list_contacts()    read (all, sorted by last_name)
  find_contact()     read (by email)
  update_phone()     update
  toggle_favorite()  update
  delete_contact()   delete
"""
from __future__ import annotations
from sqlalchemy import create_engine, String, Integer, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

engine = create_engine("sqlite:///caduceus_contacts.db", echo=False)


class Base(DeclarativeBase):
    pass


class AnalystContact(Base):
    """
    Internal directory contact for Rhenman & Partners.
    Tracks team members, data vendors, and service providers.
    """
    __tablename__ = "analyst_contacts"

    id:           Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name:   Mapped[str]      = mapped_column(String(64), nullable=False)
    last_name:    Mapped[str]      = mapped_column(String(64), nullable=False)
    email:        Mapped[str]      = mapped_column(String(128), nullable=False, unique=True)
    phone:        Mapped[str|None] = mapped_column(String(32), nullable=True)
    contact_type: Mapped[str]      = mapped_column(String(32), nullable=False, default="analyst")
    favorite:     Mapped[bool]     = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        fav = " ★" if self.favorite else ""
        return f"Contact({self.first_name} {self.last_name} | {self.email}{fav})"


Base.metadata.create_all(engine)


# ── CRUD functions ────────────────────────────────────────────────────────────

def add_contact(first_name: str, last_name: str, email: str,
                phone: str | None = None,
                contact_type: str = "analyst") -> AnalystContact:
    """Create a new contact."""
    with Session(engine) as s:
        c = AnalystContact(
            first_name=first_name, last_name=last_name,
            email=email, phone=phone, contact_type=contact_type,
        )
        s.add(c)
        s.commit()
        s.refresh(c)
        print(f"  Added: {c}")
        return c


def list_contacts() -> list[AnalystContact]:
    """Read all contacts, sorted by last name."""
    with Session(engine) as s:
        contacts = (s.query(AnalystContact)
                     .order_by(AnalystContact.last_name, AnalystContact.first_name)
                     .all())
        print(f"\n  {'Name':<30} {'Email':<35} {'Type':<15} {'Fav'}")
        print(f"  {'-'*30} {'-'*35} {'-'*15} {'-'*3}")
        for c in contacts:
            fav = "★" if c.favorite else ""
            print(f"  {c.first_name+' '+c.last_name:<30} {c.email:<35} {c.contact_type:<15} {fav}")
        return contacts


def find_contact(email: str) -> AnalystContact | None:
    """Read single contact by email."""
    with Session(engine) as s:
        c = s.query(AnalystContact).filter(AnalystContact.email == email).first()
        if c:
            print(f"  Found: {c}  phone={c.phone or 'N/A'}")
        else:
            print(f"  Not found: {email}")
        return c


def update_phone(email: str, new_phone: str) -> bool:
    """Update phone number for a contact."""
    with Session(engine) as s:
        c = s.query(AnalystContact).filter(AnalystContact.email == email).first()
        if not c:
            print(f"  Not found: {email}")
            return False
        c.phone = new_phone
        s.commit()
        print(f"  Updated phone for {c.first_name} {c.last_name}: {new_phone}")
        return True


def toggle_favorite(email: str) -> bool | None:
    """Flip favorite status (True ↔ False)."""
    with Session(engine) as s:
        c = s.query(AnalystContact).filter(AnalystContact.email == email).first()
        if not c:
            print(f"  Not found: {email}")
            return None
        c.favorite = not c.favorite
        s.commit()
        status = "★ favorited" if c.favorite else "un-favorited"
        print(f"  {c.first_name} {c.last_name} {status}")
        return c.favorite


def delete_contact(email: str) -> bool:
    """Delete a contact by email."""
    with Session(engine) as s:
        c = s.query(AnalystContact).filter(AnalystContact.email == email).first()
        if not c:
            print(f"  Not found: {email}")
            return False
        name = f"{c.first_name} {c.last_name}"
        s.delete(c)
        s.commit()
        print(f"  Deleted: {name} ({email})")
        return True


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 65)
    print("  Caduceus Contact Manager — Rhenman & Partners")
    print("=" * 65)

    # Add 6+ contacts — Rhenman team + vendors
    print("\n[ Adding contacts ]")
    add_contact("Henrik",  "Rhenman",       "h.rhenman@rhenman.se",       contact_type="analyst")
    add_contact("Kaspar",  "Hållsten",      "k.hallsten@rhenman.se",      contact_type="analyst")
    add_contact("Amennai", "Beyeen",        "a.beyeen@rhenman.se",        contact_type="analyst")
    add_contact("Hugo",    "Schmidt",       "h.schmidt@rhenman.se",       contact_type="analyst")
    add_contact("Camilla", "Oxhamre Cruse", "c.oxhamre@rhenman.se",       contact_type="analyst")
    add_contact("Kathy",   "Matosli",       "k.matosli@rhenman.se",       contact_type="analyst")
    add_contact("FactSet", "Support",       "support@factset.com",        phone="+1-877-322-8738",
                contact_type="vendor")
    add_contact("Morningstar","Data",       "data@morningstar.com",       contact_type="vendor")

    # List all
    print("\n[ All contacts, sorted by last name ]")
    list_contacts()

    # Find one
    print("\n[ Find by email ]")
    find_contact("k.matosli@rhenman.se")

    # Update phone
    print("\n[ Update phone ]")
    update_phone("k.matosli@rhenman.se", "+1-312-555-0190")

    # Toggle favorites
    print("\n[ Toggle favorites ]")
    toggle_favorite("h.rhenman@rhenman.se")
    toggle_favorite("k.matosli@rhenman.se")
    toggle_favorite("a.beyeen@rhenman.se")

    # Delete one
    print("\n[ Delete a contact ]")
    delete_contact("data@morningstar.com")

    # List again — show the changes
    print("\n[ Final contact list ]")
    list_contacts()
