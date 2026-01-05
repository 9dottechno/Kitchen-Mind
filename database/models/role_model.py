from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import Base

class Role(Base):
    __tablename__ = "roles"
    role_id = Column(String, primary_key=True)  # 'user', 'trainer', 'admin' only
    role_name = Column(String, nullable=False)
    description = Column(String)
    users = relationship("User", back_populates="role")
