# Recipe Recommendation Service

This service provides recipe recommendations and recipe CRUD operations. It is implemented using FastAPI (Python) for high performance and async support. The service integrates with Supabase for data storage and Google GenAI for advanced recipe search.

## Endpoints

- **CRUD for `Recipe` table**: Create, read, update, and delete recipes with fields: name, description, ingredients, tools, instructions, estimated_price, estimated_time, image_url.
- **POST `/recipe/recommend_recipes`**: Recommend recipes based on user profile (dietary preferences, restrictions, available tools/ingredients).
- **POST `/recipe/recommend_recipes_search`**: Recommend recipes using Google GenAI with Google Search if no local match is found.

## Getting Started

1. Create a Python virtual environment (optional but recommended):
   ```cmd
   python -m venv venv
   ```
   Then, activate the virual environment.
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
- See `API_CONTRACT.md` for detailed API contract and example payloads.

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
