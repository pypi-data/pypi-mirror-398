"""Workspace model"""
from sqlalchemy import Column, String, DateTime, Text, Integer, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from control_plane_api.app.database import Base


class Workspace(Base):
    """Model for workspaces"""

    __tablename__ = "workspaces"

    # Primary columns
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(Text, nullable=True)
    logo_url = Column(Text, nullable=True)

    # User tracking
    created_by = Column(UUID(as_uuid=True), nullable=True)
    owner_email = Column(Text, nullable=True)

    # Workspace type and settings
    type = Column(Text, nullable=False, server_default=text("'hobby'::text"))
    settings = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"))
    member_count = Column(Integer, nullable=True, server_default=text("1"))

    # Stripe integration
    stripe_customer_id = Column(Text, nullable=True)
    stripe_subscription_id = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=True, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=True, server_default=text("now()"))

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "type = ANY (ARRAY['hobby'::text, 'enterprise'::text])",
            name="workspaces_type_check"
        ),
    )

    # Relationships
    workflows = relationship("Workflow", back_populates="workspace")

    def __repr__(self):
        return f"<Workspace(id={self.id}, name={self.name}, type={self.type})>"