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

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Import all models to ensure they are registered with SQLAlchemy
    from database.models import *  # Import all models to register them
    Base.metadata.create_all(bind=engine)