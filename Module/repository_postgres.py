"""
PostgreSQL-based repository implementation for KitchenMind.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from .database import RecipeDB, IngredientDB, StepDB
from Module.models import Recipe, Ingredient


class PostgresRecipeRepository:
    """Repository using PostgreSQL for persistent storage."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add(self, recipe: Recipe):
        """Add a new recipe to the database."""
        db_recipe = RecipeDB(
            id=recipe.id,
            title=recipe.title,
            servings=recipe.servings,
            metadata=recipe.metadata,
            ratings=recipe.ratings,
            validator_confidence=recipe.validator_confidence,
            popularity=recipe.popularity,
            approved=recipe.approved
        )
        
        # Add ingredients
        for ing in recipe.ingredients:
            db_ing = IngredientDB(
                name=ing.name,
                quantity=ing.quantity,
                unit=ing.unit
            )
            db_recipe.ingredients.append(db_ing)
        
        # Add steps
        for idx, step_text in enumerate(recipe.steps):
            db_step = StepDB(order=idx, text=step_text)
            db_recipe.steps.append(db_step)
        
        self.db.add(db_recipe)
        self.db.commit()
        self.db.refresh(db_recipe)
    
    def get(self, recipe_id: str) -> Optional[Recipe]:
        """Get a recipe by ID."""
        db_recipe = self.db.query(RecipeDB).filter(RecipeDB.id == recipe_id).first()
        if not db_recipe:
            return None
        return self._to_model(db_recipe)
    
    def find_by_title(self, title: str) -> List[Recipe]:
        """Find recipes by title (case-insensitive)."""
        db_recipes = self.db.query(RecipeDB).filter(
            RecipeDB.title.ilike(f"%{title}%")
        ).all()
        return [self._to_model(r) for r in db_recipes]
    
    def pending(self) -> List[Recipe]:
        """Get all pending (unapproved) recipes."""
        db_recipes = self.db.query(RecipeDB).filter(RecipeDB.approved == False).all()
        return [self._to_model(r) for r in db_recipes]
    
    def approved(self) -> List[Recipe]:
        """Get all approved recipes."""
        db_recipes = self.db.query(RecipeDB).filter(RecipeDB.approved == True).all()
        return [self._to_model(r) for r in db_recipes]
    
    def update(self, recipe: Recipe):
        """Update an existing recipe."""
        db_recipe = self.db.query(RecipeDB).filter(RecipeDB.id == recipe.id).first()
        if not db_recipe:
            raise ValueError(f"Recipe {recipe.id} not found")
        
        db_recipe.title = recipe.title
        db_recipe.servings = recipe.servings
        db_recipe.metadata = recipe.metadata
        db_recipe.ratings = recipe.ratings
        db_recipe.validator_confidence = recipe.validator_confidence
        db_recipe.popularity = recipe.popularity
        db_recipe.approved = recipe.approved
        
        self.db.commit()
        self.db.refresh(db_recipe)
    
    def delete(self, recipe_id: str):
        """Delete a recipe by ID."""
        db_recipe = self.db.query(RecipeDB).filter(RecipeDB.id == recipe_id).first()
        if db_recipe:
            self.db.delete(db_recipe)
            self.db.commit()
    
    def _to_model(self, db_recipe: RecipeDB) -> Recipe:
        """Convert database model to Recipe model."""
        ingredients = [
            Ingredient(name=ing.name, quantity=ing.quantity, unit=ing.unit)
            for ing in db_recipe.ingredients
        ]
        steps = [s.text for s in sorted(db_recipe.steps, key=lambda x: x.order)]
        
        return Recipe(
            id=db_recipe.id,
            title=db_recipe.title,
            ingredients=ingredients,
            steps=steps,
            servings=db_recipe.servings,
            metadata=db_recipe.metadata,
            ratings=db_recipe.ratings,
            validator_confidence=db_recipe.validator_confidence,
            popularity=db_recipe.popularity,
            approved=db_recipe.approved
        )
