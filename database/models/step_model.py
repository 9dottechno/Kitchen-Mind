from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Step(Base):
    __tablename__ = "steps"
    step_id = Column(String, primary_key=True)
    version_id = Column(String, ForeignKey("recipe_versions.version_id"))
    step_order = Column(Integer)
    instruction = Column(Text)
    minutes = Column(Integer)
    version = relationship("RecipeVersion", back_populates="steps")