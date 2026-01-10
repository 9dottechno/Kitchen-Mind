# Script to populate recipe_scores for all existing recipes
from Module.database import SessionLocal, update_recipe_score, Recipe

def populate_all_recipe_scores():
    db = SessionLocal()
    try:
        recipes = db.query(Recipe).all()
        for recipe in recipes:
            update_recipe_score(db, recipe.recipe_id)
        print(f"Populated scores for {len(recipes)} recipes.")
    finally:
        db.close()

if __name__ == "__main__":
    populate_all_recipe_scores()
