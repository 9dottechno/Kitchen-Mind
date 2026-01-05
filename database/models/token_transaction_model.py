from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class TokenTransaction(Base):
    __tablename__ = "token_transactions"
    tx_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    recipe_id = Column(String, ForeignKey("recipes.recipe_id"))
    date = Column(DateTime)
    tokens = Column(Float)
    reason = Column(String)
    related_id = Column(String)
    user = relationship("User", back_populates="token_transactions")
    recipe = relationship("Recipe", back_populates="token_transactions")
