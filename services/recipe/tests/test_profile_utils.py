import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from recipe.main import app
from recipe.utils import get_user_profile
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

client = TestClient(app)


def test_get_user_profile_not_found(monkeypatch):
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
