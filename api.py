"""
FastAPI application for KitchenMind recipe synthesis system.
Provides REST API for recipe management, synthesis, and event planning.
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime

from Module.database import get_db, init_db, Recipe, Role, User
from Module.database import DietaryPreferenceEnum
from Module.repository_postgres import PostgresRecipeRepository
from Module.controller import KitchenMind
 # ...existing code...
from Module.vector_store import MockVectorStore
from Module.scoring import ScoringEngine

# Initialize FastAPI app
app = FastAPI(
    title="KitchenMind API",
    version="1.0.0",
    description="Recipe synthesis and management system with PostgreSQL backend"
)

# ============================================================================
# Admin Action Log Endpoint
# ============================================================================

class AdminActionCreate(BaseModel):
    admin_id: str
    action_type: str
    target_type: str
    target_id: str
    description: str

class AdminActionResponse(BaseModel):
    action_id: str
    admin_id: str
    action_type: str
    target_type: str
    target_id: str
    description: str
    created_at: str

@app.post("/admin_actions", response_model=AdminActionResponse)
def create_admin_action(action: AdminActionCreate, db: Session = Depends(get_db)):
    # Check if admin exists
    from Module.database import AdminProfile, AdminActionLog
    admin = db.query(AdminProfile).filter(AdminProfile.admin_id == action.admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    import uuid
    from datetime import datetime
    now = datetime.utcnow()
    admin_action = AdminActionLog(
        action_id=str(uuid.uuid4()),
        admin_id=action.admin_id,
        action_type=action.action_type,
        target_type=action.target_type,
        target_id=action.target_id,
        description=action.description,
        created_at=now
    )
    db.add(admin_action)
    db.commit()
    db.refresh(admin_action)
    return AdminActionResponse(
        action_id=admin_action.action_id,
        admin_id=admin_action.admin_id,
        action_type=admin_action.action_type,
        target_type=admin_action.target_type,
        target_id=admin_action.target_id,
        description=admin_action.description,
        created_at=str(admin_action.created_at)
    )

# ============================================================================
# Admin Profile and Session Endpoints
# ============================================================================

class AdminProfileCreate(BaseModel):
    user_id: str
    created_by: str
    is_super_admin: bool = False

class AdminProfileResponse(BaseModel):
    admin_id: str
    user_id: str
    created_by: str
    is_super_admin: bool

@app.post("/admin_profiles", response_model=AdminProfileResponse)
def create_admin_profile(profile: AdminProfileCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.user_id == profile.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Create admin profile (minimal, for test)
    from Module.database import AdminProfile
    import uuid
    admin_profile = AdminProfile(
        admin_id=str(uuid.uuid4()),
        user_id=profile.user_id,
        created_by=profile.created_by,
        is_super_admin=profile.is_super_admin
    )
    db.add(admin_profile)
    db.commit()
    db.refresh(admin_profile)
    return AdminProfileResponse(
        admin_id=admin_profile.admin_id,
        user_id=admin_profile.user_id,
        created_by=admin_profile.created_by,
        is_super_admin=admin_profile.is_super_admin
    )

class SessionCreate(BaseModel):
    user_id: str

class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    created_at: str

@app.post("/sessions", response_model=SessionResponse)
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.user_id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    from Module.database import Session as DBSession
    import uuid
    from datetime import datetime
    now = datetime.utcnow()
    db_session = DBSession(
        session_id=str(uuid.uuid4()),
        user_id=session.user_id,
        created_at=now
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return SessionResponse(
        session_id=db_session.session_id,
        user_id=db_session.user_id,
        created_at=str(db_session.created_at)
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in production, use dependency injection)
km_instance = None


# ============================================================================
# Pydantic Models (Request/Response Schemas)
# ============================================================================

class IngredientCreate(BaseModel):
    """Schema for creating an ingredient."""
    name: str
    quantity: float
    unit: str


class RecipeCreate(BaseModel):
    """Schema for creating a recipe."""
    title: str
    ingredients: List[IngredientCreate]
    steps: List[str]
    servings: int


class RecipeResponse(BaseModel):
    """Schema for recipe response."""
    id: str
    title: str
    servings: int
    approved: bool
    popularity: int
    avg_rating: float



class UserCreate(BaseModel):
    """Schema for creating a user (new schema)."""
    name: str
    email: str
    login_identifier: str
    password_hash: str
    auth_type: str
    role_id: str
    dietary_preference: str



class UserResponse(BaseModel):
    user_id: str
    name: str
    email: str
    login_identifier: str
    role_id: str
    dietary_preference: str
    rating_score: float
    total_points: int
    created_at: str = None
    last_login_at: str = None
# ============================================================================
# Role Management Endpoints
# ============================================================================

class RoleCreate(BaseModel):
    role_id: str
    role_name: str
    description: str = None

class RoleResponse(BaseModel):
    role_id: str
    role_name: str
    description: str = None

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

# Fetch a user by email
@app.get("/users/by_email/{email}", response_model=UserResponse)
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


class RecipeSynthesisRequest(BaseModel):
    """Schema for recipe synthesis request."""
    dish_name: str
    servings: int = 2
    top_k: int = 10
    reorder: bool = True


class RecipeValidationRequest(BaseModel):
    """Schema for recipe validation."""
    approved: bool
    feedback: Optional[str] = None
    confidence: float = 0.8


class EventPlanRequest(BaseModel):
    """Schema for event planning request."""
    event_name: str
    guest_count: int
    budget_per_person: float
    dietary: Optional[str] = None


# ============================================================================
# Startup and Shutdown Events
# ============================================================================

@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    global km_instance
    init_db()
    km_instance = KitchenMind()
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



@app.post("/users", response_model=UserResponse)
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



@app.get("/users/{user_id}", response_model=UserResponse)
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

@app.post("/recipes", response_model=RecipeResponse)
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


@app.get("/recipes", response_model=List[RecipeResponse])
def list_recipes(
    approved_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List recipes from database."""
    print(f"[DEBUG] list_recipes called with approved_only={approved_only}")
    postgres_repo = PostgresRecipeRepository(db)
    if approved_only:
        recipes = postgres_repo.approved()
        print(f"[DEBUG] Approved recipes: {recipes}")
    else:
        # Use new Recipe model for unfiltered listing
        db_recipes = db.query(Recipe).all() if hasattr(db.query(Recipe), 'all') else []
        print(f"[DEBUG] db_recipes: {db_recipes}")
        recipes = [postgres_repo._to_model(r) for r in db_recipes]
        print(f"[DEBUG] Unfiltered recipes: {recipes}")
    response = [
        RecipeResponse(
            id=r.id,
            title=r.title,
            servings=r.servings,
            approved=r.approved,
            popularity=r.popularity,
            avg_rating=r.avg_rating()
        )
        for r in recipes
    ]
    print(f"[DEBUG] list_recipes response: {response}")
    return response


