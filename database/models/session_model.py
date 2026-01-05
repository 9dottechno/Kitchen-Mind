from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Session(Base):
    __tablename__ = "sessions"
    session_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    created_at = Column(DateTime)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    ip_address = Column(String)
    user_agent = Column(String)
    user = relationship("User", back_populates="sessions")
