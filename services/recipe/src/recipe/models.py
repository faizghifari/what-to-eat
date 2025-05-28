from pydantic import BaseModel
from typing import Optional, List, Dict


class NameDescPair(BaseModel):
    name: str
    description: str


class Recipe(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    ingredients: List[NameDescPair]
    tools: List[NameDescPair]
    instructions: list[str]
    estimated_price: float
    estimated_time: str
    image_url: str


class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[Dict[str, str]]] = None
    tools: Optional[List[Dict[str, str]]] = None
    instructions: Optional[List[str]] = None
    estimated_price: Optional[float] = None
    estimated_time: Optional[str] = None
    image_url: Optional[str] = None


class Rating(BaseModel):
    id: int | None = None
    recipe: int
    user: str
    rating_value: int
    comment_text: str


class RatingCreate(BaseModel):
    rating_value: int
    comment_text: str = ""


class RatingUpdate(BaseModel):
    rating_value: int | None = None
    comment_text: str | None = None
