
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from database import Base


class AuditLog(Base):
    """Database model for administrator activity and audit records."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Administrator who performed the action
    actor_user_id = Column(Integer, nullable=False, index=True)
    actor_username = Column(String(50), nullable=False)

    # Account affected by the action
    target_user_id = Column(Integer, nullable=False, index=True)
    target_username = Column(String(50), nullable=False)

    # Action details
    action = Column(String(50), nullable=False)

    # Role before and after the change
    previous_role = Column(String(20), nullable=False)
    new_role = Column(String(20), nullable=False)

    # Automatically generated database timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
