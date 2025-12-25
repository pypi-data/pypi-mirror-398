import enum

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Boolean,
    Integer,
    ForeignKey,
    CheckConstraint,
    Index,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from control_plane_api.app.database import Base


class WorkflowStatus(str, enum.Enum):
    """Workflow status enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Workflow(Base):
    """Workflow model for storing workflow information"""

    __tablename__ = "workflows"

    # Primary columns
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(String(255), nullable=True)

    # Workflow definition
    definition = Column(JSONB, nullable=False)
    definition_format = Column(
        String(10),
        nullable=True,
        server_default=text("'json'::character varying"),
    )

    # Status and trigger configuration
    status = Column(
        String(50),
        nullable=True,
        server_default=text("'draft'::character varying"),
    )
    trigger_type = Column(String(50), nullable=True)
    trigger_config = Column(JSONB, nullable=True)

    # Upstash integration
    upstash_schedule_id = Column(String(255), nullable=True)
    upstash_webhook_id = Column(String(255), nullable=True)

    # User tracking
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timestamps
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=True,
        server_default=text("now()"),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        server_default=text("now()"),
    )

    # Test workflow configuration
    is_test = Column(Boolean, nullable=True, server_default=text("false"))
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Owner information
    owner_id = Column(Text, nullable=True)
    owner_email = Column(Text, nullable=True)

    # Versioning
    version = Column(Integer, nullable=True, server_default=text("1"))

    # Tags and metadata
    tags = Column(ARRAY(Text), nullable=True, server_default=text("'{}'::text[]"))
    metadata_ = Column("metadata", JSONB, nullable=True, server_default=text("'{}'::jsonb"))

    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Constraints
    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="unique_workflow_slug_per_workspace"),
        UniqueConstraint("slug", name="workflows_slug_key"),
        CheckConstraint(
            "status::text = ANY (ARRAY['draft'::character varying::text, 'published'::character varying::text, 'archived'::character varying::text])",
            name="workflows_status_check",
        ),
        CheckConstraint(
            "trigger_type::text = ANY (ARRAY['manual'::character varying::text, 'webhook'::character varying::text, 'schedule'::character varying::text])",
            name="workflows_trigger_type_check",
        ),
        CheckConstraint(
            "definition_format::text = ANY (ARRAY['json'::character varying::text, 'yaml'::character varying::text])",
            name="workflows_definition_format_check",
        ),
        Index("idx_workflows_slug", "slug"),
        Index("idx_workflows_status", "status"),
        Index("idx_workflows_workspace_id", "workspace_id"),
        Index(
            "idx_workflows_is_test_expires",
            "is_test",
            "expires_at",
            postgresql_where=text("is_test = true AND expires_at IS NOT NULL"),
        ),
    )

    # Relationships
    workspace = relationship("Workspace", back_populates="workflows", viewonly=True)
    creator = relationship(
        "UserProfile",
        foreign_keys=[created_by],
        back_populates="created_workflows",
        viewonly=True,
    )
    updater = relationship(
        "UserProfile",
        foreign_keys=[updated_by],
        back_populates="updated_workflows",
        viewonly=True,
    )

    def __repr__(self):
        return f"<Workflow(id={self.id}, name={self.name}, status={self.status})>"
