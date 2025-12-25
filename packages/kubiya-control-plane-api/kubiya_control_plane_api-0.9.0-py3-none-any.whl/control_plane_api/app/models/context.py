"""Context models for managing knowledge, resources, and policies"""
from sqlalchemy import Column, String, DateTime, Text, UUID, ARRAY, CheckConstraint, ForeignKey, Index, \
    UniqueConstraint, text, desc
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from control_plane_api.app.database import Base


class AgentContext(Base):
    """Model for contextual settings (knowledge, resources, policies) for agents"""

    __tablename__ = "agent_contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete='CASCADE'), nullable=False)
    entity_type = Column(String(50), server_default=text("'agent'::character varying"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    knowledge_uuids = Column(ARRAY(Text), server_default=text("'{}'::text[]"), nullable=True)  # Array of knowledge base UUIDs
    resource_ids = Column(ARRAY(Text), server_default=text("'{}'::text[]"), nullable=True)  # Array of resource IDs from Meilisearch
    policy_ids = Column(ARRAY(Text), server_default=text("'{}'::text[]"), nullable=True)  # Array of OPA policy IDs

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    # Relationships
    agent = relationship("Agent", foreign_keys=[agent_id], viewonly=True)

    __table_args__ = (
        UniqueConstraint('agent_id', 'organization_id', name='agent_contexts_agent_id_organization_id_key'),
        Index('idx_agent_contexts_agent_id', 'agent_id'),
        Index('idx_agent_contexts_org_id', 'organization_id'),
    )

    def __repr__(self):
        return f"<AgentContext(agent_id={self.agent_id}, org_id={self.organization_id})>"


class EnvironmentContext(Base):
    """Model for contextual settings (knowledge, resources, policies) for environments"""

    __tablename__ = "environment_contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), nullable=False)
    environment_id = Column(UUID(as_uuid=True), ForeignKey('environments.id', ondelete='CASCADE'), nullable=False)
    entity_type = Column(String(50), server_default=text("'environment'::character varying"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    knowledge_uuids = Column(ARRAY(Text), server_default=text("'{}'::text[]"), nullable=True)
    resource_ids = Column(ARRAY(Text), server_default=text("'{}'::text[]"), nullable=True)
    policy_ids = Column(ARRAY(Text), server_default=text("'{}'::text[]"), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    # Relationships
    environment = relationship("Environment", foreign_keys=[environment_id], viewonly=True)

    __table_args__ = (
        UniqueConstraint('environment_id', 'organization_id', name='environment_contexts_environment_id_organization_id_key'),
        Index('idx_environment_contexts_environment_id', 'environment_id'),
        Index('idx_environment_contexts_org_id', 'organization_id'),
    )

    def __repr__(self):
        return f"<EnvironmentContext(env_id={self.environment_id}, org_id={self.organization_id})>"


class ProjectContext(Base):
    """Model for contextual settings (knowledge, resources, policies) for projects"""

    __tablename__ = "project_contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    entity_type = Column(String(50), server_default=text("'project'::character varying"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    knowledge_uuids = Column(ARRAY(Text), server_default=text("'{}'::text[]"), nullable=True)
    resource_ids = Column(ARRAY(Text), server_default=text("'{}'::text[]"), nullable=True)
    policy_ids = Column(ARRAY(Text), server_default=text("'{}'::text[]"), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    # Relationships
    project = relationship("Project", foreign_keys=[project_id], viewonly=True)

    __table_args__ = (
        UniqueConstraint('project_id', 'organization_id', name='project_contexts_project_id_organization_id_key'),
        Index('idx_project_contexts_project_id', 'project_id'),
        Index('idx_project_contexts_org_id', 'organization_id'),
    )

    def __repr__(self):
        return f"<ProjectContext(project_id={self.project_id}, org_id={self.organization_id})>"


class TeamContext(Base):
    """Model for contextual settings (knowledge, resources, policies) for teams"""

    __tablename__ = "team_contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    entity_type = Column(String(50), server_default=text("'team'::character varying"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    knowledge_uuids = Column(ARRAY(Text), server_default=text("'{}'::text[]"), nullable=True)
    resource_ids = Column(ARRAY(Text), server_default=text("'{}'::text[]"), nullable=True)
    policy_ids = Column(ARRAY(Text), server_default=text("'{}'::text[]"), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    # Relationships
    team = relationship("Team", foreign_keys=[team_id], viewonly=True)

    __table_args__ = (
        UniqueConstraint('team_id', 'organization_id', name='team_contexts_team_id_organization_id_key'),
        Index('idx_team_contexts_team_id', 'team_id'),
        Index('idx_team_contexts_org_id', 'organization_id'),
    )

    def __repr__(self):
        return f"<TeamContext(team_id={self.team_id}, org_id={self.organization_id})>"


class ContextResource(Base):
    """Model for context resources from various platforms (read-only, synced by external processes)"""

    __tablename__ = "context_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), nullable=False)
    name = Column(Text, nullable=False)  # Resource name following MindsDB convention
    platform = Column(Text, nullable=False)  # Source platform (github, slack, discord, notion, etc.)
    organization = Column(Text, nullable=False)  # Organization identifier for data isolation
    type = Column(Text, server_default=text("'integration'::text"), nullable=True)  # Type of resource
    status = Column(Text, server_default=text("'active'::text"), nullable=True)  # active, inactive, pending, error
    description = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=True)  # Maps to 'metadata' column in DB

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    __table_args__ = (
        UniqueConstraint('name', name='context_resources_name_key'),
        CheckConstraint("status = ANY (ARRAY['active'::text, 'inactive'::text, 'pending'::text, 'error'::text])", name='valid_status'),
        Index('idx_context_resources_name', 'name'),
        Index('idx_context_resources_org_platform', 'organization', 'platform'),
        Index('idx_context_resources_organization', 'organization'),
        Index('idx_context_resources_platform', 'platform'),
        Index('idx_context_resources_status', 'status'),
        Index('idx_context_resources_updated_at', desc('updated_at')),
    )

    def __repr__(self):
        return f"<ContextResource(name={self.name}, platform={self.platform}, org={self.organization})>"
