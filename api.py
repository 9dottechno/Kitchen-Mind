
# =============================
# Imports
# =============================
from fastapi import FastAPI, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
import os
from Module.ai_validation import ai_validate_recipe
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime
from Module.repository_postgres import PostgresRecipeRepository

# =============================
# App Initialization
# =============================
app = FastAPI()
# Dependency to get DB session
def get_db():
    from database.db import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Import RecipeResponse from your schema or define it here if missing
try:
    from schema.recipe_schema import RecipeResponse
except ImportError:
    class RecipeResponse(BaseModel):
        id: str
        title: str
        servings: int
        approved: Optional[bool] = False
        popularity: Optional[int] = 0
        avg_rating: Optional[float] = 0.0

app = FastAPI()

# Rate a recipe by ID
@app.post("/recipe/{recipe_id}/rate", response_model=RecipeResponse)
def rate_recipe(recipe_id: str, rating: float = Body(..., embed=True), db: Session = Depends(get_db)):
    """Rate a recipe by its ID. Updates the recipe's avg_rating (validator_confidence)."""
    postgres_repo = PostgresRecipeRepository(db)
    recipe = postgres_repo.get_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    # Update the recipe's rating (validator_confidence)
    updated_recipe = postgres_repo.update_recipe_validation(
        recipe_id=recipe_id,
        approved=getattr(recipe, 'approved', False),
        validator_confidence=rating,
        validation_feedback=getattr(recipe, 'validation_feedback', '')
    )
    return RecipeResponse(
        id=updated_recipe.id,
        title=updated_recipe.title,
        servings=updated_recipe.servings,
        approved=getattr(updated_recipe, 'approved', False),
        popularity=getattr(updated_recipe, 'popularity', 0),
        avg_rating=getattr(updated_recipe, 'validator_confidence', 0.0)
    )
# Approve/validate a recipe by ID
@app.post("/recipe/{recipe_id}/validate", response_model=RecipeResponse)
def approve_recipe(recipe_id: str, db: Session = Depends(get_db)):
    """Approve/validate a recipe by its ID."""
    postgres_repo = PostgresRecipeRepository(db)
    recipe = postgres_repo.get_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    # Mark as approved
    updated_recipe = postgres_repo.update_recipe_validation(
        recipe_id=recipe_id,
        approved=True,
        validator_confidence=getattr(recipe, 'validator_confidence', 1.0),
        validation_feedback=getattr(recipe, 'validation_feedback', 'Approved by admin')
    )
    return RecipeResponse(
        id=updated_recipe.id,
        title=updated_recipe.title,
        servings=updated_recipe.servings,
        approved=getattr(updated_recipe, 'approved', True),
        popularity=getattr(updated_recipe, 'popularity', 0),
        avg_rating=getattr(updated_recipe, 'validator_confidence', 0.0)
    )

# Add /event/plan endpoint here to avoid circular import and use correct km_instance
from schema.event_schema import EventPlanRequest

