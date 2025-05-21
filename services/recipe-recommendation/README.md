# Menu Recommendation Service

This service provides menu recommendations and recipe CRUD operations. It is implemented using FastAPI (Python) for high performance and async support. The service integrates with Supabase for data storage and Google GenAI for advanced recipe search.

## Endpoints

- CRUD for `recipe` table (name, description, ingredients, tools, instructions, estimated_price, estimated_time, image_url)
- `POST /recipe/recommend_recipes`: Recommend recipes based on user profile (dietary preferences, restrictions, available tools/ingredients)
- `POST /recipe/recommend_recipes_search`: Recommend recipes using Google GenAI with Google Search if no local match

## Getting Started

1. Install dependencies:
   ```bash
   pip install fastapi uvicorn asyncpg supabase google-generativeai
   ```
2. Set up environment variables for Supabase and Google GenAI credentials.
3. Run the service:
   ```bash
   uvicorn src.main:app --reload
   ```

## Notes

- All endpoints are prefixed with `/recipe`.
- See `src/main.py` for implementation details.
