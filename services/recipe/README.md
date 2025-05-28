# Recipe Recommendation Service

This service provides recipe recommendations and recipe CRUD operations. It is implemented using FastAPI (Python) for high performance and async support. The service integrates with Supabase for data storage and Google GenAI for advanced recipe search.

## Endpoints

- **CRUD for `Recipe` table**: Create, read, update, and delete recipes. All recipe endpoints return a new field `average_rating` (the average of all ratings for that recipe) in their response.
- **CRUD for `Rating` table**: Users can rate recipes (create, read, update, delete their rating) with fields: rating_value, comment_text, recipe_id, and user_id (from X-User-uuid header).
- **GET `/recipe/`**: List all recipes, each with `average_rating`.
- **GET `/recipe/{recipe_id}`**: Get a recipe by ID, including `average_rating`.
- **POST `/recipe/`**: Create a recipe, response includes `average_rating` (null if no ratings yet).
- **PUT `/recipe/{recipe_id}`**: Update a recipe, response includes `average_rating`.
- **DELETE `/recipe/{recipe_id}`**: Delete a recipe.
- **POST `/recipe/matches`**: Recommend recipes based on user profile (dietary preferences, restrictions, available tools/ingredients). Requires `X-User-uuid` header. Each result includes `average_rating`.
- **POST `/recipe/matches_web`**: Recommend recipes using Google GenAI with Google Search if no local match is found. Requires `X-User-uuid` header. Each result includes `average_rating`.

## Getting Started

1. Create a Python virtual environment (optional but recommended):
   ```cmd
   python -m venv venv
   ```
   Then, activate the virtual environment.
2. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```
3. Set up environment variables for Supabase and Google GenAI credentials (see `.env` or your deployment environment):
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_TEST_UUID` (sample user uuid for testing)
   - `GOOGLE_API_KEY` (for Google Gemini/GenAI)
   - `GOOGLE_GENAI_MODEL` (optional, default: `gemini-2.0-flash`)
4. Run the service:
   ```cmd
   uvicorn src.main:app --reload
   ```

## API Overview

- All endpoints are prefixed with `/recipe`.
- All endpoints expect and return JSON.
- All recipe endpoints return an `average_rating` field in the response.
- See `API_CONTRACT.md` for detailed API contract, error handling, and example payloads.
- See the "Recipe Rating Endpoints" section for how to rate recipes (add, update, delete, and list ratings).

## Error Handling

- All errors return a JSON object with a `detail` field describing the error.
- Validation errors return HTTP 422.
- Not found errors return HTTP 404.
- Supabase or internal errors return HTTP 400 or 502 as appropriate.

## Testing

- Run tests with pytest:
  ```cmd
  pytest --cov=src
  ```
- Tests cover all CRUD endpoints and recommendation logic, including error cases.

## Notes

- See `src/main.py` for FastAPI app setup.
- See `src/crud_endpoints.py` and `src/recommendation_endpoints.py` for endpoint implementations.
- Recipes and user profiles are stored in Supabase tables `Recipe` and `Profile`.
- Google GenAI is used for advanced recipe search if no local match is found.
