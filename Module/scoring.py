"""
Scoring engine for recipe ranking.
Implements weighted scoring to pick top recipes.
"""

from typing import Optional, Dict
# Import Recipe from your models module or define it here if needed
try:
    from models import Recipe  # Adjust the import path as needed
except ImportError:
    # Minimal Recipe stub for type checking and development
    class Recipe:
        def __init__(self):
            self.ingredients = []
            self.servings = 1
            self.popularity = 0
            self.metadata = {}
            self.validator_confidence = 0.0
        def avg_rating(self):
            return 0.0


class ScoringEngine:
    """Implements the weighted scoring used to pick top recipes."""
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        # default weights (must sum to 1 ideally)
        self.weights = weights or {
            'user_rating': 0.30,
            'validator_confidence': 0.20,
            'ingredient_authenticity': 0.15,
            'serving_scalability': 0.15,
            'popularity': 0.10,
            'ai_confidence': 0.10,
        }

    def ingredient_authenticity_score(self, recipe: Recipe) -> float:
        # mock heuristic: penalize unusual units or missing quantities
        score = 1.0
        for ing in recipe.ingredients:
            if not ing.unit or ing.quantity <= 0:
                score -= 0.2
        return max(0.0, score)

    def serving_scalability_score(self, recipe: Recipe) -> float:
        # mock: recipes with reasonable serving numbers get higher score
        if 1 <= recipe.servings <= 12:
            return 1.0
        elif recipe.servings <= 50:
            return 0.8
        else:
            return 0.5

    def popularity_score(self, recipe: Recipe) -> float:
        # popularity normalized (0..1) assuming max popularity ~1000
        return min(1.0, recipe.popularity / 1000.0)

    def ai_confidence_score(self, recipe: Recipe) -> float:
        # placeholder: read from metadata
        return recipe.metadata.get('ai_confidence', 0.5)

    def normalize(self, x: float, max_val: float = 5.0) -> float:
        return max(0.0, min(1.0, x / max_val))

    def score(self, recipe: Recipe) -> float:
        def get_recipe_attr(recipe, attr):
            if isinstance(recipe, dict):
                val = recipe.get(attr, None)
                # Special case for avg_rating: could be a value or a method
                if attr == 'avg_rating':
                    if callable(val):
                        return val()
                    return val if val is not None else 0.0
                return val
            # For object, handle avg_rating as method or attribute
            if attr == 'avg_rating':
                if hasattr(recipe, 'avg_rating'):
                    avg = getattr(recipe, 'avg_rating')
                    if callable(avg):
                        return avg()
                    return avg
                return 0.0
            return getattr(recipe, attr, None)

        parts = {}
        parts['user_rating'] = self.normalize(get_recipe_attr(recipe, 'avg_rating'), max_val=5.0)
        parts['validator_confidence'] = get_recipe_attr(recipe, 'validator_confidence') or 0.0
        parts['ingredient_authenticity'] = self.ingredient_authenticity_score(recipe)
        parts['serving_scalability'] = self.serving_scalability_score(recipe)
        parts['popularity'] = self.popularity_score(recipe)
        parts['ai_confidence'] = self.ai_confidence_score(recipe)

        total = sum(self.weights[k] * parts[k] for k in parts)
        return total
