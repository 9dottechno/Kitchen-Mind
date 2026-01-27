from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from Module.database import get_db
from Module.routers.base import api_router
from Module.routers.auth import get_current_user
from Module.schemas.admin import AdminProfileCreate, AdminProfileResponse
from Module.services.admin_service import AdminService

@api_router.post("/admin_profiles")
def create_admin_profile(
    profile: AdminProfileCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Admin-only authorization
        if current_user.get("role") != "admin":
            raise PermissionError("Access denied. Only administrators can create admin profiles.")
        
        service = AdminService(db)
        result = service.create_admin_profile(profile)
        return {
            "status": True,
            "message": "Admin profile created successfully.",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin_profiles/{admin_id}")
def get_admin_profile(
    admin_id: str, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Admin-only authorization
        if current_user.get("role") != "admin":
            raise PermissionError("Access denied. Only administrators can view admin profiles.")
        
        service = AdminService(db)
        result = service.get_admin_profile(admin_id)
        return {
            "status": True,
            "message": "Admin profile fetched successfully.",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Session creation is now handled automatically during OTP verification; explicit /session endpoint removed.
