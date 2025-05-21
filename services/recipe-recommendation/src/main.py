from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Any
import os
from dotenv import load_dotenv
import httpx
from supabase import create_client, Client

# --- Environment Setup ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
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

class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[Any] = None
    tools: Optional[Any] = None
    instructions: Optional[Any] = None
    estimated_price: Optional[float] = None
    estimated_time: Optional[str] = None
    image_url: Optional[str] = None

# --- Utility Functions ---
def get_user_profile(user_id: str) -> dict:
    # Fetch user profile directly from Supabase DB
    try:
        res = supabase.table("Profile").select("*").eq("id", user_id).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="User profile not found")
        return res.data
    except Exception as e:
        detail = getattr(e, 'message', str(e))
        if hasattr(e, 'args') and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get('message', str(e))
        raise HTTPException(status_code=502, detail=f"Failed to fetch user profile: {detail}")

def extract_keys(json_obj):
    if isinstance(json_obj, dict):
        return set(json_obj.keys())
    return set(json_obj or [])

def filter_recipes(recipes, restrictions, available_tools, available_ingredients):
    filtered = []
    for r in recipes:
        # Flatten list of dicts to set of keys for ingredients and tools
        recipe_ingredients = set()
        for item in r["ingredients"]:
            if isinstance(item, dict):
                recipe_ingredients.update(item.keys())
            else:
                recipe_ingredients.add(str(item))
        recipe_tools = set()
        for item in r["tools"]:
            if isinstance(item, dict):
                recipe_tools.update(item.keys())
            else:
                recipe_tools.add(str(item))
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
    data = recipe.model_dump(exclude_unset=True)
    try:
        res = supabase.table("Recipe").insert(data).execute()
        if not res.data or (isinstance(res.data, list) and len(res.data) == 0):
            raise HTTPException(status_code=400, detail="Failed to create recipe")
        return res.data[0]
    except Exception as e:
        detail = getattr(e, 'message', str(e))
        # Try to extract supabase error message if present
        if hasattr(e, 'args') and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get('message', str(e))
        raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")

@app.get("/recipe/", response_model=List[Recipe])
def list_recipes():
    try:
        res = supabase.table("Recipe").select("*").execute()
        if res.data is None:
            raise HTTPException(status_code=400, detail="Failed to list recipes")
        return res.data
    except Exception as e:
        detail = getattr(e, 'message', str(e))
        if hasattr(e, 'args') and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get('message', str(e))
        raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")

@app.get("/recipe/{recipe_id}", response_model=Recipe)
def get_recipe(recipe_id: int):
    try:
        res = supabase.table("Recipe").select("*").eq("id", recipe_id).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Recipe not found")
        return res.data
    except Exception as e:
        # Check for Supabase 'no rows' error
        err_msg = str(getattr(e, 'args', [''])[0])
        if 'PGRST116' in err_msg or 'no rows' in err_msg or 'multiple (or no) rows returned' in err_msg:
            raise HTTPException(status_code=404, detail="Recipe not found")
        detail = getattr(e, 'message', str(e))
        if hasattr(e, 'args') and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get('message', str(e))
        raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")

@app.put("/recipe/{recipe_id}", response_model=Recipe)
def update_recipe(recipe_id: int, recipe: RecipeUpdate):
    data = recipe.model_dump(exclude_unset=True)
    try:
        res = supabase.table("Recipe").update(data).eq("id", recipe_id).execute()
        if not res.data or (isinstance(res.data, list) and len(res.data) == 0):
            raise HTTPException(status_code=400, detail="Failed to update recipe")
        return res.data[0]
    except Exception as e:
        detail = getattr(e, 'message', str(e))
        if hasattr(e, 'args') and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get('message', str(e))
        raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")

@app.delete("/recipe/{recipe_id}")
def delete_recipe(recipe_id: int):
    try:
        res = supabase.table("Recipe").delete().eq("id", recipe_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Recipe not found")
        return {"message": "Recipe deleted"}
    except HTTPException:
        raise  # Re-raise HTTPException as is
    except Exception as e:
        detail = getattr(e, 'message', str(e))
        if hasattr(e, 'args') and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get('message', str(e))
        raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")

# --- Recommendation Endpoints ---
@app.post("/recipe/recommend_recipes")
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

@app.post("/recipe/recommend_recipes_search")
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
