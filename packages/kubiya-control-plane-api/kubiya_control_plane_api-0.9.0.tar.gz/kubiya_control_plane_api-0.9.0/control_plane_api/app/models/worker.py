from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Integer, ARRAY, CheckConstraint, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from control_plane_api.app.database import Base


class WorkerStatus(str, enum.Enum):
    """Worker status enumeration"""
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    DISCONNECTED = "disconnected"


class WorkerRegistrationStatus(str, enum.Enum):
    """Worker registration status"""
    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    OFFLINE = "offline"
    ERROR = "error"


class QueueStatus(str, enum.Enum):
    """Worker queue status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class ServerHealthStatus(str, enum.Enum):
    """Orchestration server health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class WorkerHeartbeat(Base):
    """Tracks active workers and their availability for task queues"""

    __tablename__ = "worker_heartbeats"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'), nullable=False)
    organization_id = Column(String(255), nullable=False)
    worker_id = Column(String(255), nullable=False)
    hostname = Column(String(255), nullable=True)
    worker_metadata = Column(JSONB, server_default=text("'{}'::jsonb"), nullable=True)
    last_heartbeat = Column(DateTime(timezone=True), server_default=text('now()'), nullable=True)
    status = Column(String(50), server_default=text("'active'::character varying"), nullable=True)
    tasks_processed = Column(Integer, server_default=text('0'), nullable=True)
    current_task_id = Column(UUID(as_uuid=True), nullable=True)
    registered_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=True)
    worker_registration_id = Column(UUID(as_uuid=True), ForeignKey('workers.id', ondelete='SET NULL'), nullable=True)
    worker_queue_id = Column(UUID(as_uuid=True), ForeignKey('worker_queues.id', ondelete='CASCADE'), nullable=True)
    environment_name = Column(String(255), nullable=True)
    worker_token = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    worker_queue = relationship("WorkerQueue", back_populates="heartbeats")

    __table_args__ = (
        UniqueConstraint('organization_id', 'worker_id', name='unique_worker_instance'),
        CheckConstraint(
            "status IN ('active', 'idle', 'busy', 'offline', 'disconnected')",
            name="worker_heartbeats_status_check"
        ),
        Index('idx_worker_heartbeats_queue', 'worker_queue_id'),
        Index('idx_worker_heartbeats_environment', 'organization_id', 'environment_name'),
        Index('idx_worker_heartbeats_token', 'worker_token'),
        Index('idx_worker_heartbeats_org', 'organization_id'),
        Index('idx_worker_heartbeats_status', 'organization_id', 'status'),
        Index('idx_worker_heartbeats_last_heartbeat', 'last_heartbeat'),
        Index('idx_worker_heartbeats_org_status', 'organization_id', 'status'),
        Index('idx_worker_heartbeats_queue_status_heartbeat', 'worker_queue_id', 'status', text('last_heartbeat DESC')),
        Index('idx_worker_heartbeats_org_status_heartbeat', 'organization_id', 'status', text('last_heartbeat DESC')),
    )

    def __repr__(self):
        return f"<WorkerHeartbeat {self.id} (worker={self.worker_id}, status={self.status})>"


