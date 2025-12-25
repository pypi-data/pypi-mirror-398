from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
import enum

from control_plane_api.app.database import Base


class ProjectStatus(str, enum.Enum):
    """Project status enumeration"""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"


class Project(Base):
    """Project model for organizing agents, teams, and tasks"""

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), nullable=False)
    organization_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    key = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    settings = Column(JSONB, server_default=text("'{}'::jsonb"), nullable=True)
    status = Column(String(50), server_default=text("'active'::character varying"), nullable=True)
    visibility = Column(String(20), server_default=text("'private'::character varying"), nullable=True)
    owner_id = Column(String(255), nullable=True)
    owner_email = Column(String(255), nullable=True)

    # Foreign keys
    environment_id = Column(UUID(as_uuid=True), ForeignKey("environments.id", ondelete="SET NULL"), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    environment = relationship("Environment", foreign_keys=[environment_id])

    __table_args__ = (
        UniqueConstraint('organization_id', 'key', name='unique_project_key_per_org'),
        UniqueConstraint('organization_id', 'name', name='unique_project_name_per_org'),
        CheckConstraint("status IN ('active', 'archived', 'draft')", name='projects_status_check'),
        CheckConstraint("visibility IN ('private', 'org')", name='projects_visibility_check'),
        Index('idx_projects_org_id', 'organization_id'),
        Index('idx_projects_status', 'status', postgresql_where=text("status = 'active'")),
        Index('idx_projects_visibility', 'organization_id', 'visibility'),
        Index('idx_projects_owner', 'owner_id'),
        Index('idx_projects_environment_id', 'environment_id'),
    )

    # Note: Project associations are managed through junction tables (project_agents, project_teams)
    # in Supabase, not through direct foreign keys in the SQLAlchemy models

    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"
