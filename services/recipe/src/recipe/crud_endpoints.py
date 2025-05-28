from fastapi import APIRouter, HTTPException, Header

from recipe.models import Recipe, RecipeUpdate, Rating, RatingCreate, RatingUpdate
from recipe.utils import supabase

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
        detail = getattr(e, "message", str(e))
        if hasattr(e, "args") and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get("message", str(e))
        raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")


@router.get("/recipe/", response_model=List[Recipe])
def list_recipes():
    try:
        res = supabase.table("Recipe").select("*").execute()
        if res.data is None:
            raise HTTPException(status_code=400, detail="Failed to list recipes")
        return res.data
    except Exception as e:
        detail = getattr(e, "message", str(e))
        if hasattr(e, "args") and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get("message", str(e))
        raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")


@router.get("/recipe/{recipe_id}", response_model=Recipe)
def get_recipe(recipe_id: int):
    try:
        res = (
            supabase.table("Recipe").select("*").eq("id", recipe_id).single().execute()
        )
        if not res.data:
            raise HTTPException(status_code=404, detail="Recipe not found")
        return res.data
    except Exception as e:
        err_msg = str(getattr(e, "args", [""])[0])
        if (
            "PGRST116" in err_msg
            or "no rows" in err_msg
            or "multiple (or no) rows returned" in err_msg
        ):
            raise HTTPException(status_code=404, detail="Recipe not found")
        detail = getattr(e, "message", str(e))
        if hasattr(e, "args") and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get("message", str(e))
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
        detail = getattr(e, "message", str(e))
        if hasattr(e, "args") and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get("message", str(e))
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
        detail = getattr(e, "message", str(e))
        if hasattr(e, "args") and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get("message", str(e))
        raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")


# --- Rating CRUD Endpoints ---


@router.post("/recipe/{recipe_id}/rate", response_model=Rating)
def create_rating(
    recipe_id: int,
    rating: RatingCreate,
    x_user_uuid: str = Header(..., alias="X-User-uuid"),
):
    data = {
        "recipe": recipe_id,
        "user": x_user_uuid,
        "rating_value": rating.rating_value,
        "comment_text": rating.comment_text,
    }
    try:
        res = supabase.table("Rating").insert(data).execute()
        if not res.data or (isinstance(res.data, list) and len(res.data) == 0):
            raise HTTPException(status_code=400, detail="Failed to create rating")
        return res.data[0]
    except Exception as e:
        detail = getattr(e, "message", str(e))
        if hasattr(e, "args") and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get("message", str(e))
        raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")


@router.get("/recipe/{recipe_id}/rate", response_model=List[Rating])
def list_ratings(recipe_id: int):
    try:
        res = supabase.table("Rating").select("*").eq("recipe", recipe_id).execute()
        return res.data or []
    except Exception as e:
        detail = getattr(e, "message", str(e))
        if hasattr(e, "args") and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get("message", str(e))
        raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")


@router.get("/recipe/{recipe_id}/rate/me", response_model=Rating)
def get_my_rating(recipe_id: int, x_user_uuid: str = Header(..., alias="X-User-uuid")):
    try:
        res = (
            supabase.table("Rating")
            .select("*")
            .eq("recipe", recipe_id)
            .eq("user", x_user_uuid)
            .single()
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=404, detail="Rating not found")
        return res.data
    except Exception as e:
        err_msg = str(getattr(e, "args", [""])[0])
        if (
            "PGRST116" in err_msg
            or "no rows" in err_msg
            or "multiple (or no) rows returned" in err_msg
        ):
            raise HTTPException(status_code=404, detail="Rating not found")
        detail = getattr(e, "message", str(e))
        if hasattr(e, "args") and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get("message", str(e))
        raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")


@router.put("/recipe/{recipe_id}/rate/me", response_model=Rating)
def update_my_rating(
    recipe_id: int,
    rating: RatingUpdate,
    x_user_uuid: str = Header(..., alias="X-User-uuid"),
):
    data = {
        k: v
        for k, v in rating.model_dump(exclude_unset=True).items()
        if k in ["rating_value", "comment_text"]
    }
    try:
        res = (
            supabase.table("Rating")
            .update(data)
            .eq("recipe", recipe_id)
            .eq("user", x_user_uuid)
            .execute()
        )
        if not res.data or (isinstance(res.data, list) and len(res.data) == 0):
            raise HTTPException(status_code=404, detail="Rating not found")
        return res.data[0]
    except Exception as e:
        detail = getattr(e, "message", str(e))
        if hasattr(e, "args") and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get("message", str(e))
        raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")


@router.delete("/recipe/{recipe_id}/rate/me")
def delete_my_rating(
    recipe_id: int, x_user_uuid: str = Header(..., alias="X-User-uuid")
):
    try:
        res = (
            supabase.table("Rating")
            .delete()
            .eq("recipe", recipe_id)
            .eq("user", x_user_uuid)
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=404, detail="Rating not found")
        return {"message": "Rating deleted"}
    except HTTPException:
        raise
    except Exception as e:
        detail = getattr(e, "message", str(e))
        if hasattr(e, "args") and e.args and isinstance(e.args[0], dict):
            err = e.args[0]
            detail = err.get("message", str(e))
        raise HTTPException(status_code=400, detail=f"Supabase error: {detail}")
