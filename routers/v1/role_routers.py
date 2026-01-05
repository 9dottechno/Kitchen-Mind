from fastapi import APIRouter
from schema.role_schema import RoleCreate, RoleResponse

router = APIRouter()

@router.post("/roles", response_model=RoleResponse)
def create_role(role: RoleCreate):
    # Implement role creation logic here
    return RoleResponse(role_id=role.role_id, role_name=role.role_name, description=role.description)
