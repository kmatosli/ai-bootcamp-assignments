# API Documentation
**Module 4 Capstone — API Explorer**
Caduceus Healthcare Equity Platform | Rhenman & Partners

---

## API 1: JSONPlaceholder

**Base URL:** `https://jsonplaceholder.typicode.com`
**Authentication:** None required
**Rate limits:** None observed

### Endpoints Tested

| Method | Path | Description | Response shape |
|---|---|---|---|
| GET | `/users` | All users | Array of user objects |
| GET | `/users/{id}` | Single user by ID | User object with address, company |
| GET | `/posts?userId={id}` | Posts filtered by user | Array of post objects |
| GET | `/posts/{id}/comments` | Comments on a post (nested resource) | Array of comment objects |
| POST | `/posts` | Create a new post (simulated) | Created post object with new ID |

### Example Response — GET `/users/1`
```json
{
  "id": 1,
  "name": "Leanne Graham",
  "username": "Bret",
  "email": "Sincere@april.biz",
  "address": {
    "street": "Kulas Light",
    "city": "Gwenborough"
  },
  "company": {
    "name": "Romaguera-Crona"
  }
}
```

### Observations
- POST requests return status 201 Created with a simulated ID of 101 — data is not actually persisted
- Nested resources work exactly as documented: `/posts/1/comments` returns all comments for post 1
- No pagination headers — all resources return full datasets
- One surprise: DELETE returns 200, not 204 — unusual since 204 No Content is the REST convention for deletes with no response body

---

## API 2: GitHub REST API

**Base URL:** `https://api.github.com`
**Authentication:** Optional Bearer token (`Authorization: Bearer ghp_...`)
**Rate limits:** 60 requests/hour unauthenticated | 5,000/hour authenticated

### Endpoints Tested

| Method | Path | Description | Response shape |
|---|---|---|---|
| GET | `/users/{username}` | Public user profile | User object with repo count, followers |
| GET | `/users/{username}/repos` | User's public repositories | Array of repo objects |
| GET | `/user` | Authenticated user's profile | 401 without auth |
| GET | `/repos/{owner}/{repo}` | Single repository details | Repo object |

### Example Response — GET `/users/google/repos?sort=stargazers&per_page=3`
```json
[
  {
    "name": "material-design-icons",
    "description": "Material Design icons by Google",
    "stargazers_count": 50000,
    "language": "JavaScript",
    "html_url": "https://github.com/google/material-design-icons"
  }
]
```

### Rate Limit Headers (returned on every response)
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 47
X-RateLimit-Reset: 1716912000
```

### Observations
- The `Accept: application/vnd.github+json` header is recommended by GitHub docs and should always be included
- Unauthenticated requests to `/user` return 401 — the server correctly distinguishes "who are you?" from "you're not allowed"
- `sort=stargazers` is not in the official docs for `/users/{username}/repos` (docs say `sort=created|updated|pushed|full_name`) but it works — undocumented but functional
- Private repos are invisible to unauthenticated requests — they simply don't appear in the list rather than returning 403
