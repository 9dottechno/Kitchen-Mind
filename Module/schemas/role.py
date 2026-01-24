from typing import Optional
from pydantic import BaseModel, validator

class RoleCreate(BaseModel):
    """Schema for creating a role."""
    role_id: str
    role_name: str
    description: str = ""

    @validator('role_id')
    def validate_role_id(cls, v):
        """Validate role_id is not empty and follows naming convention."""
        if not v or not v.strip():
            raise ValueError("role_id cannot be empty")
        if len(v) > 50:
            raise ValueError("role_id must be 50 characters or less")
        if not v.replace('_', '').isalnum():
            raise ValueError("role_id can only contain letters, numbers, and underscores")
        return v.lower().strip()

    @validator('role_name')
    def validate_role_name(cls, v):
        """Validate role_name is not empty."""
        if not v or not v.strip():
            raise ValueError("role_name cannot be empty")
        if len(v) > 100:
            raise ValueError("role_name must be 100 characters or less")
        return v.strip()

    @validator('description')
    def validate_description(cls, v):
        """Validate description if provided."""
        if v and len(v) > 500:
            raise ValueError("description must be 500 characters or less")
        return v.strip() if v else ""

class RoleResponse(BaseModel):
    """Schema for role response."""
    role_id: str
    role_name: str
    description: Optional[str] = None
