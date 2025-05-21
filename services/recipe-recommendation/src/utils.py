from fastapi import HTTPException
from main import supabase

def get_user_profile(user_id: str) -> dict:
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
