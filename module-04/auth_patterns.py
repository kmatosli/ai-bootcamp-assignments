"""
auth_patterns.py

Module 4 — Authentication Concepts
Caduceus Healthcare Equity Platform | Rhenman & Partners

Part 1 — Documentation findings (no code):

  OpenAI API (https://platform.openai.com/docs/api-reference/authentication):
    Auth method:    API Key (Bearer token)
    Where it goes:  Authorization header
    Header name:    Authorization: Bearer sk-...
    Without auth:   401 Unauthorized — {"error": {"type": "invalid_request_error"}}

  GitHub REST API (https://docs.github.com/en/rest/authentication):
    Auth method:    Personal Access Token (Bearer) or GitHub App (JWT)
    Where it goes:  Authorization header
    Header name:    Authorization: Bearer ghp_...  or  token ghp_...
    Without auth:   200 for public endpoints, 401 for private endpoints
                    Rate limited to 60 req/hour vs 5,000 authenticated

Part 2 — Code implementation below.
"""
import requests

BASE_GH = "https://api.github.com"


def create_auth_headers(api_key: str, auth_type: str) -> dict:
    """
    Build the correct auth headers for a given auth type.

    Args:
        api_key:   The API key or token string
        auth_type: 'bearer' for Bearer token (OpenAI, GitHub)
                   'api-key' for X-API-Key header style

    Returns:
        dict of headers to include in the request
    """
    if auth_type == "bearer":
        return {"Authorization": f"Bearer {api_key}"}
    elif auth_type == "api-key":
        return {"X-API-Key": api_key}
    else:
        raise ValueError(f"Unknown auth_type: {auth_type!r}. Use 'bearer' or 'api-key'.")


print("=" * 65)
print("  Caduceus Auth Pattern Recognition")
print("=" * 65)

# ── Unauthenticated request to private endpoint → 401 ────────────────────────
print("\n  Test 1: Unauthenticated request to private endpoint")
print("  GET /user  (requires auth — your own profile)")
try:
    r = requests.get(f"{BASE_GH}/user", timeout=10)
    print(f"  Status: {r.status_code} {r.reason}")
    print(f"  Expected: 401 Unauthorized ✓" if r.status_code == 401 else
          f"  Got: {r.status_code}")
except requests.exceptions.RequestException as e:
    print(f"  Error: {e}")

# ── Unauthenticated request to public endpoint → 200 ─────────────────────────
print("\n  Test 2: Unauthenticated request to public endpoint")
print("  GET /users/octocat  (public profile — no auth needed)")
try:
    r = requests.get(f"{BASE_GH}/users/octocat", timeout=10)
    print(f"  Status: {r.status_code} {r.reason}")
    if r.status_code == 200:
        u = r.json()
        print(f"  User: {u.get('name','?')} | Public repos: {u.get('public_repos','?')}")
    print(f"  Expected: 200 OK ✓" if r.status_code == 200 else f"  Got: {r.status_code}")
except requests.exceptions.RequestException as e:
    print(f"  Error: {e}")

# ── create_auth_headers() demonstration ──────────────────────────────────────
print("\n  Test 3: create_auth_headers() function")

bearer_headers = create_auth_headers("sk-abc123", "bearer")
print(f"  Bearer:  {bearer_headers}")

apikey_headers = create_auth_headers("my-key-xyz", "api-key")
print(f"  API-Key: {apikey_headers}")

# Show how these would be used (without real keys)
print(f"\n  Usage example:")
print(f"    headers = create_auth_headers(os.environ['OPENAI_API_KEY'], 'bearer')")
print(f"    requests.post('https://api.openai.com/v1/chat/completions',")
print(f"                  headers=headers, json={{...}})")

print()
