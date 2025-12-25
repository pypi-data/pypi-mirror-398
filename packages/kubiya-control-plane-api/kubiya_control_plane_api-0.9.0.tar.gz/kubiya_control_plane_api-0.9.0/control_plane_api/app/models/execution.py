from sqlalchemy import Column, String, DateTime, Text, JSON, Enum as SQLEnum, ForeignKey, Index, desc
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from control_plane_api.app.database import Base


class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_FOR_INPUT = "waiting_for_input"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionType(str, enum.Enum):
    AGENT = "agent"
    TEAM = "team"
    WORKFLOW = "workflow"


class ExecutionTriggerSource(str, enum.Enum):
    """How the execution was triggered"""
    USER = "user"  # Triggered by a user directly via UI/API
    JOB_CRON = "job_cron"  # Triggered by a scheduled job (cron)
    JOB_WEBHOOK = "job_webhook"  # Triggered by a webhook job
    JOB_MANUAL = "job_manual"  # Triggered manually through job trigger API
    SYSTEM = "system"  # Triggered by system/automation
    API = "api"  # Triggered directly via API
    CHAT = "chat"  # Triggered from chat interface


class Execution(Base):
    """Model for tracking agent/team/workflow executions with user attribution"""

    __tablename__ = "executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # Organization
    organization_id = Column(String(255), nullable=False, index=True)

    # What is being executed
    execution_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)  # agent_id, team_id, or workflow_id
    entity_name = Column(String(255), nullable=True)  # Cached name for display
    runner_name = Column(String(100), nullable=False)  # Cached runner name for filtering

    # User attribution - who initiated this execution
    user_id = Column(String(255), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    user_name = Column(String(255), nullable=True)
    user_avatar = Column(Text, nullable=True)

    # Trigger source - how this execution was initiated
    trigger_source = Column(
        SQLEnum(ExecutionTriggerSource, name='executiontriggersource', values_callable=lambda x: [e.value for e in x]),
        server_default=ExecutionTriggerSource.USER.value,
        nullable=False,
        index=True
    )
    trigger_metadata = Column(JSON, default={}, nullable=True)  # Additional context about the trigger (job_id, webhook payload, etc.)

    # Execution details
    prompt = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=True)
    config = Column(JSONB, default={}, nullable=True)

    # Status and results
    status = Column(String(50), default='pending', nullable=True)
    response = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Temporal workflow information
    temporal_workflow_id = Column(String(255), nullable=True, unique=True)
    temporal_run_id = Column(String(255), nullable=True)

    # Task queue information
    task_queue_name = Column(String(100), default='default', nullable=True)

    # Metadata
    usage = Column(JSONB, default={}, nullable=True)  # Token usage, cost, etc.
    execution_metadata = Column(JSONB, default={}, nullable=True)  # Additional metadata

    # Worker queue assignment
    # Using SET NULL to preserve execution history when ephemeral queues are deleted
    worker_queue_id = Column(UUID(as_uuid=True), ForeignKey('worker_queues.id', ondelete="SET NULL"), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    # Relationships
    participants = relationship("ExecutionParticipant", back_populates="execution", cascade="all, delete-orphan", lazy="selectin")
    worker_queue = relationship("WorkerQueue", foreign_keys=[worker_queue_id])

    __table_args__ = (
        Index('idx_executions_workflow', 'temporal_workflow_id', postgresql_where='temporal_workflow_id IS NOT NULL'),
        Index('idx_executions_run', 'temporal_run_id', postgresql_where='temporal_run_id IS NOT NULL'),
        Index('idx_executions_runner', 'runner_name'),
        Index('idx_executions_status', 'status'),
        Index('idx_executions_user', 'user_id'),
        Index('idx_executions_created', desc('created_at')),
        Index('idx_executions_entity', 'entity_id'),
        Index('idx_executions_org', 'organization_id'),
        Index('idx_executions_task_queue', 'task_queue_name'),
        Index('idx_executions_worker_queue_id', 'worker_queue_id'),
        Index('idx_executions_user_id', 'user_id'),
        Index('idx_executions_user_email', 'user_email'),
        Index('ix_executions_trigger_source', 'trigger_source'),
    )

    def __repr__(self):
        return f"<Execution {self.id} ({self.execution_type}:{self.entity_id}) - {self.status} by {self.user_email}>"
