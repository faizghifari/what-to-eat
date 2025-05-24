from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

"""
Models
"""


class NameDescPair(BaseModel):
    name: str
    description: str


class Location(BaseModel):
    latitude: float
    longitude: float
    inside_kaist: bool = False


class Restaurant(BaseModel):
    id: int
    name: str
    address: str
    telephone: str
    image_url: Optional[str]
    location: Location
    created_at: datetime


class Menu(BaseModel):
    id: int
    name: str
    description: str
    main_ingredients: List[NameDescPair]
    price: float
    image_url: Optional[str]
    restaurant: Restaurant
    created_at: datetime


class Rating(BaseModel):
    id: int
    rating_value: int
    comment_text: str
    menu: Optional[Menu]
    recipe: None
    created_at: datetime


"""
Requests
"""


class CreateRestaurantRequest(BaseModel):
    name: str
    address: str
    telephone: str
    location: Location
    image: Optional[str]
    """
    base64 encoded image complete with its header
    e.g. data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
    """


class CreateMenuRequest(BaseModel):
    name: str
    description: str
    main_ingredients: List[NameDescPair]
    price: float
    image: Optional[str]
    """
    base64 encoded image complete with its header
    e.g. data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
    """


class CreateRatingRequest(BaseModel):
    rating_value: int
    comment_text: str = ""


"""
Responses
"""


class MenuResponse(Menu):
    average_rating: float


class RestaurantMenuResponse(BaseModel):
    restaurant: Restaurant
    menus: List[MenuResponse]
    distance: float


"""
Filters
"""


class MenuFilter(BaseModel):
    restrictions: List[str] = []
    inside_kaist: bool = True
    outside_kaist: bool = True
    price_min: float = 0.0
    price_max: float = 100000.0
    distance_min: float = 0.0
    distance_max: float = 5000.0
    rating_min: int = 1
    rating_max: int = 5
