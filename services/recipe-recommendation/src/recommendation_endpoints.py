from fastapi import APIRouter
from fastapi.responses import JSONResponse
from utils import get_user_profile, extract_keys, filter_recipes
from main import supabase, GOOGLE_GENAI_MODEL

router = APIRouter()

@router.post("/recipe/recommend_recipes")
def recommend_recipes(user_id: str):
    profile = get_user_profile(user_id)
    restrictions = extract_keys(profile.get("dietary_restrictions", {}))
    available_tools = extract_keys(profile.get("available_tools", {}))
    available_ingredients = extract_keys(profile.get("available_ingredients", {}))
    res = supabase.table("Recipe").select("*").execute()
    filtered = filter_recipes(res.data, restrictions, available_tools, available_ingredients)
    if not filtered:
        return JSONResponse(status_code=200, content={"message": "No recipes found. Search the internet?", "results": []})
    return {"results": filtered}

@router.post("/recipe/recommend_recipes_search")
def recommend_recipes_search(user_id: str):
    profile = get_user_profile(user_id)
    restrictions = extract_keys(profile.get("dietary_restrictions", {}))
    available_tools = extract_keys(profile.get("available_tools", {}))
    available_ingredients = extract_keys(profile.get("available_ingredients", {}))
    prompt = (
        f"Use a web search to find recipes that do not contain: {list(restrictions)}, "
        f"and can be made with tools: {list(available_tools)} and ingredients: {list(available_ingredients)}. "
        "Explicitly search the web for recipes. "
        "Return results as JSON with fields: name, description, ingredients, tools, instructions, estimated_price, estimated_time, image_url."
    )
    from google import genai
    from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
    client = genai.Client()
    model_id = GOOGLE_GENAI_MODEL
    google_search_tool = Tool(google_search=GoogleSearch())
    response = client.models.generate_content(
        model=model_id,
        contents=prompt,
        config=GenerateContentConfig(
            tools=[google_search_tool],
            response_modalities=["TEXT"],
        )
    )
    results = [each.text for each in response.candidates[0].content.parts]

    # Try to parse and store recipes to DB (bulk insert)
    import json
    stored = []
    recipes_to_store = []
    for text in results:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                recipes = [parsed]
            elif isinstance(parsed, list):
                recipes = parsed
            else:
                continue
            required = ["name", "description", "ingredients", "tools", "instructions", "estimated_price", "estimated_time", "image_url"]
            for recipe in recipes:
                if all(field in recipe for field in required):
                    recipes_to_store.append(recipe)
        except Exception:
            continue
    # Bulk insert if any
    if recipes_to_store:
        try:
            supabase.table("Recipe").insert(recipes_to_store).execute()
            stored = recipes_to_store
        except Exception:
            pass

    return {
        "results": results,
        "stored": stored,
        "grounding": getattr(getattr(response.candidates[0], "grounding_metadata", None), "search_entry_point", None) and getattr(response.candidates[0].grounding_metadata.search_entry_point, "rendered_content", None)
    }
