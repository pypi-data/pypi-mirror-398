"""
Custom Integrations Router

API endpoints for managing custom user-defined integrations with:
- Environment variables
- Secrets (vault references)
- Files (configs, certificates)
- Contextual prompts
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import structlog

from control_plane_api.app.database import get_db
from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.models.custom_integration import CustomIntegration, CustomIntegrationStatus

logger = structlog.get_logger()

router = APIRouter(prefix="/custom-integrations", tags=["custom-integrations"])


# Pydantic Models
class FileConfig(BaseModel):
    """Configuration for a file to be written to workspace"""
    path: str = Field(..., description="File path (e.g., ~/.postgresql/client.crt)")
    content: Optional[str] = Field(None, description="File content (direct)")
    secret_ref: Optional[str] = Field(None, description="Secret name to load content from")
    mode: Optional[str] = Field("0644", description="File permissions (octal)")
    description: Optional[str] = Field(None, description="Description of this file")

    class Config:
        json_schema_extra = {
            "example": {
                "path": "~/.postgresql/client.crt",
                "content": "-----BEGIN CERTIFICATE-----\n...",
                "mode": "0600",
                "description": "PostgreSQL client certificate"
            }
        }


class ConnectionTest(BaseModel):
    """Configuration for testing integration connectivity"""
    enabled: bool = Field(True, description="Whether to test connection")
    command: str = Field(..., description="Command to run for testing")
    timeout: int = Field(5, description="Timeout in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "command": "pg_isready -h $DB_HOST -p $DB_PORT",
                "timeout": 5
            }
        }


class CustomIntegrationConfig(BaseModel):
    """Custom integration configuration"""
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    secrets: List[str] = Field(default_factory=list, description="Secret names from vault")
    files: List[FileConfig] = Field(default_factory=list, description="Files to create")
    context_prompt: Optional[str] = Field(None, description="Contextual guidance for agent")
    connection_test: Optional[ConnectionTest] = Field(None, description="Connection test config")

    class Config:
        json_schema_extra = {
            "example": {
                "env_vars": {
                    "DB_HOST": "postgres.prod.example.com",
                    "DB_PORT": "5432",
                    "DB_NAME": "production"
                },
                "secrets": ["DB_PASSWORD", "DB_SSL_CERT"],
                "files": [
                    {
                        "path": "~/.postgresql/client.crt",
                        "secret_ref": "POSTGRES_CLIENT_CERT",
                        "mode": "0600"
                    }
                ],
                "context_prompt": "Production PostgreSQL database. Use connection pooling."
            }
        }


class CreateCustomIntegrationRequest(BaseModel):
    """Request to create a custom integration"""
    name: str = Field(..., min_length=1, max_length=255, description="Integration name")
    integration_type: str = Field(..., min_length=1, max_length=100, description="Integration type")
    description: Optional[str] = Field(None, description="Description")
    config: CustomIntegrationConfig = Field(..., description="Integration configuration")
    tags: List[str] = Field(default_factory=list, description="Tags")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "production-database",
                "integration_type": "postgres",
                "description": "Production PostgreSQL database",
                "config": {
                    "env_vars": {
                        "DB_HOST": "postgres.prod.example.com",
                        "DB_PORT": "5432"
                    },
                    "secrets": ["DB_PASSWORD"],
                    "context_prompt": "Production database - handle with care"
                },
                "tags": ["production", "database"]
            }
        }


class UpdateCustomIntegrationRequest(BaseModel):
    """Request to update a custom integration"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    integration_type: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    config: Optional[CustomIntegrationConfig] = None
    status: Optional[CustomIntegrationStatus] = None
    tags: Optional[List[str]] = None


class CustomIntegrationResponse(BaseModel):
    """Custom integration response"""
    id: str
    organization_id: str
    name: str
    integration_type: str
    description: Optional[str]
    status: str
    config: Dict[str, Any]
    tags: List[str]
    created_at: str
    updated_at: str
    created_by: Optional[str]

    class Config:
        from_attributes = True


# API Endpoints

