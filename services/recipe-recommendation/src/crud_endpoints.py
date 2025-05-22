from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from models import Recipe, RecipeUpdate
from utils import supabase, get_user_profile, extract_keys, filter_recipes

from typing import List

router = APIRouter()

@router.post("/recipe/", response_model=Recipe)
def create_recipe(recipe: Recipe):
    data = recipe.model_dump(exclude_unset=True)
    try:
        res = supabase.table("Recipe").insert(data).execute()
        if not res.data or (isinstance(res.data, list) and len(res.data) == 0):
            raise HTTPException(status_code=400, detail="Failed to create recipe")
        return res.data[0]
    except Exception as e:
        detail = getattr(e, 'message', str(e))
        if hasattr(e, 'args') and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get('message', str(e))
        raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")

@router.get("/recipe/", response_model=List[Recipe])
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

@router.get("/recipe/{recipe_id}", response_model=Recipe)
def get_recipe(recipe_id: int):
    try:
        res = supabase.table("Recipe").select("*").eq("id", recipe_id).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Recipe not found")
        return res.data
    except Exception as e:
        err_msg = str(getattr(e, 'args', [''])[0])
        if 'PGRST116' in err_msg or 'no rows' in err_msg or 'multiple (or no) rows returned' in err_msg:
            raise HTTPException(status_code=404, detail="Recipe not found")
        detail = getattr(e, 'message', str(e))
        if hasattr(e, 'args') and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get('message', str(e))
        raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")

@router.put("/recipe/{recipe_id}", response_model=Recipe)
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

@router.delete("/recipe/{recipe_id}")
def delete_recipe(recipe_id: int):
    try:
        res = supabase.table("Recipe").delete().eq("id", recipe_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Recipe not found")
        return {"message": "Recipe deleted"}
    except HTTPException:
        raise
    except Exception as e:
        detail = getattr(e, 'message', str(e))
        if hasattr(e, 'args') and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get('message', str(e))
        raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")
