from fastapi import APIRouter, Query, HTTPException
from schema.recipe_schema import RecipeCreate, RecipeResponse, IngredientCreate
from sqlalchemy.orm import Session
from fastapi import Depends
from database.db import get_db  # Make sure this import path matches your project structure
from database.models.user_model import User  # Add this import; adjust the path as needed for your project
from typing import List  # <-- Add this import
from Module.repository_postgres import PostgresRecipeRepository  # Add this import; adjust the path as needed

router = APIRouter()

@router.post("/recipe", response_model=RecipeResponse)
def submit_recipe(
    recipe: RecipeCreate,
    trainer_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Submit a new recipe (trainer only)."""
    print("[DEBUG] ENTER submit_recipe endpoint")
    print(f"[DEBUG] incoming recipe: {recipe}")
    print(f"[DEBUG] incoming trainer_id: {trainer_id}")
    print(f"[DEBUG] trainer_id: {trainer_id}")
    print(f"[DEBUG] recipe: {recipe}")
    trainer = db.query(User).filter(User.user_id == trainer_id).first()
    print(f"[DEBUG] trainer: {trainer}")
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")

    print(f"[DEBUG] trainer.role: {trainer.role}, type: {type(trainer.role)}")
    # Handle SQLAlchemy Role object, Enum, or string
    trainer_role = trainer.role
    if hasattr(trainer_role, 'role_id'):
        trainer_role = trainer_role.role_id
    elif hasattr(trainer_role, 'value'):
        trainer_role = trainer_role.value
    print(f"[DEBUG] normalized trainer_role: {trainer_role}")
    if str(trainer_role).lower() not in ["trainer", "admin"]:
        raise HTTPException(status_code=403, detail="Only trainers can submit recipes")


    # Convert ingredients to IngredientCreate objects if they are dicts
    from pydantic import parse_obj_as
    if recipe.ingredients and isinstance(recipe.ingredients[0], dict):
        ingredients_obj = parse_obj_as(List[IngredientCreate], recipe.ingredients)
    else:
        ingredients_obj = recipe.ingredients

    try:
        # Create and save recipe using repository directly
        postgres_repo = PostgresRecipeRepository(db)
        print(f"[DEBUG] PostgresRecipeRepository created: {postgres_repo}")
        recipe_obj = postgres_repo.create_recipe(
            title=recipe.title,
            ingredients=ingredients_obj,
            steps=recipe.steps,
            servings=recipe.servings,
            submitted_by=trainer.user_id
        )
        print(f"[DEBUG] recipe_obj returned: {recipe_obj}")
        print(f"[DEBUG] recipe_obj.id: {getattr(recipe_obj, 'id', None)}")
        # Ensure ingredients and steps are in the expected format
        response = RecipeResponse(
            id=recipe_obj.id,
            title=recipe_obj.title,
            servings=recipe_obj.servings,
            approved=recipe_obj.approved,
            popularity=getattr(recipe_obj, 'popularity', 0),
            avg_rating=recipe_obj.avg_rating() if hasattr(recipe_obj, 'avg_rating') else 0.0
        )
        print(f"[DEBUG] RecipeResponse: {response}")
        return response
    except Exception as e:
        print(f"[ERROR] submit_recipe exception: {e}")
        raise HTTPException(status_code=400, detail=str(e))
