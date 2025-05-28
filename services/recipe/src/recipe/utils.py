import os

from fastapi import HTTPException
from supabase import create_client, Client

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_GENAI_MODEL = os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.0-flash")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_user_profile(user_id: str) -> dict:
    try:
        res = (
            supabase.table("Profile").select("*").eq("user", user_id).single().execute()
        )
        if not res.data:
            raise HTTPException(status_code=404, detail="User profile not found")
        return res.data
    except Exception as e:
        detail = getattr(e, "message", str(e))
        if hasattr(e, "args") and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get("message", str(e))
        raise HTTPException(
            status_code=502, detail=f"Failed to fetch user profile: {detail}"
        )


def extract_names(params):
    return {item["name"] for item in params if "name" in item}


def filter_recipes(recipes, restrictions, available_tools, available_ingredients):
    filtered = []
    for r in recipes:
        recipe_ingredients = extract_names(r["ingredients"])
        recipe_tools = extract_names(r["tools"])
        if restrictions & recipe_ingredients:
            continue
        if not recipe_tools <= available_tools:
            continue
        if not recipe_ingredients <= available_ingredients:
            continue
        filtered.append(r)
    return filtered
