"""
doc_scavenger.py

Module 4 — API Documentation Scavenger Hunt
Caduceus Healthcare Equity Platform | Rhenman & Partners

Navigates the GitHub REST API documentation findings and fetches
top repos — mirrors how Caduceus queries SEC EDGAR's EFTS full-text
search API using documented endpoints and query parameters.

Documentation findings:
  Q1: List public repos for a user → GET /users/{username}/repos
  Q2: Sort parameters → sort=created|updated|pushed|full_name, direction=asc|desc
  Q3: Unauthenticated rate limit → 60 requests per hour
  Q4: Recommended Accept header → application/vnd.github+json
"""
import requests

BASE    = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github+json"}


print("=" * 65)
print("  Caduceus Documentation Scavenger Hunt — GitHub REST API")
print("=" * 65)

# ── Written answers ───────────────────────────────────────────────────────────
print("""
  Q1: Endpoint to list public repos for a user:
      GET /users/{username}/repos

  Q2: Sort query parameters:
      sort=created|updated|pushed|full_name
      direction=asc|desc
      per_page=N (max 100), page=N

  Q3: Unauthenticated rate limit:
      60 requests per hour per IP address
      (5,000/hour with a valid token)

  Q4: Recommended Accept header:
      application/vnd.github+json
""")

# ── Fetch google's 3 most-starred repos ──────────────────────────────────────
print("─" * 65)
print("  Google's Top 3 Most-Starred Repositories")
print("─" * 65)

try:
    r = requests.get(
        f"{BASE}/users/google/repos",
        headers=HEADERS,
        params={"sort": "stargazers", "per_page": 3, "direction": "desc"},
        timeout=10
    )

    if r.status_code == 200:
        repos = r.json()
        for i, repo in enumerate(repos, 1):
            print(f"\n  {i}. {repo['name']}")
            print(f"     Description: {repo.get('description','N/A')[:70]}")
            print(f"     Stars:       {repo['stargazers_count']:,}")
            print(f"     Language:    {repo.get('language','N/A')}")
    else:
        print(f"  Status {r.status_code}: {r.reason}")

    # Rate limit remaining
    remaining = r.headers.get("X-RateLimit-Remaining", "?")
    limit     = r.headers.get("X-RateLimit-Limit", "?")
    print(f"\n  Rate limit: {remaining}/{limit} requests remaining this hour")

except requests.exceptions.RequestException as e:
    print(f"  Error: {e}")

print()
