"""
request_anatomy.py

Module 4 — The Request/Response Lifecycle
Caduceus Healthcare Equity Platform | Rhenman & Partners

Inspects the full anatomy of three API transactions — the same
diagnostic pattern used when debugging Caduceus data pulls.
"""
import requests
import time

BASE = "https://jsonplaceholder.typicode.com"


def print_anatomy(label: str, r: requests.Response, request_body=None):
    print(f"\n{'='*65}")
    print(f"  {label}")
    print(f"{'='*65}")
    print(f"\n  REQUEST")
    print(f"  Method & URL:    {r.request.method} {r.request.url}")
    print(f"  Request headers:")
    for k, v in r.request.headers.items():
        print(f"    {k}: {v}")
    if request_body:
        print(f"  Request body:    {request_body}")
    else:
        print(f"  Request body:    (none)")

    elapsed_ms = r.elapsed.total_seconds() * 1000
    print(f"\n  RESPONSE")
    print(f"  Status:          {r.status_code} {r.reason}")
    print(f"  Content-Type:    {r.headers.get('Content-Type','?')}")
    print(f"  Content-Length:  {r.headers.get('Content-Length','not specified')}")
    print(f"  Elapsed:         {elapsed_ms:.0f}ms")
    # Print response body — summarized, not raw dump
    try:
        body = r.json()
        if isinstance(body, list):
            print(f"  Response body:   [{len(body)} items] first: {str(body[0])[:80]}")
        else:
            print(f"  Response body:   {str(body)[:120]}")
    except Exception:
        print(f"  Response body:   {r.text[:120]}")


# ── Request 1: GET a specific user ────────────────────────────────────────────
r1 = requests.get(f"{BASE}/users/5", timeout=10)
print_anatomy("GET — Specific User (JSONPlaceholder /users/5)", r1)

# ── Request 2: POST — create a new post ──────────────────────────────────────
body2 = {
    "title":  "Caduceus EDGAR Intelligence Layer — Phase 1 Complete",
    "body":   "All 8 Phase 1 tickers loaded and validated. Concept validation next.",
    "userId": 1,
}
r2 = requests.post(f"{BASE}/posts", json=body2, timeout=10)
print_anatomy("POST — Create New Post (JSONPlaceholder /posts)", r2, request_body=body2)

# ── Request 3: PATCH — update a post title ────────────────────────────────────
body3 = {"title": "Caduceus Universe Pull — UPDATED"}
r3 = requests.patch(f"{BASE}/posts/1", json=body3, timeout=10)
print_anatomy("PATCH — Update Post Title (JSONPlaceholder /posts/1)", r3, request_body=body3)

print()
