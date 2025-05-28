import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from recipe.main import app

client = TestClient(app)


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
