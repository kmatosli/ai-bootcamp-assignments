"""
status_detective.py

Module 4 — HTTP Status Codes: The Server's Response Language
Caduceus Healthcare Equity Platform | Rhenman & Partners

Diagnostic tool that tests JSONPlaceholder endpoints and categorizes
each response by status code — the same pattern Caduceus uses to
validate responses from EDGAR, FDA, and ClinicalTrials.gov.
"""
import requests

BASE = "https://jsonplaceholder.typicode.com"


def categorize(code: int) -> str:
    if 200 <= code < 300: return "Success"
    if 300 <= code < 400: return "Redirect"
    if 400 <= code < 500: return "Client Error"
    if 500 <= code < 600: return "Server Error"
    return "Unknown"


DESCRIPTIONS = {
    200: "Request succeeded — resource returned",
    201: "Created — new resource successfully created",
    204: "No Content — success but nothing to return",
    301: "Moved Permanently — use the new URL",
    302: "Found — temporary redirect",
    400: "Bad Request — malformed syntax or invalid parameters",
    401: "Unauthorized — authentication required",
    403: "Forbidden — authenticated but not permitted",
    404: "Not Found — resource does not exist",
    405: "Method Not Allowed — HTTP verb not supported here",
    422: "Unprocessable Entity — valid syntax but semantic error",
    429: "Too Many Requests — rate limit exceeded",
    500: "Internal Server Error — unexpected server failure",
    503: "Service Unavailable — server temporarily down",
}


def status_report(method: str, url: str, **kwargs) -> dict:
    """Make a request and return a formatted status report."""
    try:
        r = requests.request(method, url, timeout=10, **kwargs)
        code = r.status_code
        return {
            "method":      method,
            "url":         url,
            "status":      code,
            "reason":      r.reason,
            "category":    categorize(code),
            "description": DESCRIPTIONS.get(code, "See HTTP spec"),
            "content_type": r.headers.get("Content-Type", "not specified"),
        }
    except requests.exceptions.ConnectionError:
        return {"method": method, "url": url, "status": None,
                "category": "Connection Error", "description": "Could not reach server"}
    except requests.exceptions.Timeout:
        return {"method": method, "url": url, "status": None,
                "category": "Timeout", "description": "Request timed out"}


def print_report(report: dict):
    status_str = str(report["status"]) if report["status"] else "N/A"
    print(f"\n  {report['method']} {report['url']}")
    print(f"  Status:      {status_str} ({report['category']})")
    print(f"  Description: {report['description']}")


print("=" * 65)
print("  Caduceus Status Code Detective")
print("  Testing JSONPlaceholder API Responses")
print("=" * 65)

requests_to_test = [
    # (method, url, kwargs)
    ("GET",    f"{BASE}/posts/1",          {}),
    ("GET",    f"{BASE}/posts/99999",       {}),                         # 404 — nonexistent
    ("POST",   f"{BASE}/posts",            {"json": {"title": "Caduceus Test", "userId": 1}}),
    ("DELETE", f"{BASE}/posts/1",          {}),
    ("GET",    f"{BASE}/invalidendpoint",  {}),                         # 404 — bad URI
    ("GET",    f"{BASE}/users/1/todos",    {}),                         # nested resource
]

for method, url, kwargs in requests_to_test:
    report = status_report(method, url, **kwargs)
    print_report(report)

# ── BONUS: reusable status reporter function ──────────────────────────────────
print(f"\n\n{'='*65}")
print("  BONUS: Generic Status Reporter")
print(f"{'='*65}")

def report_any(method: str, url: str, **kwargs):
    """Takes any URL and method, returns a formatted status report."""
    r = status_report(method, url, **kwargs)
    print_report(r)
    return r

# Test against GitHub API
report_any("GET", "https://api.github.com/users/octocat")
report_any("GET", "https://api.github.com/user")  # 401 — auth required

print()
