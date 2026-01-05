from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Ingredient(Base):
    __tablename__ = "ingredients"
    ingredient_id = Column(String, primary_key=True)
    version_id = Column(String, ForeignKey("recipe_versions.version_id"))
    name = Column(String)
    quantity = Column(Float)
    unit = Column(String)
    notes = Column(String)
    version = relationship("RecipeVersion", back_populates="ingredients")
