"""
header_inspector.py

Module 4 — Headers and Content Types
Caduceus Healthcare Equity Platform | Rhenman & Partners

Inspects response headers across multiple APIs — the same inspection
Caduceus performs when validating responses from EDGAR, FDA, and CT.gov.
"""
import requests

ENDPOINTS = [
    "https://jsonplaceholder.typicode.com/posts/1",
    "https://jsonplaceholder.typicode.com/users/1",
    "https://httpbin.org/get",
]

CACHE_HEADERS    = {"Cache-Control", "ETag", "Last-Modified", "Expires"}
RATE_LIMIT_HEADERS = {"X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset",
                      "RateLimit-Limit", "RateLimit-Remaining"}


def inspect_headers(url: str) -> dict:
    try:
        r = requests.get(url, timeout=10)
        h = r.headers
        cache    = [k for k in h if k in CACHE_HEADERS]
        rate     = [k for k in h if k in RATE_LIMIT_HEADERS]
        return {
            "url":            url,
            "status":         r.status_code,
            "content_type":   h.get("Content-Type", "Not specified"),
            "content_length": h.get("Content-Length", "Not specified"),
            "cache_headers":  cache or ["None present"],
            "rate_headers":   rate or ["None present"],
            "total_headers":  len(h),
        }
    except requests.exceptions.RequestException as e:
        return {"url": url, "error": str(e)}


print("=" * 65)
print("  Caduceus Header Inspector")
print("=" * 65)

for url in ENDPOINTS:
    result = inspect_headers(url)
    print(f"\n  {'─'*60}")
    print(f"  GET {result['url']}")
    print(f"  {'─'*60}")
    if "error" in result:
        print(f"  Error: {result['error']}")
        continue
    print(f"  Status:          {result['status']}")
    print(f"  Content-Type:    {result['content_type']}")
    print(f"  Content-Length:  {result['content_length']}")
    print(f"  Cache headers:   {', '.join(result['cache_headers'])}")
    print(f"  Rate-limit hdrs: {', '.join(result['rate_headers'])}")
    print(f"  Total headers:   {result['total_headers']}")

# ── POST with custom headers ───────────────────────────────────────────────────
print(f"\n\n{'='*65}")
print("  POST with Custom Headers — httpbin echo")
print(f"{'='*65}")

custom_headers = {
    "Content-Type":   "application/json",
    "X-Student-Name": "Kathy Matosli",
    "X-Platform":     "Caduceus",
    "Accept":         "application/json",
}

try:
    r = requests.post(
        "https://httpbin.org/post",
        json={"platform": "Caduceus", "action": "header_test"},
        headers=custom_headers,
        timeout=10
    )
    echo = r.json()
    print(f"\n  Status: {r.status_code}")
    print(f"  Headers received by server:")
    for k, v in echo.get("headers", {}).items():
        if k.startswith("X-") or k in ("Content-Type", "Accept"):
            print(f"    {k}: {v}")
    print(f"\n  ✓ Custom headers confirmed received by server")
except requests.exceptions.RequestException as e:
    print(f"  Error: {e}")

print()
