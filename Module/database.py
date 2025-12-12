"""
SQLAlchemy database setup and ORM models for KitchenMind.
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, JSON, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://kitchenmind:password@localhost:5432/kitchenmind"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class RecipeDB(Base):
    """Recipe database model."""
    __tablename__ = "recipes"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    servings = Column(Integer)
    meta = Column("metadata", JSON, default={})
    ratings = Column(JSON, default=[])
    validator_confidence = Column(Float, default=0.0)
    popularity = Column(Integer, default=0)
    approved = Column(Boolean, default=False)
    
    ingredients = relationship("IngredientDB", back_populates="recipe", cascade="all, delete-orphan")
    steps = relationship("StepDB", back_populates="recipe", cascade="all, delete-orphan")


class IngredientDB(Base):
    """Ingredient database model."""
    __tablename__ = "ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(String, ForeignKey("recipes.id"))
    name = Column(String)
    quantity = Column(Float)
    unit = Column(String)
    
    recipe = relationship("RecipeDB", back_populates="ingredients")


class StepDB(Base):
    """Recipe step database model."""
    __tablename__ = "steps"
    
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(String, ForeignKey("recipes.id"))
    order = Column(Integer)
    text = Column(String)
    
    recipe = relationship("RecipeDB", back_populates="steps")


class UserDB(Base):
    """User database model."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    role = Column(String)
    rmdt_balance = Column(Float, default=0.0)


def get_db():
    """Get database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
