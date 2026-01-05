from pydantic import BaseModel

class RoleCreate(BaseModel):
    role_id: str
    role_name: str
    description: str = None

class RoleResponse(BaseModel):
    role_id: str
    role_name: str
    description: str = None