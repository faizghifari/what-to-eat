# Recipe Recommendation Service API Contract

This document describes the REST API contract for the Recipe Recommendation Service. All endpoints are prefixed with `/recipe`.

---

## Recipe Model

| Field           | Type   | Description                       |
| --------------- | ------ | --------------------------------- |
| id              | int    | Recipe ID (auto-generated)        |
| name            | string | Name of the recipe                |
| description     | string | Description of the recipe         |
| ingredients     | array  | List of ingredients (JSON array)  |
| tools           | array  | List of tools (JSON array)        |
| instructions    | array  | List of instructions (JSON array) |
| estimated_price | float  | Estimated price                   |
| estimated_time  | string | Estimated time (e.g. '30 min')    |
| image_url       | string | Image URL                         |

---

## Endpoints

### 1. Create Recipe

- **POST** `/recipe/`
- **Request Body:**

```json
{
  "name": "string",
  "description": "string",
  "ingredients": ["string", ...],
  "tools": ["string", ...],
  "instructions": ["string", ...],
  "estimated_price": 0.0,
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
  "ingredients": ["string", ...],
  "tools": ["string", ...],
  "instructions": ["string", ...],
  "estimated_price": 0.0,
  "estimated_time": "string",
  "image_url": "string"
}
```

- **400 Response:**
  - Code: `400 Bad Request`

```json
{ "detail": "<error message>" }
```

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
- **Request Body:** (same as Create Recipe)
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

- **400 Response:**
  - Code: `400 Bad Request`

```json
{ "detail": "<error message>" }
```

---

### 6. Recommend Recipes

- **POST** `/recipe/recommend_recipes`
- **Request Body (query param):**
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
- **Request Body (query param):**
  - `user_id` (string, required)
- **Response:**
  - Code: `200 OK`

```json
{
  "results": [ "string (LLM text response)", ... ],
  "grounding": "string (web content)"
}
```
