# Recipe Recommendation Service API Contract

This document describes the REST API contract for the Recipe Recommendation Service. All endpoints are prefixed with `/recipe`.

---

## Recipe Model

| Field           | Type   | Description                                  |
| --------------- | ------ | -------------------------------------------- |
| id              | int    | Recipe ID (auto-generated)                   |
| name            | string | Name of the recipe                           |
| description     | string | Description of the recipe                    |
| ingredients     | array  | List of ingredient objects                   |
| tools           | array  | List of tool objects                         |
| instructions    | array  | List of instructions (JSON array of strings) |
| estimated_price | string | Estimated price (e.g. '10.000-15.000')       |
| estimated_time  | string | Estimated time (e.g. '30 min')               |
| image_url       | string | Image URL                                    |

- `ingredients` and `tools` are arrays of objects, e.g.:
  ```json
  [{ "egg": "A large egg" }, { "flour": "All-purpose flour" }]
  ```
- `instructions` is an array of strings, e.g.:
  ```json
  ["Mix ingredients.", "Bake at 180C for 30 minutes."]
  ```

---

## Endpoints

### 1. Create Recipe

- **POST** `/recipe/`
- **Request Body:**

```json
{
  "name": "string",
  "description": "string",
  "ingredients": [ { "ingredient": "desc" }, ... ],
  "tools": [ { "tool": "desc" }, ... ],
  "instructions": [ "step 1", "step 2" ],
  "estimated_price": "10.000-15.000",
  "estimated_time": "string",
  "image_url": "string"
}
```

- **Response:**
  - Code: `200 OK`

```json
{
  "id": 1,
  "name": "string",
  "description": "string",
  "ingredients": [{ "ingredient": "desc" }],
  "tools": [{ "tool": "desc" }],
  "instructions": ["step 1", "step 2"],
  "estimated_price": "10.000-15.000",
  "estimated_time": "string",
  "image_url": "string"
}
```

- **400 Response:**
  - Code: `400 Bad Request`

```json
{ "detail": "<error message>" }
```

- **422 Response:**
  - Code: `422 Unprocessable Entity` (validation error)

---

### 2. List Recipes

- **GET** `/recipe/`
- **Response:**
  - Code: `200 OK`

```json
[
  { ...Recipe },
  ...
]
```

---

### 3. Get Recipe by ID

- **GET** `/recipe/{recipe_id}`
- **Response:**
  - Code: `200 OK`

```json
{ ...Recipe }
```

- **404 Response:**
  - Code: `404 Not Found`

```json
{ "detail": "Recipe not found" }
```

---

### 4. Update Recipe

- **PUT** `/recipe/{recipe_id}`
- **Request Body:** (any subset of Recipe fields)
- **Response:**
  - Code: `200 OK`

```json
{ ...Recipe }
```

- **400 Response:**
  - Code: `400 Bad Request`

```json
{ "detail": "<error message>" }
```

---

### 5. Delete Recipe

- **DELETE** `/recipe/{recipe_id}`
- **Response:**
  - Code: `200 OK`

```json
{ "message": "Recipe deleted" }
```

- **404 Response:**
  - Code: `404 Not Found`

```json
{ "detail": "Recipe not found" }
```

---

### 6. Recommend Recipes

- **POST** `/recipe/recommend_recipes`
- **Query Parameter:**
  - `user_id` (string, required)
- **Response:**
  - Code: `200 OK`

```json
{
  "results": [ { ...Recipe }, ... ]
}
```

- **If no results:**
  - Code: `200 OK`

```json
{
  "message": "No recipes found. Search the internet?",
  "results": []
}
```

---

### 7. Recommend Recipes with Google GenAI

- **POST** `/recipe/recommend_recipes_search`
- **Query Parameter:**
  - `user_id` (string, required)
- **Response:**
  - Code: `200 OK`

```json
{
  "results": [ "string (LLM text response)", ... ],
  "stored": [ { ...Recipe }, ... ],
  "grounding": "string (web content)" // may be null
}
```

---

## Error Handling

- All errors return a JSON object with a `detail` field describing the error.
- Validation errors return HTTP 422.
- Not found errors return HTTP 404.
- Supabase or internal errors return HTTP 400 or 502 as appropriate.

---

## Notes

- All endpoints expect and return JSON.
- See tests in `tests/test_main.py` for example requests and responses.
