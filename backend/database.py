"""
PostgreSQL database connection and session management.
Uses SQLAlchemy with sync engine; FastAPI Depends(get_db) for routes.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Base class for all models (import this in models.py)
Base = declarative_base()

# Database URL from environment (e.g. postgresql://user:pass@localhost:5432/dbname)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/customer_support_ai",
)

# Create engine; pool_pre_ping for health checks
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=os.getenv("SQL_ECHO", "").lower() == "true",
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables. Call on app startup (after importing models)."""
    from models import Tenant, User, Integration, KnowledgeDocument, ChatLog  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency that yields a DB session. Use in FastAPI routes:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
