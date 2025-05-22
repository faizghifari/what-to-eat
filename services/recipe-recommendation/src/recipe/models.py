from pydantic import BaseModel
from typing import Optional, Any

class Recipe(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    ingredients: Any
    tools: Any
    instructions: Any
    estimated_price: float
    estimated_time: str
    image_url: str

class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[Any] = None
    tools: Optional[Any] = None
    instructions: Optional[Any] = None
    estimated_price: Optional[float] = None
    estimated_time: Optional[str] = None
    image_url: Optional[str] = None
