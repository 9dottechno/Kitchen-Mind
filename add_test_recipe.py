from sqlalchemy.orm import Session
from Module.models import Recipe, Ingredient
from Module.repository_postgres import PostgresRecipeRepository
from Module.database import get_db

# Example test recipe data
def add_test_recipe(db: Session):
    repo = PostgresRecipeRepository(db)
    repo.create_recipe(
        title="Test Idli",
        ingredients=[
            {"name": "Rice", "quantity": 2, "unit": "cups"},
            {"name": "Urad dal", "quantity": 1, "unit": "cup"},
            {"name": "Salt", "quantity": 0.5, "unit": "tsp"}
        ],
        steps=[
            "Soak rice and urad dal separately for 4-6 hours.",
            "Grind them to a smooth batter.",
            "Mix and ferment overnight.",
            "Add salt, pour into idli molds, and steam for 10-12 minutes."
        ],
        servings=4
    )
    print("Test recipe added.")

if __name__ == "__main__":
    import sys
    from Module.database import init_db
    db = next(get_db())
    add_test_recipe(db)
