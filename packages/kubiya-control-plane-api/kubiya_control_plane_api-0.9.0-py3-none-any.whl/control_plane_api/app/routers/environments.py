"""
Environments router - Clean API for environment management.

This router provides /environments endpoints that map to the environments table.
The naming "environments" is internal - externally we call them "environments".
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
import structlog
import uuid
import os

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.database import get_db
from control_plane_api.app.models.environment import Environment
from control_plane_api.app.models.skill import Skill, SkillAssociation
from control_plane_api.app.lib.temporal_client import get_temporal_client

logger = structlog.get_logger()

router = APIRouter()


# Execution Environment Model (shared with agents/teams)
class ExecutionEnvironment(BaseModel):
    """
    Execution environment configuration - env vars, secrets, integration credentials, and MCP servers.

    All string fields in mcp_servers support template syntax:
    - {{variable}} - Simple variables
    - {{.secret.name}} - Secrets from vault
    - {{.env.VAR}} - Environment variables
    """
    env_vars: dict[str, str] = Field(default_factory=dict, description="Environment variables (key-value pairs)")
    secrets: list[str] = Field(default_factory=list, description="Secret names from Kubiya vault")
    integration_ids: list[str] = Field(default_factory=list, description="Integration UUIDs for delegated credentials")
    mcp_servers: dict[str, dict] = Field(
        default_factory=dict,
        description="MCP (Model Context Protocol) server configurations. Supports stdio, HTTP, and SSE transports. All string values support template syntax."
    )


# Pydantic schemas
class EnvironmentCreate(BaseModel):
    name: str = Field(..., description="Environment name (e.g., default, production)", min_length=2, max_length=100)
    display_name: str | None = Field(None, description="User-friendly display name")
    description: str | None = Field(None, description="Environment description")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    settings: dict = Field(default_factory=dict, description="Environment settings")
    execution_environment: ExecutionEnvironment | None = Field(None, description="Execution environment configuration")
    # Note: priority and policy_ids not supported by environments table


class EnvironmentUpdate(BaseModel):
    name: str | None = None
    display_name: str | None = None
    description: str | None = None
    tags: List[str] | None = None
    settings: dict | None = None
    status: str | None = None
    execution_environment: ExecutionEnvironment | None = None
    # Note: priority and policy_ids not supported by environments table


class EnvironmentResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    display_name: str | None
    description: str | None
    tags: List[str]
    settings: dict
    status: str
    created_at: str
    updated_at: str
    created_by: str | None

    # Temporal Cloud provisioning fields
    worker_token: str | None = None
    provisioning_workflow_id: str | None = None
    provisioned_at: str | None = None
    error_message: str | None = None
    temporal_namespace_id: str | None = None

    # Worker metrics (deprecated at environment level, use worker_queues)
    active_workers: int = 0
    idle_workers: int = 0
    busy_workers: int = 0

    # Skills (populated from associations)
    skill_ids: List[str] = []
    skills: List[dict] = []

    # Execution environment configuration
    execution_environment: dict = {}


class WorkerCommandResponse(BaseModel):
    """Response with worker registration command"""
    worker_token: str
    environment_name: str
    command: str
    command_parts: dict
    namespace_status: str
    can_register: bool
    provisioning_workflow_id: str | None = None


def ensure_default_environment(db: Session, organization: dict) -> Optional[Environment]:
    """
    Ensure the organization has a default environment.
    Creates one if it doesn't exist.
    """
    try:
        # Check if default environment exists
        existing = db.query(Environment).filter(
            Environment.organization_id == organization["id"],
            Environment.name == "default"
        ).first()

        if existing:
            return existing

        # Create default environment
        default_env = Environment(
            id=uuid.uuid4(),
            organization_id=organization["id"],
            name="default",
            display_name="Default Environment",
            description="Default environment for all workers",
            tags=[],
            settings={},
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=organization.get("user_id"),
        )

        db.add(default_env)
        db.commit()
        db.refresh(default_env)

        logger.info(
            "default_environment_created",
            environment_id=str(default_env.id),
            org_id=organization["id"],
        )
        return default_env

    except Exception as e:
        db.rollback()
        logger.error("ensure_default_environment_failed", error=str(e), org_id=organization.get("id"))
        return None


def get_environment_skills(db: Session, organization_id: str, environment_id: str) -> tuple[List[str], List[dict]]:
    """Get skills associated with an environment"""
    try:
        # Get associations with full skill data
        associations = db.query(SkillAssociation).options(
            joinedload(SkillAssociation.skill)
        ).filter(
            SkillAssociation.organization_id == organization_id,
            SkillAssociation.entity_type == "environment",
            SkillAssociation.entity_id == environment_id
        ).all()

        skill_ids = []
        skills = []

        for assoc in associations:
            skill_data = assoc.skill
            if skill_data:
                skill_ids.append(str(skill_data.id))

                # Merge configuration with override
                config = skill_data.configuration or {}
                override = assoc.configuration_override
                if override:
                    config = {**config, **override}

                skills.append({
                    "id": str(skill_data.id),
                    "name": skill_data.name,
                    "type": skill_data.skill_type,
                    "description": skill_data.description,
                    "enabled": skill_data.enabled if skill_data.enabled is not None else True,
                    "configuration": config,
                })

        return skill_ids, skills

    except Exception as e:
        logger.error("get_environment_skills_failed", error=str(e), environment_id=environment_id)
        return [], []


@router.post("", response_model=EnvironmentResponse, status_code=status.HTTP_201_CREATED)
async def create_environment(
    env_data: EnvironmentCreate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Create a new environment.

    If this is the first environment for the organization, it will trigger
    Temporal Cloud namespace provisioning workflow.
    """
    try:
        # Check if environment name already exists
        existing = db.query(Environment).filter(
            Environment.organization_id == organization["id"],
            Environment.name == env_data.name
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Environment with name '{env_data.name}' already exists"
            )

        # Check if this is the first environment
        env_count = db.query(Environment).filter(
            Environment.organization_id == organization["id"]
        ).count()
        is_first_env = env_count == 0

        # Check if namespace already exists (temporal_namespaces table check)
        # Note: We need to check if the table exists first
        has_namespace = False
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.bind)
            if 'temporal_namespaces' in inspector.get_table_names():
                from sqlalchemy import text
                result = db.execute(
                    text("SELECT COUNT(*) FROM temporal_namespaces WHERE organization_id = :org_id"),
                    {"org_id": organization["id"]}
                )
                has_namespace = result.scalar() > 0
        except Exception:
            pass

        needs_provisioning = is_first_env and not has_namespace

        # Set initial status
        initial_status = "provisioning" if needs_provisioning else "ready"

        env_obj = Environment(
            id=uuid.uuid4(),
            organization_id=organization["id"],
            name=env_data.name,
            display_name=env_data.display_name or env_data.name,
            description=env_data.description,
            tags=env_data.tags,
            settings=env_data.settings,
            status=initial_status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=organization.get("user_id"),
            worker_token=uuid.uuid4(),
            execution_environment=env_data.execution_environment.model_dump() if env_data.execution_environment else {},
        )

        db.add(env_obj)
        db.commit()
        db.refresh(env_obj)

        env_id = str(env_obj.id)

        # Trigger namespace provisioning if needed
        if needs_provisioning:
            try:
                from control_plane_api.app.workflows.namespace_provisioning import (
                    ProvisionTemporalNamespaceWorkflow,
                    ProvisionNamespaceInput,
                )

                temporal_client = await get_temporal_client()
                account_id = os.environ.get("TEMPORAL_CLOUD_ACCOUNT_ID", "default-account")

                workflow_input = ProvisionNamespaceInput(
                    organization_id=organization["id"],
                    organization_name=organization.get("name", organization["id"]),
                    task_queue_id=env_id,
                    account_id=account_id,
                    region=os.environ.get("TEMPORAL_CLOUD_REGION", "aws-us-east-1"),
                )

                workflow_handle = await temporal_client.start_workflow(
                    ProvisionTemporalNamespaceWorkflow.run,
                    workflow_input,
                    id=f"provision-namespace-{organization['id']}",
                    task_queue="agent-control-plane",
                )

                env_obj.provisioning_workflow_id = workflow_handle.id
                env_obj.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(env_obj)

                logger.info(
                    "namespace_provisioning_workflow_started",
                    workflow_id=workflow_handle.id,
                    environment_id=env_id,
                    org_id=organization["id"],
                )
            except Exception as e:
                logger.error(
                    "failed_to_start_provisioning_workflow",
                    error=str(e),
                    environment_id=env_id,
                    org_id=organization["id"],
                )
                env_obj.status = "error"
                env_obj.error_message = f"Failed to start provisioning: {str(e)}"
                env_obj.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(env_obj)

        logger.info(
            "environment_created",
            environment_id=env_id,
            environment_name=env_obj.name,
            org_id=organization["id"],
            needs_provisioning=needs_provisioning,
        )

        # Convert SQLAlchemy model to dict
        environment_dict = {
            "id": str(env_obj.id),
            "organization_id": env_obj.organization_id,
            "name": env_obj.name,
            "display_name": env_obj.display_name,
            "description": env_obj.description,
            "tags": env_obj.tags or [],
            "settings": env_obj.settings or {},
            "status": env_obj.status,
            "created_at": env_obj.created_at.isoformat() if env_obj.created_at else None,
            "updated_at": env_obj.updated_at.isoformat() if env_obj.updated_at else None,
            "created_by": env_obj.created_by,
            "worker_token": str(env_obj.worker_token) if env_obj.worker_token else None,
            "provisioning_workflow_id": env_obj.provisioning_workflow_id,
            "provisioned_at": env_obj.provisioned_at.isoformat() if env_obj.provisioned_at else None,
            "error_message": env_obj.error_message,
            "temporal_namespace_id": str(env_obj.temporal_namespace_id) if env_obj.temporal_namespace_id else None,
            "execution_environment": env_obj.execution_environment or {},
        }

        return EnvironmentResponse(
            **environment_dict,
            active_workers=0,
            idle_workers=0,
            busy_workers=0,
            skill_ids=[],
            skills=[],
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("environment_creation_failed", error=str(e), org_id=organization["id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create environment: {str(e)}"
        )


@router.get("", response_model=List[EnvironmentResponse])
async def list_environments(
    request: Request,
    status_filter: str | None = None,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """List all environments in the organization"""
    try:
        # Ensure default environment exists
        ensure_default_environment(db, organization)

        # Query environments
        query = db.query(Environment).filter(
            Environment.organization_id == organization["id"]
        )

        if status_filter:
            query = query.filter(Environment.status == status_filter)

        query = query.order_by(Environment.created_at.asc())
        env_objects = query.all()

        if not env_objects:
            return []

        # BATCH FETCH: Get all skills for all environments in one query
        environment_ids = [str(env.id) for env in env_objects]
        skills_associations = db.query(SkillAssociation).options(
            joinedload(SkillAssociation.skill)
        ).filter(
            SkillAssociation.organization_id == organization["id"],
            SkillAssociation.entity_type == "environment",
            SkillAssociation.entity_id.in_(environment_ids)
        ).all()

        # Group skills by environment_id
        skills_by_env = {}
        for assoc in skills_associations:
            env_id = str(assoc.entity_id)
            skill_data = assoc.skill
            if skill_data:
                if env_id not in skills_by_env:
                    skills_by_env[env_id] = {"ids": [], "data": []}

                # Merge configuration with override
                config = skill_data.configuration or {}
                override = assoc.configuration_override
                if override:
                    config = {**config, **override}

                skills_by_env[env_id]["ids"].append(str(skill_data.id))
                skills_by_env[env_id]["data"].append({
                    "id": str(skill_data.id),
                    "name": skill_data.name,
                    "type": skill_data.skill_type,
                    "description": skill_data.description,
                    "enabled": skill_data.enabled if skill_data.enabled is not None else True,
                    "configuration": config,
                })

        # Build environment responses
        environments = []
        for env in env_objects:
            env_id = str(env.id)
            env_skills = skills_by_env.get(env_id, {"ids": [], "data": []})

            env_dict = {
                "id": env_id,
                "organization_id": env.organization_id,
                "name": env.name,
                "display_name": env.display_name,
                "description": env.description,
                "tags": env.tags or [],
                "settings": env.settings or {},
                "status": env.status,
                "created_at": env.created_at.isoformat() if env.created_at else None,
                "updated_at": env.updated_at.isoformat() if env.updated_at else None,
                "created_by": env.created_by,
                "worker_token": str(env.worker_token) if env.worker_token else None,
                "provisioning_workflow_id": env.provisioning_workflow_id,
                "provisioned_at": env.provisioned_at.isoformat() if env.provisioned_at else None,
                "error_message": env.error_message,
                "temporal_namespace_id": str(env.temporal_namespace_id) if env.temporal_namespace_id else None,
                "execution_environment": env.execution_environment or {},
            }

            environments.append(
                EnvironmentResponse(
                    **env_dict,
                    active_workers=0,
                    idle_workers=0,
                    busy_workers=0,
                    skill_ids=env_skills["ids"],
                    skills=env_skills["data"],
                )
            )

        logger.info(
            "environments_listed",
            count=len(environments),
            org_id=organization["id"],
        )

        return environments

    except Exception as e:
        logger.error("environments_list_failed", error=str(e), org_id=organization["id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list environments: {str(e)}"
        )


@router.get("/{environment_id}", response_model=EnvironmentResponse)
async def get_environment(
    environment_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Get a specific environment by ID"""
    try:
        env = db.query(Environment).filter(
            Environment.id == environment_id,
            Environment.organization_id == organization["id"]
        ).first()

        if not env:
            raise HTTPException(status_code=404, detail="Environment not found")

        # Get skills
        skill_ids, skills = get_environment_skills(db, organization["id"], environment_id)

        env_dict = {
            "id": str(env.id),
            "organization_id": env.organization_id,
            "name": env.name,
            "display_name": env.display_name,
            "description": env.description,
            "tags": env.tags or [],
            "settings": env.settings or {},
            "status": env.status,
            "created_at": env.created_at.isoformat() if env.created_at else None,
            "updated_at": env.updated_at.isoformat() if env.updated_at else None,
            "created_by": env.created_by,
            "worker_token": str(env.worker_token) if env.worker_token else None,
            "provisioning_workflow_id": env.provisioning_workflow_id,
            "provisioned_at": env.provisioned_at.isoformat() if env.provisioned_at else None,
            "error_message": env.error_message,
            "temporal_namespace_id": str(env.temporal_namespace_id) if env.temporal_namespace_id else None,
            "execution_environment": env.execution_environment or {},
        }

        return EnvironmentResponse(
            **env_dict,
            active_workers=0,
            idle_workers=0,
            busy_workers=0,
            skill_ids=skill_ids,
            skills=skills,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("environment_get_failed", error=str(e), environment_id=environment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get environment: {str(e)}"
        )


@router.patch("/{environment_id}", response_model=EnvironmentResponse)
async def update_environment(
    environment_id: str,
    env_data: EnvironmentUpdate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Update an environment"""
    try:
        # Check if environment exists
        env = db.query(Environment).filter(
            Environment.id == environment_id,
            Environment.organization_id == organization["id"]
        ).first()

        if not env:
            raise HTTPException(status_code=404, detail="Environment not found")

        # Build update dict
        update_data = env_data.model_dump(exclude_unset=True)

        # Convert execution_environment Pydantic model to dict if present
        if "execution_environment" in update_data and update_data["execution_environment"]:
            if hasattr(update_data["execution_environment"], "model_dump"):
                update_data["execution_environment"] = update_data["execution_environment"].model_dump()

        # Update fields
        for field, value in update_data.items():
            if hasattr(env, field):
                setattr(env, field, value)

        env.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(env)

        # Get skills
        skill_ids, skills = get_environment_skills(db, organization["id"], environment_id)

        logger.info(
            "environment_updated",
            environment_id=environment_id,
            org_id=organization["id"],
        )

        env_dict = {
            "id": str(env.id),
            "organization_id": env.organization_id,
            "name": env.name,
            "display_name": env.display_name,
            "description": env.description,
            "tags": env.tags or [],
            "settings": env.settings or {},
            "status": env.status,
            "created_at": env.created_at.isoformat() if env.created_at else None,
            "updated_at": env.updated_at.isoformat() if env.updated_at else None,
            "created_by": env.created_by,
            "worker_token": str(env.worker_token) if env.worker_token else None,
            "provisioning_workflow_id": env.provisioning_workflow_id,
            "provisioned_at": env.provisioned_at.isoformat() if env.provisioned_at else None,
            "error_message": env.error_message,
            "temporal_namespace_id": str(env.temporal_namespace_id) if env.temporal_namespace_id else None,
            "execution_environment": env.execution_environment or {},
        }

        return EnvironmentResponse(
            **env_dict,
            active_workers=0,
            idle_workers=0,
            busy_workers=0,
            skill_ids=skill_ids,
            skills=skills,
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("environment_update_failed", error=str(e), environment_id=environment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update environment: {str(e)}"
        )


@router.delete("/{environment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_environment(
    environment_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Delete an environment"""
    try:
        # Prevent deleting default environment
        env = db.query(Environment).filter(
            Environment.id == environment_id,
            Environment.organization_id == organization["id"]
        ).first()

        if not env:
            raise HTTPException(status_code=404, detail="Environment not found")

        if env.name == "default":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the default environment"
            )

        db.delete(env)
        db.commit()

        logger.info("environment_deleted", environment_id=environment_id, org_id=organization["id"])

        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("environment_delete_failed", error=str(e), environment_id=environment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete environment: {str(e)}"
        )


@router.get("/{environment_id}/worker-command", response_model=WorkerCommandResponse)
async def get_worker_registration_command(
    environment_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Get the worker registration command for an environment.

    Returns the kubiya worker start command with the worker token.
    """
    try:
        # Get environment
        env = db.query(Environment).filter(
            Environment.id == environment_id,
            Environment.organization_id == organization["id"]
        ).first()

        if not env:
            raise HTTPException(status_code=404, detail="Environment not found")

        worker_token = str(env.worker_token) if env.worker_token else None

        # Generate worker_token if it doesn't exist
        if not worker_token:
            env.worker_token = uuid.uuid4()
            env.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(env)
            worker_token = str(env.worker_token)

            logger.info(
                "worker_token_generated",
                environment_id=environment_id,
                org_id=organization["id"],
            )

        environment_name = env.name
        namespace_status = env.status or "unknown"
        provisioning_workflow_id = env.provisioning_workflow_id

        # Check if namespace is ready
        can_register = namespace_status in ["ready", "active"]

        # Build command
        command = f"kubiya worker start --token {worker_token} --environment {environment_name}"

        command_parts = {
            "binary": "kubiya",
            "subcommand": "worker start",
            "flags": {
                "--token": worker_token,
                "--environment": environment_name,
            },
        }

        logger.info(
            "worker_command_retrieved",
            environment_id=environment_id,
            can_register=can_register,
            status=namespace_status,
            org_id=organization["id"],
        )

        return WorkerCommandResponse(
            worker_token=worker_token,
            environment_name=environment_name,
            command=command,
            command_parts=command_parts,
            namespace_status=namespace_status,
            can_register=can_register,
            provisioning_workflow_id=provisioning_workflow_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("worker_command_get_failed", error=str(e), environment_id=environment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get worker command: {str(e)}"
        )