class WorkerQueue(Base):
    """Worker queues within environments for fine-grained worker management"""

    __tablename__ = "worker_queues"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'), nullable=False)
    organization_id = Column(Text, nullable=False)
    environment_id = Column(UUID(as_uuid=True), ForeignKey('environments.id', ondelete='CASCADE'), nullable=False)
    name = Column(Text, nullable=False)
    display_name = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(Text, server_default=text("'active'::text"), nullable=False)
    max_workers = Column(Integer, nullable=True)
    heartbeat_interval = Column(Integer, server_default=text('30'), nullable=True)
    tags = Column(ARRAY(Text), server_default=text("'{}'::text[]"), nullable=True)
    settings = Column(JSONB, server_default=text("'{}'::jsonb"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)
    created_by = Column(Text, nullable=True)

    # Ephemeral queue support (for temporary/on-demand workers)
    ephemeral = Column(Boolean, server_default=text('false'), nullable=False)
    single_execution_mode = Column(Boolean, server_default=text('false'), nullable=False)
    auto_cleanup_after_seconds = Column(Integer, nullable=True)
    parent_execution_id = Column(Text, nullable=True)

    # Relationships
    environment = relationship("Environment", foreign_keys=[environment_id])
    heartbeats = relationship("WorkerHeartbeat", back_populates="worker_queue")

    __table_args__ = (
        UniqueConstraint('environment_id', 'name', name='worker_queues_environment_id_name_key'),
        Index('idx_worker_queues_org', 'organization_id'),
        Index('idx_worker_queues_env', 'environment_id'),
        Index('idx_worker_queues_status', 'status'),
        Index('idx_worker_queues_ephemeral_cleanup', 'ephemeral', 'created_at',
              postgresql_where=text("ephemeral = true")),
        Index('idx_worker_queues_parent_execution', 'parent_execution_id',
              postgresql_where=text("parent_execution_id IS NOT NULL")),
    )

    def __repr__(self):
        return f"<WorkerQueue {self.id} (name={self.name}, org={self.organization_id})>"


class Worker(Base):
    """Registered workers for task queues"""

    __tablename__ = "workers"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'), nullable=False)
    organization_id = Column(String(255), nullable=False)
    task_queue_id = Column(UUID(as_uuid=True), ForeignKey('environments.id', ondelete='CASCADE'), nullable=False)
    worker_name = Column(String(255), nullable=True)
    worker_token = Column(UUID(as_uuid=True), nullable=False)
    worker_id = Column(String(255), nullable=True)
    capabilities = Column(JSONB, server_default=text("'{}'::jsonb"), nullable=True)
    environment = Column(JSONB, server_default=text("'{}'::jsonb"), nullable=True)
    metadata_ = Column("metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=True)
    status = Column(String(50), server_default=text("'registered'::character varying"), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=True)
    registered_by = Column(String(255), nullable=True)

    # Relationships
    task_queue = relationship("Environment", foreign_keys=[task_queue_id])

    __table_args__ = (
        UniqueConstraint('worker_token', name='unique_worker_token'),
        CheckConstraint(
            "status IN ('registered', 'active', 'inactive', 'offline', 'error')",
            name="workers_status_check"
        ),
        Index('idx_workers_org', 'organization_id'),
        Index('idx_workers_task_queue', 'task_queue_id'),
        Index('idx_workers_token', 'worker_token'),
        Index('idx_workers_status', 'organization_id', 'status'),
    )

    def __repr__(self):
        return f"<Worker {self.id} (name={self.worker_name}, status={self.status})>"


class OrchestrationServerHealth(Base):
    """Health tracking for orchestration servers"""

    __tablename__ = "orchestration_server_health"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    server_id = Column(Text, ForeignKey('orchestration_servers.id', ondelete='CASCADE'), nullable=False)
    status = Column(Text, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    checked_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=True)
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('healthy', 'degraded', 'unhealthy')", name="orchestration_server_health_status_check"),
        Index('idx_orchestration_server_health_checked_at', text('checked_at DESC')),
        Index('idx_orchestration_server_health_server_id', 'server_id'),
    )

    def __repr__(self):
        return f"<OrchestrationServerHealth {self.id} (server={self.server_id}, status={self.status})>"


class OrchestrationServer(Base):
    """Orchestration servers configuration"""

    __tablename__ = "orchestration_servers"

    id = Column(Text, primary_key=True, server_default=text("(gen_random_uuid())::text"), nullable=False)
    user_id = Column(Text, nullable=True)
    organization_id = Column(Text, nullable=True)
    name = Column(Text, nullable=False)
    endpoint = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    config = Column(JSONB, server_default=text("'{}'::jsonb"), nullable=True)
    health_check_interval_seconds = Column(Integer, server_default=text('60'), nullable=True)
    is_active = Column(Boolean, server_default=text('true'), nullable=True)
    is_default = Column(Boolean, server_default=text('false'), nullable=True)
    scope = Column(Text, server_default=text("'user'::text"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=True)

    __table_args__ = (
        Index('idx_orchestration_servers_is_active', 'is_active'),
        Index('idx_orchestration_servers_is_default', 'is_default'),
        Index('idx_orchestration_servers_scope', 'scope'),
        Index('idx_orchestration_servers_user_id', 'user_id'),
    )

    def __repr__(self):
        return f"<OrchestrationServer {self.id} (name={self.name}, active={self.is_active})>"