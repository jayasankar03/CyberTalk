
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Get the current project directory
BASE_DIR = Path(__file__).resolve().parent

# Define the SQLite database location
DATABASE_PATH = BASE_DIR / "cybertalk.db"

# Create the SQLite database URL
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"


# Create the database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)


# Create a database session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Base class for all database models
class Base(DeclarativeBase):
    pass


# Database session dependency
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# Create all registered database tables
def create_db_tables():
    Base.metadata.create_all(bind=engine)
