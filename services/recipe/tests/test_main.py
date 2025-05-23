import os
import sys
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Add src to sys.path for import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from recipe.main import app
from recipe.utils import get_user_profile
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

client = TestClient(app)

def dummy_profile_response(*args, **kwargs):
    class DummyResp:
        def raise_for_status(self):
            pass
        def json(self):
            return {
                "restrictions": ["peanut"],
                "tools": ["pan", "oven"],
                "ingredients": ["egg", "flour", "milk", "sugar"]
            }
    return DummyResp()

@pytest.fixture(autouse=True)
def patch_profile(monkeypatch):
    # Mock httpx.get to always return a dummy profile response
    monkeypatch.setattr("httpx.get", dummy_profile_response)

@pytest.fixture
def recipe_payload():
    return {
        "name": "Test Cake",
        "description": "A test recipe.",
        "ingredients": [
            {"name": "quinoa", "description": "a gluten-free grain high in protein and fiber."},
            {"name": "chickpeas", "description": "a legume used in salads, stews, and hummus."}
        ],
        "tools": [
            {"name": "oven", "description": "used for baking, roasting, and broiling foods."}
        ],
        "instructions": [
            "Mix ingredients. Combine all ingredients thoroughly.",
            "Bake. Place in oven and bake until done."
        ],
        "estimated_price": 10.5,
        "estimated_time": "30 min",
        "image_url": "http://example.com/cake.jpg"
    }

@pytest.fixture(autouse=True)
def cleanup_test_recipes():
    # Cleanup before and after each test
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Before: delete any leftover test data
    supabase.table("Recipe").delete().eq("name", "Test Cake").execute()
    supabase.table("Recipe").delete().eq("name", "Updated Cake").execute()
    yield
    # After: delete any test data created
    supabase.table("Recipe").delete().eq("name", "Test Cake").execute()
    supabase.table("Recipe").delete().eq("name", "Updated Cake").execute()

def test_create_recipe(recipe_payload):
    response = client.post("/recipe/", json=recipe_payload)
    assert response.status_code == 200
    data = response.json()
    for key in recipe_payload:
        assert key in data

