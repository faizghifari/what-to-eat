import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from recipe.main import app

client = TestClient(app)


def test_create_rating():
    recipe_payload = {
        "name": "Test Cake For Rating",
        "description": "A test recipe for rating.",
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
    create_resp = client.post("/recipe/", json=recipe_payload)
    recipe_id = create_resp.json()["id"]
    rating_payload = {"rating_value": 5, "comment_text": "Amazing!"}
    response = client.post(
        f"/recipe/{recipe_id}/rate",
        json=rating_payload,
        headers={"X-User-uuid": os.getenv("SUPABASE_TEST_UUID")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rating_value"] == 5
    assert data["comment_text"] == "Amazing!"
    assert data["recipe"] == recipe_id
    assert data["user"] == os.getenv("SUPABASE_TEST_UUID")


def test_list_ratings():
    recipe_payload = {
        "name": "Test Cake For Rating List",
        "description": "A test recipe for rating list.",
        "ingredients": [
            {
                "name": "quinoa",
                "description": "a gluten-free grain high in protein and fiber.",
            }
        ],
        "tools": [
            {
                "name": "oven",
                "description": "used for baking, roasting, and broiling foods.",
            }
        ],
        "instructions": ["Mix ingredients.", "Bake."],
        "estimated_price": 10.5,
        "estimated_time": "30 min",
        "image_url": "http://example.com/cake.jpg",
    }
    create_resp = client.post("/recipe/", json=recipe_payload)
    recipe_id = create_resp.json()["id"]
    rating_payload = {"rating_value": 4, "comment_text": "Pretty good!"}
    client.post(
        f"/recipe/{recipe_id}/rate",
        json=rating_payload,
        headers={"X-User-uuid": os.getenv("SUPABASE_TEST_UUID")},
    )
    response = client.get(f"/recipe/{recipe_id}/rate")
    assert response.status_code == 200
    ratings = response.json()
    assert isinstance(ratings, list)
    assert any(r["comment_text"] == "Pretty good!" for r in ratings)


def test_get_my_rating():
    recipe_payload = {
        "name": "Test Cake For My Rating",
        "description": "A test recipe for my rating.",
        "ingredients": [
            {
                "name": "quinoa",
                "description": "a gluten-free grain high in protein and fiber.",
            }
        ],
        "tools": [
            {
                "name": "oven",
                "description": "used for baking, roasting, and broiling foods.",
            }
        ],
        "instructions": ["Mix ingredients.", "Bake."],
        "estimated_price": 10.5,
        "estimated_time": "30 min",
        "image_url": "http://example.com/cake.jpg",
    }
    create_resp = client.post("/recipe/", json=recipe_payload)
    recipe_id = create_resp.json()["id"]
    rating_payload = {"rating_value": 3, "comment_text": "It was ok."}
    client.post(
        f"/recipe/{recipe_id}/rate",
        json=rating_payload,
        headers={"X-User-uuid": os.getenv("SUPABASE_TEST_UUID")},
    )
    response = client.get(
        f"/recipe/{recipe_id}/rate/me",
        headers={"X-User-uuid": os.getenv("SUPABASE_TEST_UUID")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rating_value"] == 3
    assert data["comment_text"] == "It was ok."
    assert data["user"] == os.getenv("SUPABASE_TEST_UUID")


def test_update_my_rating():
    recipe_payload = {
        "name": "Test Cake For Update Rating",
        "description": "A test recipe for update rating.",
        "ingredients": [
            {
                "name": "quinoa",
                "description": "a gluten-free grain high in protein and fiber.",
            }
        ],
        "tools": [
            {
                "name": "oven",
                "description": "used for baking, roasting, and broiling foods.",
            }
        ],
        "instructions": ["Mix ingredients.", "Bake."],
        "estimated_price": 10.5,
        "estimated_time": "30 min",
        "image_url": "http://example.com/cake.jpg",
    }
    create_resp = client.post("/recipe/", json=recipe_payload)
    recipe_id = create_resp.json()["id"]
    rating_payload = {"rating_value": 2, "comment_text": "Not great."}
    client.post(
        f"/recipe/{recipe_id}/rate",
        json=rating_payload,
        headers={"X-User-uuid": os.getenv("SUPABASE_TEST_UUID")},
    )
    update_payload = {"rating_value": 4, "comment_text": "Improved!"}
    response = client.put(
        f"/recipe/{recipe_id}/rate/me",
        json=update_payload,
        headers={"X-User-uuid": os.getenv("SUPABASE_TEST_UUID")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rating_value"] == 4
    assert data["comment_text"] == "Improved!"


def test_delete_my_rating():
    recipe_payload = {
        "name": "Test Cake For Delete Rating",
        "description": "A test recipe for delete rating.",
        "ingredients": [
            {
                "name": "quinoa",
                "description": "a gluten-free grain high in protein and fiber.",
            }
        ],
        "tools": [
            {
                "name": "oven",
                "description": "used for baking, roasting, and broiling foods.",
            }
        ],
        "instructions": ["Mix ingredients.", "Bake."],
        "estimated_price": 10.5,
        "estimated_time": "30 min",
        "image_url": "http://example.com/cake.jpg",
    }
    create_resp = client.post("/recipe/", json=recipe_payload)
    recipe_id = create_resp.json()["id"]
    rating_payload = {"rating_value": 1, "comment_text": "Terrible."}
    client.post(
        f"/recipe/{recipe_id}/rate",
        json=rating_payload,
        headers={"X-User-uuid": os.getenv("SUPABASE_TEST_UUID")},
    )
    response = client.delete(
        f"/recipe/{recipe_id}/rate/me",
        headers={"X-User-uuid": os.getenv("SUPABASE_TEST_UUID")},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Rating deleted"
    response = client.get(
        f"/recipe/{recipe_id}/rate/me",
        headers={"X-User-uuid": os.getenv("SUPABASE_TEST_UUID")},
    )
    assert response.status_code == 404
