import os

import base64
import uuid
from dotenv import load_dotenv

from supabase import create_client, Client
from fastapi import FastAPI, HTTPException, Query, Header

from typing import (
    Annotated,
)

from utils import calculate_distance

from models import (
    Location,
    Restaurant,
    Menu,
    Rating,
    MenuFilter,
    CreateRestaurantRequest,
    CreateMenuRequest,
    CreateRatingRequest,
    MenuResponse,
    RestaurantMenuResponse,
)


app = FastAPI()

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

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

    # Decode base64 image and upload to supabase storage
    if body.image is not None:
        header, base64_image = body.image.split(",", 1)

        image = base64.b64decode(base64_image)
        mime_type = header.split(";")[0].split(":")[1]
        image_type = mime_type.split("/")[1]
        if image_type == "jpeg":
            image_type = "jpg"
        elif image_type == "svg+xml":
            image_type = "svg"

        image_path = supabase.storage.from_("media").upload(
            f"restaurant/{uuid.uuid4()}.{image_type}",
            image,
            {"content-type": mime_type},
        )
        image_url = supabase.storage.from_("media").get_public_url(image_path.path)

    # Create location
    new_location = body.location.model_dump()
    create_location_resp = supabase.table("Location").insert(new_location).execute()
    location = create_location_resp.data[0]

    # create restaurant
    new_restaurant = body.model_dump()
    new_restaurant["location"] = location["id"]
    new_restaurant["image_url"] = image_url if body.image is not None else None
    del new_restaurant["image"]

    restaurant = supabase.table("Restaurant").insert(new_restaurant).execute()
    restaurant = restaurant.data[0]
    restaurant["location"] = location

    return Restaurant(**restaurant)


@app.delete("/restaurant/{restaurant_id}", status_code=204)
def delete_restaurant(restaurant_id: str):
    # Check if restaurant exists
    restaurant = (
        supabase.table("Restaurant").select("*").eq("id", restaurant_id).execute()
    ).data
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Delete restaurant
    supabase.table("Restaurant").delete().eq("id", restaurant_id).execute()

    # Delete location
    location_id = restaurant[0]["location"]
    supabase.table("Location").delete().eq("id", location_id).execute()

    # Delete image from storage
    if restaurant[0]["image_url"] is not None:
        image_path = f"restaurant/{restaurant[0]['image_url'].split('/')[-1][:-1]}"
        supabase.storage.from_("media").remove([image_path])

    return None


@app.get("/restaurant")
def list_all_restaurants():
    response = []
    for restaurant in supabase.table("Restaurant").select("*").execute().data:
        location = Location(
            **(
                supabase.table("Location")
                .select("*")
                .eq("id", restaurant["location"])
                .execute()
                .data[0]
            )
        )
        restaurant["location"] = location
        response.append(Restaurant(**restaurant))

    return response


