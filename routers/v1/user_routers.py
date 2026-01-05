from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from schema.user_schema import UserCreate, UserResponse
from database.models.user_model import User, DietaryPreferenceEnum
from database.models.role_model import Role
from database.db import get_db
import uuid
from datetime import datetime

from controllers.v1.user_controllers import create_user, get_user, get_user_by_email

router = APIRouter(prefix="/user", tags=["User"])

@router.post("/user", response_model=UserResponse)
def create_user_wrapper(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(user, db)

@router.get("/user/{user_id}", response_model=UserResponse)
def get_user_wrapper(user_id: str, db: Session = Depends(get_db)):
    return get_user(user_id, db)

@router.get("/user/email/{email}", response_model=UserResponse)
def get_user_by_wrapper(email: str, db: Session = Depends(get_db)):
    return get_user_by_email(email, db)