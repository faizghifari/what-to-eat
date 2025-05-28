import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from recipe.main import app
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

client = TestClient(app)


@pytest.fixture
def recipe_payload():
    return {
        "name": "Test Cake",
        "description": "A test recipe.",
        "ingredients": [
            {
                "name": "quinoa",
                "description": "a gluten-free grain high in protein and fiber.",
            },
            {
                "name": "chickpeas",
                "description": "a legume used in salads, stews, and hummus.",
            },
        ],
        "tools": [
            {
                "name": "oven",
                "description": "used for baking, roasting, and broiling foods.",
            }
        ],
        "instructions": [
            "Mix ingredients. Combine all ingredients thoroughly.",
            "Bake. Place in oven and bake until done.",
        ],
        "estimated_price": 10.5,
        "estimated_time": "30 min",
        "image_url": "http://example.com/cake.jpg",
    }


@pytest.fixture(autouse=True)
def cleanup_test_recipes():
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    for name in [
        "Test Cake",
        "Updated Cake",
        "Test Cake For Rating",
        "Test Cake For Rating List",
        "Test Cake For My Rating",
        "Test Cake For Update Rating",
        "Test Cake For Delete Rating",
    ]:
        recipes = (
            supabase.table("Recipe").select("id").eq("name", name).execute().data or []
        )
        for recipe in recipes:
            supabase.table("Rating").delete().eq("recipe", recipe["id"]).execute()
        supabase.table("Recipe").delete().eq("name", name).execute()
    yield
    for name in [
        "Test Cake",
        "Updated Cake",
        "Test Cake For Rating",
        "Test Cake For Rating List",
        "Test Cake For My Rating",
        "Test Cake For Update Rating",
        "Test Cake For Delete Rating",
    ]:
        recipes = (
            supabase.table("Recipe").select("id").eq("name", name).execute().data or []
        )
        for recipe in recipes:
            supabase.table("Rating").delete().eq("recipe", recipe["id"]).execute()
        supabase.table("Recipe").delete().eq("name", name).execute()


def test_create_recipe(recipe_payload):
    response = client.post("/recipe/", json=recipe_payload)
    assert response.status_code == 200
    data = response.json()
    for key in recipe_payload:
        assert key in data
    assert "average_rating" in data
    assert data["average_rating"] is None


def test_list_recipes():
    response = client.get("/recipe/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    for recipe in response.json():
        assert "average_rating" in recipe


def test_get_recipe(recipe_payload):
    create_resp = client.post("/recipe/", json=recipe_payload)
    recipe_id = create_resp.json()["id"]
    response = client.get(f"/recipe/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["id"] == recipe_id
    assert "average_rating" in response.json()


def test_update_recipe(recipe_payload):
    create_resp = client.post("/recipe/", json=recipe_payload)
    recipe_id = create_resp.json()["id"]
    update = {"name": "Updated Cake", "estimated_price": 12.0}
    response = client.put(f"/recipe/{recipe_id}", json=update)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Cake"
    assert "average_rating" in response.json()


def test_delete_recipe(recipe_payload):
    create_resp = client.post("/recipe/", json=recipe_payload)
    recipe_id = create_resp.json()["id"]
    response = client.delete(f"/recipe/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Recipe deleted"


def test_create_recipe_missing_required_field():
    payload = {
        "description": "No name field",
        "ingredients": [
            {
                "name": "quinoa",
                "description": "a gluten-free grain high in protein and fiber.",
            },
            {
                "name": "chickpeas",
                "description": "a legume used in salads, stews, and hummus.",
            },
        ],
        "tools": [
            {
                "name": "oven",
                "description": "used for baking, roasting, and broiling foods.",
            }
        ],
        "instructions": [
            "Mix ingredients. Combine all ingredients thoroughly.",
            "Bake. Place in oven and bake until done.",
        ],
        "estimated_price": 1.0,
        "estimated_time": "10 min",
        "image_url": "http://example.com/img.jpg",
    }
    response = client.post("/recipe/", json=payload)
    assert response.status_code == 422


def test_get_recipe_not_found():
    response = client.get("/recipe/99999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe not found"


def test_delete_recipe_not_found():
    response = client.delete("/recipe/99999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe not found"
