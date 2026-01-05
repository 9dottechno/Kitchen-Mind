from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class PointLog(Base):
    __tablename__ = "point_logs"
    log_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    activity_type = Column(String)
    quantity = Column(Integer)
    points = Column(Integer)
    created_at = Column(DateTime)
    user = relationship("User", back_populates="point_logs")