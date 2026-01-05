from pydantic import BaseModel
from typing import List
from .ingredient_schema import IngredientCreate

class RecipeCreate(BaseModel):
    """Schema for creating a recipe."""
    title: str
    ingredients: List[IngredientCreate]
    steps: List[str]
    servings: int


class RecipeResponse(BaseModel):
    """Schema for recipe response."""
    id: str
    title: str
    servings: int
    approved: bool
    popularity: int
    avg_rating: float