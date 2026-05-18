"""
cli.py

Module 3 Capstone — Drug Pipeline Tracker CLI
Caduceus Healthcare Equity Platform | Rhenman & Partners
"""
from __future__ import annotations
import sys
from seed import seed
import crud


MENU = """
╔══════════════════════════════════════════════════════════╗
║       💊 Caduceus Drug Pipeline Tracker                  ║
║          Rhenman & Partners                              ║
╠══════════════════════════════════════════════════════════╣
║  1. List all drugs                                       ║
║  2. Search drugs by name                                 ║
║  3. Find drugs by therapeutic area                       ║
║  4. Add a new drug                                       ║
║  5. Add a new analyst                                    ║
║  6. Assign analyst to cover a drug                       ║
║  7. End analyst's drug coverage                          ║
║  8. View analyst's current coverage                      ║
║  9. List uncovered drugs                                 ║
║ 10. List all analysts                                    ║
║  0. Exit                                                 ║
╚══════════════════════════════════════════════════════════╝
"""


def prompt(label: str) -> str:
    return input(f"  {label}: ").strip()


def _fmt_drug(d: dict) -> str:
    rev   = f"${d['annual_revenue_usd_m']:,.0f}M" if d['annual_revenue_usd_m'] else "N/A"
    areas = ", ".join(d['areas']) if d['areas'] else "N/A"
    return f"  [{d['ticker']}] {d['brand_name']:<18} ({d['generic_name']}) | {rev} | {areas}"


def _fmt_analyst(a: dict) -> str:
    return f"  {a['full_name']:<28} {a['role']:<35} | {a['active_covs']} coverage(s)"


def menu_list_drugs():
    drugs = crud.list_drugs()
    if not drugs:
        print("  No drugs in the pipeline.")
        return
    print(f"\n  {'─'*65}")
    print(f"  All Drugs ({len(drugs)} total)")
    print(f"  {'─'*65}")
    for d in drugs:
        print(_fmt_drug(d))


def menu_search_drugs():
    q = prompt("Search term (brand name)")
    if not q:
        return
    results = crud.search_drugs(q)
    if not results:
        print(f"  No drugs found matching '{q}'")
        return
    for d in results:
        print(_fmt_drug(d))


def menu_drugs_by_area():
    area = prompt("Therapeutic area (Oncology / Immunology / Cardiometabolic / Rare Disease / Virology)")
    results = crud.find_drugs_by_area(area)
    if not results:
        print(f"  No drugs found in area '{area}'")
        return
    print(f"\n  Drugs in {area}:")
    for d in results:
        print(_fmt_drug(d))


def menu_add_drug():
    brand     = prompt("Brand name")
    generic   = prompt("Generic name")
    ticker    = prompt("Company ticker (PFE/MRK/JNJ/ABBV/BMY/LLY/AMGN/GILD)")
    areas_raw = prompt("Therapeutic area(s) comma-separated")
    areas     = [a.strip() for a in areas_raw.split(",") if a.strip()]
    rev_raw   = prompt("Annual revenue $M (or leave blank)")
    revenue   = float(rev_raw) if rev_raw else None
    try:
        result = crud.add_drug(brand, generic, ticker, areas, revenue)
        print(f"  Added: {result['brand_name']} [{result['ticker']}]")
    except ValueError as e:
        print(f"  Error: {e}")


def menu_add_analyst():
    first = prompt("First name")
    last  = prompt("Last name")
    email = prompt("Email")
    role  = prompt("Role")
    result = crud.add_analyst(first, last, email, role)
    print(f"  Added analyst: {result['full_name']} ({result['role']})")


def menu_assign():
    email = prompt("Analyst email")
    drug  = prompt("Drug brand name")
    notes = prompt("Coverage notes (optional)")
    try:
        crud.assign_coverage(email, drug, notes or None)
        print(f"  Coverage assigned: {drug} → {email}")
    except ValueError as e:
        print(f"  Error: {e}")


def menu_end_coverage():
    email = prompt("Analyst email")
    drug  = prompt("Drug brand name")
    ok = crud.end_coverage(email, drug)
    if ok:
        print(f"  Coverage ended: {drug} | {email}")
    else:
        print(f"  No active coverage found.")


def menu_view_coverage():
    email = prompt("Analyst email")
    rows = crud.list_analyst_coverage(email)
    if not rows:
        print(f"  No active coverage for {email}")
        return
    print(f"\n  Active coverage for {email}:")
    for c in rows:
        print(f"    {c['drug_brand']:<20} [{c['drug_ticker']}]  since {c['assigned_date']}")


def menu_uncovered():
    drugs = crud.list_uncovered_drugs()
    if not drugs:
        print("  All drugs have active coverage.")
        return
    print(f"\n  Uncovered drugs ({len(drugs)}):")
    for d in drugs:
        print(_fmt_drug(d))


def menu_list_analysts():
    analysts = crud.list_all_analysts()
    print(f"\n  Rhenman Team ({len(analysts)} active analysts):")
    print(f"  {'─'*75}")
    for a in analysts:
        print(_fmt_analyst(a))


HANDLERS = {
    "1":  menu_list_drugs,
    "2":  menu_search_drugs,
    "3":  menu_drugs_by_area,
    "4":  menu_add_drug,
    "5":  menu_add_analyst,
    "6":  menu_assign,
    "7":  menu_end_coverage,
    "8":  menu_view_coverage,
    "9":  menu_uncovered,
    "10": menu_list_analysts,
}


def main():
    print("\n  Seeding database with Phase 1 universe data...")
    seed()
    print("\n  Welcome to the Caduceus Drug Pipeline Tracker.\n")

    while True:
        print(MENU)
        choice = input("  Enter option: ").strip()

        if choice == "0":
            print("\n  Goodbye.\n")
            sys.exit(0)

        handler = HANDLERS.get(choice)
        if handler:
            print()
            try:
                handler()
            except Exception as e:
                print(f"  Error: {e}")
        else:
            print(f"  Invalid option: '{choice}'. Enter 0-10.")


if __name__ == "__main__":
    main()
