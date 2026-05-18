"""
consuming_apis.py

Module 4 — Consuming & Testing APIs
Caduceus Healthcare Equity Platform | Rhenman & Partners

Builds a reusable APIClient base class and extends it to a
JSONPlaceholderClient — the same pattern Caduceus uses for its
BasePuller class hierarchy across 19 data sources.
"""
import requests
from typing import Any


# ── Base class — mirrors Caduceus BasePuller architecture ─────────────────────
class APIClient:
    """
    Reusable base API client with error handling and logging.
    Mirrors the Caduceus BasePuller abstract base class pattern.
    """

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout  = timeout
        self.session  = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def get(self, endpoint: str, params: dict | None = None) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            r = self.session.get(url, params=params, timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as e:
            print(f"  HTTP error {r.status_code}: {url}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"  Connection error: {e}")
            return None

    def post(self, endpoint: str, data: dict) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            r = self.session.post(url, json=data, timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            print(f"  Post error: {e}")
            return None


# ── Extended client — JSONPlaceholder ─────────────────────────────────────────
class JSONPlaceholderClient(APIClient):
    """
    Client for JSONPlaceholder — a free fake REST API for testing.
    Caduceus equivalent: EdgarClient, FdaClient, CtGovClient.
    """

    def __init__(self):
        super().__init__("https://jsonplaceholder.typicode.com")

    def get_user(self, user_id: int) -> dict | None:
        """Get a specific user's profile."""
        return self.get(f"/users/{user_id}")

    def get_user_posts(self, user_id: int) -> list | None:
        """Get all posts by a specific user."""
        return self.get("/posts", params={"userId": user_id})

    def create_post(self, user_id: int, title: str, body: str) -> dict | None:
        """Create a new post for a user. Returns the created resource."""
        return self.post("/posts", {
            "userId": user_id,
            "title":  title,
            "body":   body,
        })

    def search_posts(self, query: str) -> list:
        """Search posts by title — client-side filtering."""
        all_posts = self.get("/posts") or []
        return [p for p in all_posts if query.lower() in p["title"].lower()]


# ── Test script ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    client = JSONPlaceholderClient()

    print("=" * 65)
    print("  Caduceus API Client — JSONPlaceholder Test")
    print("=" * 65)

    # Get user 5's profile
    print("\n  [1] User 5 Profile")
    user = client.get_user(5)
    if user:
        print(f"  Name: {user['name']}")
        print(f"  City: {user['address']['city']}")
        print(f"  Company: {user['company']['name']}")

    # Get user 5's posts
    print("\n  [2] User 5 Posts")
    posts = client.get_user_posts(5)
    if posts:
        print(f"  Post count: {len(posts)}")
        print(f"  First post: '{posts[0]['title'][:50]}'")

    # Create a new post
    print("\n  [3] Create New Post")
    new_post = client.create_post(
        user_id=1,
        title="Caduceus Concept Validation — R&D Adapter Gaps Closed",
        body="ResearchAndDevelopmentExpenses mapped across all 8 tickers via concept_alias_table."
    )
    if new_post:
        # Status 201 = Created — the server made a new resource
        print(f"  Created post ID: {new_post['id']}")
        print(f"  Title: '{new_post['title'][:50]}'")

    # Search posts
    print("\n  [4] Search Posts Containing 'qui'")
    results = client.search_posts("qui")
    print(f"  Matches: {len(results)}")
    for p in results[:3]:
        print(f"  • '{p['title']}'")

print()
