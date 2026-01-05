from pydantic import BaseModel


class UserCreate(BaseModel):
    """Schema for creating a user (new schema)."""
    name: str
    email: str
    login_identifier: str
    password_hash: str
    auth_type: str
    role_id: str
    dietary_preference: str



class UserResponse(BaseModel):
    user_id: str
    name: str
    email: str
    login_identifier: str
    role_id: str
    dietary_preference: str
    rating_score: float
    total_points: int
    created_at: str = None
    last_login_at: str = None