@app.post("/event/plan")
def plan_event(request: EventPlanRequest):
    import sys
    print(f"[DEBUG] (plan_event) module={__name__}, id(km_instance)={id(km_instance)}, sys.modules={list(sys.modules.keys())}")
    """Plan an event with recipes."""
    print(f"[DEBUG] /event/plan called with: event_name={request.event_name!r} guest_count={request.guest_count} budget_per_person={request.budget_per_person} dietary={request.dietary}")
    print(f"[DEBUG] km_instance at /event/plan: {km_instance}")
    print(f"[DEBUG] km_instance type: {type(km_instance)}")
    if km_instance is None:
        print("[ERROR] km_instance is not initialized. Startup may have failed.")
        raise HTTPException(status_code=500, detail="Server not initialized. Please restart the application.")
    try:
        print(f"[DEBUG] Calling km_instance.event_plan with: event_name={request.event_name}, guest_count={request.guest_count}, budget_per_person={request.budget_per_person}, dietary={request.dietary}")
        plan = km_instance.event_plan(
            request.event_name,
            request.guest_count,
            request.budget_per_person,
            request.dietary
        )
        return plan
    except Exception as e:
        print(f"[ERROR] /event/plan exception: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in production, use dependency injection)
import sys
print(f"[DEBUG] (module load) km_instance initial value: None, id={id(None)}, module={__name__}, sys.modules={list(sys.modules.keys())}")
km_instance = None




# Define RoleResponse and RoleCreate if not already imported
try:
    from schema.role_schema import RoleResponse, RoleCreate
except ImportError:
    class RoleResponse(BaseModel):
        role_id: str
        role_name: str
        description: str

    class RoleCreate(BaseModel):
        role_id: str
        role_name: str
        description: str

from database.models.role_model import Role

# Fetch a role by role_id
@app.get("/roles/{role_id}", response_model=RoleResponse)
def get_role(role_id: str, db: Session = Depends(get_db)):
    db_role = db.query(Role).filter(Role.role_id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail=f"Role '{role_id}' not found.")
    return RoleResponse(
        role_id=db_role.role_id,
        role_name=db_role.role_name,
        description=db_role.description
    )

# Define UserResponse and UserCreate if not already imported
try:
    from schema.user_schema import UserResponse, UserCreate
except ImportError:
    class UserResponse(BaseModel):
        user_id: str
        name: str
        email: str
        login_identifier: str
        role_id: str
        dietary_preference: Optional[str] = None
        rating_score: Optional[float] = 0.0
        total_points: Optional[int] = 0
        created_at: Optional[str] = None
        last_login_at: Optional[str] = None

    class UserCreate(BaseModel):
        name: str
        email: str
        login_identifier: str
        password_hash: str
        auth_type: str
        role_id: str
        dietary_preference: Optional[str] = None

# Fetch a user by email
from database.models.user_model import User

# Import DietaryPreferenceEnum if not already imported
try:
    from database.models.user_model import DietaryPreferenceEnum
except ImportError:
    from enum import Enum
    class DietaryPreferenceEnum(str, Enum):
        OMNIVORE = "omnivore"
        VEGETARIAN = "vegetarian"
        VEGAN = "vegan"
        PESCATARIAN = "pescatarian"
        GLUTEN_FREE = "gluten_free"
        KETO = "keto"
        PALEO = "paleo"
        OTHER = "other"

@app.get("/user/email/{email}", response_model=UserResponse)
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail=f"User with email '{email}' not found.")
    return UserResponse(
        user_id=db_user.user_id,
        name=db_user.name,
        email=db_user.email,
        login_identifier=db_user.login_identifier,
        role_id=db_user.role_id,
        dietary_preference=db_user.dietary_preference.value if db_user.dietary_preference else None,
        rating_score=db_user.rating_score,
        total_points=db_user.total_points,
        created_at=str(db_user.created_at) if db_user.created_at else None,
        last_login_at=str(db_user.last_login_at) if db_user.last_login_at else None
    )

