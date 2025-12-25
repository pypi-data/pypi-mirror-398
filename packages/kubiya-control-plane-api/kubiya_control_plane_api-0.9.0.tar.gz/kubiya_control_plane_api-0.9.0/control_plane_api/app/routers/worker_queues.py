"""
Worker Queues router - Manage worker queues within environments.

Each environment can have multiple worker queues for fine-grained worker management.
Task queue naming: {org_id}.{environment_name}.{worker_queue_name}
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import PlainTextResponse
from typing import List, Optional, Literal, Dict
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field, field_validator
import structlog
import uuid
import os
import json
import hashlib

from control_plane_api.app.utils.helpers import is_local_temporal
from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.lib.redis_client import get_redis_client
from control_plane_api.app.database import get_db
from control_plane_api.app.models.worker import WorkerQueue, WorkerHeartbeat
from control_plane_api.app.models.environment import Environment
from control_plane_api.app.models.execution import Execution
from control_plane_api.app.config import settings
from control_plane_api.app.schemas.worker_queue_observability_schemas import (
    WorkerQueueMetricsResponse,
    WorkflowsListResponse
)
from control_plane_api.app.services.worker_queue_metrics_service import WorkerQueueMetricsService
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from control_plane_api.app.lib.environment import detect_environment

logger = structlog.get_logger()

router = APIRouter()

# Stale worker threshold: Must be >= 2x the heartbeat interval to avoid false negatives
# Default heartbeat interval is 60s, so threshold is 120s (2x) plus 30s grace period
# Workers that haven't sent heartbeat in 150s are considered inactive
STALE_WORKER_THRESHOLD_SECONDS = 150


# LiteLLM Configuration Schemas
class LiteLLMModelConfig(BaseModel):
    """Single model configuration for LiteLLM proxy"""
    model_name: str = Field(..., description="User-facing model name (e.g., gpt-4)")
    litellm_params: dict = Field(..., description="Parameters passed to litellm.completion() including model, api_base, api_key, etc.")


class LiteLLMConfig(BaseModel):
    """Complete LiteLLM proxy configuration for local worker proxy"""
    model_list: List[LiteLLMModelConfig] = Field(..., description="List of models to configure in the local proxy")
    litellm_settings: Optional[dict] = Field(None, description="LiteLLM settings (callbacks, rate limits, etc.)")
    environment_variables: Optional[dict] = Field(None, description="Environment variables for the proxy (Langfuse keys, etc.)")


class QueueSettings(BaseModel):
    """Worker queue settings schema with validation"""
    enable_local_litellm_proxy: bool = Field(False, description="Enable local LiteLLM proxy for this queue")
    litellm_config: Optional[LiteLLMConfig] = Field(None, description="LiteLLM proxy configuration (required if enable_local_litellm_proxy is true)")
    local_proxy_timeout_seconds: int = Field(10, ge=5, le=60, description="Proxy startup timeout in seconds")
    local_proxy_max_retries: int = Field(3, ge=1, le=10, description="Maximum retry attempts for proxy startup")


async def get_active_workers_from_redis(org_id: str, queue_id: Optional[str] = None, db: Session = None) -> dict:
    """
    Get active workers from Redis heartbeats.

    Redis heartbeats have automatic TTL (5 minutes), so if a worker hasn't sent a heartbeat
    the key will automatically expire. This eliminates the need to manually mark workers as stale.

    Args:
        org_id: Organization ID
        queue_id: Optional queue ID to filter by
        db: Database session (optional)

    Returns:
        Dict with worker_id -> heartbeat_data mapping
    """
    redis_client = get_redis_client()

    if not redis_client:
        logger.warning("redis_unavailable_for_worker_query", org_id=org_id)
        return {}

    # If no session provided, create one
    should_close_db = False
    if db is None:
        from control_plane_api.app.database import get_session_local
        SessionLocal = get_session_local()
        db = SessionLocal()
        should_close_db = True

    try:
        # Get all worker heartbeat keys for this org
        # We need to get worker records from DB to map worker_id -> queue_id
        workers_db = db.query(WorkerHeartbeat).filter(
            WorkerHeartbeat.organization_id == org_id
        ).all()

        if not workers_db:
            return {}

        # Filter workers by queue_id if specified
        workers_to_check = []
        worker_queue_map = {}
        # Also track registered_at times (as timezone-aware datetimes)
        worker_registered_at = {}
        for worker in workers_db:
            worker_id = str(worker.id)
            worker_queue_id = str(worker.worker_queue_id) if worker.worker_queue_id else None

            # Skip if queue_id filter is specified and doesn't match
            if queue_id and worker_queue_id != queue_id:
                continue

            workers_to_check.append(worker_id)
            worker_queue_map[worker_id] = worker_queue_id
            # Ensure registered_at is timezone-aware for any future comparisons
            if worker.registered_at:
                reg_at = worker.registered_at
                if reg_at.tzinfo is None:
                    reg_at = reg_at.replace(tzinfo=timezone.utc)
                worker_registered_at[worker_id] = reg_at

        if not workers_to_check:
            return {}

        # Batch fetch all heartbeats in a single Redis pipeline request
        redis_keys = [f"worker:{worker_id}:heartbeat" for worker_id in workers_to_check]
        heartbeat_results = await redis_client.mget(redis_keys)

        # Process results
        active_workers = {}
        now_utc = datetime.now(timezone.utc)  # Pre-compute timezone-aware now

        for worker_id in workers_to_check:
            redis_key = f"worker:{worker_id}:heartbeat"
            heartbeat_data = heartbeat_results.get(redis_key)

            if heartbeat_data:
                try:
                    data = json.loads(heartbeat_data)
                    # Check if heartbeat is recent (within threshold)
                    last_heartbeat_str = data.get("last_heartbeat", "")
                    if not last_heartbeat_str:
                        logger.warning("missing_last_heartbeat", worker_id=worker_id)
                        continue

                    # Handle ISO format with 'Z' suffix (Python < 3.11 doesn't handle 'Z')
                    if last_heartbeat_str.endswith('Z'):
                        last_heartbeat_str = last_heartbeat_str[:-1] + '+00:00'

                    last_heartbeat = datetime.fromisoformat(last_heartbeat_str)

                    # Ensure timezone-aware datetime
                    if last_heartbeat.tzinfo is None:
                        last_heartbeat = last_heartbeat.replace(tzinfo=timezone.utc)

                    # Calculate age - convert both to timestamps to avoid timezone issues
                    try:
                        now_ts = datetime.now(timezone.utc).timestamp()
                        # Convert last_heartbeat to timestamp
                        if last_heartbeat.tzinfo is None:
                            last_heartbeat = last_heartbeat.replace(tzinfo=timezone.utc)
                        hb_ts = last_heartbeat.timestamp()
                        age_seconds = now_ts - hb_ts
                    except (TypeError, AttributeError, OSError) as dt_err:
                        # If datetime comparison fails, skip this worker
                        logger.warning("datetime_comparison_failed", worker_id=worker_id, error=str(dt_err))
                        continue

                    if age_seconds <= STALE_WORKER_THRESHOLD_SECONDS:
                        active_workers[worker_id] = {
                            **data,
                            "worker_queue_id": worker_queue_map[worker_id],
                        }
                    else:
                        logger.debug(
                            "worker_heartbeat_stale",
                            worker_id=worker_id,
                            age_seconds=age_seconds,
                            threshold=STALE_WORKER_THRESHOLD_SECONDS
                        )
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.warning("invalid_heartbeat_data", worker_id=worker_id, error=str(e))
                    continue

        logger.debug(
            "active_workers_fetched",
            org_id=org_id,
            total_workers=len(workers_to_check),
            active_workers=len(active_workers),
            queue_id=queue_id,
        )

        return active_workers

    except Exception as e:
        import traceback
        logger.error(
            "failed_to_get_active_workers_from_redis",
            error=str(e),
            org_id=org_id,
            error_type=type(e).__name__,
            line_info=traceback.format_exc().split("\n")[-3] if traceback.format_exc() else "unknown",
        )
        return {}
    finally:
        if should_close_db and db:
            db.close()


# Pydantic schemas
class WorkerQueueCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Worker queue name (lowercase, no spaces)")
    display_name: Optional[str] = Field(None, description="User-friendly display name")
    description: Optional[str] = Field(None, description="Queue description")
    max_workers: Optional[int] = Field(None, ge=1, description="Max workers allowed (NULL = unlimited)")
    heartbeat_interval: int = Field(60, ge=10, le=300, description="Seconds between heartbeats (lightweight)")
    tags: List[str] = Field(default_factory=list)
    settings: dict = Field(default_factory=dict)

    @field_validator("settings")
    def validate_settings(cls, v):
        """Validate settings structure including litellm_config"""
        if not v:
            return v

        try:
            # Validate entire settings dict using QueueSettings schema
            QueueSettings(**v)
        except Exception as e:
            raise ValueError(f"Invalid settings: {str(e)}")

        # Additional validation: if enable_local_litellm_proxy is true, litellm_config is required
        if v.get("enable_local_litellm_proxy") and not v.get("litellm_config"):
            raise ValueError("litellm_config is required when enable_local_litellm_proxy is true")

        return v


class WorkerQueueUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    display_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    max_workers: Optional[int] = Field(None, ge=1)
    heartbeat_interval: Optional[int] = Field(None, ge=10, le=300)
    tags: Optional[List[str]] = None
    settings: Optional[dict] = None

    @field_validator("settings")
    def validate_settings(cls, v):
        """Validate settings structure including litellm_config"""
        if not v:
            return v

        try:
            # Validate entire settings dict using QueueSettings schema
            QueueSettings(**v)
        except Exception as e:
            raise ValueError(f"Invalid settings: {str(e)}")

        # Additional validation: if enable_local_litellm_proxy is true, litellm_config is required
        if v.get("enable_local_litellm_proxy") and not v.get("litellm_config"):
            raise ValueError("litellm_config is required when enable_local_litellm_proxy is true")

        return v


class WorkerQueueResponse(BaseModel):
    id: str
    organization_id: str
    environment_id: str
    name: str
    display_name: Optional[str]
    description: Optional[str]
    status: str
    max_workers: Optional[int]
    heartbeat_interval: int
    tags: List[str]
    settings: dict
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    # Computed
    active_workers: int = 0
    task_queue_name: str  # Full task queue name: org.env.worker_queue


    @field_validator("id", "environment_id", "created_by", mode="before")
    def cast_to_string(cls, v):
        if v is None:
            return None
        return str(v)


@router.get("/worker-queues", response_model=List[WorkerQueueResponse])
async def list_all_worker_queues(
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """List all worker queues across all environments for the organization (excluding ephemeral queues)"""
    try:
        org_id = organization["id"]

        # Get all non-ephemeral worker queues for this organization with environment relationship
        # Also exclude queues starting with "local-exec" (ephemeral local execution queues)
        queues_db = (
            db.query(WorkerQueue)
            .options(joinedload(WorkerQueue.environment))
            .filter(
                WorkerQueue.organization_id == org_id,
                WorkerQueue.ephemeral == False,  # Exclude ephemeral queues
                ~WorkerQueue.name.startswith('local-exec')  # Exclude local-exec queues
            )
            .order_by(WorkerQueue.created_at.asc())
            .all()
        )

        if not queues_db:
            return []

        # Get active workers from Redis (with automatic TTL-based expiration)
        active_workers = await get_active_workers_from_redis(org_id, db=db)

        # Count workers per queue
        worker_counts = {}
        for worker_id, worker_data in active_workers.items():
            queue_id = worker_data.get("worker_queue_id")
            if queue_id:
                worker_counts[queue_id] = worker_counts.get(queue_id, 0) + 1

        # Build response
        queues = []
        for queue in queues_db:
            # Use queue UUID as task queue name for security
            task_queue_name = str(queue.id)
            active_worker_count = worker_counts.get(str(queue.id), 0)

            # Get environment name from relationship
            environment_name = queue.environment.name if queue.environment else None

            from sqlalchemy.inspection import inspect
            queue_dict = {c.key: getattr(queue, c.key) for c in inspect(queue).mapper.column_attrs}

            queues.append(
                WorkerQueueResponse(
                    **queue_dict,
                    active_workers=active_worker_count,
                    task_queue_name=task_queue_name,
                    environment_name=environment_name,
                )
            )

        logger.info(
            "all_worker_queues_listed",
            count=len(queues),
            org_id=org_id,
        )

        return queues

    except HTTPException:
        raise
    except Exception as e:
        logger.error("all_worker_queues_list_failed", error=str(e), org_id=org_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list all worker queues: {str(e)}"
        )


@router.post("/environments/{environment_id}/worker-queues", response_model=WorkerQueueResponse, status_code=status.HTTP_201_CREATED)
async def create_worker_queue(
    environment_id: str,
    queue_data: WorkerQueueCreate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Create a new worker queue within an environment"""
    try:
        org_id = organization["id"]

        # Validate environment exists
        environment = (
            db.query(Environment)
            .filter(Environment.id == environment_id, Environment.organization_id == org_id)
            .first()
        )

        if not environment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Environment not found"
            )

        # Check if worker queue name already exists in this environment
        existing = (
            db.query(WorkerQueue)
            .filter(
                WorkerQueue.environment_id == environment_id,
                WorkerQueue.name == queue_data.name
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Worker queue '{queue_data.name}' already exists in this environment"
            )

        # Create worker queue
        queue_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Automatically mark as ephemeral if name starts with "local-exec"
        is_ephemeral = queue_data.name.startswith("local-exec")

        queue = WorkerQueue(
            id=queue_id,
            organization_id=org_id,
            environment_id=environment_id,
            name=queue_data.name,
            display_name=queue_data.display_name or queue_data.name,
            description=queue_data.description,
            status="active",
            max_workers=queue_data.max_workers,
            heartbeat_interval=queue_data.heartbeat_interval,
            tags=queue_data.tags,
            settings=queue_data.settings,
            ephemeral=is_ephemeral,
            created_at=now,
            updated_at=now,
            created_by=organization.get("user_id"),
        )

        db.add(queue)
        db.commit()
        db.refresh(queue)

        # Convert to dict for Pydantic response
        from sqlalchemy.inspection import inspect
        queue_dict = {c.key: getattr(queue, c.key) for c in inspect(queue).mapper.column_attrs}

        # Use queue UUID as task queue name for security (unpredictable)
        task_queue_name = queue_id

        logger.info(
            "worker_queue_created",
            queue_id=queue_id,
            queue_name=queue.name,
            environment_id=environment_id,
            task_queue_name=task_queue_name,
            org_id=org_id,
        )

        return WorkerQueueResponse(
            **queue_dict,
            active_workers=0,
            task_queue_name=task_queue_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("worker_queue_creation_failed", error=str(e), org_id=organization["id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create worker queue: {str(e)}"
        )


@router.get("/environments/{environment_id}/worker-queues", response_model=List[WorkerQueueResponse])
async def list_worker_queues(
    environment_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """List all worker queues in an environment (excluding ephemeral queues)"""
    try:
        org_id = organization["id"]

        # Get environment name
        environment = (
            db.query(Environment)
            .filter(Environment.id == environment_id, Environment.organization_id == org_id)
            .first()
        )

        if not environment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Environment not found"
            )

        environment_name = environment.name

        # Get non-ephemeral worker queues only
        # Also exclude queues starting with "local-exec" (ephemeral local execution queues)
        queues_db = (
            db.query(WorkerQueue)
            .filter(
                WorkerQueue.environment_id == environment_id,
                WorkerQueue.ephemeral == False,  # Exclude ephemeral queues
                ~WorkerQueue.name.startswith('local-exec')  # Exclude local-exec queues
            )
            .order_by(WorkerQueue.created_at.asc())
            .all()
        )

        if not queues_db:
            return []

        # Get active workers from Redis (with automatic TTL-based expiration)
        active_workers = await get_active_workers_from_redis(org_id, db=db)

        # Count workers per queue
        worker_counts = {}
        for worker_id, worker_data in active_workers.items():
            queue_id = worker_data.get("worker_queue_id")
            if queue_id:
                worker_counts[queue_id] = worker_counts.get(queue_id, 0) + 1

        # Build response
        queues = []
        for queue in queues_db:
            # Use queue UUID as task queue name for security
            task_queue_name = str(queue.id)
            active_worker_count = worker_counts.get(str(queue.id), 0)

            from sqlalchemy.inspection import inspect
            queue_dict = {c.key: getattr(queue, c.key) for c in inspect(queue).mapper.column_attrs}

            queues.append(
                WorkerQueueResponse(
                    **queue_dict,
                    active_workers=active_worker_count,
                    task_queue_name=task_queue_name,
                )
            )

        logger.info(
            "worker_queues_listed",
            count=len(queues),
            environment_id=environment_id,
            org_id=org_id,
        )

        return queues

    except HTTPException:
        raise
    except Exception as e:
        logger.error("worker_queues_list_failed", error=str(e), environment_id=environment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list worker queues: {str(e)}"
        )


@router.get("/worker-queues/{queue_id}", response_model=WorkerQueueResponse)
async def get_worker_queue(
    queue_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Get a specific worker queue by ID"""
    try:
        org_id = organization["id"]

        # Get worker queue with environment relationship
        queue = (
            db.query(WorkerQueue)
            .options(joinedload(WorkerQueue.environment))
            .filter(WorkerQueue.id == queue_id, WorkerQueue.organization_id == org_id)
            .first()
        )

        if not queue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker queue not found"
            )

        # Get environment name from relationship
        environment_name = queue.environment.name if queue.environment else "unknown"

        # Get active workers from Redis for this specific queue
        active_workers_dict = await get_active_workers_from_redis(org_id, queue_id, db=db)
        active_worker_count = len(active_workers_dict)

        # Convert to dict for Pydantic response
        from sqlalchemy.inspection import inspect
        queue_dict = {c.key: getattr(queue, c.key) for c in inspect(queue).mapper.column_attrs}

        # Use queue UUID as task queue name for security
        task_queue_name = queue_id

        return WorkerQueueResponse(
            **queue_dict,
            active_workers=active_worker_count,
            task_queue_name=task_queue_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("worker_queue_get_failed", error=str(e), queue_id=queue_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get worker queue: {str(e)}"
        )


@router.patch("/worker-queues/{queue_id}", response_model=WorkerQueueResponse)
async def update_worker_queue(
    queue_id: str,
    queue_data: WorkerQueueUpdate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Update a worker queue"""
    try:
        org_id = organization["id"]

        # Check if queue exists and get it with environment relationship
        queue = (
            db.query(WorkerQueue)
            .options(joinedload(WorkerQueue.environment))
            .filter(WorkerQueue.id == queue_id, WorkerQueue.organization_id == org_id)
            .first()
        )

        if not queue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker queue not found"
            )

        # Build update dict and apply updates
        update_data = queue_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(queue, key, value)

        queue.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(queue)

        # Get environment name from relationship
        environment_name = queue.environment.name if queue.environment else "unknown"

        # Get active workers from Redis for this specific queue
        active_workers_dict = await get_active_workers_from_redis(org_id, queue_id, db=db)
        active_worker_count = len(active_workers_dict)

        # Convert to dict for Pydantic response
        from sqlalchemy.inspection import inspect
        queue_dict = {c.key: getattr(queue, c.key) for c in inspect(queue).mapper.column_attrs}

        # Use queue UUID as task queue name for security
        task_queue_name = queue_id

        logger.info(
            "worker_queue_updated",
            queue_id=queue_id,
            org_id=org_id,
        )

        return WorkerQueueResponse(
            **queue_dict,
            active_workers=active_worker_count,
            task_queue_name=task_queue_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("worker_queue_update_failed", error=str(e), queue_id=queue_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update worker queue: {str(e)}"
        )


@router.delete("/worker-queues/{queue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_worker_queue(
    queue_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Delete a worker queue"""
    try:
        org_id = organization["id"]

        # Prevent deleting default queue and check if queue exists
        queue = (
            db.query(WorkerQueue)
            .filter(WorkerQueue.id == queue_id, WorkerQueue.organization_id == org_id)
            .first()
        )

        if not queue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker queue not found"
            )

        if queue.name == "default":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the default worker queue"
            )

        # Check for active workers in Redis
        active_workers = await get_active_workers_from_redis(org_id, queue_id, db=db)

        if active_workers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete worker queue with {len(active_workers)} active workers"
            )

        # Delete queue
        db.delete(queue)
        db.commit()

        logger.info("worker_queue_deleted", queue_id=queue_id, org_id=org_id)

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error("worker_queue_delete_failed", error=str(e), queue_id=queue_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete worker queue: {str(e)}"
        )


@router.get("/worker-queues/{queue_id}/install-script")
async def get_installation_script(
    queue_id: str,
    deployment_type: Literal["docker", "kubernetes", "openshift", "local"] = "local",
    request: Request = None,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Generate an installation script for setting up a worker for this queue.

    Supports multiple deployment types:
    - local: Python virtual environment setup
    - docker: Docker run command
    - kubernetes: Kubernetes deployment YAML
    - openshift: OpenShift deployment YAML
    """
    try:
        org_id = organization["id"]

        # Get worker queue details with environment relationship
        queue = (
            db.query(WorkerQueue)
            .options(joinedload(WorkerQueue.environment))
            .filter(WorkerQueue.id == queue_id, WorkerQueue.organization_id == org_id)
            .first()
        )

        if not queue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker queue not found"
            )

        # Get environment name from relationship
        environment_name = "default"
        if queue.environment:
            environment_name = queue.environment.name

        queue_name = queue.name

        # Get control plane URL from the request that reached us
        # This ensures installation scripts use the correct URL
        control_plane_url = f"{request.url.scheme}://{request.url.netloc}"

        # Generate new worker ID
        worker_id = str(uuid.uuid4())

        # Generate script based on deployment type
        if deployment_type == "local":
            script = _generate_local_script(worker_id, control_plane_url)
        elif deployment_type == "docker":
            script = _generate_docker_script(worker_id, control_plane_url, queue_name, environment_name)
        elif deployment_type == "kubernetes":
            script = _generate_kubernetes_script(worker_id, control_plane_url, queue_name, environment_name)
        elif deployment_type == "openshift":
            script = _generate_openshift_script(worker_id, control_plane_url, queue_name, environment_name)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported deployment type: {deployment_type}"
            )

        logger.info(
            "installation_script_generated",
            queue_id=queue_id,
            deployment_type=deployment_type,
            worker_id=worker_id,
            org_id=org_id,
        )

        return PlainTextResponse(content=script, media_type="text/plain")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("installation_script_generation_failed", error=str(e), queue_id=queue_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate installation script: {str(e)}"
        )


class WorkerSystemInfo(BaseModel):
    """Worker system information"""
    hostname: Optional[str] = None
    platform: Optional[str] = None
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    python_version: Optional[str] = None
    cli_version: Optional[str] = None
    sdk_version: Optional[str] = None  # Worker SDK version
    pid: Optional[int] = None  # Process ID
    cwd: Optional[str] = None  # Current working directory
    supported_runtimes: Optional[List[str]] = None  # Available runtimes (e.g., ["agno", "claude_code"])
    llm_gateway_url: Optional[str] = None  # LiteLLM/LLM gateway URL
    docker_available: Optional[bool] = None
    docker_version: Optional[str] = None
    cpu_count: Optional[int] = None
    cpu_percent: Optional[float] = None
    memory_total: Optional[int] = None
    memory_used: Optional[int] = None
    memory_percent: Optional[float] = None
    disk_total: Optional[int] = None
    disk_used: Optional[int] = None
    disk_percent: Optional[float] = None
    uptime_seconds: Optional[float] = None


class WorkerStartRequest(BaseModel):
    """Worker start request with SDK version and system info"""
    worker_sdk_version: Optional[str] = None
    system_info: Optional[WorkerSystemInfo] = None
    control_plane_url: Optional[str] = None


class WorkerStartResponse(BaseModel):
    """Worker start configuration"""
    worker_id: str
    task_queue_name: str  # The queue UUID
    temporal_namespace: str
    temporal_host: str
    temporal_api_key: str
    organization_id: str
    control_plane_url: str
    heartbeat_interval: int
    # LiteLLM configuration for agno workflows/activities
    litellm_api_url: str
    litellm_api_key: str
    # Queue metadata
    queue_name: str
    environment_name: str
    queue_id: str  # Queue UUID for cleanup
    queue_ephemeral: bool = False  # Whether queue is ephemeral
    queue_single_execution: bool = False  # Whether queue is for single execution
    # Redis configuration for direct event streaming (default fast path)
    redis_url: Optional[str] = None
    redis_password: Optional[str] = None
    redis_enabled: bool = False
    # WebSocket configuration for per-worker persistent connections
    websocket_enabled: bool = True
    websocket_url: Optional[str] = None
    websocket_features: List[str] = Field(default_factory=lambda: ["events", "control", "heartbeat", "config_update"])
    # NATS configuration for high-performance event bus (optional)
    nats_config: Optional[Dict[str, str]] = None
    # SDK version for compatibility check
    control_plane_sdk_version: str


@router.post("/worker-queues/{queue_id}/start", response_model=WorkerStartResponse)
async def start_worker_for_queue(
    queue_id: str,
    request: Request,
    body: WorkerStartRequest = WorkerStartRequest(),
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Start a worker for a specific queue.

    This endpoint is called by the CLI with: kubiya worker start --queue-id={queue_id}

    Returns all configuration needed for the worker to connect to Temporal.
    """
    # Get control plane SDK version for compatibility check
    from control_plane_api.version import get_sdk_version
    control_plane_sdk_version = get_sdk_version()

    # Log worker SDK version if provided
    if body.worker_sdk_version:
        logger.info(
            "worker_registration_with_version",
            queue_id=queue_id,
            worker_sdk_version=body.worker_sdk_version,
            control_plane_sdk_version=control_plane_sdk_version,
        )

    try:
        org_id = organization["id"]

        # Get worker queue with environment relationship
        queue = (
            db.query(WorkerQueue)
            .options(joinedload(WorkerQueue.environment))
            .filter(WorkerQueue.id == queue_id, WorkerQueue.organization_id == org_id)
            .first()
        )

        if not queue:
            # Check if queue exists at all (might be in different org)
            queue_check = (
                db.query(WorkerQueue)
                .filter(WorkerQueue.id == queue_id)
                .first()
            )

            if queue_check:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Worker queue '{queue_id}' not found in your organization"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Worker queue '{queue_id}' does not exist. Please create a queue from the UI first."
                )

        # Check if environment is configured
        if not queue.environment_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Worker queue '{queue.name}' has no environment configured. Please contact support."
            )

        if not queue.environment:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Environment configuration error for queue '{queue.name}'. Please contact support."
            )

        environment_name = queue.environment.name

        # Check if queue is active
        if queue.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Worker queue is not active (status: {queue.status})"
            )

        # Get organization-specific Temporal credentials
        import os
        from control_plane_api.app.lib.temporal_credentials_service import (
            get_temporal_credentials_for_org,
            is_local_temporal
        )

        org_id = organization["id"]
        token = request.state.kubiya_token

        # Check if local Temporal (for development)
        if is_local_temporal():
            logger.info("using_local_temporal_config", queue_id=queue_id, org_id=org_id)
            temporal_credentials = {
                "namespace": os.getenv("TEMPORAL_NAMESPACE", "default"),
                "api_key": "",
                "host": os.getenv("TEMPORAL_HOST", "localhost:7233"),
                "org": org_id,
            }
        else:
            # Fetch org-specific credentials from Kubiya API
            # use_fallback=True for backwards compatibility during rollout
            try:
                temporal_credentials = await get_temporal_credentials_for_org(
                    org_id=org_id,
                    token=token,
                    use_fallback=True  # Enable fallback during migration
                )

                logger.info(
                    "temporal_credentials_fetched_for_worker",
                    queue_id=queue_id,
                    org_id=org_id,
                    namespace=temporal_credentials["namespace"],
                    source="kubiya_api"
                )
            except Exception as e:
                logger.error(
                    "temporal_credentials_fetch_failed",
                    queue_id=queue_id,
                    org_id=org_id,
                    error=str(e)
                )
                # If fallback is enabled, this won't raise; if disabled, it will
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch Temporal credentials. Please contact support."
                )

        # For backwards compatibility with existing code
        namespace = {
            "namespace_name": temporal_credentials["namespace"],
            "api_key_encrypted": temporal_credentials["api_key"],
        }

        # Generate worker ID
        worker_id = str(uuid.uuid4())

        # Use worker's provided URL (preserves user configuration)
        # Fallback to request URL for backward compatibility with old workers
        if body.control_plane_url:
            control_plane_url = body.control_plane_url.rstrip("/")
            logger.info(
                "using_worker_provided_control_plane_url",
                queue_id=queue_id,
                worker_url=control_plane_url,
                request_url=f"{request.url.scheme}://{request.url.netloc}"
            )
        else:
            # Backward compatibility for old workers
            control_plane_url = f"{request.url.scheme}://{request.url.netloc}"
            logger.info(
                "using_request_derived_control_plane_url",
                queue_id=queue_id,
                control_plane_url=control_plane_url
            )
        temporal_host = temporal_credentials["host"]

        # Get LiteLLM configuration for agno workflows/activities
        litellm_api_url = os.getenv("LITELLM_API_URL", "https://llm-proxy.kubiya.ai")
        litellm_api_key = os.getenv("LITELLM_API_KEY", "")

        # Create worker heartbeat record

        now = datetime.now(timezone.utc)
        worker_metadata = {}
        if body.system_info:
            worker_metadata = body.system_info.model_dump(exclude_none=True)
            logger.info(
                "worker_registration_with_system_info",
                worker_id=worker_id[:8],
                hostname=worker_metadata.get("hostname"),
                sdk_version=worker_metadata.get("sdk_version"),
                pid=worker_metadata.get("pid"),
                cwd=worker_metadata.get("cwd"),
            )

        # Add LLM gateway URL from control plane config
        worker_metadata["llm_gateway_url"] = litellm_api_url

        worker_heartbeat = WorkerHeartbeat(
            id=worker_id,
            worker_id=worker_id,
            organization_id=org_id,
            worker_queue_id=queue_id,
            environment_name=environment_name,
            status="active",
            tasks_processed=0,
            registered_at=now,
            last_heartbeat=now,
            updated_at=now,
            worker_metadata={},
        )

        db.add(worker_heartbeat)
        db.commit()

        # Task queue name is just the queue UUID for security
        task_queue_name = queue_id

        # Determine WebSocket configuration
        # WebSocket is only supported when control plane is NOT in serverless environment
        # (Vercel, AWS Lambda, etc. don't support persistent WebSocket connections)
        control_plane_env = detect_environment()
        websocket_enabled = (
            os.getenv("WEBSOCKET_ENABLED", "true").lower() == "true"
            and control_plane_env == "standard"
        )
        websocket_url = None

        if websocket_enabled:
            # Convert HTTP(S) to WS(S) for WebSocket URL
            ws_base = control_plane_url.replace("https://", "wss://").replace("http://", "ws://")
            websocket_url = f"{ws_base}/api/v1/ws/workers/{worker_id}"

        if not websocket_enabled and control_plane_env == "serverless":
            logger.info(
                "websocket_disabled_serverless_control_plane",
                worker_id=worker_id[:8],
                environment=control_plane_env
            )

        # Redis configuration for direct event streaming (default fast path)
        # Workers will use Redis directly instead of HTTP endpoint for better performance
        redis_url = None
        redis_password = None
        redis_enabled = False

        if settings.redis_url:
            redis_url = settings.redis_url
            redis_enabled = True

            # Extract password from Redis URL if present (redis://:password@host:port/db)
            if "@" in redis_url and ":" in redis_url:
                try:
                    # Parse URL to extract password
                    from urllib.parse import urlparse
                    parsed = urlparse(redis_url)
                    if parsed.password:
                        redis_password = parsed.password
                except Exception as e:
                    logger.warning(
                        "redis_password_extraction_failed",
                        error=str(e),
                        worker_id=worker_id[:8],
                    )

            logger.info(
                "redis_config_provided_to_worker",
                worker_id=worker_id[:8],
                redis_url=redis_url.split("@")[-1] if "@" in redis_url else redis_url,  # Log without password
            )

        # NATS configuration (optional, enterprise-grade event bus)
        nats_config = None
        if (
            hasattr(settings, "event_bus")
            and settings.event_bus
            and isinstance(settings.event_bus, dict)
            and "nats" in settings.event_bus
            and settings.event_bus["nats"].get("enabled", False)
        ):
            try:
                from control_plane_api.app.lib.nats import NATSCredentialsManager

                # Get NATS operator credentials from settings/env
                nats_operator_jwt = os.getenv("NATS_OPERATOR_JWT")
                nats_operator_seed = os.getenv("NATS_OPERATOR_SEED")

                if nats_operator_jwt and nats_operator_seed:
                    # Create credentials manager
                    creds_manager = NATSCredentialsManager(
                        operator_jwt=nats_operator_jwt,
                        operator_seed=nats_operator_seed,
                    )

                    # Generate temporary worker credentials (24-hour TTL)
                    worker_creds = creds_manager.create_worker_credentials(
                        worker_id=worker_id,
                        organization_id=org_id,
                        ttl_hours=24,
                    )

                    # Get NATS URL from config
                    nats_url = settings.event_bus["nats"].get("nats_url")

                    # Build NATS config for worker
                    nats_config = {
                        "nats_url": nats_url,
                        "nats_jwt": worker_creds.jwt,
                        "nats_seed": worker_creds.seed,
                        "subject_prefix": worker_creds.subject_prefix,
                        "organization_id": org_id,
                        "worker_id": worker_id,
                        "jetstream_enabled": str(
                            settings.event_bus["nats"].get("jetstream_enabled", True)
                        ),
                        "expires_at": worker_creds.expires_at.isoformat(),
                    }

                    logger.info(
                        "nats_credentials_generated_for_worker",
                        worker_id=worker_id[:8],
                        organization_id=org_id,
                        subject_prefix=worker_creds.subject_prefix,
                        expires_at=worker_creds.expires_at.isoformat(),
                    )
                else:
                    logger.warning(
                        "nats_operator_credentials_not_configured",
                        message="NATS enabled but NATS_OPERATOR_JWT or NATS_OPERATOR_SEED not set",
                    )

            except ImportError:
                logger.warning(
                    "nats_dependency_missing",
                    message="NATS credentials generation skipped - nkeys not installed",
                )
            except Exception as e:
                logger.error(
                    "nats_credentials_generation_failed",
                    error=str(e),
                    worker_id=worker_id[:8],
                )

        logger.info(
            "worker_started_for_queue",
            worker_id=worker_id,
            queue_id=queue_id,
            task_queue_name=task_queue_name,
            org_id=org_id,
            websocket_enabled=websocket_enabled,
            nats_enabled=nats_config is not None,
        )

        return WorkerStartResponse(
            worker_id=worker_id,
            task_queue_name=task_queue_name,
            temporal_namespace=namespace["namespace_name"],
            temporal_host=temporal_host,
            temporal_api_key=namespace["api_key_encrypted"],
            organization_id=org_id,
            control_plane_url=control_plane_url,
            heartbeat_interval=queue.heartbeat_interval or 60,
            litellm_api_url=litellm_api_url,
            litellm_api_key=litellm_api_key,
            queue_name=queue.name,
            environment_name=environment_name,
            queue_id=queue_id,
            queue_ephemeral=queue.ephemeral or False,
            queue_single_execution=queue.single_execution_mode or False,
            redis_url=redis_url,
            redis_password=redis_password,
            redis_enabled=redis_enabled,
            websocket_enabled=websocket_enabled,
            websocket_url=websocket_url,
            websocket_features=["events", "control", "heartbeat", "config_update"],
            nats_config=nats_config,
            control_plane_sdk_version=control_plane_sdk_version,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "worker_start_for_queue_failed",
            error=str(e),
            error_type=type(e).__name__,
            queue_id=queue_id,
            org_id=organization.get("id")
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start worker due to an internal error. Please try again or contact support. (Error ID: {queue_id[:8]})"
        )


def _generate_local_script(worker_id: str, control_plane_url: str) -> str:
    """Generate a bash script for local Python installation"""
    return f"""#!/bin/bash
# Kubiya Agent Worker - Local Installation Script
# Generated: {datetime.now(timezone.utc).isoformat()}

set -e

echo "🚀 Setting up Kubiya Agent Worker..."
echo ""

# Configuration
WORKER_ID="{worker_id}"
CONTROL_PLANE_URL="{control_plane_url}"

# Check if KUBIYA_API_KEY is set
if [ -z "$KUBIYA_API_KEY" ]; then
    echo "❌ Error: KUBIYA_API_KEY environment variable is not set"
    echo "Please set it with: export KUBIYA_API_KEY=your-api-key"
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Create directory
WORKER_DIR="$HOME/.kubiya/workers/$WORKER_ID"
mkdir -p "$WORKER_DIR"
cd "$WORKER_DIR"

echo "✓ Created worker directory: $WORKER_DIR"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install worker package (includes all dependencies from pyproject.toml)
echo "📦 Installing worker package..."
if command -v uv &> /dev/null; then
    echo "✓ Using uv (fast mode)"
    uv pip install --quiet kubiya-control-plane-api[worker]
else
    echo "ℹ️  Using pip (consider installing uv: https://github.com/astral-sh/uv)"
    pip install --quiet --upgrade pip
    pip install --quiet kubiya-control-plane-api[worker]
fi

echo "✓ Worker package installed"

# Create systemd service file (optional)
cat > kubiya-worker.service <<EOF
[Unit]
Description=Kubiya Agent Worker
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORKER_DIR
Environment="WORKER_ID=$WORKER_ID"
Environment="KUBIYA_API_KEY=$KUBIYA_API_KEY"
Environment="CONTROL_PLANE_URL=$CONTROL_PLANE_URL"
ExecStart=$WORKER_DIR/venv/bin/python $WORKER_DIR/worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Systemd service file created (optional)"

# Create run script
cat > run.sh <<EOF
#!/bin/bash
cd "$WORKER_DIR"
source venv/bin/activate
export WORKER_ID="$WORKER_ID"
export KUBIYA_API_KEY="$KUBIYA_API_KEY"
export CONTROL_PLANE_URL="$CONTROL_PLANE_URL"
python worker.py
EOF

chmod +x run.sh

echo ""
echo "✅ Installation complete!"
echo ""
echo "To start the worker:"
echo "  cd $WORKER_DIR && ./run.sh"
echo ""
echo "Or to install as a systemd service:"
echo "  sudo cp $WORKER_DIR/kubiya-worker.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable kubiya-worker"
echo "  sudo systemctl start kubiya-worker"
echo ""
"""


def _generate_docker_script(worker_id: str, control_plane_url: str, queue_name: str, environment_name: str) -> str:
    """Generate Docker commands for running the worker"""
    return f"""# Kubiya Agent Worker - Docker Installation
# Generated: {datetime.now(timezone.utc).isoformat()}

# Configuration
WORKER_ID="{worker_id}"
CONTROL_PLANE_URL="{control_plane_url}"
QUEUE_NAME="{queue_name}"
ENVIRONMENT_NAME="{environment_name}"

# Make sure to set your API key
# export KUBIYA_API_KEY=your-api-key

# Run with Docker
docker run -d \\
  --name kubiya-worker-{queue_name}-{worker_id[:8]} \\
  --restart unless-stopped \\
  -e WORKER_ID="$WORKER_ID" \\
  -e KUBIYA_API_KEY="$KUBIYA_API_KEY" \\
  -e CONTROL_PLANE_URL="$CONTROL_PLANE_URL" \\
  -e LOG_LEVEL="INFO" \\
  kubiya/agent-worker:latest

# Check logs
# docker logs -f kubiya-worker-{queue_name}-{worker_id[:8]}

# Stop worker
# docker stop kubiya-worker-{queue_name}-{worker_id[:8]}

# Remove worker
# docker rm kubiya-worker-{queue_name}-{worker_id[:8]}

# Docker Compose (save as docker-compose.yml)
cat > docker-compose.yml <<EOF
version: '3.8'

services:
  worker:
    image: kubiya/agent-worker:latest
    container_name: kubiya-worker-{queue_name}
    restart: unless-stopped
    environment:
      - WORKER_ID={worker_id}
      - KUBIYA_API_KEY=${{KUBIYA_API_KEY}}
      - CONTROL_PLANE_URL={control_plane_url}
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('{control_plane_url}/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
EOF

# To use docker-compose:
# docker-compose up -d
"""


def _generate_kubernetes_script(worker_id: str, control_plane_url: str, queue_name: str, environment_name: str) -> str:
    """Generate Kubernetes deployment YAML"""
    return f"""# Kubiya Agent Worker - Kubernetes Deployment
# Generated: {datetime.now(timezone.utc).isoformat()}
#
# To deploy:
# 1. Create secret: kubectl create secret generic kubiya-worker-secret --from-literal=api-key=YOUR_API_KEY
# 2. Apply this file: kubectl apply -f kubiya-worker.yaml
#
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: kubiya-worker-{queue_name}-config
  labels:
    app: kubiya-worker
    queue: {queue_name}
    environment: {environment_name}
data:
  WORKER_ID: "{worker_id}"
  CONTROL_PLANE_URL: "{control_plane_url}"
  LOG_LEVEL: "INFO"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kubiya-worker-{queue_name}
  labels:
    app: kubiya-worker
    queue: {queue_name}
    environment: {environment_name}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kubiya-worker
      queue: {queue_name}
  template:
    metadata:
      labels:
        app: kubiya-worker
        queue: {queue_name}
        environment: {environment_name}
    spec:
      containers:
      - name: worker
        image: kubiya/agent-worker:latest
        imagePullPolicy: Always
        envFrom:
        - configMapRef:
            name: kubiya-worker-{queue_name}-config
        env:
        - name: KUBIYA_API_KEY
          valueFrom:
            secretKeyRef:
              name: kubiya-worker-secret
              key: api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
      restartPolicy: Always

---
apiVersion: v1
kind: Service
metadata:
  name: kubiya-worker-{queue_name}
  labels:
    app: kubiya-worker
    queue: {queue_name}
spec:
  selector:
    app: kubiya-worker
    queue: {queue_name}
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
  type: ClusterIP

---
# Optional: HorizontalPodAutoscaler
# apiVersion: autoscaling/v2
# kind: HorizontalPodAutoscaler
# metadata:
#   name: kubiya-worker-{queue_name}
# spec:
#   scaleTargetRef:
#     apiVersion: apps/v1
#     kind: Deployment
#     name: kubiya-worker-{queue_name}
#   minReplicas: 1
#   maxReplicas: 10
#   metrics:
#   - type: Resource
#     resource:
#       name: cpu
#       target:
#         type: Utilization
#         averageUtilization: 70
"""


class WorkerQueueCommandResponse(BaseModel):
    """Worker queue connection command"""
    queue_id: str
    command: str
    command_parts: dict
    can_register: bool
    queue_status: str
    active_workers: int
    max_workers: Optional[int]


class WorkerDetail(BaseModel):
    """Individual worker details"""
    id: str
    worker_id: str
    status: str
    tasks_processed: int
    current_task_id: Optional[str]
    last_heartbeat: str
    registered_at: str
    system_info: Optional[WorkerSystemInfo] = None
    logs: Optional[List[str]] = None
    worker_metadata: dict


@router.get("/worker-queues/{queue_id}/workers", response_model=List[WorkerDetail])
async def list_queue_workers(
    queue_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    List all workers for a specific queue with detailed information.
    """
    try:
        org_id = organization["id"]

        # Get active workers from Redis for this queue
        active_workers = await get_active_workers_from_redis(org_id, queue_id, db=db)

        # Get worker registration details from database (registered_at, worker_id, worker_metadata)
        if active_workers:
            db_workers = (
                db.query(WorkerHeartbeat)
                .filter(
                    WorkerHeartbeat.organization_id == org_id,
                    WorkerHeartbeat.id.in_(list(active_workers.keys()))
                )
                .all()
            )
            db_workers_map = {str(w.id): w for w in db_workers}
        else:
            db_workers_map = {}

        workers = []
        for worker_id, heartbeat_data in active_workers.items():
            # Get DB data for registration time
            db_data = db_workers_map.get(worker_id, None)

            # Extract system info and logs from Redis heartbeat data
            metadata = heartbeat_data.get("metadata", {})
            system_info_data = heartbeat_data.get("system_info")
            logs = heartbeat_data.get("logs", [])

            # Fall back to worker_metadata from database if system_info not in Redis
            if not system_info_data and db_data and db_data.worker_metadata:
                system_info_data = db_data.worker_metadata

            system_info = WorkerSystemInfo(**system_info_data) if system_info_data else None

            workers.append(
                WorkerDetail(
                    id=worker_id,
                    worker_id=db_data.worker_id if db_data else worker_id,
                    status=heartbeat_data.get("status", "unknown"),
                    tasks_processed=heartbeat_data.get("tasks_processed", 0),
                    current_task_id=heartbeat_data.get("current_task_id"),
                    last_heartbeat=heartbeat_data.get("last_heartbeat", ""),
                    registered_at=db_data.registered_at.isoformat() if db_data and db_data.registered_at else "",
                    system_info=system_info,
                    logs=logs,
                    worker_metadata=metadata,
                )
            )

        # Sort by last_heartbeat desc
        workers.sort(key=lambda w: w.last_heartbeat, reverse=True)

        logger.info(
            "queue_workers_listed",
            queue_id=queue_id,
            worker_count=len(workers),
            org_id=org_id,
        )

        return workers

    except HTTPException:
        raise
    except Exception as e:
        logger.error("queue_workers_list_failed", error=str(e), queue_id=queue_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list queue workers: {str(e)}"
        )


@router.get("/worker-queues/{queue_id}/metrics", response_model=WorkerQueueMetricsResponse)
async def get_worker_queue_metrics(
    queue_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive metrics for a worker queue.

    Returns worker health metrics, task statistics, and performance data.
    """
    try:
        org_id = organization["id"]

        # Use service layer for business logic
        metrics_service = WorkerQueueMetricsService(db)
        metrics = await metrics_service.get_queue_metrics(queue_id, org_id)

        logger.info(
            "queue_metrics_retrieved",
            queue_id=queue_id,
            org_id=org_id
        )

        return metrics

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "queue_metrics_failed",
            error=str(e),
            queue_id=queue_id,
            org_id=org_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue metrics: {str(e)}"
        )


@router.get("/worker-queues/{queue_id}/workflows", response_model=WorkflowsListResponse)
async def list_queue_workflows(
    queue_id: str,
    request: Request,
    status_filter: Optional[str] = None,
    limit: int = 100,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    List workflows/tasks for a worker queue.

    Returns list of workflows with status counts and filtering options.
    """
    try:
        org_id = organization["id"]

        # Import service here to avoid circular imports
        from control_plane_api.app.services.workflow_operations_service import WorkflowOperationsService

        # Use service layer for business logic
        workflow_service = WorkflowOperationsService(db)
        workflows = await workflow_service.list_queue_workflows(
            queue_id=queue_id,
            organization_id=org_id,
            status_filter=status_filter,
            limit=limit
        )

        logger.info(
            "queue_workflows_listed",
            queue_id=queue_id,
            total=workflows.total,
            org_id=org_id
        )

        return workflows

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "queue_workflows_list_failed",
            error=str(e),
            queue_id=queue_id,
            org_id=org_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list queue workflows: {str(e)}"
        )


@router.get("/worker-queues/{queue_id}/worker-command", response_model=WorkerQueueCommandResponse)
async def get_worker_queue_command(
    queue_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Get the worker registration command for a specific worker queue.

    Returns the kubiya worker start command with the queue ID that users
    should run to start a worker for this specific queue.
    """
    try:
        org_id = organization["id"]

        # Get worker queue
        queue = (
            db.query(WorkerQueue)
            .filter(WorkerQueue.id == queue_id, WorkerQueue.organization_id == org_id)
            .first()
        )

        if not queue:
            raise HTTPException(status_code=404, detail="Worker queue not found")

        queue_status = queue.status or "unknown"

        # Check if queue is active
        can_register = queue_status == "active"

        # Get active workers from Redis for this specific queue
        active_workers_dict = await get_active_workers_from_redis(org_id, queue_id, db=db)
        active_worker_count = len(active_workers_dict)

        # Build command
        command = f"kubiya worker start --queue-id {queue_id}"

        command_parts = {
            "binary": "kubiya",
            "subcommand": "worker start",
            "flags": {
                "--queue-id": queue_id,
            },
        }

        logger.info(
            "worker_queue_command_retrieved",
            queue_id=queue_id,
            can_register=can_register,
            status=queue_status,
            active_workers=active_worker_count,
            org_id=org_id,
        )

        return WorkerQueueCommandResponse(
            queue_id=queue_id,
            command=command,
            command_parts=command_parts,
            can_register=can_register,
            queue_status=queue_status,
            active_workers=active_worker_count,
            max_workers=queue.max_workers,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("worker_queue_command_failed", error=str(e), queue_id=queue_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get worker queue command: {str(e)}"
        )


def _generate_openshift_script(worker_id: str, control_plane_url: str, queue_name: str, environment_name: str) -> str:
    """Generate OpenShift deployment YAML"""
    return f"""# Kubiya Agent Worker - OpenShift Deployment
# Generated: {datetime.now(timezone.utc).isoformat()}
#
# To deploy:
# 1. Create secret: oc create secret generic kubiya-worker-secret --from-literal=api-key=YOUR_API_KEY
# 2. Apply this file: oc apply -f kubiya-worker.yaml
#
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: kubiya-worker-{queue_name}-config
  labels:
    app: kubiya-worker
    queue: {queue_name}
    environment: {environment_name}
data:
  WORKER_ID: "{worker_id}"
  CONTROL_PLANE_URL: "{control_plane_url}"
  LOG_LEVEL: "INFO"

---
apiVersion: apps.openshift.io/v1
kind: DeploymentConfig
metadata:
  name: kubiya-worker-{queue_name}
  labels:
    app: kubiya-worker
    queue: {queue_name}
    environment: {environment_name}
spec:
  replicas: 1
  selector:
    app: kubiya-worker
    queue: {queue_name}
  template:
    metadata:
      labels:
        app: kubiya-worker
        queue: {queue_name}
        environment: {environment_name}
    spec:
      containers:
      - name: worker
        image: kubiya/agent-worker:latest
        imagePullPolicy: Always
        envFrom:
        - configMapRef:
            name: kubiya-worker-{queue_name}-config
        env:
        - name: KUBIYA_API_KEY
          valueFrom:
            secretKeyRef:
              name: kubiya-worker-secret
              key: api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
      restartPolicy: Always
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
  triggers:
  - type: ConfigChange
  - type: ImageChange
    imageChangeParams:
      automatic: true
      containerNames:
      - worker
      from:
        kind: ImageStreamTag
        name: agent-worker:latest

---
apiVersion: v1
kind: Service
metadata:
  name: kubiya-worker-{queue_name}
  labels:
    app: kubiya-worker
    queue: {queue_name}
spec:
  selector:
    app: kubiya-worker
    queue: {queue_name}
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
  type: ClusterIP

---
# Optional: Route to expose the service
# apiVersion: route.openshift.io/v1
# kind: Route
# metadata:
#   name: kubiya-worker-{queue_name}
#   labels:
#     app: kubiya-worker
#     queue: {queue_name}
# spec:
#   to:
#     kind: Service
#     name: kubiya-worker-{queue_name}
#   port:
#     targetPort: 8080
#   tls:
#     termination: edge
#     insecureEdgeTerminationPolicy: Redirect
"""


# ============================================================================
# Worker Auto-Update Endpoints
# ============================================================================


class WorkerQueueConfigResponse(BaseModel):
    """Worker queue configuration with version tracking for auto-updates"""
    queue_id: str
    name: str
    display_name: Optional[str]
    description: Optional[str]
    status: str
    max_workers: Optional[int]
    heartbeat_interval: int
    tags: List[str]
    settings: dict
    config_version: str  # SHA256 hash of configuration for change detection
    config_updated_at: str  # Timestamp of last configuration change
    recommended_package_version: Optional[str] = None  # Latest recommended worker package version
    environment_id: str
    environment_name: str


class UpdateLockRequest(BaseModel):
    """Request to acquire an update lock for coordinated rolling updates"""
    worker_id: str
    lock_duration_seconds: int = Field(default=300, ge=60, le=600, description="Lock TTL (60-600 seconds)")


class UpdateLockResponse(BaseModel):
    """Response with update lock information"""
    lock_id: str
    worker_id: str
    queue_id: str
    acquired_at: str
    expires_at: str
    locked: bool


def _compute_config_hash(queue: dict) -> str:
    """
    Compute SHA256 hash of worker queue configuration.

    This hash is used to detect configuration changes for auto-updates.
    Only includes fields that affect worker behavior.
    """
    config_data = {
        "name": queue.get("name"),
        "status": queue.get("status"),
        "max_workers": queue.get("max_workers"),
        "heartbeat_interval": queue.get("heartbeat_interval"),
        "tags": sorted(queue.get("tags", [])),  # Sort for consistency
        "settings": queue.get("settings", {}),
    }

    # Serialize to JSON with sorted keys for consistent hashing
    config_json = json.dumps(config_data, sort_keys=True)
    return hashlib.sha256(config_json.encode()).hexdigest()


@router.get("/worker-queues/{queue_id}/config", response_model=WorkerQueueConfigResponse)
async def get_worker_queue_config(
    queue_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Get worker queue configuration with version tracking for auto-updates.

    This endpoint is called by CLI workers periodically to check for configuration changes.
    The config_version hash allows workers to detect when they need to reload.

    Args:
        queue_id: Worker queue ID

    Returns:
        Configuration with version hash and recommended package version
    """
    try:
        org_id = organization["id"]

        # Get worker queue with environment relationship
        queue = (
            db.query(WorkerQueue)
            .options(joinedload(WorkerQueue.environment))
            .filter(WorkerQueue.id == queue_id, WorkerQueue.organization_id == org_id)
            .first()
        )

        if not queue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker queue not found"
            )

        # Get environment name from relationship
        environment_name = queue.environment.name if queue.environment else "unknown"

        # Convert queue to dict for config hash computation
        from sqlalchemy.inspection import inspect
        queue_dict = {c.key: getattr(queue, c.key) for c in inspect(queue).mapper.column_attrs}

        # Compute configuration hash for change detection
        config_version = _compute_config_hash(queue_dict)

        # Get recommended package version from control plane settings or PyPI
        # This can be configured via environment variable or fetched from PyPI
        recommended_package_version = os.getenv("KUBIYA_RECOMMENDED_WORKER_VERSION")
        if not recommended_package_version:
            # Fetch latest version from PyPI (cached for performance)
            try:
                import httpx
                response = httpx.get("https://pypi.org/pypi/kubiya-control-plane-api/json", timeout=5.0)
                if response.status_code == 200:
                    pypi_data = response.json()
                    recommended_package_version = pypi_data.get("info", {}).get("version")
            except Exception as e:
                logger.warning(
                    "failed_to_fetch_pypi_version",
                    error=str(e),
                    queue_id=queue_id,
                )
                # Fallback: no recommendation if PyPI fetch fails
                recommended_package_version = None

        logger.info(
            "worker_queue_config_fetched",
            queue_id=queue_id,
            config_version=config_version[:8],  # Log first 8 chars of hash
            org_id=org_id,
        )

        return WorkerQueueConfigResponse(
            queue_id=queue_id,
            name=queue.name,
            display_name=queue.display_name,
            description=queue.description,
            status=queue.status,
            max_workers=queue.max_workers,
            heartbeat_interval=queue.heartbeat_interval or 60,
            tags=queue.tags or [],
            settings=queue.settings or {},
            config_version=config_version,
            config_updated_at=queue.updated_at.isoformat() if queue.updated_at else queue.created_at.isoformat(),
            recommended_package_version=recommended_package_version,
            environment_id=str(queue.environment_id),
            environment_name=environment_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("worker_queue_config_fetch_failed", error=str(e), queue_id=queue_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch worker queue config: {str(e)}"
        )


@router.post("/worker-queues/{queue_id}/workers/{worker_id}/update-lock", response_model=UpdateLockResponse)
async def acquire_update_lock(
    queue_id: str,
    worker_id: str,
    lock_request: UpdateLockRequest,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Acquire an update lock for coordinated rolling updates.

    This ensures only one worker in a queue updates at a time.
    Uses Redis for distributed locking with automatic TTL expiration.

    Args:
        queue_id: Worker queue ID
        worker_id: Worker ID requesting the lock
        lock_request: Lock configuration (duration)

    Returns:
        Lock information if acquired, or error if another worker holds the lock
    """
    try:
        org_id = organization["id"]
        redis_client = get_redis_client()

        if not redis_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Update coordination unavailable (Redis not configured)"
            )

        # Verify queue exists and worker belongs to this queue
        queue = (
            db.query(WorkerQueue)
            .filter(WorkerQueue.id == queue_id, WorkerQueue.organization_id == org_id)
            .first()
        )

        if not queue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker queue not found"
            )

        # Check if worker exists (optional - for validation)
        worker_heartbeat_key = f"worker:{worker_id}:heartbeat"
        worker_data = await redis_client.get(worker_heartbeat_key)

        if not worker_data:
            logger.warning(
                "worker_not_found_in_heartbeats",
                worker_id=worker_id,
                queue_id=queue_id,
                org_id=org_id,
            )

        # Try to acquire lock using Redis SET NX (set if not exists)
        lock_key = f"worker_queue:{queue_id}:update_lock"
        lock_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=lock_request.lock_duration_seconds)

        lock_data = {
            "lock_id": lock_id,
            "worker_id": worker_id,
            "queue_id": queue_id,
            "organization_id": org_id,
            "acquired_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        # SET NX EX: Set if not exists with expiration
        acquired = await redis_client.set(
            lock_key,
            json.dumps(lock_data),
            ex=lock_request.lock_duration_seconds,
            nx=True,  # Only set if key doesn't exist
        )

        if not acquired:
            # Lock already held by another worker
            existing_lock_data = await redis_client.get(lock_key)
            if existing_lock_data:
                existing_lock = json.loads(existing_lock_data)
                logger.info(
                    "update_lock_already_held",
                    queue_id=queue_id,
                    requesting_worker=worker_id,
                    lock_holder=existing_lock.get("worker_id"),
                    org_id=org_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Update lock already held by worker {existing_lock.get('worker_id')}"
                )
            else:
                # Race condition: lock was released between check and get
                logger.warning("update_lock_race_condition", queue_id=queue_id, worker_id=worker_id)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Failed to acquire lock due to race condition, please retry"
                )

        logger.info(
            "update_lock_acquired",
            lock_id=lock_id,
            worker_id=worker_id,
            queue_id=queue_id,
            duration_seconds=lock_request.lock_duration_seconds,
            org_id=org_id,
        )

        return UpdateLockResponse(
            lock_id=lock_id,
            worker_id=worker_id,
            queue_id=queue_id,
            acquired_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
            locked=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "update_lock_acquisition_failed",
            error=str(e),
            queue_id=queue_id,
            worker_id=worker_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acquire update lock: {str(e)}"
        )


@router.delete("/worker-queues/{queue_id}/workers/{worker_id}/update-lock", status_code=status.HTTP_204_NO_CONTENT)
async def release_update_lock(
    queue_id: str,
    worker_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
):
    """
    Release an update lock after worker has completed its update.

    Only the worker that acquired the lock can release it (verified by worker_id).

    Args:
        queue_id: Worker queue ID
        worker_id: Worker ID that holds the lock
    """
    try:
        org_id = organization["id"]
        redis_client = get_redis_client()

        if not redis_client:
            # If Redis is unavailable, just return success (lock will expire naturally)
            logger.warning(
                "redis_unavailable_for_lock_release",
                queue_id=queue_id,
                worker_id=worker_id,
                org_id=org_id,
            )
            return None

        lock_key = f"worker_queue:{queue_id}:update_lock"

        # Get current lock to verify ownership
        lock_data_str = await redis_client.get(lock_key)

        if not lock_data_str:
            # Lock doesn't exist (already expired or never acquired)
            logger.info(
                "update_lock_not_found",
                queue_id=queue_id,
                worker_id=worker_id,
                org_id=org_id,
            )
            return None

        lock_data = json.loads(lock_data_str)

        # Verify lock is held by this worker
        if lock_data.get("worker_id") != worker_id:
            logger.warning(
                "update_lock_ownership_mismatch",
                queue_id=queue_id,
                requesting_worker=worker_id,
                lock_holder=lock_data.get("worker_id"),
                org_id=org_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Lock is held by another worker ({lock_data.get('worker_id')})"
            )

        # Release the lock
        await redis_client.delete(lock_key)

        logger.info(
            "update_lock_released",
            lock_id=lock_data.get("lock_id"),
            worker_id=worker_id,
            queue_id=queue_id,
            org_id=org_id,
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "update_lock_release_failed",
            error=str(e),
            queue_id=queue_id,
            worker_id=worker_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to release update lock: {str(e)}"
        )


@router.get("/worker-queues/{queue_id}/update-lock-status")
async def get_update_lock_status(
    queue_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
):
    """
    Get the current update lock status for a queue.

    Useful for checking if updates are in progress before triggering manual updates.

    Args:
        queue_id: Worker queue ID

    Returns:
        Lock status (locked/unlocked) and lock holder if locked
    """
    try:
        org_id = organization["id"]
        redis_client = get_redis_client()

        if not redis_client:
            return {
                "locked": False,
                "lock_coordination_available": False,
                "message": "Lock coordination unavailable (Redis not configured)",
            }

        lock_key = f"worker_queue:{queue_id}:update_lock"
        lock_data_str = await redis_client.get(lock_key)

        if not lock_data_str:
            return {
                "locked": False,
                "queue_id": queue_id,
                "lock_coordination_available": True,
            }

        lock_data = json.loads(lock_data_str)

        # Get TTL for expiration info
        ttl = await redis_client.ttl(lock_key)

        return {
            "locked": True,
            "queue_id": queue_id,
            "worker_id": lock_data.get("worker_id"),
            "lock_id": lock_data.get("lock_id"),
            "acquired_at": lock_data.get("acquired_at"),
            "expires_at": lock_data.get("expires_at"),
            "ttl_seconds": ttl if ttl > 0 else 0,
            "lock_coordination_available": True,
        }

    except Exception as e:
        logger.error(
            "update_lock_status_check_failed",
            error=str(e),
            queue_id=queue_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check lock status: {str(e)}"
        )


@router.get("/worker-queues/{queue_id}/executions")
async def list_queue_executions(
    queue_id: str,
    request: Request,
    limit: int = 10,
    status: str = "all",
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    List recent executions for a specific worker queue.

    Used by workers in single-execution mode to monitor when their task completes.

    Args:
        queue_id: Worker queue ID
        limit: Maximum number of executions to return (default: 10)
        status: Filter by status ('all', 'running', 'completed', 'failed', etc.)

    Returns:
        List of executions for this queue
    """
    try:
        org_id = organization["id"]

        # Verify queue exists and belongs to this org
        queue = (
            db.query(WorkerQueue)
            .filter(WorkerQueue.id == queue_id, WorkerQueue.organization_id == org_id)
            .first()
        )

        if not queue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker queue not found"
            )

        # Import Execution model
        from control_plane_api.app.models.execution import Execution

        # Query executions for this queue
        query = db.query(Execution).filter(
            Execution.organization_id == org_id,
            Execution.worker_queue_id == queue_id
        )

        # Filter by status if not 'all'
        if status != "all":
            query = query.filter(Execution.status == status)

        # Order by created_at descending and limit
        executions = query.order_by(desc(Execution.created_at)).limit(limit).all()

        # Convert to dict for JSON response
        result = []
        for execution in executions:
            result.append({
                "id": str(execution.id),
                "status": execution.status,
                "entity_id": str(execution.entity_id),
                "entity_name": execution.entity_name,
                "execution_type": execution.execution_type,
                "prompt": execution.prompt[:200] if execution.prompt else None,  # Truncate for brevity
                "created_at": execution.created_at.isoformat() if execution.created_at else None,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "temporal_workflow_id": execution.temporal_workflow_id,
            })

        logger.info(
            "queue_executions_listed",
            queue_id=queue_id,
            count=len(result),
            org_id=org_id,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("queue_executions_list_failed", error=str(e), queue_id=queue_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list queue executions: {str(e)}"
        )
