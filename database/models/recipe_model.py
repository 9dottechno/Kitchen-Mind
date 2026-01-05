from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Recipe(Base):
    __tablename__ = "recipes"
    recipe_id = Column(String, primary_key=True)
    dish_name = Column(String)
    servings = Column(Integer, nullable=False, default=1)
    current_version_id = Column(String, nullable=True)  # Removed FK to break circular dependency
    created_by = Column(String, ForeignKey("users.user_id"))
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime)
    creator = relationship("User", back_populates="recipes")
    versions = relationship("RecipeVersion", back_populates="recipe")
    feedbacks = relationship("Feedback", back_populates="recipe")
    recipe_score = relationship("RecipeScore", uselist=False, back_populates="recipe")
    token_transactions = relationship("TokenTransaction", back_populates="recipe")