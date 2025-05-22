from pydantic import BaseModel
from datetime import datetime


class Location(BaseModel):
    latitude: float
    longitude: float


class Restaurant(BaseModel):
    id: int
    name: str
    address: str
    telephone: str
    image_url: str | None
    location: Location
    created_at: datetime


class Menu(BaseModel):
    id: int
    name: str
    description: str
    main_ingredients: dict
    price: float
    average_rating: float
    image_url: str | None
    restaurant: Restaurant
    created_at: datetime


class CreateRestaurantRequest(BaseModel):
    name: str
    address: str
    telephone: str
    location: Location


class CreateMenuRequest(BaseModel):
    name: str
    description: str
    main_ingredients: dict
    price: float
    average_rating: float