def test_list_recipes():
    response = client.get("/recipe/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_recipe(recipe_payload):
    # Create first
    create_resp = client.post("/recipe/", json=recipe_payload)
    recipe_id = create_resp.json()["id"]
    response = client.get(f"/recipe/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["id"] == recipe_id

def test_update_recipe(recipe_payload):
    create_resp = client.post("/recipe/", json=recipe_payload)
    recipe_id = create_resp.json()["id"]
    update = {"name": "Updated Cake", "estimated_price": 12.0}
    response = client.put(f"/recipe/{recipe_id}", json=update)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Cake"

def test_delete_recipe(recipe_payload):
    create_resp = client.post("/recipe/", json=recipe_payload)
    recipe_id = create_resp.json()["id"]
    response = client.delete(f"/recipe/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Recipe deleted"

def test_recommend_recipes():
    # Insert a test recipe that should be recommended
    test_recipe = {
        "name": "Test Cake",
        "description": "A test recipe.",
        "ingredients": [
            {"name": "quinoa", "description": "a gluten-free grain high in protein and fiber."},
            {"name": "chickpeas", "description": "a legume used in salads, stews, and hummus."}
        ],
        "tools": [
            {"name": "oven", "description": "used for baking, roasting, and broiling foods."}
        ],
        "instructions": [
            "Mix ingredients. Combine all ingredients thoroughly.",
            "Bake. Place in oven and bake until done."
        ],
        "estimated_price": 10.5,
        "estimated_time": "30 min",
        "image_url": "http://example.com/cake.jpg"
    }
    client.post("/recipe/", json=test_recipe)
    response = client.post(
        "/recipe/recommend_recipes",
        headers={"X-User-uuid": os.getenv("SUPABASE_TEST_UUID")}
    )
    assert response.status_code == 200
    assert "results" in response.json()
    found = any(r["name"] == "Test Cake" for r in response.json()["results"])
    assert found
    # Check that filtering works with new profile structure
    for recipe in response.json()["results"]:
        for restricted in ["gluten", "lactose", "soy", "pork", "shellfish", "nuts"]:
            for ingredient in recipe["ingredients"]:
                assert restricted not in ingredient["name"]


def test_recommend_recipes_search_real():
    # Use real profile from Supabase with id=1
    response = client.post(
        "/recipe/recommend_recipes_search",
        headers={"X-User-uuid": os.getenv("SUPABASE_TEST_UUID")}
    )
    assert response.status_code == 200
    assert "results" in response.json()
    for recipe in response.json()["results"]:
        assert "name" in recipe
        assert isinstance(recipe["name"], str)
        assert "ingredients" in recipe
        assert isinstance(recipe["ingredients"], list)
        for ingredient in recipe["ingredients"]:
            assert isinstance(ingredient, dict)
            assert "name" in ingredient
            assert "description" in ingredient
        assert "tools" in recipe
        assert isinstance(recipe["tools"], list)
        for tool in recipe["tools"]:
            assert isinstance(tool, dict)
            assert "name" in tool
            assert "description" in tool
        assert "instructions" in recipe
        assert isinstance(recipe["instructions"], list)
        for instruction in recipe["instructions"]:
            assert isinstance(instruction, str)
        assert "estimated_price" in recipe
        assert isinstance(recipe["estimated_price"], (float, int))
        assert "estimated_time" in recipe
        assert isinstance(recipe["estimated_time"], str)
        assert "image_url" in recipe

def test_create_recipe_missing_required_field():
    # Should fail because 'name' is required
    payload = {
        "description": "No name field",
        "ingredients": [
            {"quinoa": "a gluten-free grain high in protein and fiber."},
            {"chickpeas": "a legume used in salads, stews, and hummus."}
        ],
        "tools": [
            {"oven": "used for baking, roasting, and broiling foods."}
        ],
        "instructions": [
            "Mix ingredients. Combine all ingredients thoroughly.",
            "Bake. Place in oven and bake until done."
        ],
        "estimated_price": 1.0,
        "estimated_time": "10 min",
        "image_url": "http://example.com/img.jpg"
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


def test_get_user_profile_not_found(monkeypatch):
    # Patch supabase.table to return no data
    class DummyRes:
        data = None
    class DummyTable:
        def select(self, *a, **k):
            return self
        def eq(self, *a, **k):
            return self
        def single(self):
            return self
        def execute(self):
            return DummyRes()
    from recipe.utils import supabase
    monkeypatch.setattr(supabase, "table", lambda name: DummyTable())
    with pytest.raises(Exception) as exc:
        get_user_profile("99999999")
    assert "User profile not found" in str(exc.value)


def test_get_user_profile_supabase_error(monkeypatch):
    class DummyTable:
        def select(self, *a, **k):
            return self
        def eq(self, *a, **k):
            return self
        def single(self):
            return self
        def execute(self):
            raise Exception({"message": "Simulated supabase error"})
    from recipe.utils import supabase
    monkeypatch.setattr(supabase, "table", lambda name: DummyTable())
    from recipe.utils import get_user_profile
    with pytest.raises(Exception) as exc:
        get_user_profile("99999999")
    assert "Simulated supabase error" in str(exc.value)

def test_recommend_recipes_no_match(monkeypatch):
    # Patch filter_recipes to always return an empty list
    from recipe import recommendation_endpoints
    monkeypatch.setattr(recommendation_endpoints, "filter_recipes", lambda *a, **k: [])
    response = client.post(
        "/recipe/recommend_recipes",
        headers={"X-User-uuid": os.getenv("SUPABASE_TEST_UUID")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["results"] == []
    assert "message" in data
    assert data["message"].startswith("No recipes found")
