import os

from dotenv import load_dotenv

from supabase import create_client, Client
from fastapi import FastAPI, HTTPException

from models import (
    Location,
    Restaurant,
    Menu,
    CreateRestaurantRequest,
    CreateMenuRequest,
)


app = FastAPI()

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.get("/")
def hello_world():
    return {"Hello": "World"}


"""
Restaurant API
"""


@app.post("/restaurant", status_code=201)
def create_restaurant(body: CreateRestaurantRequest):
    # Check if restaurant already exists
    restaurant_exists = (
        supabase.table("Restaurant").select("*").eq("name", body.name).execute()
    ).data

    if restaurant_exists:
        raise HTTPException(status_code=409, detail="Restaurant already exists")

    new_location = body.location.model_dump()
    create_location_resp = supabase.table("Location").insert(new_location).execute()
    location = create_location_resp.data[0]

    new_restaurant = body.model_dump()
    new_restaurant["location"] = location["id"]
    restaurant = supabase.table("Restaurant").insert(new_restaurant).execute()
    restaurant = restaurant.data[0]
    restaurant["location"] = location

    return Restaurant(**restaurant)


@app.post("/restaurant/{restaurant_id}/menu", status_code=201)
def create_menu(restaurant_id: str, body: CreateMenuRequest):
    restaurant = (
        supabase.table("Restaurant").select("*").eq("id", restaurant_id).execute()
    )
    if not restaurant.data:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    new_menu = body.model_dump()
    new_menu["restaurant"] = restaurant.data[0]["id"]
    menu = supabase.table("Menu").insert(new_menu).execute()
    menu = menu.data[0]
    menu["restaurant"] = restaurant.data[0]

    return Menu(**menu)
