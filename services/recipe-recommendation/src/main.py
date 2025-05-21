from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Any
import os
from dotenv import load_dotenv
import httpx
from supabase import create_client, Client

# --- Environment Setup ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PROFILE_SERVICE_URL = os.getenv("PROFILE_SERVICE_URL", "http://profile:5004/profile/")
GOOGLE_GENAI_MODEL = os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.0-flash")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Recipe Recommendation Service")

# --- Models ---
class Recipe(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    ingredients: Any
    tools: Any
    instructions: Any
    estimated_price: float
    estimated_time: str
    image_url: str

# --- Utility Functions ---
def get_user_profile(user_id: str) -> dict:
    profile_url = f"{PROFILE_SERVICE_URL}{user_id}"
    try:
        resp = httpx.get(profile_url, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to fetch user profile")

def filter_recipes(recipes, restrictions, available_tools, available_ingredients):
    filtered = []
    for r in recipes:
        recipe_ingredients = set(r["ingredients"])
        recipe_tools = set(r["tools"])
        if restrictions & recipe_ingredients:
            continue
        if not recipe_tools <= available_tools:
            continue
        if not recipe_ingredients <= available_ingredients:
            continue
        filtered.append(r)
    return filtered

# --- CRUD Endpoints ---
@app.post("/recipe/", response_model=Recipe)
def create_recipe(recipe: Recipe):
    data = recipe.dict(exclude_unset=True)
    res = supabase.table("recipe").insert(data).execute()
    if res.error:
        raise HTTPException(status_code=400, detail=res.error.message)
    return res.data[0]

@app.get("/recipe/", response_model=List[Recipe])
def list_recipes():
    res = supabase.table("recipe").select("*").execute()
    return res.data

@app.get("/recipe/{recipe_id}", response_model=Recipe)
def get_recipe(recipe_id: int):
    res = supabase.table("recipe").select("*").eq("id", recipe_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return res.data

@app.put("/recipe/{recipe_id}", response_model=Recipe)
def update_recipe(recipe_id: int, recipe: Recipe):
    data = recipe.dict(exclude_unset=True)
    res = supabase.table("recipe").update(data).eq("id", recipe_id).execute()
    if res.error:
        raise HTTPException(status_code=400, detail=res.error.message)
    return res.data[0]

@app.delete("/recipe/{recipe_id}")
def delete_recipe(recipe_id: int):
    res = supabase.table("recipe").delete().eq("id", recipe_id).execute()
    if res.error:
        raise HTTPException(status_code=400, detail=res.error.message)
    return {"message": "Recipe deleted"}

# --- Recommendation Endpoints ---
@app.post("/recipe/recommend_recipes")
def recommend_recipes(user_id: str):
    profile = get_user_profile(user_id)
    restrictions = set(profile.get("restrictions", []))
    available_tools = set(profile.get("tools", []))
    available_ingredients = set(profile.get("ingredients", []))
    res = supabase.table("recipe").select("*").execute()
    filtered = filter_recipes(res.data, restrictions, available_tools, available_ingredients)
    if not filtered:
        return JSONResponse(status_code=200, content={"message": "No recipes found. Search the internet?", "results": []})
    return {"results": filtered}

@app.post("/recipe/recommend_recipes_search")
def recommend_recipes_search(user_id: str):
    profile = get_user_profile(user_id)
    restrictions = profile.get("restrictions", [])
    available_tools = profile.get("tools", [])
    available_ingredients = profile.get("ingredients", [])
    prompt = (
        f"Find recipes that do not contain: {restrictions}, "
        f"and can be made with tools: {available_tools} and ingredients: {available_ingredients}. "
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
            supabase.table("recipe").insert(recipes_to_store).execute()
            stored = recipes_to_store
        except Exception:
            pass

    return {
        "results": results,
        "stored": stored,
        "grounding": response.candidates[0].grounding_metadata.search_entry_point.rendered_content
    }
