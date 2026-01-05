from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Validation(Base):
    __tablename__ = "validations"
    validation_id = Column(String, primary_key=True)
    version_id = Column(String, ForeignKey("recipe_versions.version_id"))
    validated_at = Column(DateTime)
    approved = Column(Boolean)
    feedback = Column(Text)
    version = relationship("RecipeVersion", back_populates="validations")