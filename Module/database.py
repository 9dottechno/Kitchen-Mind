# --- Recipe Score Calculation Utility ---
def update_recipe_score(db, recipe_id, ai_scores=None, popularity=None):
    """
    Update or create RecipeScore for a recipe.
    ai_scores: dict with keys 'validator_confidence_score', 'ingredient_authenticity_score',
        'serving_scalability_score', 'ai_confidence_score'.
    popularity: float (calculated from user interactions)
    """
    from sqlalchemy import func
    from datetime import datetime
    # 1. Calculate user_rating_score
    # Find all version_ids for this recipe
    version_ids = [v.version_id for v in db.query(RecipeVersion).filter(RecipeVersion.recipe_id == recipe_id).all()]
    avg_rating = 0.0
    if version_ids:
        avg_rating = db.query(func.avg(Feedback.rating)).filter(Feedback.version_id.in_(version_ids)).scalar() or 0.0
    # Ensure avg_rating is a float (func.avg may return Decimal)
    try:
        avg_rating = float(avg_rating)
    except Exception:
        avg_rating = 0.0

    # 2. Get or create RecipeScore
    score = db.query(RecipeScore).filter(RecipeScore.recipe_id == recipe_id).first()
    if not score:
        import uuid
        score = RecipeScore(score_id=str(uuid.uuid4()), recipe_id=recipe_id)
        db.add(score)

    # 3. Set scores
    score.user_rating_score = avg_rating
    if ai_scores:
        score.validator_confidence_score = ai_scores.get('validator_confidence_score', 0.0)
        score.ingredient_authenticity_score = ai_scores.get('ingredient_authenticity_score', 0.0)
        score.serving_scalability_score = ai_scores.get('serving_scalability_score', 0.0)
        score.ai_confidence_score = ai_scores.get('ai_confidence_score', 0.0)
    if popularity is not None:
        score.popularity_score = popularity

    # 4. Calculate final_score (example weights, adjust as needed)
    weights = {
        'user_rating_score': 0.2,
        'validator_confidence_score': 0.2,
        'ingredient_authenticity_score': 0.15,
        'serving_scalability_score': 0.15,
        'popularity_score': 0.1,
        'ai_confidence_score': 0.2
    }
    final = (
        (score.user_rating_score or 0) * weights['user_rating_score'] +
        (score.validator_confidence_score or 0) * weights['validator_confidence_score'] +
        (score.ingredient_authenticity_score or 0) * weights['ingredient_authenticity_score'] +
        (score.serving_scalability_score or 0) * weights['serving_scalability_score'] +
        (score.popularity_score or 0) * weights['popularity_score'] +
        (score.ai_confidence_score or 0) * weights['ai_confidence_score']
    )
    score.final_score = final
    score.calculated_at = datetime.utcnow()
    db.commit()
    db.refresh(score)
    # --- Sync validator_confidence and avg_rating to RecipeVersion ---
    from sqlalchemy import desc
    version = db.query(RecipeVersion).filter(RecipeVersion.recipe_id == recipe_id).order_by(desc(RecipeVersion.submitted_at)).first()
    if version:
        version.validator_confidence = score.validator_confidence_score
        version.avg_rating = score.user_rating_score
        db.commit()
        db.refresh(version)
    return score
"""
SQLAlchemy database setup and ORM models for KitchenMind.
"""

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean, DateTime, Text, Enum, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
import enum
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://kitchenmind:password@localhost:5432/kitchenmind"
)

from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Checks connection before use, auto-reconnects
    pool_size=10,            # Number of connections to keep in pool
    max_overflow=20,         # Extra connections allowed above pool_size
    pool_recycle=1800        # Recycle connections every 30 min
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enums
class DietaryPreferenceEnum(enum.Enum):
    VEG = "VEG"
    NON_VEG = "NON_VEG"

class PlanStatusEnum(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"

# Tables
class Role(Base):
    __tablename__ = "roles"
    role_id = Column(String, primary_key=True)  # 'user', 'trainer', 'admin' only
    role_name = Column(String, nullable=False)
    description = Column(String)
    user = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "user"
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
    credit = Column(Float, default=0.0)
    created_at = Column(DateTime)
    last_login_at = Column(DateTime)
    role = relationship("Role", back_populates="user")
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


class Session(Base):
    __tablename__ = "sessions"
    session_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("user.user_id"))
    created_at = Column(DateTime)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    ip_address = Column(String)
    user_agent = Column(String)
    user = relationship("User", back_populates="sessions")


