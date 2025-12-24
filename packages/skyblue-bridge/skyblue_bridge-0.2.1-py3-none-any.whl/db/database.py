"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Clean up the URL - remove quotes and extra spaces
DATABASE_URL = DATABASE_URL.strip().strip('"').strip("'")

# Debug log (will show in Docker logs)
print(f"[DB] Connecting to database: {DATABASE_URL[:30]}...")

try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,  # Max 10 concurrent connections
        max_overflow=20,  # Allow 20 more if needed
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,  # Recycle connections every hour
    )
except Exception as e:
    print(f"[DB ERROR] Failed to create engine with URL: {DATABASE_URL}")
    raise
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
