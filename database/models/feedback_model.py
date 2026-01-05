from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Feedback(Base):
    __tablename__ = "feedbacks"
    feedback_id = Column(String, primary_key=True)
    recipe_id = Column(String, ForeignKey("recipes.recipe_id"))
    user_id = Column(String, ForeignKey("users.user_id"))
    created_at = Column(DateTime)
    rating = Column(Integer)
    comment = Column(Text)
    flagged = Column(Boolean, default=False)
    is_revised = Column(Boolean, default=False)
    revised_at = Column(DateTime)
    recipe = relationship("Recipe", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")
