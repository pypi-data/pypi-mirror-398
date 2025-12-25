from sqlalchemy import Column, String, DateTime, Text, Enum as SQLEnum, ForeignKey, UniqueConstraint, ARRAY, Index, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from control_plane_api.app.database import Base


class TeamStatus(str, enum.Enum):
    """Team status enumeration"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    IDLE = "idle"


class RuntimeType(str, enum.Enum):
    """Team runtime type enumeration"""

    DEFAULT = "default"
    CLAUDE_CODE = "claude_code"


class Team(Base):
    """Team model for storing team information"""

    __tablename__ = "teams"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), nullable=False)
    organization_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), server_default=text("'active'::character varying"), nullable=True)
    coordination_type = Column(String(50), server_default=text("'sequential'::character varying"), nullable=True)
    configuration = Column(JSONB, server_default=text("'{}'::jsonb"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=True)
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    state = Column(JSONB, server_default=text("'{}'::jsonb"), nullable=True)
    error_message = Column(Text, nullable=True)
    visibility = Column(String(20), server_default=text("'private'::character varying"), nullable=True)
    environment_id = Column(PG_UUID(as_uuid=True), ForeignKey("environments.id", ondelete="SET NULL"), nullable=True)
    skill_ids = Column(ARRAY(PG_UUID(as_uuid=True)), server_default=text("'{}'::uuid[]"), nullable=True)
    execution_environment = Column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    policy_ids = Column(ARRAY(String(255)), server_default=text("'{}'::character varying[]"), nullable=True)
    runtime = Column(
        SQLEnum(RuntimeType, name="runtimetype", values_callable=lambda x: [e.value for e in x]),
        server_default=RuntimeType.DEFAULT.value,
        nullable=False,
    )
    model_id = Column(String, nullable=True)

    # Relationships
    environment = relationship("Environment", foreign_keys=[environment_id])
    agents = relationship("Agent", back_populates="team")

    # Many-to-many relationship with environments
    environment_associations = relationship(
        "TeamEnvironment",
        foreign_keys="TeamEnvironment.team_id",
        cascade="all, delete-orphan",
        lazy="select"
    )

    __table_args__ = (
        UniqueConstraint('organization_id', 'name', name='teams_organization_id_name_key'),
        UniqueConstraint('organization_id', 'name', name='uq_team_org_name'),
        CheckConstraint("visibility IN ('private', 'org')", name='teams_visibility_check'),
        Index('idx_teams_status', 'status'),
        Index('idx_teams_org', 'organization_id'),
        Index('idx_teams_visibility', 'organization_id', 'visibility'),
        Index('ix_teams_runtime', 'runtime'),
        Index('idx_teams_environment_id', 'environment_id'),
        Index('idx_teams_toolset_ids', 'skill_ids', postgresql_using='gin'),
        Index('idx_teams_execution_environment', 'execution_environment', postgresql_using='gin'),
        Index('idx_teams_policy_ids', 'policy_ids', postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<Team(id={self.id}, name={self.name}, status={self.status})>"

    @property
    def environment_ids(self):
        return [assoc.environment_id for assoc in self.environment_associations]

