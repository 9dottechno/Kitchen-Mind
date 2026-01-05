from fastapi import APIRouter
from schema.ingredient_schema import IngredientCreate

router = APIRouter()

@router.post("/ingredient")
def create_ingredient(ingredient: IngredientCreate):
    # Implement ingredient creation logic here
    return {"message": "Ingredient created", "ingredient": ingredient}
