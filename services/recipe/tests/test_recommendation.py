import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from recipe.main import app

client = TestClient(app)


def test_recommend_recipes():
    test_recipe = {
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
    client.post("/recipe/", json=test_recipe)
    response = client.get(
        "/recipe/matches", headers={"X-User-uuid": os.getenv("SUPABASE_TEST_UUID")}
    )
    assert response.status_code == 200
    assert "results" in response.json()
    found = any(r["name"] == "Test Cake" for r in response.json()["results"])
    assert found
    for recipe in response.json()["results"]:
        assert "average_rating" in recipe
        for restricted in ["gluten", "lactose", "soy", "pork", "shellfish", "nuts"]:
            for ingredient in recipe["ingredients"]:
                assert restricted not in ingredient["name"]


def test_recommend_recipes_search_real():
    response = client.get(
        "/recipe/matches_web", headers={"X-User-uuid": os.getenv("SUPABASE_TEST_UUID")}
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
        assert "average_rating" in recipe


def test_recommend_recipes_no_match(monkeypatch):
    from recipe import recommendation_endpoints

    monkeypatch.setattr(recommendation_endpoints, "filter_recipes", lambda *a, **k: [])
    response = client.get(
        "/recipe/matches", headers={"X-User-uuid": os.getenv("SUPABASE_TEST_UUID")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["results"] == []
    assert "message" in data
    assert data["message"].startswith("No recipes found")
