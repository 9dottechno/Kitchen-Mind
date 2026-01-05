from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
import enum

class PlanStatusEnum(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"

class EventPlan(Base):
    __tablename__ = "event_plans"
    event_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    event_date = Column(DateTime)
    guest_count = Column(Integer)
    budget = Column(Float)
    preferences = Column(Text)
    plan_status = Column(Enum(PlanStatusEnum))
    user = relationship("User", back_populates="event_plans")
