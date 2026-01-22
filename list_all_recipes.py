from sqlalchemy.orm import Session
from Module.repository_postgres import PostgresRecipeRepository
from Module.database import get_db

def list_all_recipes(db: Session):
    repo = PostgresRecipeRepository(db)
    recipes = repo.list()
    for r in recipes:
        print(f"ID: {r.id}, Title: {r.title}, Approved: {getattr(r, 'approved', None)}")
        print(f"  Ingredients: {r.ingredients}")
        print(f"  Steps: {r.steps}")
        print("-")

if __name__ == "__main__":
    db = next(get_db())
    list_all_recipes(db)
