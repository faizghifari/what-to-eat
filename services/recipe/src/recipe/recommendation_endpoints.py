import json

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from recipe.utils import supabase, get_user_profile, extract_names, filter_recipes, GOOGLE_GENAI_MODEL
from recipe.models import Recipe

router = APIRouter()

@router.post("/recipe/recommend_recipes")
def recommend_recipes(x_user_uuid: str = Header(..., alias="X-User-uuid")):
    profile = get_user_profile(x_user_uuid)
    restrictions = extract_names(profile.get("dietary_restrictions", {}))
    available_tools = extract_names(profile.get("available_tools", {}))
    available_ingredients = extract_names(profile.get("available_ingredients", {}))
    res = supabase.table("Recipe").select("*").execute()
    filtered = filter_recipes(res.data, restrictions, available_tools, available_ingredients)
    if not filtered:
        return JSONResponse(status_code=200, content={"message": "No recipes found. Search the internet?", "results": []})
    return {"results": filtered}

@router.post("/recipe/recommend_recipes_search")
def recommend_recipes_search(x_user_uuid: str = Header(..., alias="X-User-uuid")):
    profile = get_user_profile(x_user_uuid)
    restrictions = extract_names(profile.get("dietary_restrictions", {}))
    available_tools = extract_names(profile.get("available_tools", {}))
    available_ingredients = extract_names(profile.get("available_ingredients", {}))
    prompt = (
        f"Use a web search to find recipes that do not contain: {list(restrictions)}, "
        f"and can be made with tools: {list(available_tools)} and ingredients: {list(available_ingredients)}. "
        "Explicitly search the web for recipes, the more the better. "
        "For each recipe, try to find the following fields: "
        "name, description, ingredients, tools, instructions, estimated_price, estimated_time, image_url. "
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
    recipes = "".join(part.text for part in response.candidates[0].content.parts)
    
    prompt_parts = (
        "Given this web search result, extract the recipes in JSON format:\n"
        f"{recipes}\n"
        "Return results as JSON according to the schema. "
    )
    response = client.models.generate_content(
        model=model_id,
        contents=prompt_parts,
        config={
            'response_mime_type': 'application/json',
            'response_schema': list[Recipe]
        }
    )
    try:
        recipes_to_store = json.loads(response.candidates[0].content.parts[0].text)
    except Exception:
        from json import JSONDecodeError
        raise JSONDecodeError("Failed to parse JSON", text, 0)
    
    if recipes_to_store:
        try:
            stored = supabase.table("Recipe").insert(recipes_to_store).execute()
            if not stored.data or (isinstance(stored.data, list) and len(stored.data) == 0):
                raise HTTPException(status_code=400, detail="Failed to create gathered recipes")
            return {
                "results": stored.data,
            }
        except Exception as e:
            detail = getattr(e, 'message', str(e))
            if hasattr(e, 'args') and e.args and isinstance(e.args[0], dict):
                err = e.args[0]
                detail = err.get('message', str(e))
            raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")
    else:
        return JSONResponse(status_code=200, content={"message": "No matched recipes found from the internet", "results": []})
