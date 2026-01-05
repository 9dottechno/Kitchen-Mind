from pydantic import BaseModel
from typing import Optional

class EventPlanRequest(BaseModel):
    """Schema for event planning request."""
    event_name: str
    guest_count: int
    budget_per_person: float
    dietary: Optional[str] = None