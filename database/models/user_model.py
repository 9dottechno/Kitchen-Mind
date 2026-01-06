
# User table mapping
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from .base import Base

# Enums
class DietaryPreferenceEnum(enum.Enum):
    VEG = "VEG"
    NON_VEG = "NON_VEG"

class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    login_identifier = Column(String, unique=True)
    password_hash = Column(String)
    auth_type = Column(String)
    otp_hash = Column(String)
    otp_expires_at = Column(DateTime)
    otp_verified = Column(Boolean, default=False)
    role_id = Column(String, ForeignKey("roles.role_id"))
    dietary_preference = Column(Enum(DietaryPreferenceEnum))
    rating_score = Column(Float, default=0.0)
    total_points = Column(Integer, default=0)
    created_at = Column(DateTime)
    last_login_at = Column(DateTime)
    role = relationship("Role", back_populates="users")
    is_super_admin = Column(Boolean, default=False)
    created_by = Column(String)  # user_id of creator (admin)
    admin_action_type = Column(String)  # last admin action type (if admin)
    admin_action_target_type = Column(String)  # last admin action target type
    admin_action_target_id = Column(String)  # last admin action target id
    admin_action_description = Column(Text)  # last admin action description
    admin_action_created_at = Column(DateTime)  # last admin action timestamp
    sessions = relationship("Session", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")
    point_logs = relationship("PointLog", back_populates="user")
    token_transactions = relationship("TokenTransaction", back_populates="user")
    event_plans = relationship("EventPlan", back_populates="user")
    recipes = relationship("Recipe", back_populates="creator")
