import os
from dotenv import load_dotenv
from supabase import create_client, Client
from pydantic import BaseModel
from google import genai
import json

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

GOOGLE_GENAI_MODEL = os.environ.get("GOOGLE_GENAI_MODEL")
google_client = genai.Client()
model_id = GOOGLE_GENAI_MODEL


class NameDescPair(BaseModel):
    name: str
    description: str


def get_restaurant_id_by_name(restaurant_name):
    resp = (
        supabase.table("Restaurant").select("id").eq("name", restaurant_name).execute()
    )
    if resp.data:
        return resp.data[0]["id"]
    return None


def delete_menus_by_restaurant_id(restaurant_id):
    supabase.table("Menu").delete().eq("restaurant", restaurant_id).execute()


def insert_menus(restaurant_id, menus):
    payloads = []
    for menu in menus:
        payloads.append(
            {
                "restaurant": restaurant_id,
                "name": menu["menu_name"],
                "description": menu.get("description", ""),
                "main_ingredients": menu.get("main_ingredients", []),
                "price": menu["price"],
            }
        )
    try:
        response = supabase.table("Menu").insert(payloads).execute()
        return response
    except Exception as exception:
        return exception


def get_name_and_description_from_llm(menu_name):
    prompt = (
        f"Given the menu information, choose a menu name and description for a cafeteria menu, both in English.\n"
        f"For the name, avoid using unclear names such as 'Set Menu A', 'Menu 2', 'Today's Special', etc. Use short, concise, clear and descriptive names.\n"
        f"Reuse the the text in the menu information as much possible, and limit your own generated text.\n"
        f"Menu info: {menu_name}\n"
        "Return results as JSON according to the schema."
    )
    response = google_client.models.generate_content(
        model=model_id,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": NameDescPair,
        },
    )
    try:
        result = json.loads(response.candidates[0].content.parts[0].text)
        return result
    except Exception:
        from json import JSONDecodeError

        raise JSONDecodeError(
            "Failed to parse JSON", response.candidates[0].content.parts[0].text, 0
        )


def adjust_menus_with_llm(menus):
    adjusted = []
    for menu in menus:
        try:
            name_desc = get_name_and_description_from_llm(menu["menu_name"])
            menu["menu_name"] = name_desc["name"]
            menu["description"] = name_desc["description"]
        except Exception as e:
            print(f"LLM adjustment failed for {menu['menu_name']}: {e}")
        adjusted.append(menu)
    return adjusted