@app.get("/restaurant/matches")
def list_matches_restaurant(
    x_user_uuid: Annotated[str, Header()],
    menu_filter: Annotated[MenuFilter, Query(...)],
):
    # Get user dietary preferences and current location
    user = supabase.auth.admin.get_user_by_id(x_user_uuid).user
    user_profile = (
        supabase.table("Profile").select("*").eq("user", user.id).execute()
    ).data[0]
    user_dietary_preferences = set(
        [
            preferences["name"].lower()
            for preferences in user_profile["dietary_preferences"]
        ]
    )

    # Get all menu which matches the dietary preferences, restrictions and price
    menus = (
        supabase.table("Menu")
        .select("*")
        .gte("price", menu_filter.price_min)
        .lte("price", menu_filter.price_max)
        .execute()
    ).data

    filter_restrictions = set(menu_filter.restrictions)
    matches_restaurant_menus = {}
    for menu in menus:
        # TODO: Change string matching between main ingredients and user restrictions and dietary preferences
        main_ingredients = set(
            [ingredients["name"].lower() for ingredients in menu["main_ingredients"]]
        )

        # If the main ingredients contains any of the restrictions, skip
        if len((main_ingredients - filter_restrictions)) != len(main_ingredients):
            continue

        # If the main ingredients does not contain at least one of the dietary preferences, skip
        if len((main_ingredients - user_dietary_preferences)) == len(main_ingredients):
            continue

        if menu["restaurant"] not in matches_restaurant_menus:
            matches_restaurant_menus[menu["restaurant"]] = [menu]
        else:
            matches_restaurant_menus[menu["restaurant"]].append(menu)

    restaurants = (
        supabase.table("Restaurant")
        .select("*")
        .in_("id", list(matches_restaurant_menus.keys()))
        .execute()
    ).data

    user_current_location = Location(
        **(
            supabase.table("Location")
            .select("*")
            .eq("id", user_profile["current_location"])
            .execute()
        ).data[0]
    )

    response = []
    # Filter restaurants based on location and inside/outside KAIST
    for restaurant in restaurants:
        restaurant_location = Location(
            **(
                supabase.table("Location")
                .select("*")
                .eq("id", restaurant["location"])
                .execute()
            ).data[0]
        )

        if (
            restaurant_location.inside_kaist != menu_filter.inside_kaist
            and not restaurant_location.inside_kaist != menu_filter.outside_kaist
        ):
            del matches_restaurant_menus[restaurant["id"]]
            continue

        # calculate distance from user current location to restaurant location
        distance = calculate_distance(user_current_location, restaurant_location)
        if distance > menu_filter.distance_max or distance < menu_filter.distance_min:
            del matches_restaurant_menus[restaurant["id"]]
            continue

        # Get the average rating for the menu
        for menu in matches_restaurant_menus[restaurant["id"]]:
            average_rating = (
                supabase.table("Rating")
                .select("rating_value")
                .eq("menu", menu["id"])
                .execute()
            ).data
            average_rating_value = (
                sum(rating["rating_value"] for rating in average_rating)
                / len(average_rating)
                if average_rating
                else 0
            )

            menu["average_rating"] = average_rating_value
            menu["restaurant"] = None

        restaurant["location"] = restaurant_location

        response.append(
            RestaurantMenuResponse(
                restaurant=Restaurant(**restaurant),
                menus=[
                    MenuResponse(**menu)
                    for menu in matches_restaurant_menus[restaurant["id"]]
                ],
                distance=int(distance),
                food_matches=len(matches_restaurant_menus[restaurant["id"]]),
            )
        )

    return response


@app.get("/restaurant/{restaurant_id}")
def get_restaurant(restaurant_id: str):
    restaurant = (
        supabase.table("Restaurant").select("*").eq("id", restaurant_id).execute()
    ).data
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    restaurant = restaurant[0]
    location = Location(
        **(
            supabase.table("Location")
            .select("*")
            .eq("id", restaurant["location"])
            .execute()
            .data[0]
        )
    )
    restaurant["location"] = location
    return Restaurant(**restaurant)


"""
Menu API
"""


@app.post("/restaurant/{restaurant_id}/menu", status_code=201)
def create_menu(restaurant_id: str, body: CreateMenuRequest):
    restaurant = (
        supabase.table("Restaurant").select("*").eq("id", restaurant_id).execute()
    )
    if not restaurant.data:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    restaurant = restaurant.data[0]
    restaurant_location = (
        supabase.table("Location")
        .select("*")
        .eq("id", restaurant["location"])
        .execute()
    ).data[0]
    restaurant["location"] = Location(**restaurant_location)

    # Decode base64 image and upload to supabase storage
    if body.image is not None:
        header, base64_image = body.image.split(",", 1)

        image = base64.b64decode(base64_image)
        mime_type = header.split(";")[0].split(":")[1]
        image_type = mime_type.split("/")[1]
        if image_type == "jpeg":
            image_type = "jpg"
        elif image_type == "svg+xml":
            image_type = "svg"

        image_path = supabase.storage.from_("media").upload(
            f"menu/{uuid.uuid4()}.{image_type}",
            image,
            {"content-type": mime_type},
        )
        image_url = supabase.storage.from_("media").get_public_url(image_path.path)

    new_menu = body.model_dump()
    new_menu["restaurant"] = restaurant["id"]
    new_menu["image_url"] = image_url if body.image is not None else None
    del new_menu["image"]

    menu = supabase.table("Menu").insert(new_menu).execute()
    menu = menu.data[0]
    menu["restaurant"] = restaurant

    return Menu(**menu)


