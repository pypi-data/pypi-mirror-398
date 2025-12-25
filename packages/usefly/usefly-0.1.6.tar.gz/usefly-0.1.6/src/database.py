"""
Database configuration and initialization for Usefly.
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Base class for all models
Base = declarative_base()

# Database file path - use fixed path in Docker, relative path otherwise
import os
if os.environ.get("IN_DOCKER"):
    DB_PATH = Path("/app/src/data/usefly.db")
else:
    DB_PATH = Path(__file__).parent / "data" / "usefly.db"

# Create data directory if it doesn't exist
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Create engine with SQLite
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite specific
    echo=False,  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize the database by creating all tables."""
    # Import models to register them with Base
    from src import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
