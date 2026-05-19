# Design Critic: Evaluate API URIs
**Module 4 — REST API Fundamentals**
Caduceus Healthcare Equity Platform | Rhenman & Partners

---

## Part 1 — URI Evaluation

### `GET /getAllUsers`
**❌ Bad** — verb in the URI. REST uses HTTP methods as the verbs; the URI should name the resource only.
**✓ Corrected:** `GET /users`

---

### `POST /users`
**✅ Good** — correct HTTP verb (POST = create), plural noun, no verb in URI.

---

### `GET /user/5`
**❌ Bad** — singular noun. REST convention uses plural nouns for all resource names for consistency.
**✓ Corrected:** `GET /users/5`

---

### `DELETE /removeProduct?id=12`
**❌ Bad** — two problems: verb in the URI (`remove`), and the resource ID belongs in the path, not a query string. Query strings are for filtering, not identifying a specific resource.
**✓ Corrected:** `DELETE /products/12`

---

### `GET /products?category=electronics&sort=price`
**✅ Good** — correct use of query parameters for filtering and sorting. The resource is `products`, the query string narrows the result set. This is exactly the right pattern.

---

### `PUT /updateUser/5`
**❌ Bad** — verb in the URI. The HTTP method PUT already communicates "update". Repeating it in the path is redundant and violates REST conventions.
**✓ Corrected:** `PUT /users/5`

---

### `GET /users/5/orders`
**✅ Good** — clean nested resource. Reads naturally: "get the orders belonging to user 5." Two levels of nesting is acceptable and common.

---

### `GET /users/5/orders/10/items/3/reviews/1/replies`
**❌ Bad** — over-nested (5 levels deep). Deep nesting creates tight coupling, makes URLs fragile, and is hard to read and document. Replies have their own identity — they should be a top-level resource.
**✓ Corrected:** `GET /replies?review_id=1`
or, if replies are always accessed in context:
`GET /reviews/1/replies`
(flatten everything above that — access reviews directly by ID, not through the full parent chain)

---

## Part 2 — Recipe Manager API Design

**Domain:** Caduceus framing — recipes map to drug protocols, ingredients map to drug components, authors map to researchers.

### Resources
- `recipes` — the primary resource
- `ingredients` — belong to a recipe (one-to-many)
- `authors` — create recipes (one-to-many)

### Endpoints

| Method | URI | Description |
|---|---|---|
| GET | `/recipes` | List all recipes |
| GET | `/recipes/{id}` | Get a specific recipe |
| POST | `/recipes` | Create a new recipe |
| PUT | `/recipes/{id}` | Update a recipe (full replace) |
| PATCH | `/recipes/{id}` | Partially update a recipe |
| DELETE | `/recipes/{id}` | Delete a recipe |
| GET | `/recipes/{id}/ingredients` | Get all ingredients for a recipe |
| POST | `/recipes/{id}/ingredients` | Add an ingredient to a recipe |
| GET | `/recipes?cuisine={type}` | Filter recipes by cuisine type |
| GET | `/recipes?author_id={id}` | Get all recipes by a specific author |
| GET | `/authors` | List all authors |
| GET | `/authors/{id}` | Get a specific author |
| GET | `/authors/{id}/recipes` | All recipes by this author |

### Design decisions

**Why `GET /recipes?cuisine=italian` instead of `GET /recipes/cuisine/italian`?**
Cuisine is a filter on the collection, not a sub-resource. Query parameters are the correct mechanism for filtering. A path segment implies the cuisine itself is a resource you can GET, POST, DELETE — which it isn't.

**Why `GET /recipes?author_id=5` AND `GET /authors/5/recipes`?**
Both are valid and serve different use cases. The first is used when you already have a recipe list and want to filter. The second is used when you're navigating from an author's profile page to their recipes. Offering both is fine — they return the same data.

**Why PATCH in addition to PUT?**
PUT replaces the entire recipe (you send all fields). PATCH updates only the fields you send — useful for changing just the title without re-sending the full ingredient list.

**Why not `/recipes/{id}/author`?**
An author is their own resource — they exist independently of any recipe. Nesting would imply the author only exists in the context of that recipe. Use `GET /authors/{id}` instead, with `author_id` as a field on the recipe response.
