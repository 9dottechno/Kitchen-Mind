print("[DEBUG] repository_postgres.py loaded")
"""
PostgreSQL-based repository implementation for KitchenMind.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
import uuid
from .database import Recipe, Ingredient, Step
from Module.models import Recipe, Ingredient


class PostgresRecipeRepository:

    def create_recipe(self, title, ingredients, steps, servings, submitted_by=None):
        """Create and persist a new recipe, returning the Recipe model with id."""
        db_recipe = Recipe(
            recipe_id=str(uuid.uuid4()),
            dish_name=title,
            servings=servings,
            created_by=submitted_by,
            is_published=False,
            created_at=None
        )
        # Add ingredients
        for ing in ingredients:
            db_ing = Ingredient(
                ingredient_id=str(uuid.uuid4()),
                version_id=None,
                name=ing["name"] if isinstance(ing, dict) else ing.name,
                quantity=ing["quantity"] if isinstance(ing, dict) else ing.quantity,
                unit=ing["unit"] if isinstance(ing, dict) else ing.unit,
                notes=None
            )
            db_recipe.ingredients.append(db_ing)
        # Add steps
        for idx, step_text in enumerate(steps):
            db_step = Step(
                step_id=str(uuid.uuid4()),
                version_id=None,
                step_order=idx,
                instruction=step_text,
                minutes=None
            )
            db_recipe.steps.append(db_step)
        self.db.add(db_recipe)
        self.db.commit()
        self.db.refresh(db_recipe)
        print(f"[DEBUG] After commit: db_recipe.recipe_id={getattr(db_recipe, 'recipe_id', None)}")
        # Return as Recipe model
        model = self._to_model(db_recipe)
        print(f"[DEBUG] _to_model returned: id={getattr(model, 'id', None)}")
        return model

    """Repository using PostgreSQL for persistent storage."""

    def __init__(self, db: Session):
        self.db = db
    
    def add(self, recipe: Recipe):
        """Add a new recipe to the database."""
        db_recipe = Recipe(
            recipe_id=recipe.id,
            dish_name=recipe.title,
            servings=recipe.servings,
            created_by=None,  # Set appropriately if available
            is_published=recipe.approved,
            created_at=None  # Set appropriately if available
        )
        # Add ingredients
        for ing in recipe.ingredients:
            db_ing = Ingredient(
                ingredient_id=str(uuid.uuid4()),
                version_id=None,  # Set appropriately if available
                name=ing.name,
                quantity=ing.quantity,
                unit=ing.unit,
                notes=None
            )
            db_recipe.ingredients.append(db_ing)
        # Add steps
        for idx, step_text in enumerate(recipe.steps):
            db_step = Step(
                step_id=str(uuid.uuid4()),
                version_id=None,  # Set appropriately if available
                step_order=idx,
                instruction=step_text,
                minutes=None
            )
            db_recipe.steps.append(db_step)
        self.db.add(db_recipe)
        self.db.commit()
        self.db.refresh(db_recipe)
    
    def get(self, recipe_id: str) -> Optional[Recipe]:
        """Get a recipe by ID."""
        db_recipe = self.db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
        if not db_recipe:
            return None
        return self._to_model(db_recipe)
    
    def find_by_title(self, title: str) -> List[Recipe]:
        """Find recipes by title (case-insensitive)."""
        db_recipes = self.db.query(Recipe).filter(
            Recipe.dish_name.ilike(f"%{title}%")
        ).all()
        return [self._to_model(r) for r in db_recipes]
    
    def pending(self) -> List[Recipe]:
        """Get all pending (unapproved) recipes."""
        db_recipes = self.db.query(Recipe).filter(Recipe.is_published == False).all()
        return [self._to_model(r) for r in db_recipes]
    
    def approved(self) -> List[Recipe]:
        """Get all approved recipes."""
        db_recipes = self.db.query(Recipe).filter(Recipe.is_published == True).all()
        return [self._to_model(r) for r in db_recipes]
    
    def update(self, recipe: Recipe):
        """Update an existing recipe."""
        db_recipe = self.db.query(Recipe).filter(Recipe.recipe_id == recipe.id).first()
        if not db_recipe:
            raise ValueError(f"Recipe {recipe.id} not found")
        
        db_recipe.dish_name = recipe.title
        db_recipe.servings = recipe.servings
        # Update other fields as needed
        db_recipe.is_published = recipe.approved
        
        self.db.commit()
        self.db.refresh(db_recipe)
    
    def delete(self, recipe_id: str):
        """Delete a recipe by ID."""
        db_recipe = self.db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
        if db_recipe:
            self.db.delete(db_recipe)
            self.db.commit()
    
    def _to_model(self, db_recipe: Recipe) -> Recipe:
        """Convert database model to Recipe model."""
        ingredients = [
            Ingredient(name=ing.name, quantity=ing.quantity, unit=ing.unit)
            for ing in getattr(db_recipe, 'ingredients', [])
        ]
        steps = [s.instruction for s in sorted(getattr(db_recipe, 'steps', []), key=lambda x: x.step_order)]
        model = Recipe(
            id=getattr(db_recipe, 'recipe_id', None),
            title=db_recipe.dish_name,
            ingredients=ingredients,
            steps=steps,
            servings=db_recipe.servings,
            metadata={},
            ratings=[],
            validator_confidence=0.0,
            popularity=0,
            approved=db_recipe.is_published
        )
        print(f"[DEBUG] _to_model: db_recipe.recipe_id={getattr(db_recipe, 'recipe_id', None)}, model.id={getattr(model, 'id', None)}")
        return model
