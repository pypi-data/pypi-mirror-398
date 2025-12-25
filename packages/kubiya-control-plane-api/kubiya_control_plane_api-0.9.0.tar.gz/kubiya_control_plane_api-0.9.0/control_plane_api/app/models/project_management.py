"""Project management and organization models"""
from sqlalchemy import Column, String, DateTime, Text, JSON, UUID, CheckConstraint, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from control_plane_api.app.database import Base


class Profile(Base):
    """Model for user profiles"""

    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    full_name = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    __table_args__ = (
        Index('idx_profiles_email', 'email'),
    )

    def __repr__(self):
        return f"<Profile(email={self.email}, full_name={self.full_name})>"


class ProjectAgent(Base):
    """Model for many-to-many relationship between projects and agents"""

    __tablename__ = "project_agents"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete='CASCADE'), nullable=False)
    role = Column(String(50), nullable=True)
    added_by = Column(String(255), nullable=True)

    # Metadata
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    # Relationships
    project = relationship("Project", foreign_keys=[project_id], viewonly=True)
    agent = relationship("Agent", foreign_keys=[agent_id], viewonly=True)

    __table_args__ = (
        Index('idx_project_agents_project', 'project_id'),
        Index('idx_project_agents_agent', 'agent_id'),
        UniqueConstraint('project_id', 'agent_id', name='unique_project_agent'),
    )

    def __repr__(self):
        return f"<ProjectAgent(project_id={self.project_id}, agent_id={self.agent_id}, role={self.role})>"


class ProjectTeam(Base):
    """Model for many-to-many relationship between projects and teams"""

    __tablename__ = "project_teams"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    role = Column(String(50), nullable=True)
    added_by = Column(String(255), nullable=True)

    # Metadata
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    # Relationships
    project = relationship("Project", foreign_keys=[project_id], viewonly=True)
    team = relationship("Team", foreign_keys=[team_id], viewonly=True)

    __table_args__ = (
        Index('idx_project_teams_project', 'project_id'),
        Index('idx_project_teams_team', 'team_id'),
        UniqueConstraint('project_id', 'team_id', name='unique_project_team'),
    )

    def __repr__(self):
        return f"<ProjectTeam(project_id={self.project_id}, team_id={self.team_id}, role={self.role})>"
