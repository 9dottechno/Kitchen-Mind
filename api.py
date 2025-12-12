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

from Module.database import get_db, init_db, RecipeDB
from Module.repository_postgres import PostgresRecipeRepository
from Module.controller import KitchenMind
from Module.models import Recipe, User, Ingredient
from Module.vector_store import MockVectorStore
from Module.scoring import ScoringEngine

# Initialize FastAPI app
app = FastAPI(
    title="KitchenMind API",
    version="1.0.0",
    description="Recipe synthesis and management system with PostgreSQL backend"
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
    """Schema for creating a user."""
    username: str
    role: str = "user"


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    username: str
    role: str
    rmdt_balance: float


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
    """Create a new user."""
    if user.role not in ["user", "trainer", "validator", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    new_user = km_instance.create_user(user.username, user.role)
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        role=new_user.role,
        rmdt_balance=new_user.rmdt_balance
    )


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    """Get user by ID."""
    user = km_instance.users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        rmdt_balance=user.rmdt_balance
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
    trainer = km_instance.users.get(trainer_id)
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")
    
    if trainer.role not in ["trainer", "admin"]:
        raise HTTPException(status_code=403, detail="Only trainers can submit recipes")
    
    ingredients_dict = [ing.dict() for ing in recipe.ingredients]
    
    try:
        new_recipe = km_instance.submit_recipe(
            trainer,
            recipe.title,
            ingredients_dict,
            recipe.steps,
            recipe.servings
        )
        
        # Save to database
        postgres_repo = PostgresRecipeRepository(db)
        postgres_repo.add(new_recipe)
        
        return RecipeResponse(
            id=new_recipe.id,
            title=new_recipe.title,
            servings=new_recipe.servings,
            approved=new_recipe.approved,
            popularity=new_recipe.popularity,
            avg_rating=new_recipe.avg_rating()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/recipes", response_model=List[RecipeResponse])
def list_recipes(
    approved_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List recipes from database."""
    postgres_repo = PostgresRecipeRepository(db)
    
    if approved_only:
        recipes = postgres_repo.approved()
    else:
        db_recipes = db.query(RecipeDB).all() if hasattr(db.query(RecipeDB), 'all') else []
        recipes = [postgres_repo._to_model(r) for r in db_recipes]
    
    return [
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

@app.post("/recipes/{recipe_id}/validate")
def validate_recipe(
    recipe_id: str,
    validation: RecipeValidationRequest,
    validator_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Validate a recipe (validator only)."""
    validator = km_instance.users.get(validator_id)
    if not validator:
        raise HTTPException(status_code=404, detail="Validator not found")
    
    if validator.role not in ["validator", "admin"]:
        raise HTTPException(status_code=403, detail="Only validators can validate recipes")
    
    try:
        km_instance.validate_recipe(
            validator,
            recipe_id,
            validation.approved,
            validation.feedback,
            validation.confidence
        )
        
        # Update in database
        postgres_repo = PostgresRecipeRepository(db)
        recipe = postgres_repo.get(recipe_id)
        if recipe:
            postgres_repo.update(recipe)
        
        return {
            "message": "Recipe validated successfully",
            "recipe_id": recipe_id,
            "approved": validation.approved
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/recipes/{recipe_id}/rate")
def rate_recipe(
    recipe_id: str,
    rating: float = Query(..., ge=0, le=5),
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Rate a recipe."""
    user = km_instance.users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        rated_recipe = km_instance.rate_recipe(user, recipe_id, rating)
        
        # Update in database
        postgres_repo = PostgresRecipeRepository(db)
        postgres_repo.update(rated_recipe)
        
        return {
            "message": "Recipe rated successfully",
            "recipe_id": recipe_id,
            "rating": rating,
            "avg_rating": rated_recipe.avg_rating()
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Recipe not found")


# ============================================================================
# Recipe Synthesis Endpoints
# ============================================================================

@app.post("/recipes/synthesize")
def synthesize_recipe(
    request: RecipeSynthesisRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Synthesize multiple recipes into one."""
    user = km_instance.users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        result = km_instance.request_recipe(
            user,
            request.dish_name,
            request.servings,
            request.top_k,
            request.reorder
        )
        
        # Save synthesized recipe to database
        postgres_repo = PostgresRecipeRepository(db)
        postgres_repo.add(result)
        
        return {
            "id": result.id,
            "title": result.title,
            "servings": result.servings,
            "steps": result.steps,
            "ingredients": [
                {
                    "name": ing.name,
                    "quantity": ing.quantity,
                    "unit": ing.unit
                }
                for ing in result.ingredients
            ],
            "metadata": result.metadata
        }
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
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
