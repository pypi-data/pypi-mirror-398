from sqlalchemy import Column, String, DateTime, Boolean, Index
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from control_plane_api.app.database import Base


class UserPresence(Base):
    """Model for tracking user presence on agents/tasks for real-time collaboration"""

    __tablename__ = "user_presence"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # User information
    user_id = Column(String, nullable=False, index=True)
    user_email = Column(String, nullable=True)
    user_name = Column(String, nullable=True)
    user_avatar = Column(String, nullable=True)

    # What the user is viewing/interacting with
    agent_id = Column(String, nullable=True, index=True)
    session_id = Column(String, nullable=True, index=True)
    execution_id = Column(String, nullable=True, index=True)

    # Presence state
    is_active = Column(Boolean, default=True, nullable=False)
    is_typing = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_active_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Create composite index for efficient queries
    __table_args__ = (
        Index('idx_presence_lookup', 'agent_id', 'is_active', 'last_active_at'),
        Index('idx_presence_user', 'user_id', 'is_active'),
    )

    def __repr__(self):
        return f"<UserPresence(user_id={self.user_id}, agent_id={self.agent_id}, is_active={self.is_active})>"

    @property
    def is_stale(self) -> bool:
        """Check if presence is stale (no activity in last 5 minutes)"""
        if not self.last_active_at:
            return True
        return (datetime.utcnow() - self.last_active_at).total_seconds() > 300  # 5 minutes
