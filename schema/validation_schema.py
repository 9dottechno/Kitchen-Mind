from pydantic import BaseModel
from typing import Optional

class RecipeValidationRequest(BaseModel):
    """Schema for recipe validation."""
    approved: bool
    feedback: Optional[str] = None
    confidence: float = 0.8
