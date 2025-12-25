"""Environment model for execution environments"""
from sqlalchemy import Column, String, DateTime, Text, ARRAY, ForeignKey, UniqueConstraint, Index, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

from control_plane_api.app.database import Base


class EnvironmentStatus(str, enum.Enum):
    """Environment status"""
    PENDING = "pending"
    PROVISIONING = "provisioning"
    READY = "ready"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    ARCHIVED = "archived"


class Environment(Base):
    """
    Execution environment - represents a worker queue environment.
    Maps to task queues in Temporal.
    """

    __tablename__ = "environments"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()"))
    organization_id = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True, server_default=text("'[]'::jsonb"))
    settings = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"))
    status = Column(String(50), nullable=True, server_default=text("'active'::character varying"))
    created_at = Column(DateTime(timezone=True), nullable=True, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=True, server_default=text("now()"))
    created_by = Column(String(255), nullable=True)
    temporal_namespace_id = Column(UUID(as_uuid=True), nullable=True) # TODO add foreign key to temporal_namespaces table later or totally remove.
    worker_token = Column(UUID(as_uuid=True), nullable=True, server_default=text("gen_random_uuid()"))
    provisioning_workflow_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    provisioned_at = Column(DateTime(timezone=True), nullable=True)
    execution_environment = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    policy_ids = Column(ARRAY(String(255)), nullable=True, server_default=text("'{}'::character varying[]"))

    __table_args__ = (
        UniqueConstraint('organization_id', 'name', name='unique_queue_name_per_org'),
        CheckConstraint(
            "status::text = ANY (ARRAY['pending'::character varying, 'provisioning'::character varying, 'ready'::character varying, 'active'::character varying, 'inactive'::character varying, 'error'::character varying, 'archived'::character varying]::text[])",
            name='task_queues_status_check'
        ),
        Index('idx_task_queues_namespace', 'temporal_namespace_id'),
        Index('idx_task_queues_worker_token', 'worker_token'),
        Index('idx_task_queues_org', 'organization_id'),
        Index('idx_task_queues_status', 'organization_id', 'status', postgresql_where=text("status::text = 'active'::text")),
        Index('idx_task_queues_name', 'organization_id', 'name'),
        Index('idx_environments_execution_environment', 'execution_environment', postgresql_using='gin'),
        Index('idx_environments_policy_ids', 'policy_ids', postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<Environment(id={self.id}, name={self.name}, organization_id={self.organization_id}, status={self.status})>"

