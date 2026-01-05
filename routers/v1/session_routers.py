from fastapi import APIRouter
from schema.session_schema import SessionCreate, SessionResponse

router = APIRouter()

@router.post("/session", response_model=SessionResponse)
def create_session(session: SessionCreate):
    # Implement session creation logic here
    return SessionResponse(session_id="1", user_id=session.user_id, created_at="2026-01-05T00:00:00Z")
