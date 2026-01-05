from pydantic import BaseModel

class IngredientCreate(BaseModel):
    """Schema for creating an ingredient."""
    name: str
    quantity: float
    unit: str
