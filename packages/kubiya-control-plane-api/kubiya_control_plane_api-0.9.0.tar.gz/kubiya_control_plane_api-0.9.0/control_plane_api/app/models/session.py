from sqlalchemy import Column, DateTime, Text, Index, text, desc
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from control_plane_api.app.database import Base


class Session(Base):
    """Session model for storing agent session information"""

    __tablename__ = "sessions"

    execution_id = Column(Text, primary_key=True, nullable=False)
    session_id = Column(Text, nullable=False)
    organization_id = Column(Text, nullable=False)
    user_id = Column(Text, nullable=True)
    messages = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    metadata_ = Column("metadata", JSONB, nullable=True, server_default=text("'{}'::jsonb"))
    created_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now())

    __table_args__ = (
        Index("idx_sessions_organization_id", "organization_id"),
        Index("idx_sessions_session_id", "session_id"),
        Index("idx_sessions_updated_at", desc('updated_at')),
    )

    def __repr__(self):
        return f"<Session(execution_id={self.execution_id}, session_id={self.session_id}, organization_id={self.organization_id})>"
