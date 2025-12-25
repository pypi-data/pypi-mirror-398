from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Enum, UniqueConstraint, Index, CheckConstraint, \
    text, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY as PG_ARRAY, JSONB
import enum

from sqlalchemy.orm import relationship

from control_plane_api.app.database import Base


class AgentStatus(str, enum.Enum):
    """Agent status enumeration"""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class RuntimeType(str, enum.Enum):
    """Agent runtime type enumeration"""

    DEFAULT = "default"  # Agno-based runtime (current implementation)
    CLAUDE_CODE = "claude_code"  # Claude Code SDK runtime


class Agent(Base):
    """Agent model for storing agent information"""

    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), nullable=False)
    organization_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), server_default='idle', nullable=True)
    capabilities = Column(JSONB, server_default=text("'[]'::jsonb"), nullable=True)
    configuration = Column(JSONB, server_default=text("'{}'::jsonb"), nullable=True)
    model_id = Column(String(100), nullable=True)
    model_config = Column(JSONB, server_default=text("'{}'::jsonb"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    state = Column(JSONB, server_default=text("'{}'::jsonb"), nullable=True)
    error_message = Column(Text, nullable=True)
    runner_name = Column(String(100), nullable=True)
    visibility = Column(String(20), server_default='private', nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    environment_id = Column(UUID(as_uuid=True), ForeignKey("environments.id", ondelete="SET NULL"), nullable=True)
    toolset_ids = Column(PG_ARRAY(UUID(as_uuid=True)), server_default=text("'{}'::uuid[]"), nullable=True)
    runtime = Column(String(50), server_default='default', nullable=False)
    execution_environment = Column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    policy_ids = Column(PG_ARRAY(String(255)), server_default=text("'{}'::character varying[]"), nullable=True)

    # Relationships
    team = relationship("Team", back_populates="agents")
    project = relationship("Project", foreign_keys=[project_id])
    environment = relationship("Environment", foreign_keys=[environment_id])

    # Many-to-many relationship with environments
    environment_associations = relationship(
        "AgentEnvironment",
        foreign_keys="AgentEnvironment.agent_id",
        cascade="all, delete-orphan",
        lazy="select"
    )

    __table_args__ = (
        UniqueConstraint('organization_id', 'name', name='agents_organization_id_name_key'),
        CheckConstraint("visibility IN ('private', 'org')", name='agents_visibility_check'),
        CheckConstraint("runtime IN ('default', 'claude_code')", name='chk_agents_runtime'),
        Index('idx_agents_status', 'status'),
        Index('idx_agents_team', 'team_id'),
        Index('idx_agents_org', 'organization_id'),
        Index('idx_agents_visibility', 'organization_id', 'visibility'),
        Index('idx_agents_team_id', 'team_id'),
        Index('idx_agents_project_id', 'project_id'),
        Index('idx_agents_environment_id', 'environment_id'),
        Index('idx_agents_toolset_ids', 'toolset_ids', postgresql_using='gin'),
        Index('idx_agents_runtime', 'runtime'),
        Index('idx_agents_org_runtime', 'organization_id', 'runtime'),
        Index('idx_agents_execution_environment', 'execution_environment', postgresql_using='gin'),
        Index('idx_agents_policy_ids', 'policy_ids', postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<Agent(id={self.id}, name={self.name}, status={self.status})>"
