
from sqlalchemy import Column, DateTime, Integer, String, Boolean
from sqlalchemy.sql import func

from database import Base


class User(Base):
    """Database model representing a CyberTalk user."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    hashed_password = Column(String(255), nullable=False)

    role = Column(
        String(20),
        nullable=False,
        default="user",
    )

    # Account lifecycle management
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )

    auth_version = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    # Profile picture filename stored on the server
    profile_picture = Column(
        String(255),
        nullable=True,
    )

    deactivated_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Protected primary administrator designation
    is_primary_admin = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
