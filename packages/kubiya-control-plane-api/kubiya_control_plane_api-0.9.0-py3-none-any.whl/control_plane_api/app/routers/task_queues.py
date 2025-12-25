"""
Task Queues router - Worker queue management for routing work to specific workers.

This router handles task queue CRUD operations and tracks worker availability.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import structlog
import uuid
import os

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.database import get_db
from control_plane_api.app.models.environment import Environment
from control_plane_api.app.models.orchestration import TemporalNamespace
from control_plane_api.app.lib.temporal_client import get_temporal_client

logger = structlog.get_logger()

router = APIRouter()


# Pydantic schemas
class TaskQueueCreate(BaseModel):
    name: str = Field(..., description="Queue name (e.g., default, high-priority)", min_length=2, max_length=100)
    display_name: str | None = Field(None, description="User-friendly display name")
    description: str | None = Field(None, description="Queue description")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    settings: dict = Field(default_factory=dict, description="Queue settings")
    priority: int | None = Field(None, ge=1, le=10, description="Priority level (1-10)")
    policy_ids: List[str] = Field(default_factory=list, description="OPA policy IDs")


class TaskQueueUpdate(BaseModel):
    name: str | None = None
    display_name: str | None = None
    description: str | None = None
    tags: List[str] | None = None
    settings: dict | None = None
    status: str | None = None
    priority: int | None = Field(None, ge=1, le=10)
    policy_ids: List[str] | None = None


class TaskQueueResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    display_name: str | None
    description: str | None
    tags: List[str]
    settings: dict
    status: str
    priority: int | None = None
    policy_ids: List[str] = []
    created_at: str
    updated_at: str
    created_by: str | None

    # Temporal Cloud provisioning fields
    worker_token: str | None = None  # UUID token for worker registration
    provisioning_workflow_id: str | None = None  # Temporal workflow ID
    provisioned_at: str | None = None
    error_message: str | None = None
    temporal_namespace_id: str | None = None

    # Worker metrics
    active_workers: int = 0
    idle_workers: int = 0
    busy_workers: int = 0


class WorkerHeartbeatResponse(BaseModel):
    id: str
    organization_id: str
    task_queue_name: str
    worker_id: str
    hostname: str | None
    worker_metadata: dict
    last_heartbeat: str
    status: str
    tasks_processed: int
    current_task_id: str | None
    registered_at: str
    updated_at: str


def ensure_default_queue(db: Session, organization: dict) -> Optional[Environment]:
    """
    Ensure the organization has a default task queue.
    Creates one if it doesn't exist.

    Returns the default queue or None if creation failed.
    """
    try:
        # Check if default queue exists
        existing = db.query(Environment).filter(
            Environment.organization_id == organization["id"],
            Environment.name == "default"
        ).first()

        if existing:
            return existing

        # Create default queue
        default_queue = Environment(
            id=uuid.uuid4(),
            organization_id=organization["id"],
            name="default",
            display_name="Default Queue",
            description="Default task queue for all workers",
            tags=[],
            settings={},
            status="active",
            created_by=organization.get("user_id"),
        )

        db.add(default_queue)
        db.commit()
        db.refresh(default_queue)

        logger.info(
            "default_queue_created",
            queue_id=str(default_queue.id),
            org_id=organization["id"],
        )
        return default_queue

    except Exception as e:
        db.rollback()
        logger.error("ensure_default_queue_failed", error=str(e), org_id=organization.get("id"))
        return None


@router.post("", response_model=TaskQueueResponse, status_code=status.HTTP_201_CREATED)
async def create_task_queue(
    queue_data: TaskQueueCreate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Create a new task queue.

    If this is the first task queue for the organization, it will trigger
    Temporal Cloud namespace provisioning workflow.
    """
    try:
        # Check if queue name already exists for this organization
        existing = db.query(Environment).filter(
            Environment.organization_id == organization["id"],
            Environment.name == queue_data.name
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Task queue with name '{queue_data.name}' already exists"
            )

        # Check if this is the first task queue for this org
        queue_count = db.query(Environment).filter(
            Environment.organization_id == organization["id"]
        ).count()
        is_first_queue = queue_count == 0

        # Check if namespace already exists
        has_namespace = db.query(TemporalNamespace).filter(
            TemporalNamespace.organization_id == organization["id"]
        ).first() is not None
        needs_provisioning = is_first_queue and not has_namespace

        # Set initial status
        initial_status = "provisioning" if needs_provisioning else "ready"

        queue = Environment(
            id=uuid.uuid4(),
            organization_id=organization["id"],
            name=queue_data.name,
            display_name=queue_data.display_name or queue_data.name,
            description=queue_data.description,
            tags=queue_data.tags,
            settings=queue_data.settings,
            status=initial_status,
            created_by=organization.get("user_id"),
            worker_token=uuid.uuid4(),  # Generate worker token
            policy_ids=queue_data.policy_ids,
        )

        db.add(queue)
        db.commit()
        db.refresh(queue)

        queue_id = str(queue.id)

        # Trigger namespace provisioning workflow if needed
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
                    task_queue_id=queue_id,
                    account_id=account_id,
                    region=os.environ.get("TEMPORAL_CLOUD_REGION", "aws-us-east-1"),
                )

                # Start provisioning workflow on control plane's task queue
                workflow_handle = await temporal_client.start_workflow(
                    ProvisionTemporalNamespaceWorkflow.run,
                    workflow_input,
                    id=f"provision-namespace-{organization['id']}",
                    task_queue="agent-control-plane",  # Control plane's task queue
                )

                # Update queue with workflow ID
                queue.provisioning_workflow_id = workflow_handle.id
                db.commit()

                logger.info(
                    "namespace_provisioning_workflow_started",
                    workflow_id=workflow_handle.id,
                    queue_id=queue_id,
                    org_id=organization["id"],
                )
            except Exception as e:
                logger.error(
                    "failed_to_start_provisioning_workflow",
                    error=str(e),
                    queue_id=queue_id,
                    org_id=organization["id"],
                )
                # Update queue status to error
                queue.status = "error"
                queue.error_message = f"Failed to start provisioning: {str(e)}"
                db.commit()

        logger.info(
            "task_queue_created",
            queue_id=queue_id,
            queue_name=queue.name,
            org_id=organization["id"],
            needs_provisioning=needs_provisioning,
        )

        return TaskQueueResponse(
            id=str(queue.id),
            organization_id=queue.organization_id,
            name=queue.name,
            display_name=queue.display_name,
            description=queue.description,
            tags=queue.tags or [],
            settings=queue.settings or {},
            status=queue.status,
            priority=None,
            policy_ids=queue.policy_ids or [],
            created_at=queue.created_at.isoformat() if queue.created_at else datetime.utcnow().isoformat(),
            updated_at=queue.updated_at.isoformat() if queue.updated_at else datetime.utcnow().isoformat(),
            created_by=queue.created_by,
            worker_token=str(queue.worker_token) if queue.worker_token else None,
            provisioning_workflow_id=queue.provisioning_workflow_id,
            provisioned_at=queue.provisioned_at.isoformat() if queue.provisioned_at else None,
            error_message=queue.error_message,
            temporal_namespace_id=str(queue.temporal_namespace_id) if queue.temporal_namespace_id else None,
            active_workers=0,
            idle_workers=0,
            busy_workers=0,
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("task_queue_creation_failed", error=str(e), org_id=organization["id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task queue: {str(e)}"
        )


@router.get("", response_model=List[TaskQueueResponse])
async def list_task_queues(
    request: Request,
    status_filter: str | None = None,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """List all task queues in the organization"""
    try:
        # Ensure default queue exists
        ensure_default_queue(db, organization)

        # Query queues
        query = db.query(Environment).filter(
            Environment.organization_id == organization["id"]
        )

        if status_filter:
            query = query.filter(Environment.status == status_filter)

        queues_data = query.order_by(Environment.created_at.asc()).all()

        # Note: Worker stats are now tracked at worker_queue level, not environment level
        # For backward compatibility, we return 0 for environment-level worker counts
        # Use worker_queues endpoints for detailed worker information
        queues = []
        for queue in queues_data:
            queues.append(
                TaskQueueResponse(
                    id=str(queue.id),
                    organization_id=queue.organization_id,
                    name=queue.name,
                    display_name=queue.display_name,
                    description=queue.description,
                    tags=queue.tags or [],
                    settings=queue.settings or {},
                    status=queue.status,
                    priority=None,
                    policy_ids=queue.policy_ids or [],
                    created_at=queue.created_at.isoformat() if queue.created_at else datetime.utcnow().isoformat(),
                    updated_at=queue.updated_at.isoformat() if queue.updated_at else datetime.utcnow().isoformat(),
                    created_by=queue.created_by,
                    worker_token=str(queue.worker_token) if queue.worker_token else None,
                    provisioning_workflow_id=queue.provisioning_workflow_id,
                    provisioned_at=queue.provisioned_at.isoformat() if queue.provisioned_at else None,
                    error_message=queue.error_message,
                    temporal_namespace_id=str(queue.temporal_namespace_id) if queue.temporal_namespace_id else None,
                    active_workers=0,
                    idle_workers=0,
                    busy_workers=0,
                )
            )

        logger.info(
            "task_queues_listed",
            count=len(queues),
            org_id=organization["id"],
        )

        return queues

    except Exception as e:
        logger.error("task_queues_list_failed", error=str(e), org_id=organization["id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list task queues: {str(e)}"
        )


@router.get("/{queue_id}", response_model=TaskQueueResponse)
async def get_task_queue(
    queue_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Get a specific task queue by ID"""
    try:
        queue = db.query(Environment).filter(
            Environment.id == queue_id,
            Environment.organization_id == organization["id"]
        ).first()

        if not queue:
            raise HTTPException(status_code=404, detail="Task queue not found")

        # Note: Worker stats are now tracked at worker_queue level
        # Return 0 for environment-level worker counts
        return TaskQueueResponse(
            id=str(queue.id),
            organization_id=queue.organization_id,
            name=queue.name,
            display_name=queue.display_name,
            description=queue.description,
            tags=queue.tags or [],
            settings=queue.settings or {},
            status=queue.status,
            priority=None,
            policy_ids=queue.policy_ids or [],
            created_at=queue.created_at.isoformat() if queue.created_at else datetime.utcnow().isoformat(),
            updated_at=queue.updated_at.isoformat() if queue.updated_at else datetime.utcnow().isoformat(),
            created_by=queue.created_by,
            worker_token=str(queue.worker_token) if queue.worker_token else None,
            provisioning_workflow_id=queue.provisioning_workflow_id,
            provisioned_at=queue.provisioned_at.isoformat() if queue.provisioned_at else None,
            error_message=queue.error_message,
            temporal_namespace_id=str(queue.temporal_namespace_id) if queue.temporal_namespace_id else None,
            active_workers=0,
            idle_workers=0,
            busy_workers=0,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("task_queue_get_failed", error=str(e), queue_id=queue_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task queue: {str(e)}"
        )


@router.patch("/{queue_id}", response_model=TaskQueueResponse)
async def update_task_queue(
    queue_id: str,
    queue_data: TaskQueueUpdate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Update a task queue"""
    try:
        # Check if queue exists
        queue = db.query(Environment).filter(
            Environment.id == queue_id,
            Environment.organization_id == organization["id"]
        ).first()

        if not queue:
            raise HTTPException(status_code=404, detail="Task queue not found")

        # Build update dict
        update_data = queue_data.model_dump(exclude_unset=True)

        # Apply updates
        for key, value in update_data.items():
            if hasattr(queue, key):
                setattr(queue, key, value)

        db.commit()
        db.refresh(queue)

        logger.info(
            "task_queue_updated",
            queue_id=queue_id,
            org_id=organization["id"],
        )

        # Note: Worker stats are now tracked at worker_queue level
        return TaskQueueResponse(
            id=str(queue.id),
            organization_id=queue.organization_id,
            name=queue.name,
            display_name=queue.display_name,
            description=queue.description,
            tags=queue.tags or [],
            settings=queue.settings or {},
            status=queue.status,
            priority=None,
            policy_ids=queue.policy_ids or [],
            created_at=queue.created_at.isoformat() if queue.created_at else datetime.utcnow().isoformat(),
            updated_at=queue.updated_at.isoformat() if queue.updated_at else datetime.utcnow().isoformat(),
            created_by=queue.created_by,
            worker_token=str(queue.worker_token) if queue.worker_token else None,
            provisioning_workflow_id=queue.provisioning_workflow_id,
            provisioned_at=queue.provisioned_at.isoformat() if queue.provisioned_at else None,
            error_message=queue.error_message,
            temporal_namespace_id=str(queue.temporal_namespace_id) if queue.temporal_namespace_id else None,
            active_workers=0,
            idle_workers=0,
            busy_workers=0,
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("task_queue_update_failed", error=str(e), queue_id=queue_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task queue: {str(e)}"
        )


@router.delete("/{queue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_queue(
    queue_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Delete a task queue"""
    try:
        # Prevent deleting default queue
        queue = db.query(Environment).filter(
            Environment.id == queue_id,
            Environment.organization_id == organization["id"]
        ).first()

        if not queue:
            raise HTTPException(status_code=404, detail="Task queue not found")

        if queue.name == "default":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the default queue"
            )

        db.delete(queue)
        db.commit()

        logger.info("task_queue_deleted", queue_id=queue_id, org_id=organization["id"])

        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("task_queue_delete_failed", error=str(e), queue_id=queue_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task queue: {str(e)}"
        )


@router.get("/{queue_name}/workers", response_model=List[WorkerHeartbeatResponse])
async def list_queue_workers(
    queue_name: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
):
    """
    List all workers for a specific queue.

    NOTE: This endpoint is deprecated. Workers are now organized by worker_queues.
    Use GET /environments/{env_id}/worker-queues and worker_queues endpoints instead.
    """
    logger.warning(
        "deprecated_endpoint_called",
        endpoint="/task-queues/{queue_name}/workers",
        queue_name=queue_name,
        org_id=organization["id"],
    )

    # Return empty list for backward compatibility
    return []


# Worker Registration

class WorkerCommandResponse(BaseModel):
    """Response with worker registration command"""
    worker_token: str
    task_queue_name: str
    command: str
    command_parts: dict  # Broken down for UI display
    namespace_status: str  # pending, provisioning, ready, error
    can_register: bool
    provisioning_workflow_id: str | None = None


@router.get("/{queue_id}/worker-command", response_model=WorkerCommandResponse)
async def get_worker_registration_command(
    queue_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Get the worker registration command for a task queue.

    Returns the kubiya worker start command with the worker token that users
    should run to start a worker for this task queue.

    The UI should display this in a "Register Worker" dialog when the queue
    is ready, and show provisioning status while the namespace is being created.
    """
    try:
        # Get task queue
        queue = db.query(Environment).filter(
            Environment.id == queue_id,
            Environment.organization_id == organization["id"]
        ).first()

        if not queue:
            raise HTTPException(status_code=404, detail="Task queue not found")

        worker_token = queue.worker_token

        # Generate worker_token if it doesn't exist (for existing queues)
        if not worker_token:
            worker_token = uuid.uuid4()
            queue.worker_token = worker_token
            db.commit()

            logger.info(
                "worker_token_generated",
                queue_id=queue_id,
                org_id=organization["id"],
            )

        task_queue_name = queue.name
        namespace_status = queue.status or "unknown"
        provisioning_workflow_id = queue.provisioning_workflow_id

        # Check if namespace is ready
        can_register = namespace_status in ["ready", "active"]

        # Build command
        worker_token_str = str(worker_token)
        command = f"kubiya worker start --token {worker_token_str} --task-queue {task_queue_name}"

        command_parts = {
            "binary": "kubiya",
            "subcommand": "worker start",
            "flags": {
                "--token": worker_token_str,
                "--task-queue": task_queue_name,
            },
        }

        logger.info(
            "worker_command_retrieved",
            queue_id=queue_id,
            can_register=can_register,
            status=namespace_status,
            org_id=organization["id"],
        )

        return WorkerCommandResponse(
            worker_token=worker_token_str,
            task_queue_name=task_queue_name,
            command=command,
            command_parts=command_parts,
            namespace_status=namespace_status,
            can_register=can_register,
            provisioning_workflow_id=provisioning_workflow_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("worker_command_get_failed", error=str(e), queue_id=queue_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get worker command: {str(e)}"
        )
