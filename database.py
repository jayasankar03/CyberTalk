
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import inspect, text

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
    # Import models so SQLAlchemy registers them with Base.metadata
    import user_model
    import chat_history_model
    import password_reset_model
    import share_link_model
    import audit_log_model

    Base.metadata.create_all(bind=engine)

def migrate_user_account_lifecycle():
    """Add account lifecycle columns to existing users table."""

    inspector = inspect(engine)

    if "users" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("users")
    }

    with engine.begin() as connection:

        if "is_active" not in existing_columns:
            connection.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN is_active BOOLEAN "
                    "NOT NULL DEFAULT 1"
                )
            )

        if "deactivated_at" not in existing_columns:
            connection.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN deactivated_at DATETIME"
                )
            )
def migrate_audit_log_account_status():
    """Add account status fields to existing audit logs."""

    inspector = inspect(engine)

    if "audit_logs" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("audit_logs")
    }

    with engine.begin() as connection:

        if "previous_status" not in existing_columns:
            connection.execute(
                text(
                    "ALTER TABLE audit_logs "
                    "ADD COLUMN previous_status VARCHAR(20)"
                )
            )

        if "new_status" not in existing_columns:
            connection.execute(
                text(
                    "ALTER TABLE audit_logs "
                    "ADD COLUMN new_status VARCHAR(20)"
                )
            )

def migrate_primary_admin():
    """Add primary administrator designation to existing users."""

    inspector = inspect(engine)

    if "users" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("users")
    }

    if "is_primary_admin" not in existing_columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN is_primary_admin BOOLEAN "
                    "NOT NULL DEFAULT 0"
                )
            )

def migrate_user_auth_version():
    """Add authentication version to existing users."""

    inspector = inspect(engine)

    if "users" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("users")
    }

    if "auth_version" not in existing_columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN auth_version INTEGER "
                    "NOT NULL DEFAULT 0"
                )
            )
def migrate_user_profile_picture():
    """Add profile picture storage reference to existing users."""

    inspector = inspect(engine)

    if "users" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("users")
    }

    if "profile_picture" not in existing_columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN profile_picture VARCHAR(255)"
                )
            )
