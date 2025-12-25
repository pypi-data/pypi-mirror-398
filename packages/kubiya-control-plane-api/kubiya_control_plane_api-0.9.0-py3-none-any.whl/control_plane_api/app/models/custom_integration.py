"""
Custom Integration Model

Allows users to define custom integration instances with:
- Environment variables
- Secrets (references to secrets vault)
- Files (content to be written to workspace)
- Contextual prompt (guidance for the agent)
"""
from sqlalchemy import Column, String, DateTime, Text, JSON, Enum, Index, CheckConstraint, text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

from control_plane_api.app.database import Base


class CustomIntegrationStatus(str, enum.Enum):
    """Custom integration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


class CustomIntegration(Base):
    """
    Custom Integration Model

    Allows users to define custom integrations that can be referenced
    in execution environments, providing:
    - Environment variables for credentials/config
    - Secrets vault references
    - Files to be written to workspace (e.g., config files, certificates)
    - Contextual prompts to guide the agent
    """
    __tablename__ = "custom_integrations"

    id = Column(UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    organization_id = Column(String(255), nullable=False, index=True)

    # Identification
    name = Column(String(255), nullable=False)  # e.g., "production-database"
    integration_type = Column(String(100), nullable=False)  # e.g., "postgres", "mongodb", "redis", "custom"
    description = Column(Text, nullable=True)

    # Status
    status = Column(Enum(CustomIntegrationStatus), nullable=False, server_default="active")

    # Configuration
    config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    # Structure:
    # {
    #   "env_vars": {
    #     "DB_HOST": "postgres.prod.example.com",
    #     "DB_PORT": "5432",
    #     "DB_NAME": "production"
    #   },
    #   "secrets": [
    #     "DB_PASSWORD",      # Reference to secrets vault
    #     "DB_SSL_CERT"       # Another secret reference
    #   ],
    #   "files": [
    #     {
    #       "path": "~/.postgresql/client.crt",
    #       "content": "-----BEGIN CERTIFICATE-----...",
    #       "mode": "0600",
    #       "description": "PostgreSQL client certificate"
    #     },
    #     {
    #       "path": "~/.postgresql/client.key",
    #       "secret_ref": "POSTGRES_CLIENT_KEY",  # Load content from secret
    #       "mode": "0600",
    #       "description": "PostgreSQL client key"
    #     }
    #   ],
    #   "context_prompt": "This is a PostgreSQL production database. Always use connection pooling. Max connections: 100.",
    #   "connection_test": {
    #     "enabled": true,
    #     "command": "pg_isready -h $DB_HOST -p $DB_PORT",
    #     "timeout": 5
    #   }
    # }

    # Metadata
    tags = Column(JSONB, nullable=True, server_default=text("'[]'::jsonb"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(255), nullable=True)

    # Constraints
    __table_args__ = (
        Index("idx_custom_integrations_org_name", "organization_id", "name", unique=True),
        Index("idx_custom_integrations_org_type", "organization_id", "integration_type"),
        Index("idx_custom_integrations_status", "status"),
        CheckConstraint("name != ''", name="ck_custom_integration_name_not_empty"),
        CheckConstraint("integration_type != ''", name="ck_custom_integration_type_not_empty"),
    )

    def __repr__(self):
        return f"<CustomIntegration(id={self.id}, name={self.name}, type={self.integration_type})>"
