"""Association tables for many-to-many relationships"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from control_plane_api.app.database import Base


class ParticipantRole(str, enum.Enum):
    """Role of a participant in an execution"""
    OWNER = "owner"  # User who created the execution
    COLLABORATOR = "collaborator"  # User actively participating
    VIEWER = "viewer"  # User with read-only access


class AgentEnvironment(Base):
    """Many-to-many association between agents and environments"""

    __tablename__ = "agent_environments"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    environment_id = Column(UUID(as_uuid=True), ForeignKey("environments.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(String, nullable=False)

    # Assignment metadata
    assigned_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    assigned_by = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint('agent_id', 'environment_id', name='uq_agent_environment'),
        Index('idx_agent_environments_agent_id', 'agent_id'),
        Index('idx_agent_environments_environment_id', 'environment_id'),
        Index('idx_agent_environments_org_id', 'organization_id'),
        Index('idx_agent_environments_org_env', 'organization_id', 'environment_id'),
    )

    def __repr__(self):
        return f"<AgentEnvironment(agent_id={self.agent_id}, environment_id={self.environment_id})>"


class TeamEnvironment(Base):
    """Many-to-many association between teams and environments"""

    __tablename__ = "team_environments"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    environment_id = Column(UUID(as_uuid=True), ForeignKey("environments.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(String, nullable=False)

    # Assignment metadata
    assigned_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    assigned_by = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint('team_id', 'environment_id', name='uq_team_environment'),
        Index('idx_team_environments_team_id', 'team_id'),
        Index('idx_team_environments_environment_id', 'environment_id'),
        Index('idx_team_environments_org_id', 'organization_id'),
        Index('idx_team_environments_org_env', 'organization_id', 'environment_id'),
    )

    def __repr__(self):
        return f"<TeamEnvironment(team_id={self.team_id}, environment_id={self.environment_id})>"


class ExecutionParticipant(Base):
    """Many-to-many association between executions and users (multiplayer support)"""

    __tablename__ = "execution_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(String, nullable=False)

    # User information
    user_id = Column(String, nullable=False)
    user_email = Column(String, nullable=True)
    user_name = Column(String, nullable=True)
    user_avatar = Column(String, nullable=True)

    # Participant role and status
    role = Column(
        SQLEnum(ParticipantRole, name="participant_role", values_callable=lambda x: [e.value for e in x]),
        server_default=ParticipantRole.COLLABORATOR.value,
        nullable=False
    )

    # Timestamps
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_active_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    execution = relationship("Execution", back_populates="participants")

    __table_args__ = (
        UniqueConstraint('execution_id', 'user_id', name='unique_execution_user'),
        Index('idx_execution_participants_execution', 'execution_id'),
        Index('idx_execution_participants_user', 'user_id'),
        Index('idx_execution_participants_org', 'organization_id'),
    )

    def __repr__(self):
        return f"<ExecutionParticipant(execution_id={self.execution_id}, user_id={self.user_id}, role={self.role})>"
