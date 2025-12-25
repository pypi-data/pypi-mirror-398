from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from control_plane_api.app.database import Base


class JobStatus(str, enum.Enum):
    """Job status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"
    DISABLED = "disabled"


class JobTriggerType(str, enum.Enum):
    """Job trigger type enumeration"""
    CRON = "cron"
    WEBHOOK = "webhook"
    MANUAL = "manual"


class ExecutorType(str, enum.Enum):
    """Job executor routing type"""
    AUTO = "auto"  # First available worker queue with active workers
    SPECIFIC_QUEUE = "specific_queue"  # Explicit worker queue selection
    ENVIRONMENT = "environment"  # Route to specific environment


class PlanningMode(str, enum.Enum):
    """Planning mode for job execution"""
    ON_THE_FLY = "on_the_fly"  # Use planner to determine execution
    PREDEFINED_AGENT = "predefined_agent"  # Execute specific agent
    PREDEFINED_TEAM = "predefined_team"  # Execute specific team
    PREDEFINED_WORKFLOW = "predefined_workflow"  # Execute specific workflow


class Job(Base):
    """
    Model for scheduled and webhook-triggered jobs.

    Jobs can be triggered via:
    - Cron schedule (using Temporal Schedules)
    - Webhook URL (with HMAC signature verification)
    - Manual API trigger

    Jobs execute agents, teams, or workflows with configurable routing.
    """

    __tablename__ = "jobs"

    # Column order matches SQL schema
    id = Column(String(255), primary_key=True, default=lambda: f"job_{uuid.uuid4()}", nullable=False)
    organization_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    status = Column(
        String(50),
        default="active",
        nullable=False
    )
    trigger_type = Column(
        String(50),
        nullable=False
    )
    cron_schedule = Column(String(255), nullable=True)
    cron_timezone = Column(String(100), default="UTC", nullable=True)
    webhook_url_path = Column(String(500), nullable=True, unique=True)
    webhook_secret = Column(String(500), nullable=True)
    temporal_schedule_id = Column(String(255), nullable=True, unique=True)
    planning_mode = Column(
        String(50),
        default="predefined_agent",
        nullable=False
    )
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(255), nullable=True)
    entity_name = Column(String(255), nullable=True)
    prompt_template = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=True)
    executor_type = Column(
        String(50),
        default="auto",
        nullable=False
    )
    worker_queue_name = Column(String(255), nullable=True)
    environment_name = Column(String(255), nullable=True)
    config = Column(JSON, nullable=True, default={})
    execution_environment = Column(JSON, nullable=True, default={})
    last_execution_at = Column(DateTime(timezone=True), nullable=True)
    next_execution_at = Column(DateTime(timezone=True), nullable=True)
    total_executions = Column(Integer, default=0, nullable=False)
    successful_executions = Column(Integer, default=0, nullable=False)
    failed_executions = Column(Integer, default=0, nullable=False)
    execution_history = Column(JSON, nullable=True, default=[])
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    last_execution_id = Column(UUID(as_uuid=True), ForeignKey("executions.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    last_execution = relationship("Execution", foreign_keys=[last_execution_id], lazy="select")

    __table_args__ = (
        Index('idx_jobs_organization_id', 'organization_id'),
        Index('idx_jobs_name', 'organization_id', 'name'),
        Index('idx_jobs_enabled', 'enabled'),
        Index('idx_jobs_status', 'status'),
        Index('idx_jobs_trigger_type', 'trigger_type'),
        Index('idx_jobs_webhook_url_path', 'webhook_url_path'),
        Index('idx_jobs_temporal_schedule_id', 'temporal_schedule_id'),
        Index('idx_jobs_created_at', 'created_at'),
        Index('idx_jobs_next_execution_at', 'next_execution_at'),
    )

    def __repr__(self):
        return f"<Job {self.id} ({self.name}) - {self.trigger_type}:{self.status}>"


class JobExecution(Base):
    """
    Junction table linking Jobs to Executions.
    Tracks which executions were triggered by which jobs.
    """

    __tablename__ = "job_executions"

    # Column order matches SQL schema
    id = Column(String(255), primary_key=True, default=lambda: f"jobexec_{uuid.uuid4()}", nullable=False)
    job_id = Column(String(255), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(String(255), nullable=False)
    trigger_type = Column(String(50), nullable=False)
    trigger_metadata = Column(JSON, nullable=True, default={})
    execution_status = Column(String(50), nullable=True)
    execution_duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    job = relationship("Job", foreign_keys=[job_id], lazy="select")
    execution = relationship("Execution", foreign_keys=[execution_id], lazy="select")

    __table_args__ = (
        Index('idx_job_executions_job_id', 'job_id'),
        Index('idx_job_executions_organization_id', 'organization_id'),
        Index('idx_job_executions_created_at', 'created_at'),
        Index('idx_job_executions_trigger_type', 'trigger_type'),
        Index('idx_job_executions_execution_status', 'execution_status'),
        Index('idx_job_executions_execution_id', 'execution_id'),
    )

    def __repr__(self):
        return f"<JobExecution job={self.job_id} execution={self.execution_id}>"
