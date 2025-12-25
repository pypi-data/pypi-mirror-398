"""User profile model"""
from sqlalchemy import Column, DateTime, Text, CheckConstraint, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from control_plane_api.app.database import Base


class UserProfile(Base):
    """Model for user_profiles"""

    __tablename__ = "user_profiles"

    # Primary columns
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), nullable=False)
    email = Column(Text, nullable=False)
    name = Column(Text, nullable=True)
    first_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)

    # Auth integration
    auth0_id = Column(Text, nullable=True)

    # Workspace association
    workspace_type = Column(Text, nullable=True)
    primary_workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=True, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=True, server_default=text("now()"))

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "workspace_type = ANY (ARRAY['hobby'::text, 'enterprise'::text])",
            name="user_profiles_workspace_type_check"
        ),
    )

    # Relationships
    created_workflows = relationship(
        "Workflow",
        foreign_keys="Workflow.created_by",
        back_populates="creator"
    )
    updated_workflows = relationship(
        "Workflow",
        foreign_keys="Workflow.updated_by",
        back_populates="updater"
    )

    def __repr__(self):
        return f"<UserProfile(id={self.id}, email={self.email}, name={self.name})>"