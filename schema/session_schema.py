from pydantic import BaseModel

class SessionCreate(BaseModel):
    user_id: str

class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    created_at: str
