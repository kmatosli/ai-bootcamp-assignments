"""
api_explorer.py

Module 4 — What is REST: API Explorer
Caduceus Healthcare Equity Platform | Rhenman & Partners

Explores two public APIs using the same patterns we use to pull data
for the Caduceus platform — JSONPlaceholder (simulates our internal
analyst API) and GitHub (mirrors how we hit SEC EDGAR and FDA APIs).

Makes 6 API calls demonstrating: collection GET, single resource GET,
query parameters, nested resources, POST, and error handling.
"""
import requests

BASE_JPH   = "https://jsonplaceholder.typicode.com"
BASE_GH    = "https://api.github.com"


def print_call(method, url, status, reason, content_type, summary):
    print(f"\n  {'─'*60}")
    print(f"  {method} {url}")
    print(f"  Status: {status} {reason}")
    print(f"  Content-Type: {content_type}")
    print(f"  {summary}")


def safe_get(url, params=None, headers=None):
    """GET with error handling — script never crashes on 4xx/5xx."""
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        return r
    except requests.exceptions.RequestException as e:
        print(f"  Connection error: {e}")
        return None


print("=" * 65)
print("  CADUCEUS API Explorer — REST Fundamentals")
print("  JSONPlaceholder + GitHub REST API")
print("=" * 65)

# ── Call 1: GET collection — all users (like GET /analysts in Caduceus) ───────
r = safe_get(f"{BASE_JPH}/users")
if r:
    users = r.json()
    summary = f"Returned {len(users)} users | First: {users[0]['name']} ({users[0]['email']})"
    print_call("GET", f"{BASE_JPH}/users", r.status_code, r.reason,
               r.headers.get("Content-Type","?"), summary)

# ── Call 2: GET single resource — user #3 (like GET /analysts/3) ─────────────
# This is a single resource fetch — returns one object, not a list
r = safe_get(f"{BASE_JPH}/users/3")
if r:
    u = r.json()
    summary = f"User: {u['name']} | City: {u['address']['city']} | Company: {u['company']['name']}"
    print_call("GET", f"{BASE_JPH}/users/3", r.status_code, r.reason,
               r.headers.get("Content-Type","?"), summary)

# ── Call 3: GET with query parameters — posts by user #3 ─────────────────────
# Query parameters filter results server-side — like ?ticker=MRK&metric=revenue
r = safe_get(f"{BASE_JPH}/posts", params={"userId": 3})
if r:
    posts = r.json()
    summary = f"User 3 has {len(posts)} posts | First title: '{posts[0]['title'][:40]}...'"
    print_call("GET", f"{BASE_JPH}/posts?userId=3", r.status_code, r.reason,
               r.headers.get("Content-Type","?"), summary)

# ── Call 4: GET nested resource — comments on post #1 ────────────────────────
# Nested resources show parent-child relationships — like /companies/PFE/drugs
r = safe_get(f"{BASE_JPH}/posts/1/comments")
if r:
    comments = r.json()
    summary = f"Post 1 has {len(comments)} comments | First commenter: {comments[0]['email']}"
    print_call("GET", f"{BASE_JPH}/posts/1/comments", r.status_code, r.reason,
               r.headers.get("Content-Type","?"), summary)

# ── Call 5: POST — create a new resource ─────────────────────────────────────
# POST creates a new resource — like POST /coverage to assign analyst to drug
# JSONPlaceholder simulates this — returns 201 Created with the new resource
payload = {
    "title":  "Caduceus EDGAR Pull — FY2025 Universe Complete",
    "body":   "All 8 Phase 1 tickers loaded. Revenue validated against Morningstar.",
    "userId": 1
}
try:
    r = requests.post(f"{BASE_JPH}/posts", json=payload, timeout=10)
    # Status 201 = Created — the server created a new resource
    new_post = r.json()
    summary = f"Created post ID: {new_post['id']} | Title: '{new_post['title'][:40]}'"
    print_call("POST", f"{BASE_JPH}/posts", r.status_code, r.reason,
               r.headers.get("Content-Type","?"), summary)
except requests.exceptions.RequestException as e:
    print(f"  POST error: {e}")

# ── Call 6: GitHub API — Caduceus repo info ────────────────────────────────────
# Real API with rate limiting — mirrors how we hit EDGAR and FDA
# Unauthenticated: 60 requests/hour. Authenticated: 5,000/hour
headers = {"Accept": "application/vnd.github+json"}
r = safe_get(f"{BASE_GH}/repos/kmatosli/Caduceus", headers=headers)
if r:
    if r.status_code == 200:
        repo = r.json()
        remaining = r.headers.get("X-RateLimit-Remaining", "?")
        summary = (f"Repo: {repo['full_name']} | Stars: {repo['stargazers_count']} | "
                   f"Language: {repo['language']} | Rate limit remaining: {remaining}")
    elif r.status_code == 404:
        summary = "Repo is private — 404 as expected for unauthenticated access"
    else:
        summary = f"Unexpected status: {r.status_code}"
    print_call("GET", f"{BASE_GH}/repos/kmatosli/Caduceus", r.status_code, r.reason,
               r.headers.get("Content-Type","?"), summary)

# ── API Discovery: GitHub public endpoints ────────────────────────────────────
print(f"\n\n{'='*65}")
print("  API Discovery — GitHub REST API")
print(f"{'='*65}")

r = safe_get(f"{BASE_GH}/users/kmatosli", headers=headers)
if r:
    u = r.json()
    print(f"\n  Base URL:     {BASE_GH}")
    print(f"  Auth method:  Bearer token (optional for public endpoints)")
    print(f"  Rate limit:   {r.headers.get('X-RateLimit-Limit','?')} req/hour unauthenticated")
    print(f"  User:         {u.get('name','?')} | Public repos: {u.get('public_repos','?')}")
    print(f"  Resources:    /users, /repos, /orgs, /gists, /issues, /pulls")
    print(f"  Filter:       /users/kmatosli/repos?sort=stars&per_page=3")

print()
