from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class RecipeVersion(Base):
    __tablename__ = "recipe_versions"
    version_id = Column(String, primary_key=True)
    recipe_id = Column(String, ForeignKey("recipes.recipe_id"))
    submitted_by = Column(String, ForeignKey("users.user_id"))
    submitted_at = Column(DateTime)
    status = Column(String)
    validator_confidence = Column(Float)
    base_servings = Column(Integer)
    avg_rating = Column(Float)
    recipe = relationship("Recipe", back_populates="versions")
    ingredients = relationship("Ingredient", back_populates="version")
    steps = relationship("Step", back_populates="version")
    validations = relationship("Validation", back_populates="version")