@app.get("/restaurant/{restaurant_id}/menu")
def list_restaurant_menus(x_user_uuid: Annotated[str, Header()], restaurant_id: str):
    restaurant = (
        supabase.table("Restaurant").select("*").eq("id", restaurant_id).execute()
    )
    if not restaurant.data:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    restaurant = restaurant.data[0]
    restaurant_location = Location(
        **(
            supabase.table("Location")
            .select("*")
            .eq("id", restaurant["location"])
            .execute()
        ).data[0]
    )
    restaurant["location"] = restaurant_location

    menus = (
        supabase.table("Menu").select("*").eq("restaurant", restaurant_id).execute()
    ).data

    menu_responses = []
    for menu in menus:
        # Get the average rating for the menu
        average_rating = (
            supabase.table("Rating")
            .select("rating_value")
            .eq("menu", menu["id"])
            .execute()
        ).data
        average_rating_value = (
            sum(rating["rating_value"] for rating in average_rating)
            / len(average_rating)
            if average_rating
            else 0
        )
        menu["average_rating"] = average_rating_value
        del menu["restaurant"]
        menu_response = MenuResponse(**menu)
        menu_responses.append(menu_response)

    # Get user current location
    user = supabase.auth.admin.get_user_by_id(x_user_uuid).user
    user_profile = (
        supabase.table("Profile").select("*").eq("user", user.id).execute()
    ).data[0]
    user_current_location = Location(
        **(
            supabase.table("Location")
            .select("*")
            .eq("id", user_profile["current_location"])
            .execute()
        ).data[0]
    )

    return RestaurantMenuResponse(
        restaurant=Restaurant(**restaurant),
        menus=menu_responses,
        distance=calculate_distance(user_current_location, restaurant_location),
    )


@app.get("/menu")
def list_all_menus():
    menus = supabase.table("Menu").select("*").execute().data

    menu_responses = []
    for menu in menus:
        # Get the restaurant
        restaurant = (
            supabase.table("Restaurant")
            .select("*")
            .eq("id", menu["restaurant"])
            .execute()
        ).data[0]
        restaurant_location = (
            supabase.table("Location")
            .select("*")
            .eq("id", restaurant["location"])
            .execute()
        ).data[0]
        restaurant["location"] = Location(**restaurant_location)

        # Get the average rating for the menu
        average_rating = (
            supabase.table("Rating")
            .select("rating_value")
            .eq("menu", menu["id"])
            .execute()
        ).data
        average_rating_value = (
            sum(rating["rating_value"] for rating in average_rating)
            / len(average_rating)
            if average_rating
            else 0
        )

        menu["average_rating"] = average_rating_value
        menu["restaurant"] = Restaurant(**restaurant)
        menu_response = MenuResponse(**menu)
        menu_responses.append(menu_response)

    return menu_responses


@app.get("/menu/{menu_id}")
def get_menu(menu_id: str):
    menu = supabase.table("Menu").select("*").eq("id", menu_id).execute().data
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    menu = menu[0]

    # Get restaurant information
    restaurant = (
        supabase.table("Restaurant").select("*").eq("id", menu["restaurant"]).execute()
    ).data[0]
    restaurant_location = (
        supabase.table("Location")
        .select("*")
        .eq("id", restaurant["location"])
        .execute()
    ).data[0]
    restaurant["location"] = Location(**restaurant_location)

    # Get the average rating for the menu
    average_rating = (
        supabase.table("Rating").select("rating_value").eq("menu", menu_id).execute()
    ).data
    average_rating_value = (
        sum(rating["rating_value"] for rating in average_rating) / len(average_rating)
        if average_rating
        else 0
    )
    menu["average_rating"] = average_rating_value
    menu["restaurant"] = Restaurant(**restaurant)

    return MenuResponse(**menu)


@app.delete("/menu/{menu_id}", status_code=204)
def delete_menu(menu_id: str):
    # Check if menu exists
    menu = supabase.table("Menu").select("*").eq("id", menu_id).execute().data
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    menu = menu[0]

    # Delete menu
    supabase.table("Menu").delete().eq("id", menu_id).execute()

    # Delete image from storage
    if menu["image_url"] is not None:
        image_path = f"menu/{menu['image_url'].split('/')[-1][:-1]}"
        supabase.storage.from_("media").remove([image_path])

    # Delete ratings associated with the menu
    supabase.table("Rating").delete().eq("menu", menu_id).execute()

    return None


@app.post("/menu/{menu_id}/rate", status_code=201)
def rate_menu(menu_id: str, request: CreateRatingRequest):
    # Check if menu exists
    menu = supabase.table("Menu").select("*").eq("id", menu_id).execute().data
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    restaurant = (
        supabase.table("Restaurant")
        .select("*")
        .eq("id", menu[0]["restaurant"])
        .execute()
    ).data
    restaurant_location = (
        supabase.table("Location")
        .select("*")
        .eq("id", restaurant[0]["location"])
        .execute()
    ).data[0]

    restaurant[0]["location"] = Location(**restaurant_location)
    menu = menu[0]
    menu["restaurant"] = Restaurant(**restaurant[0])

    # Create rating
    new_rating = {
        "rating_value": request.rating_value,
        "comment_text": request.comment_text,
        "menu": menu_id,
    }
    rating = supabase.table("Rating").insert(new_rating).execute().data[0]
    rating["menu"] = menu

    return Rating(**rating)
