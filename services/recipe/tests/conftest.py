import pytest


def dummy_profile_response(*args, **kwargs):
    class DummyResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "dietary_restrictions": [{"name": "peanut", "description": "allergy"}],
                "available_tools": [
                    {"name": "pan", "description": "frying pan"},
                    {"name": "oven", "description": "baking oven"},
                ],
                "available_ingredients": [
                    {"name": "egg", "description": "chicken egg"},
                    {"name": "flour", "description": "wheat flour"},
                    {"name": "milk", "description": "dairy milk"},
                    {"name": "sugar", "description": "white sugar"},
                ],
            }

    return DummyResp()


@pytest.fixture(autouse=True)
def patch_profile(monkeypatch):
    monkeypatch.setattr("httpx.get", dummy_profile_response)
