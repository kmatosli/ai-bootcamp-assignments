"""
api_explorer.py - Module 6: API Explorer
Caduceus Healthcare Equity Platform - Rhenman & Partners
Fetches pharma company data from the SEC EDGAR API.
"""
import requests

BASE = "https://data.sec.gov/submissions/CIK{}.json"
HEADERS = {"User-Agent": "Caduceus Research caduceus@research.com"}

PHASE1 = {
    "Pfizer":              "0000078003",
    "Merck":               "0000310158",
    "Johnson & Johnson":   "0000200406",
}

MISSING = "9999999999"  # does not exist

def fetch_company(name, cik):
    url = BASE.format(cik.zfill(10))
    r = requests.get(url, headers=HEADERS, timeout=10)
    if r.status_code == 404:
        print(f"  ERROR 404: Company with CIK {cik} not found.")
        return
    if not r.ok:
        print(f"  ERROR {r.status_code}: {r.text[:100]}")
        return
    data = r.json()
    print(f"  Name:      {data.get('name', 'N/A')}")
    print(f"  CIK:       {data.get('cik', 'N/A')}")
    print(f"  SIC:       {data.get('sic', 'N/A')} - {data.get('sicDescription', 'N/A')}")
    print(f"  State:     {data.get('stateOfIncorporation', 'N/A')}")
    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    tenk = [f for f in forms if f == "10-K"]
    print(f"  10-K filings on record: {len(tenk)}")

print("=" * 55)
print("Caduceus - SEC EDGAR Company Explorer")
print("=" * 55)

for name, cik in PHASE1.items():
    print(f"\n{name} (CIK {cik})")
    fetch_company(name, cik)

print(f"\nMissing CIK test (CIK {MISSING}):")
fetch_company("Unknown", MISSING)

print("\nDone.")