@app.post("/roles", response_model=RoleResponse)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    existing = db.query(Role).filter(Role.role_id == role.role_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Role with role_id '{role.role_id}' already exists.")
    db_role = Role(
        role_id=role.role_id,
        role_name=role.role_name,
        description=role.description
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return RoleResponse(
        role_id=db_role.role_id,
        role_name=db_role.role_name,
        description=db_role.description
    )

@app.get("/roles", response_model=list[RoleResponse])
def list_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    return [RoleResponse(role_id=r.role_id, role_name=r.role_name, description=r.description) for r in roles]



# ============================================================================
# Startup and Shutdown Events
# ============================================================================

@app.on_event("startup")
def startup_event():
    global km_instance
    # Import init_db here to ensure it's defined
    from database.db import init_db
    print(f"[DEBUG] (startup) Before init_db, km_instance: {km_instance}, id={id(km_instance)}")
    init_db()
    print(f"[DEBUG] (startup) After init_db, km_instance: {km_instance}, id={id(km_instance)}")
    # Create a DB session for the repository
    from database.db import SessionLocal as DBSession
    db_session = DBSession()
    repo = PostgresRecipeRepository(db_session)
    # Import KitchenMind here to ensure it's defined
    from Module.controller import KitchenMind
    km_instance = KitchenMind(repo)
    print(f"[DEBUG] (startup) After KitchenMind(), km_instance: {km_instance}, id={id(km_instance)}")
    print("✓ Database initialized")
    print("✓ KitchenMind instance created")


# ============================================================================
# Health Check
# ============================================================================

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "message": "KitchenMind API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "api": "running"
    }


# ============================================================================
# User Management Endpoints
# ============================================================================



@app.post("/user", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if role exists
    role = db.query(Role).filter(Role.role_id == user.role_id).first()
    if not role:
        raise HTTPException(status_code=400, detail=f"Role '{user.role_id}' does not exist.")

    # Check for duplicate email or login_identifier
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=409, detail=f"User with email '{user.email}' already exists.")
    if db.query(User).filter(User.login_identifier == user.login_identifier).first():
        raise HTTPException(status_code=409, detail=f"User with login_identifier '{user.login_identifier}' already exists.")

    # Convert dietary_preference to Enum
    try:
        dietary_pref = DietaryPreferenceEnum[user.dietary_preference] if user.dietary_preference in DietaryPreferenceEnum.__members__ else DietaryPreferenceEnum(user.dietary_preference)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid dietary_preference: {user.dietary_preference}")

    now = datetime.utcnow()
    db_user = User(
        user_id=str(uuid.uuid4()),
        name=user.name,
        email=user.email,
        login_identifier=user.login_identifier,
        password_hash=user.password_hash,
        auth_type=user.auth_type,
        role_id=user.role_id,
        dietary_preference=dietary_pref,
        rating_score=0.0,
        total_points=0,
        created_at=now,
        last_login_at=now
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserResponse(
        user_id=db_user.user_id,
        name=db_user.name,
        email=db_user.email,
        login_identifier=db_user.login_identifier,
        role_id=db_user.role_id,
        dietary_preference=db_user.dietary_preference.value if db_user.dietary_preference else None,
        rating_score=db_user.rating_score,
        total_points=db_user.total_points,
        created_at=str(db_user.created_at) if db_user.created_at else None,
        last_login_at=str(db_user.last_login_at) if db_user.last_login_at else None
    )



@app.get("/user/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        login_identifier=user.login_identifier,
        role_id=user.role_id,
        dietary_preference=user.dietary_preference,
        rating_score=user.rating_score,
        total_points=user.total_points,
        created_at=str(user.created_at) if user.created_at else None,
        last_login_at=str(user.last_login_at) if user.last_login_at else None
    )


# ============================================================================
# Recipe Management Endpoints
# ============================================================================
# ============================================================================
# Recipe Management Endpoints
# ============================================================================
@app.get("/recipe/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: str, db: Session = Depends(get_db)):
    """Fetch a single recipe by its ID."""
    postgres_repo = PostgresRecipeRepository(db)
    recipe = postgres_repo.get_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return RecipeResponse(
        id=getattr(recipe, 'id', None) if not isinstance(recipe, dict) else recipe['id'],
        title=getattr(recipe, 'title', None) if not isinstance(recipe, dict) else recipe['title'],
        servings=getattr(recipe, 'servings', None) if not isinstance(recipe, dict) else recipe['servings'],
        approved=getattr(recipe, 'approved', False) if not isinstance(recipe, dict) else recipe.get('approved', False),
        popularity=getattr(recipe, 'popularity', 0) if not isinstance(recipe, dict) else recipe.get('popularity', 0),
        avg_rating=getattr(recipe, 'validator_confidence', 0.0) if not isinstance(recipe, dict) else recipe.get('validator_confidence', 0.0)
    )

# Import RecipeCreate, IngredientCreate, and RecipeSynthesisRequest if not already imported
try:
    from schema.recipe_schema import RecipeCreate, IngredientCreate, RecipeSynthesisRequest
except ImportError:
    class IngredientCreate(BaseModel):
        name: str
        quantity: float
        unit: str

    class RecipeCreate(BaseModel):
        title: str
        ingredients: List[IngredientCreate]
        steps: List[str]
        servings: int

    class RecipeSynthesisRequest(BaseModel):
        dish_name: str
        servings: int
        top_k: int = 3
        reorder: bool = False


# (submit_recipe endpoint, properly indented)
@app.post("/recipe/submit", response_model=RecipeResponse)
def submit_recipe(recipe_obj: dict = Body(...), db: Session = Depends(get_db)):
    if not (isinstance(recipe_obj, dict) and 'id' in recipe_obj):
        print(f"[ERROR] recipe_obj does not have 'id' key! recipe_obj: {recipe_obj}")
    # --- Auto-validate using AI ---
    try:
        approved, feedback, confidence = ai_validate_recipe(
            recipe_obj['title'],
            recipe_obj['ingredients'],
            recipe_obj['steps']
        )
        print(f"[DEBUG] AI validation: approved={approved}, confidence={confidence}, feedback={feedback}")
        # Update recipe in DB with validation results
        print(f"[DEBUG] Passing recipe_id to update_recipe_validation: {recipe_obj['id']}")
        postgres_repo = PostgresRecipeRepository(db)
        updated_recipe = postgres_repo.update_recipe_validation(
            recipe_id=recipe_obj['id'],
            approved=approved,
            validator_confidence=confidence,
            validation_feedback=feedback
        )
        print(f"[DEBUG] updated_recipe: {updated_recipe}")
    except Exception as e:
        print(f"[ERROR] AI auto-validation failed: {e}")
        updated_recipe = recipe_obj

    # Ensure ingredients and steps are in the expected format
    response = RecipeResponse(
        id=getattr(updated_recipe, 'id', None) if not isinstance(updated_recipe, dict) else updated_recipe['id'],
        title=getattr(updated_recipe, 'title', None) if not isinstance(updated_recipe, dict) else updated_recipe['title'],
        servings=getattr(updated_recipe, 'servings', None) if not isinstance(updated_recipe, dict) else updated_recipe['servings'],
        approved=getattr(updated_recipe, 'approved', False) if not isinstance(updated_recipe, dict) else updated_recipe.get('approved', False),
        popularity=getattr(updated_recipe, 'popularity', 0) if not isinstance(updated_recipe, dict) else updated_recipe.get('popularity', 0),
        avg_rating=getattr(updated_recipe, 'validator_confidence', 0.0) if not isinstance(updated_recipe, dict) else updated_recipe.get('validator_confidence', 0.0)
    )
    print(f"[DEBUG] RecipeResponse: {response}")
    return response


@app.get("/recipes", response_model=List[RecipeResponse])
def list_recipes(
    approved_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List recipes, optionally filtering by approval status."""
    postgres_repo = PostgresRecipeRepository(db)
    recipes = postgres_repo.approved() if approved_only else postgres_repo.list()
    response = [
        RecipeResponse(
            id=getattr(r, 'id', None) if not isinstance(r, dict) else r.get('id'),
            title=getattr(r, 'title', None) if not isinstance(r, dict) else r.get('title'),
            servings=getattr(r, 'servings', None) if not isinstance(r, dict) else r.get('servings'),
            approved=getattr(r, 'approved', False) if not isinstance(r, dict) else r.get('approved', False),
            popularity=getattr(r, 'popularity', 0) if not isinstance(r, dict) else r.get('popularity', 0),
            avg_rating=getattr(r, 'validator_confidence', 0.0) if not isinstance(r, dict) else r.get('validator_confidence', 0.0)
        )
        for r in recipes
    ]
    print(f"[DEBUG] list_recipes response: {response}")
    return response


# ============================================================================
# Recipe Synthesis Endpoints
# ============================================================================

@app.post("/recipe/synthesize", response_model=RecipeResponse)
def synthesize_recipe(
    request: RecipeSynthesisRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Synthesize multiple recipes into one."""
    print(f"[DEBUG] synthesize_recipe called with user_id: {user_id}, request: {request}")
    # Fetch user from the database
    from database.models.user_model import User as DBUser
    user = db.query(DBUser).filter(DBUser.user_id == user_id).first()
    print(f"[DEBUG] user: {user}")
    if not user:
        print("[ERROR] User not found")
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Synthesize recipe using controller, then save using repository
        result = km_instance.request_recipe(
            user,
            request.dish_name,
            request.servings,
            request.top_k,
            request.reorder,
            db=db
        )
        print(f"[DEBUG] Synthesis result: {result}")
        postgres_repo = PostgresRecipeRepository(db)
        print(f"[DEBUG] PostgresRecipeRepository created: {postgres_repo}")
        # Normalize result to dict
        # Normalize result to dict-like for DB, but always support Recipe object for response
        if not isinstance(result, dict):
            # Convert object to dict if needed for DB
            result_dict = {
                'id': getattr(result, 'id', None),
                'title': getattr(result, 'title', None),
                'ingredients': [
                    {"name": getattr(ing, 'name', None), "quantity": getattr(ing, 'quantity', None), "unit": getattr(ing, 'unit', None)}
                    for ing in getattr(result, 'ingredients', [])
                ],
                'steps': getattr(result, 'steps', []),
                'servings': getattr(result, 'servings', None),
                'approved': getattr(result, 'approved', False),
                'popularity': getattr(result, 'popularity', 0),
                'validator_confidence': getattr(result, 'validator_confidence', 0.0)
            }
        else:
            result_dict = result
        # Ensure ingredients is a list of dicts
        ingredients = result_dict.get('ingredients', [])
        if ingredients and isinstance(ingredients[0], dict):
            ingredients_list = ingredients
        else:
            ingredients_list = [
                {"name": getattr(ing, 'name', None), "quantity": getattr(ing, 'quantity', None), "unit": getattr(ing, 'unit', None)}
                for ing in ingredients
            ]
        recipe_obj = postgres_repo.create_recipe(
            title=result_dict.get('title'),
            ingredients=ingredients_list,
            steps=result_dict.get('steps', []),
            servings=result_dict.get('servings'),
            submitted_by=user.user_id
        )
        print(f"[DEBUG] recipe_obj returned: {recipe_obj}")
        print(f"[DEBUG] recipe_obj type: {type(recipe_obj)}")
        # Always use getattr for Recipe objects, dict access for dicts
        return RecipeResponse(
            id=getattr(recipe_obj, 'id', None) if not isinstance(recipe_obj, dict) else recipe_obj.get('id'),
            title=getattr(recipe_obj, 'title', None) if not isinstance(recipe_obj, dict) else recipe_obj.get('title'),
            servings=getattr(recipe_obj, 'servings', None) if not isinstance(recipe_obj, dict) else recipe_obj.get('servings'),
            approved=getattr(recipe_obj, 'approved', False) if not isinstance(recipe_obj, dict) else recipe_obj.get('approved', False),
            popularity=getattr(recipe_obj, 'popularity', 0) if not isinstance(recipe_obj, dict) else recipe_obj.get('popularity', 0),
            avg_rating=getattr(recipe_obj, 'validator_confidence', 0.0) if not isinstance(recipe_obj, dict) else recipe_obj.get('validator_confidence', 0.0)
        )
    except LookupError as e:
        print(f"[ERROR] synthesize_recipe LookupError: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"[ERROR] synthesize_recipe Exception: {e}")
        raise HTTPException(status_code=500, detail=f"Synthesis error: {str(e)}")


# ============================================================================
# Event Planning Endpoints
# ============================================================================

@app.post("/event/plan")
def plan_event(request: EventPlanRequest):
    global km_instance
    import sys
    print(f"[DEBUG] (plan_event) module={__name__}, id(km_instance)={id(km_instance)}, sys.modules={list(sys.modules.keys())}")
    """Plan an event with recipes."""
    print(f"[DEBUG] /event/plan called with: event_name={request.event_name!r} guest_count={request.guest_count} budget_per_person={request.budget_per_person} dietary={request.dietary}")
    print(f"[DEBUG] km_instance at /event/plan: {km_instance}")
    print(f"[DEBUG] km_instance type: {type(km_instance)}")
    if km_instance is None:
        print("[ERROR] km_instance is not initialized. Startup may have failed.")
        raise HTTPException(status_code=500, detail="Server not initialized. Please restart the application.")
    try:
        print(f"[DEBUG] Calling km_instance.event_plan with: event_name={request.event_name}, guest_count={request.guest_count}, budget_per_person={request.budget_per_person}, dietary={request.dietary}")
        plan = km_instance.event_plan(
            request.event_name,
            request.guest_count,
            request.budget_per_person,
            request.dietary
        )
        print(f"[DEBUG] event_plan returned: {plan}")
        if plan is None:
            print("[ERROR] event_plan returned None!")
            raise HTTPException(status_code=500, detail="Internal error: event_plan returned None.")
        return plan
    except Exception as e:
        print(f"[ERROR] /event/plan exception: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/recipes/pending")
def get_pending_recipes(db: Session = Depends(get_db)):
    """Get all pending (unapproved) recipes."""
    postgres_repo = PostgresRecipeRepository(db)
    recipes = postgres_repo.pending()
    
    return [
        {
            "id": r['id'],
            "title": r['title'],
            "servings": r['servings'],
            "submitted_by": r.get('metadata', {}).get("submitted_by", "unknown")
        }
        for r in recipes
    ]


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    print("[API ERROR] Exception occurred:")
    print(f"Request: {request.method} {request.url}")
    print(f"Exception: {exc!r}")
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
