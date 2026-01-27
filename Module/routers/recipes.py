from typing import List
import uuid

from fastapi import Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from Module.database import get_db, User
from Module.routers.base import api_router
from Module.routers.auth import get_current_user
from Module.schemas.recipe import (
    RecipeCreate, RecipeResponse, RecipeSynthesisRequest
)
from Module.services.recipe_service import RecipeService

@api_router.post("/recipe")
def submit_recipe(
    recipe: RecipeCreate,
    trainer_id: str = Query(..., description="Trainer user ID (UUID)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Validate trainer_id format
        if not trainer_id or trainer_id.strip() == "":
            raise HTTPException(status_code=400, detail="trainer_id is required")
        try:
            uuid.UUID(trainer_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid trainer ID format. Please provide a valid user identifier.")
        
        # Validate trainer exists
        trainer = db.query(User).filter(User.user_id == trainer_id).first()
        if not trainer:
            raise HTTPException(status_code=404, detail="Trainer user not found")

        # Authorization: only admins can submit on behalf of others.
        # Trainers may submit only for themselves.
        current_role = str(current_user.get("role", "")).lower()
        current_user_id = current_user.get("user_id")
        if current_role == "trainer":
            if current_user_id != trainer_id:
                raise HTTPException(status_code=403, detail="Trainers can only submit recipes for themselves.")
        elif current_role == "admin":
            pass  # admins allowed to submit for any trainer
        else:
            # regular users cannot submit recipes
            raise HTTPException(status_code=403, detail="Access denied. Only trainers or administrators can submit recipes.")
        
        service = RecipeService(db)
        result = service.submit_recipe(recipe, trainer_id)
        return {
            "status": True,
            "message": "Recipe submitted successfully.",
            "data": result
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        print(f"[ERROR] submit_recipe exception: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while submitting the recipe. Please try again.")

@api_router.get("/recipes")
def list_recipes(
    approved_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    service = RecipeService(db)
    response = service.list_recipes(approved_only)
    return {
        "status": True,
        "message": "Recipes fetched successfully.",
        "data": response
    }

@api_router.post("/recipe/synthesize")
def synthesize_recipe(
    request: RecipeSynthesisRequest,
    user_id: str = Query(..., description="User ID (UUID)"),
    db: Session = Depends(get_db)
):
    try:
        # Validate user_id format first (before request body validation)
        if not user_id or user_id.strip() == "":
            raise HTTPException(status_code=400, detail="user_id is required")
        try:
            uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format. Please provide a valid UUID.")
        
        # Validate user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Now process the request body (dish_name and servings validation happens here)
        service = RecipeService(db)
        return service.synthesize_recipe(request, user_id)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print(f"[ERROR] synthesize_recipe exception: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while synthesizing the recipe. Please try again later.")

@api_router.get("/recipes/pending")
def get_pending_recipes(db: Session = Depends(get_db)):
    service = RecipeService(db)
    recipes = service.get_pending_recipes()
    return {
        "status": True,
        "message": "Pending recipes fetched successfully.",
        "data": recipes
    }

@api_router.get("/recipe/version/{version_id}")
def get_single_recipe_by_version(version_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a recipe by its version ID.
    
    Validations:
    - UUID format validation for version_id
    - Recipe version existence check
    - Proper error handling with appropriate status codes
    """
    # Validate UUID format
    try:
        uuid.UUID(version_id)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid version_id format. Expected UUID, got: {version_id}"
        )
    
    try:
        service = RecipeService(db)
        result = service.get_recipe_by_version(version_id)
        if not result:
            raise HTTPException(
                status_code=404, 
                detail=f"Recipe version not found: {version_id}"
            )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Log the error for debugging but don't expose internal details
        raise HTTPException(
            status_code=500, 
            detail="An error occurred while retrieving the recipe"
        )

@api_router.post("/recipe/version/{version_id}/rate")
def rate_recipe(
    version_id: str,
    user_id: str = Query(...),
    rating: float = Query(...),
    comment: str = Body(default="", embed=True),
    db: Session = Depends(get_db)
):
    """
    Rate a recipe version.
    
    Validations:
    - UUID format for version_id and user_id
    - Rating must be between 08-5
    - Proper error handling
    """
    # Validate UUID formats
    try:
        uuid.UUID(version_id)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid version_id format. Expected UUID, got: {version_id}"
        )
    
    try:
        uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid user_id format. Expected UUID, got: {user_id}"
        )
    
    # Validate rating range
    if not (0 <= rating <= 5):
        raise HTTPException(
            status_code=400, 
            detail=f"Rating must be between 0 and 5. Got: {rating}"
        )
    
    try:
        service = RecipeService(db)
        return service.rate_recipe(version_id, user_id, rating, comment)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="An error occurred while rating the recipe"
        )