@router.get(
    "",
    response_model=List[CustomIntegrationResponse],
    summary="List Custom Integrations",
    description="""
    List all custom integrations for the organization.

    **Filtering Options:**
    - `integration_type`: Filter by type (postgres, mongodb, redis, etc.)
    - `status`: Filter by status (active, inactive, deleted)
    - `tags`: Filter by tags (comma-separated, e.g., "production,database")

    **Default Behavior:**
    - Excludes deleted integrations unless explicitly filtered
    - Results sorted by creation date (newest first)

    **Example:**
    ```
    GET /api/v1/custom-integrations?integration_type=postgres&tags=production
    ```
    """,
    responses={
        200: {
            "description": "List of custom integrations",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "organization_id": "org-123",
                            "name": "production-postgres",
                            "integration_type": "postgres",
                            "description": "Production PostgreSQL database",
                            "status": "active",
                            "config": {
                                "env_vars": {"DB_HOST": "postgres.example.com"},
                                "secrets": ["DB_PASSWORD"]
                            },
                            "tags": ["production", "database"],
                            "created_at": "2025-12-16T10:00:00Z",
                            "updated_at": "2025-12-16T10:00:00Z",
                            "created_by": "user-123"
                        }
                    ]
                }
            }
        }
    }
)
async def list_custom_integrations(
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
    integration_type: Optional[str] = Query(None, description="Filter by integration type (e.g., postgres, mongodb, redis)"),
    status: Optional[CustomIntegrationStatus] = Query(None, description="Filter by status (active, inactive, deleted)"),
    tags: Optional[str] = Query(None, description="Filter by tags - comma-separated (e.g., production,database)"),
):
    """List all custom integrations for the organization with optional filtering."""
    org_id = organization["id"]

    query = db.query(CustomIntegration).filter(
        CustomIntegration.organization_id == org_id
    )

    if integration_type:
        query = query.filter(CustomIntegration.integration_type == integration_type)

    if status:
        query = query.filter(CustomIntegration.status == status)
    else:
        # By default, exclude deleted integrations
        query = query.filter(CustomIntegration.status != CustomIntegrationStatus.DELETED)

    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        # Filter integrations that have ANY of the specified tags
        for tag in tag_list:
            query = query.filter(CustomIntegration.tags.contains([tag]))

    integrations = query.order_by(CustomIntegration.created_at.desc()).all()

    logger.info(
        "custom_integrations_listed",
        org_id=org_id,
        count=len(integrations),
        filters={"type": integration_type, "status": status, "tags": tags}
    )

    return integrations


