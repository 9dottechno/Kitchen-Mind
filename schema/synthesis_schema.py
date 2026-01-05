from pydantic import BaseModel

class RecipeSynthesisRequest(BaseModel):
    """Schema for recipe synthesis request."""
    dish_name: str
    servings: int = 2
    top_k: int = 10
    reorder: bool = True