@app.get("/recipes/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: str, db: Session = Depends(get_db)):
    """Get a specific recipe."""
    postgres_repo = PostgresRecipeRepository(db)
    recipe = postgres_repo.get(recipe_id)
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return RecipeResponse(
        id=recipe.id,
        title=recipe.title,
        servings=recipe.servings,
        approved=recipe.approved,
        popularity=recipe.popularity,
        avg_rating=recipe.avg_rating()
    )


# ============================================================================
# Recipe Validation Endpoints
# ============================================================================

@app.post("/recipes/{recipe_id}/validate", response_model=RecipeResponse)
def validate_recipe(
    recipe_id: str,
    validation: RecipeValidationRequest,
    validator_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Validate a recipe with AI validator (no RMDT for AI).
    
    Workflow:
    - confidence >= 90%: AUTO-APPROVED → Added to database
    - confidence < 90% and approved=True: MANUALLY APPROVED → Added to database
    - confidence < 90% and approved=False: REJECTED → AI suggestions sent to trainer
    
    NOTE: AI validators do not receive RMDT rewards.
    """
    # Fetch validator from the database
    from Module.database import User as DBUser, Role as DBRole
    validator = db.query(DBUser).filter(DBUser.user_id == validator_id).first()
    if not validator:
        raise HTTPException(status_code=404, detail="Validator not found")
    # Normalize role
    role_obj = validator.role
    if hasattr(role_obj, 'name'):
        validator_role = role_obj.name.lower()
    else:
        validator_role = str(role_obj).lower() if role_obj else None
    if validator_role not in ["validator", "admin"]:
        raise HTTPException(status_code=403, detail="Only AI validators (role='validator') can validate recipes")
    
    try:
        # Fetch recipe from DB
        from Module.database import Recipe as DBRecipe
        db_recipe = db.query(DBRecipe).filter(DBRecipe.recipe_id == recipe_id).first()
        if not db_recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")

        # Simulate AI model call (replace with real call)
        def call_ai_model(recipe, api_key):
            # Dummy: always return 0.92 accuracy for demo
            return {"accuracy": 0.92, "reasons": []}

        # Get API key from header (for demo, use a fixed key)
        import inspect
        api_key = None
        for frame in inspect.stack():
            if 'request' in frame.frame.f_locals:
                req = frame.frame.f_locals['request']
                api_key = req.headers.get('x-api-key')
                break

        ai_result = call_ai_model(db_recipe, api_key)
        accuracy = ai_result.get("accuracy", 0)

        if accuracy > 0.9:
            db_recipe.is_published = True
            approved = True
            rejection_suggestions = []
        else:
            db_recipe.is_published = False
            approved = False
            rejection_suggestions = ai_result.get("reasons", ["Accuracy below threshold"])

        db.commit()
        db.refresh(db_recipe)

        # Update model for response
        postgres_repo = PostgresRecipeRepository(db)
        validated_recipe = postgres_repo._to_model(db_recipe)
        validated_recipe.approved = approved
        validated_recipe.validator_confidence = accuracy
        validated_recipe.rejection_suggestions = rejection_suggestions

        response = RecipeResponse(
            id=recipe_id,
            title=validated_recipe.title,
            servings=getattr(validated_recipe, "servings", 1),
            approved=validated_recipe.approved,
            popularity=getattr(validated_recipe, "popularity", 0),
            avg_rating=validated_recipe.avg_rating() if hasattr(validated_recipe, "avg_rating") else 0.0
        )
        print(f"[DEBUG] validate_recipe response: {response}")
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/recipes/{recipe_id}/rate", response_model=RecipeResponse)
def rate_recipe(
    recipe_id: str,
    rating: float = Query(..., ge=0, le=5),
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Rate a recipe."""
    print(f"[DEBUG] rate_recipe called with user_id={user_id}, recipe_id={recipe_id}, rating={rating}")
    # Fetch user from the database
    from Module.database import User as DBUser
    user = db.query(DBUser).filter(DBUser.user_id == user_id).first()
    print(f"[DEBUG] user: {user}")
    if not user:
        print("[ERROR] User not found")
        raise HTTPException(status_code=404, detail="User not found")
    try:
        # Fetch recipe from the database
        from Module.database import Recipe as DBRecipe
        db_recipe = db.query(DBRecipe).filter(DBRecipe.recipe_id == recipe_id).first()
        if not db_recipe:
            print("[ERROR] Recipe not found in DB")
            raise HTTPException(status_code=404, detail="Recipe not found")
        postgres_repo = PostgresRecipeRepository(db)
        # Persist rating in Feedback table
        postgres_repo.add_rating(recipe_id, user_id, rating)
        # Get updated ratings and average
        ratings = postgres_repo.get_ratings(recipe_id)
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        recipe_model = postgres_repo._to_model(db_recipe)
        response = RecipeResponse(
            id=recipe_id,
            title=recipe_model.title,
            servings=getattr(recipe_model, "servings", 1),
            approved=recipe_model.approved,
            popularity=getattr(recipe_model, "popularity", 0),
            avg_rating=avg_rating
        )
        print(f"[DEBUG] rate_recipe response: {response}")
        return response
    except KeyError:
        print("[ERROR] Recipe not found")
        raise HTTPException(status_code=404, detail="Recipe not found")


# ============================================================================
# Recipe Synthesis Endpoints
# ============================================================================

@app.post("/recipes/synthesize", response_model=RecipeResponse)
def synthesize_recipe(
    request: RecipeSynthesisRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Synthesize multiple recipes into one."""
    print(f"[DEBUG] synthesize_recipe called with user_id: {user_id}, request: {request}")
    # Fetch user from the database
    from Module.database import User as DBUser
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
            request.reorder
        )
        print(f"[DEBUG] Synthesis result: {result}")
        postgres_repo = PostgresRecipeRepository(db)
        print(f"[DEBUG] PostgresRecipeRepository created: {postgres_repo}")
        recipe_obj = postgres_repo.create_recipe(
            title=result.title,
            ingredients=[{"name": ing.name, "quantity": ing.quantity, "unit": ing.unit} for ing in result.ingredients],
            steps=result.steps,
            servings=result.servings,
            submitted_by=user.user_id
        )
        print(f"[DEBUG] recipe_obj returned: {recipe_obj}")
        print(f"[DEBUG] recipe_obj.id: {getattr(recipe_obj, 'id', None)}")
        # Ensure ingredients and steps are in the expected format
        response = RecipeResponse(
            id=recipe_obj.id,
            title=recipe_obj.title,
            servings=recipe_obj.servings,
            approved=getattr(recipe_obj, "approved", False),
            popularity=getattr(recipe_obj, "popularity", 0),
            avg_rating=recipe_obj.validator_confidence if hasattr(recipe_obj, "validator_confidence") else 0.0
        )
        print(f"[DEBUG] Synthesize response: {response}")
        return response
    except LookupError as e:
        print(f"[ERROR] synthesize_recipe LookupError: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"[ERROR] synthesize_recipe Exception: {e}")
        raise HTTPException(status_code=500, detail=f"Synthesis error: {str(e)}")


# ============================================================================
# Event Planning Endpoints
# ============================================================================

@app.post("/events/plan")
def plan_event(request: EventPlanRequest):
    """Plan an event with recipes."""
    try:
        plan = km_instance.event_plan(
            request.event_name,
            request.guest_count,
            request.budget_per_person,
            request.dietary
        )
        return plan
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/recipes/pending")
def get_pending_recipes(db: Session = Depends(get_db)):
    """Get all pending (unapproved) recipes."""
    postgres_repo = PostgresRecipeRepository(db)
    recipes = postgres_repo.pending()
    
    return [
        {
            "id": r.id,
            "title": r.title,
            "servings": r.servings,
            "submitted_by": r.metadata.get("submitted_by", "unknown")
        }
        for r in recipes
    ]


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return {
        "error": "Internal server error",
        "detail": str(exc)
    }


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
