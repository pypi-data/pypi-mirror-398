"""
Execution Transition Model

Tracks state transitions for executions with AI reasoning.
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from control_plane_api.app.database import Base


class ExecutionTransition(Base):
    """Model for tracking execution state transitions with AI reasoning"""

    __tablename__ = "execution_transitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # Organization and execution references
    organization_id = Column(String, nullable=False, index=True)
    execution_id = Column(UUID(as_uuid=True), ForeignKey('executions.id', ondelete='CASCADE'), nullable=False, index=True)

    # Turn context
    turn_number = Column(Integer, nullable=False)

    # State transition
    from_state = Column(String(50), nullable=False)
    to_state = Column(String(50), nullable=False)

    # AI decision details
    reasoning = Column(String, nullable=False)
    confidence = Column(String(20), nullable=False)  # low, medium, high
    decision_factors = Column(JSON, default={}, nullable=True)

    # Model and timing
    ai_model = Column(String(100), nullable=True)
    decision_time_ms = Column(Integer, nullable=True)

    # Manual override flag
    is_manual_override = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<ExecutionTransition {self.id} ({self.from_state} → {self.to_state}) confidence={self.confidence}>"
