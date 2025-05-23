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
| estimated_price | float  | Estimated price                              |
| estimated_time  | string | Estimated time (e.g. '30 min')               |
| image_url       | string | Image URL                                    |

- `ingredients` and `tools` are arrays of objects, e.g.:
  ```json
  [
    { "name": "egg", "description": "A large egg" },
    { "name": "flour", "description": "All-purpose flour" }
  ]
  ```
- `instructions` is an array of strings, e.g.:
  ```json
  ["Mix ingredients.", "Bake at 180C for 30 minutes."]
  ```

---

## Rating Model

| Field        | Type   | Description                       |
| ------------ | ------ | --------------------------------- |
| id           | int    | Rating ID (auto-generated)        |
| recipe       | int    | Recipe ID (foreign key)           |
| user         | string | User ID (from X-User-uuid header) |
| rating_value | int    | Rating value (e.g. 1-5)           |
| comment_text | string | User's comment on the recipe      |

---

## Endpoints

All endpoints expect and return JSON.

### 1. Create Recipe

- **POST** `/recipe/`
- **Request Body:**

```json
{
  "name": "string",
  "description": "string",
  "ingredients": [ { "name": "egg", "description": "A large egg" }, ... ],
  "tools": [ { "name": "pan", "description": "Non-stick pan" }, ... ],
  "instructions": [ "step 1", "step 2" ],
  "estimated_price": 10.5,
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
  "ingredients": [{ "name": "egg", "description": "A large egg" }],
  "tools": [{ "name": "pan", "description": "Non-stick pan" }],
  "instructions": ["step 1", "step 2"],
  "estimated_price": 10.5,
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

- **POST** `/recipe/matches`
- **Headers:**
  - `X-User-uuid` (string, required)
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

- **POST** `/recipe/matches_web`
- **Headers:**
  - `X-User-uuid` (string, required)
- **Response:**
  - Code: `200 OK`

```json
{
  "results": [ { ...Recipe }, ... ]
}
```

---

### 8. Recipe Rating Endpoints

#### Create Rating

- **POST** `/recipe/{recipe_id}/rate`
- **Headers:**
  - `X-User-uuid` (string, required)
- **Request Body:**

```json
{
  "rating_value": 5,
  "comment_text": "Delicious!"
}
```

- **Response:**
  - Code: `200 OK`

```json
{
  "id": 1,
  "recipe": 1,
  "user": "string",
  "rating_value": 5,
  "comment_text": "Delicious!"
}
```

- **400 Response:**

```json
{ "detail": "<error message>" }
```

- **422 Response:**
  - Code: `422 Unprocessable Entity` (validation error)

---

#### List Ratings for a Recipe

- **GET** `/recipe/{recipe_id}/rate`
- **Response:**
  - Code: `200 OK`

```json
[
  {
    "id": 1,
    "recipe": 1,
    "user": "string",
    "rating_value": 5,
    "comment_text": "Delicious!"
  },
  ...
]
```

---

#### Get Rating by User for a Recipe

- **GET** `/recipe/{recipe_id}/rate/me`
- **Headers:**
  - `X-User-uuid` (string, required)
- **Response:**
  - Code: `200 OK`

```json
{
  "id": 1,
  "recipe": 1,
  "user": "string",
  "rating_value": 5,
  "comment_text": "Delicious!"
}
```

- **404 Response:**

```json
{ "detail": "Rating not found" }
```

---

#### Update Rating by User for a Recipe

- **PUT** `/recipe/{recipe_id}/rate/me`
- **Headers:**
  - `X-User-uuid` (string, required)
- **Request Body:** (any subset of fields)

```json
{
  "rating_value": 4,
  "comment_text": "Pretty good!"
}
```

- **Response:**
  - Code: `200 OK`

```json
{
  "id": 1,
  "recipe": 1,
  "user": "string",
  "rating_value": 4,
  "comment_text": "Pretty good!"
}
```

- **404 Response:**

```json
{ "detail": "Rating not found" }
```

---

#### Delete Rating by User for a Recipe

- **DELETE** `/recipe/{recipe_id}/rate/me`
- **Headers:**
  - `X-User-uuid` (string, required)
- **Response:**
  - Code: `200 OK`

```json
{ "message": "Rating deleted" }
```

- **404 Response:**

```json
{ "detail": "Rating not found" }
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
