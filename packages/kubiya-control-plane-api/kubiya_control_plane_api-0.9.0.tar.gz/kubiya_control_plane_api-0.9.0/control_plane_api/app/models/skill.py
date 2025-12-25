from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Integer, CheckConstraint, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from control_plane_api.app.database import Base


class SkillType(str, enum.Enum):
    """Skill type enumeration"""
    FILE_SYSTEM = "file_system"
    SHELL = "shell"
    PYTHON = "python"
    DOCKER = "docker"
    SLEEP = "sleep"
    FILE_GENERATION = "file_generation"
    DATA_VISUALIZATION = "data_visualization"
    WORKFLOW_EXECUTOR = "workflow_executor"
    CUSTOM = "custom"


class SkillEntityType(str, enum.Enum):
    """Entity types that can be associated with skills"""
    AGENT = "agent"
    TEAM = "team"
    ENVIRONMENT = "environment"


class SlashCommandStatus(str, enum.Enum):
    """Slash command execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Skill(Base):
    """Skill definitions with type-specific configurations"""

    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()"))
    organization_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    skill_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True, server_default=text("'Tool'::character varying"))
    enabled = Column(Boolean, nullable=True, server_default=text("true"))
    configuration = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"))
    created_at = Column(DateTime, nullable=True, server_default=text("now()"))
    updated_at = Column(DateTime, nullable=True, server_default=text("now()"))

    # Relationships
    associations = relationship("SkillAssociation", back_populates="skill", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('organization_id', 'name', name='unique_toolset_per_org'),
        Index('idx_skills_type', 'skill_type'),
        Index('idx_skills_enabled', 'enabled'),
        CheckConstraint(
            "skill_type IN ('file_system', 'shell', 'python', 'docker', 'sleep', 'file_generation', 'data_visualization', 'workflow_executor', 'custom')",
            name="toolsets_type_check"
        ),
    )

    def __repr__(self):
        return f"<Skill {self.id} ({self.name}, type={self.skill_type})>"


class SkillAssociation(Base):
    """Associates skills with agents, teams, or environments"""

    __tablename__ = "skill_associations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    organization_id = Column(String(255), nullable=False, index=True)
    skill_id = Column(UUID(as_uuid=True), ForeignKey('skills.id', ondelete='CASCADE'), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    configuration_override = Column(JSON, default=dict)  # Entity-specific configuration overrides
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    skill = relationship("Skill", back_populates="associations")

    __table_args__ = (
        UniqueConstraint('skill_id', 'entity_type', 'entity_id', name='unique_skill_entity'),
        Index('ix_skill_associations_skill_id', 'skill_id'),
        Index('ix_skill_associations_entity', 'entity_type', 'entity_id'),
        Index('ix_skill_associations_org_skill', 'organization_id', 'skill_id'),
        CheckConstraint(
            "entity_type IN ('agent', 'team', 'environment')",
            name="toolset_associations_entity_type_check"
        ),
    )

    def __repr__(self):
        return f"<SkillAssociation {self.id} ({self.entity_type}:{self.entity_id} -> {self.skill_id})>"


class SlashCommand(Base):
    """Custom slash commands for workflows"""

    __tablename__ = "slash_commands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    command = Column(Text, nullable=False)
    workflow_id = Column(Text, nullable=False)
    workflow_name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)
    runner = Column(Text, nullable=True)
    args = Column(JSON, default=list)
    user_id = Column(Text, nullable=False, index=True)
    project_id = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz=datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz=datetime.timezone.utc))
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    executions = relationship("SlashCommandExecution", back_populates="command", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SlashCommand {self.id} (/{self.command})>"


class SlashCommandExecution(Base):
    """Execution history for slash commands"""

    __tablename__ = "slash_command_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    command_id = Column(UUID(as_uuid=True), ForeignKey('slash_commands.id', ondelete='CASCADE'), nullable=False)
    command = Column(Text, nullable=False)
    args = Column(JSON, default=dict)
    workflow_id = Column(Text, nullable=False)
    task_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(Text, default="pending", nullable=False)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz=datetime.timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    user_id = Column(Text, nullable=False, index=True)

    # Relationships
    command = relationship("SlashCommand", back_populates="executions")

    __table_args__ = (
        Index('ix_slash_command_executions_command_id', 'command_id'),
        Index('ix_slash_command_executions_user_id', 'user_id'),
    )

    def __repr__(self):
        return f"<SlashCommandExecution {self.id} ({self.command}, status={self.status})>"