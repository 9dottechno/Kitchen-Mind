from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class RecipeScore(Base):
    __tablename__ = "recipe_scores"
    score_id = Column(String, primary_key=True)
    recipe_id = Column(String, ForeignKey("recipes.recipe_id"))
    user_rating_score = Column(Float)
    validator_confidence_score = Column(Float)
    ingredient_authenticity_score = Column(Float)
    serving_scalability_score = Column(Float)
    popularity_score = Column(Float)
    ai_confidence_score = Column(Float)
    final_score = Column(Float)
    calculated_at = Column(DateTime)
    recipe = relationship("Recipe", back_populates="recipe_score")
