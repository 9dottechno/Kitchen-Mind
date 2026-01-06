from fastapi import APIRouter
from schema.validation_schema import RecipeValidationRequest

router = APIRouter()

@router.post("/recipe/validate")
def validate_recipe(request: RecipeValidationRequest):
    print("[DEBUG] /recipe/validate called with:", request)
    # Implement recipe validation logic here
    result = {"message": "Recipe validated", "request": request}
    print("[DEBUG] /recipe/validate result:", result)
    return result
