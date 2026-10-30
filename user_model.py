
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from database import Base


class User(Base):
    """Database model representing a CyberTalk user."""

    __tablename__ = "users"

    # Unique user identifier
    id = Column(Integer, primary_key=True, index=True)

    # User account details
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)

    # Store the hashed password, never the original password
    hashed_password = Column(String(255), nullable=False)

    # User permissions
    role = Column(String(20), nullable=False, default="user")

    # Account creation timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
