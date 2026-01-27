"""
Scoring engine for recipe ranking.
Implements weighted scoring to pick top recipes.
"""

from typing import Optional, Dict
from .models import Recipe


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
        # mock heuristic: penalize unusual units or missing quantities (0-5 scale)
        score = 5.0
        for ing in recipe.ingredients:
            if not ing.unit or ing.quantity <= 0:
                score -= 1.0
        return max(0.0, score)

    def serving_scalability_score(self, recipe: Recipe) -> float:
        # mock: recipes with reasonable serving numbers get higher score (0-5 scale)
        if 1 <= recipe.servings <= 12:
            return 5.0
        elif recipe.servings <= 50:
            return 4.0
        else:
            return 1.5

    def popularity_score(self, recipe: Recipe) -> float:
        # popularity on 0-5 scale (assuming max popularity ~1000)
        normalized = min(1.0, recipe.popularity / 1000.0)
        return normalized * 5.0

    def ai_confidence_score(self, recipe: Recipe) -> float:
        # placeholder: read from metadata (0-5 scale)
        raw = recipe.metadata.get('ai_confidence', 0.5)
        return raw * 5.0

    def normalize(self, x: float, max_val: float = 5.0) -> float:
        # normalize from 0-5 scale to 0-5 scale
        normalized = max(0.0, min(1.0, x / max_val))
        return normalized * 5.0

    def score(self, recipe: Recipe) -> float:
        parts = {}
        parts['user_rating'] = self.normalize(recipe.avg_rating(), max_val=5.0)
        parts['ai_confidence'] = recipe.ai_confidence_score
        parts['ingredient_authenticity'] = self.ingredient_authenticity_score(recipe)
        parts['serving_scalability'] = self.serving_scalability_score(recipe)
        parts['popularity'] = self.popularity_score(recipe)

        total = sum(self.weights[k] * parts.get(k, 1.0) for k in self.weights if k != 'validator_confidence')
        return total