class Recipe(Base):
    __tablename__ = "recipes"
    recipe_id = Column(String, primary_key=True)
    dish_name = Column(String)
    servings = Column(Integer, nullable=False, default=1)
    current_version_id = Column(String, nullable=True)  # Removed FK to break circular dependency
    created_by = Column(String, ForeignKey("user.user_id"))
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime)
    creator = relationship("User", back_populates="recipes")
    versions = relationship("RecipeVersion", back_populates="recipe")
    # feedbacks relationship removed; now on RecipeVersion
    recipe_score = relationship("RecipeScore", uselist=False, back_populates="recipe")
    token_transactions = relationship("TokenTransaction", back_populates="recipe")

class RecipeVersion(Base):
    __tablename__ = "recipe_versions"
    version_id = Column(String, primary_key=True)
    recipe_id = Column(String, ForeignKey("recipes.recipe_id"))
    submitted_by = Column(String, ForeignKey("user.user_id"))
    submitted_at = Column(DateTime)
    status = Column(String)
    validator_confidence = Column(Float)
    base_servings = Column(Integer)
    avg_rating = Column(Float)
    recipe = relationship("Recipe", back_populates="versions")
    ingredients = relationship("Ingredient", back_populates="version")
    steps = relationship("Step", back_populates="version")
    validations = relationship("Validation", back_populates="version")
    feedbacks = relationship("Feedback", back_populates="version")

class Ingredient(Base):
    __tablename__ = "ingredients"
    ingredient_id = Column(String, primary_key=True)
    version_id = Column(String, ForeignKey("recipe_versions.version_id"))
    name = Column(String)
    quantity = Column(Float)
    unit = Column(String)
    version = relationship("RecipeVersion", back_populates="ingredients")

class Step(Base):
    __tablename__ = "steps"
    step_id = Column(String, primary_key=True)
    version_id = Column(String, ForeignKey("recipe_versions.version_id"))
    step_order = Column(Integer)
    instruction = Column(Text)
    minutes = Column(Integer)
    version = relationship("RecipeVersion", back_populates="steps")

class Validation(Base):
    __tablename__ = "validations"
    validation_id = Column(String, primary_key=True)
    version_id = Column(String, ForeignKey("recipe_versions.version_id"))
    validated_at = Column(DateTime)
    approved = Column(Boolean)
    feedback = Column(Text)
    version = relationship("RecipeVersion", back_populates="validations")

class Feedback(Base):
    __tablename__ = "feedbacks"
    feedback_id = Column(String, primary_key=True)
    version_id = Column(String, ForeignKey("recipe_versions.version_id"))
    user_id = Column(String, ForeignKey("user.user_id"))
    created_at = Column(DateTime)
    rating = Column(Integer)
    comment = Column(Text)
    flagged = Column(Boolean, default=False)
    is_revised = Column(Boolean, default=False)
    revised_at = Column(DateTime)
    version = relationship("RecipeVersion", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")

class TokenTransaction(Base):
    __tablename__ = "token_transactions"
    tx_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("user.user_id"))
    recipe_id = Column(String, ForeignKey("recipes.recipe_id"))
    date = Column(DateTime)
    tokens = Column(Float)
    reason = Column(String)
    related_id = Column(String)
    user = relationship("User", back_populates="token_transactions")
    recipe = relationship("Recipe", back_populates="token_transactions")

class PointLog(Base):
    __tablename__ = "point_logs"
    log_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("user.user_id"))
    activity_type = Column(String)
    quantity = Column(Integer)
    points = Column(Integer)
    created_at = Column(DateTime)
    user = relationship("User", back_populates="point_logs")

class RecipeScore(Base):
    __tablename__ = "recipe_scores"
    score_id = Column(String, primary_key=True)
    recipe_id = Column(String, ForeignKey("recipes.recipe_id"))
    user_rating_score = Column(Float)
    validator_confidence_score = Column(Float)
    ingredient_authenticity_score = Column(Float)
    serving_scalability_score = Column(Float)
    popularity_score = Column(Float)
    ai_confidence_score = Column(Float)
    final_score = Column(Float)
    calculated_at = Column(DateTime)
    recipe = relationship("Recipe", back_populates="recipe_score")



class EventPlan(Base):
    __tablename__ = "event_plans"
    event_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("user.user_id"))
    event_date = Column(DateTime)
    guest_count = Column(Integer)
    budget = Column(Float)
    preferences = Column(Text)
    plan_status = Column(Enum(PlanStatusEnum))
    user = relationship("User", back_populates="event_plans")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