@router.get(
    "/{integration_id}",
    response_model=CustomIntegrationResponse,
    summary="Get Custom Integration",
    description="""
    Retrieve detailed information about a specific custom integration.

    Returns the complete configuration including:
    - Environment variables
    - Secret references
    - File configurations
    - Context prompt
    - Tags and metadata

    **Example:**
    ```
    GET /api/v1/custom-integrations/550e8400-e29b-41d4-a716-446655440000
    ```
    """,
    responses={
        200: {"description": "Custom integration details"},
        404: {"description": "Integration not found"}
    }
)
async def get_custom_integration(
    integration_id: str,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Retrieve a specific custom integration by ID."""
    org_id = organization["id"]

    integration = db.query(CustomIntegration).filter(
        CustomIntegration.id == integration_id,
        CustomIntegration.organization_id == org_id
    ).first()

    if not integration:
        raise HTTPException(status_code=404, detail="Custom integration not found")

    logger.info(
        "custom_integration_fetched",
        org_id=org_id,
        integration_id=integration_id[:8],
        integration_name=integration.name
    )

    return integration


@router.post(
    "",
    response_model=CustomIntegrationResponse,
    status_code=201,
    summary="Create Custom Integration",
    description="""
    Create a new custom integration instance.

    **Configuration Options:**
    - `env_vars`: Key-value pairs for environment variables
    - `secrets`: List of secret names to resolve from vault
    - `files`: List of files to create in workspace
    - `context_prompt`: Contextual guidance for AI agents
    - `connection_test`: Optional command to test connectivity

    **Name Requirements:**
    - Must be unique within the organization
    - Cannot be empty
    - Alphanumeric and hyphens recommended

    **Example Request:**
    ```json
    {
      "name": "production-postgres",
      "integration_type": "postgres",
      "description": "Production PostgreSQL database",
      "config": {
        "env_vars": {
          "DB_HOST": "postgres.prod.example.com",
          "DB_PORT": "5432",
          "DB_NAME": "production"
        },
        "secrets": ["DB_PASSWORD"],
        "files": [
          {
            "path": "~/.postgresql/client.crt",
            "secret_ref": "POSTGRES_CLIENT_CERT",
            "mode": "0600"
          }
        ],
        "context_prompt": "Production database - use connection pooling"
      },
      "tags": ["production", "database"]
    }
    ```
    """,
    responses={
        201: {"description": "Integration created successfully"},
        409: {"description": "Integration with this name already exists"},
        422: {"description": "Validation error"}
    }
)
async def create_custom_integration(
    request: CreateCustomIntegrationRequest,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Create a new custom integration for the organization."""
    org_id = organization["id"]
    user_id = organization.get("user_id")

    # Check if integration with this name already exists
    existing = db.query(CustomIntegration).filter(
        CustomIntegration.organization_id == org_id,
        CustomIntegration.name == request.name,
        CustomIntegration.status != CustomIntegrationStatus.DELETED
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Custom integration with name '{request.name}' already exists"
        )

    # Create the integration
    integration = CustomIntegration(
        organization_id=org_id,
        name=request.name,
        integration_type=request.integration_type,
        description=request.description,
        config=request.config.model_dump(),
        tags=request.tags,
        status=CustomIntegrationStatus.ACTIVE,
        created_by=user_id
    )

    db.add(integration)
    db.commit()
    db.refresh(integration)

    logger.info(
        "custom_integration_created",
        org_id=org_id,
        integration_id=str(integration.id)[:8],
        integration_name=integration.name,
        integration_type=integration.integration_type
    )

    return integration


@router.put("/{integration_id}", response_model=CustomIntegrationResponse)
async def update_custom_integration(
    integration_id: str,
    request: UpdateCustomIntegrationRequest,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Update a custom integration."""
    org_id = organization["id"]

    integration = db.query(CustomIntegration).filter(
        CustomIntegration.id == integration_id,
        CustomIntegration.organization_id == org_id
    ).first()

    if not integration:
        raise HTTPException(status_code=404, detail="Custom integration not found")

    # Update fields
    if request.name is not None:
        # Check name uniqueness
        existing = db.query(CustomIntegration).filter(
            CustomIntegration.organization_id == org_id,
            CustomIntegration.name == request.name,
            CustomIntegration.id != integration_id,
            CustomIntegration.status != CustomIntegrationStatus.DELETED
        ).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Custom integration with name '{request.name}' already exists"
            )
        integration.name = request.name

    if request.integration_type is not None:
        integration.integration_type = request.integration_type

    if request.description is not None:
        integration.description = request.description

    if request.config is not None:
        integration.config = request.config.model_dump()

    if request.status is not None:
        integration.status = request.status

    if request.tags is not None:
        integration.tags = request.tags

    db.commit()
    db.refresh(integration)

    logger.info(
        "custom_integration_updated",
        org_id=org_id,
        integration_id=integration_id[:8],
        integration_name=integration.name
    )

    return integration


@router.delete("/{integration_id}", status_code=204)
async def delete_custom_integration(
    integration_id: str,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
    hard_delete: bool = Query(False, description="Permanently delete (vs soft delete)"),
):
    """
    Delete a custom integration.

    By default, this is a soft delete (sets status to DELETED).
    Use hard_delete=true to permanently remove from database.
    """
    org_id = organization["id"]

    integration = db.query(CustomIntegration).filter(
        CustomIntegration.id == integration_id,
        CustomIntegration.organization_id == org_id
    ).first()

    if not integration:
        raise HTTPException(status_code=404, detail="Custom integration not found")

    if hard_delete:
        db.delete(integration)
        logger.info(
            "custom_integration_hard_deleted",
            org_id=org_id,
            integration_id=integration_id[:8],
            integration_name=integration.name
        )
    else:
        integration.status = CustomIntegrationStatus.DELETED
        logger.info(
            "custom_integration_soft_deleted",
            org_id=org_id,
            integration_id=integration_id[:8],
            integration_name=integration.name
        )

    db.commit()
