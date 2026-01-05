from fastapi import APIRouter, HTTPException
from schema.event_schema import EventPlanRequest

km_instance = None
router = APIRouter()

@router.post("/event/plan")
def plan_event(request: EventPlanRequest):
    """Plan an event with recipes."""
    try:
        plan = km_instance.event_plan(
            request.event_name,
            request.guest_count,
            request.budget_per_person,
            request.dietary
        )
        return plan
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
