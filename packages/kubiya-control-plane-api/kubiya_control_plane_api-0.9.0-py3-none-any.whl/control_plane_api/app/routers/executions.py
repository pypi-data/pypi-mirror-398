"""
Multi-tenant executions router with SQLAlchemy.

This router handles execution queries for the authenticated organization.
Uses SQLAlchemy for database operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import structlog
import asyncio
import json
import uuid as uuid_module

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.database import get_db
from control_plane_api.app.lib.sqlalchemy_utils import model_to_dict, models_to_dict_list
from control_plane_api.app.lib.temporal_client import get_temporal_client
from control_plane_api.app.lib.redis_client import get_redis_client
from control_plane_api.app.workflows.agent_execution import AgentExecutionWorkflow
from control_plane_api.app.services.agno_service import agno_service
from control_plane_api.app.models.execution import Execution
from control_plane_api.app.models.job import Job, JobExecution
from control_plane_api.app.models.agent import Agent
from control_plane_api.app.models.team import Team
from control_plane_api.app.models.worker import WorkerQueue
from control_plane_api.app.models.associations import ExecutionParticipant
from control_plane_api.app.models.session import Session as SessionModel
from control_plane_api.app.schemas.worker_queue_observability_schemas import (
    WorkflowDetailsResponse,
    TerminateWorkflowRequest,
    TerminateWorkflowResponse,
    BatchTerminateRequest,
    BatchTerminateResult,
    BatchTerminateResponse
)
from control_plane_api.app.services.workflow_operations_service import WorkflowOperationsService

# Import new streaming router (Task 15 - Resumable Execution Stream Architecture)
from control_plane_api.app.routers.executions.router import router as new_streaming_router

logger = structlog.get_logger()

router = APIRouter()

# Include the new streaming router (this adds the /{execution_id}/stream endpoint)
# The new router replaces the old ~1,400 line monolithic streaming implementation
# with a modular ExecutionStreamer architecture
router.include_router(new_streaming_router, tags=["executions"])


def sanitize_jsonb_field(value: Any, field_name: str = None) -> dict:
    """Sanitize a JSONB field value to ensure it's a valid dict."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    return {}


async def validate_job_exists(
    db: Session,
    job_id: str,
    organization_id: str,
    logger_context: dict = None
) -> dict:
    """
    Validate that a job exists and belongs to the organization.

    Args:
        db: SQLAlchemy session
        job_id: Job ID to validate
        organization_id: Organization ID for security check
        logger_context: Additional context for logging

    Returns:
        dict: Job record if valid

    Raises:
        HTTPException: 404 if not found, 410 if deleted
    """
    # Log validation attempt
    logger.info(
        "validating_job_existence",
        job_id=job_id,
        organization_id=organization_id,
        **(logger_context or {})
    )

    try:
        job_obj = db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == organization_id
        ).first()

        # Check if result exists
        if not job_obj:
            logger.error(
                "job_not_found_validation_failed",
                job_id=job_id,
                organization_id=organization_id,
                **(logger_context or {})
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found or does not belong to organization"
            )

        job = model_to_dict(job_obj)

        # Check if job is in deleted/inactive state
        if job_obj.status == "deleted":
            logger.error(
                "job_deleted_validation_failed",
                job_id=job_id,
                job_name=job_obj.name,
                **(logger_context or {})
            )
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=f"Job {job_id} has been deleted"
            )

        logger.info(
            "job_validation_successful",
            job_id=job_id,
            job_name=job_obj.name,
            job_enabled=job_obj.enabled,
        )

        return job

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "job_validation_error",
            job_id=job_id,
            error=str(e),
            **(logger_context or {})
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate job: {str(e)}"
        )


# Pydantic schemas
class ParticipantResponse(BaseModel):
    """Participant in an execution"""
    id: str
    user_id: str
    user_name: str | None
    user_email: str | None
    user_avatar: str | None
    role: str
    joined_at: str
    last_active_at: str


class ExecutionResponse(BaseModel):
    id: str
    organization_id: str
    execution_type: str
    entity_id: str
    entity_name: str | None
    prompt: str
    system_prompt: str | None
    status: str
    response: str | None
    error_message: str | None
    usage: dict
    execution_metadata: dict
    runner_name: str | None
    user_id: str | None
    user_name: str | None
    user_email: str | None
    user_avatar: str | None
    created_at: str
    started_at: str | None
    completed_at: str | None
    updated_at: str
    participants: List[ParticipantResponse] = Field(default_factory=list)


# Worker-specific endpoints for job execution tracking


class CreateExecutionRecordRequest(BaseModel):
    """Request model for creating execution records from workers"""
    execution_id: str
    job_id: Optional[str] = None
    organization_id: str
    entity_type: str  # "agent" or "team"
    entity_id: Optional[str] = None
    prompt: str
    trigger_type: str  # "cron", "webhook", "manual"
    trigger_metadata: dict


class UpdateJobExecutionStatusRequest(BaseModel):
    """Request model for updating job execution status"""
    status: str
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_execution_record(
    request_data: CreateExecutionRecordRequest,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Create execution and job_executions records for scheduled jobs.

    This endpoint is used by workers to create execution records via HTTP
    instead of directly accessing the database.
    """
    try:
        from croniter import croniter

        now = datetime.now(timezone.utc)

        # Enhanced logging for debugging stale job_id sources
        logger.info(
            "execution_request_received",
            execution_id=request_data.execution_id,
            job_id=request_data.job_id,
            trigger_type=request_data.trigger_type,
            organization_id=request_data.organization_id,
            endpoint=request.url.path,
            source_headers={
                "temporal_workflow": request.headers.get("X-Temporal-Workflow-Id"),
                "temporal_run": request.headers.get("X-Temporal-Run-Id"),
            },
        )

        # Get entity name for display using SQLAlchemy
        entity_name = None
        runner_name = None

        if request_data.entity_id and request_data.entity_type:
            try:
                if request_data.entity_type == "agent":
                    entity = db.query(Agent).filter(Agent.id == request_data.entity_id).first()
                elif request_data.entity_type == "team":
                    entity = db.query(Team).filter(Team.id == request_data.entity_id).first()
                else:
                    entity = None
                if entity:
                    entity_name = entity.name
                    runner_name = getattr(entity, 'runner_name', None)
            except Exception as e:
                logger.warning(
                    "failed_to_get_entity_name",
                    entity_type=request_data.entity_type,
                    entity_id=request_data.entity_id,
                    error=str(e)
                )

        # If runner_name is still None, try to get it from the job's worker_queue_name
        if runner_name is None and request_data.job_id:
            try:
                job = db.query(Job).filter(Job.id == request_data.job_id).first()
                if job and job.worker_queue_name:
                    worker_queue_name = job.worker_queue_name
                    # Extract runner_name from worker_queue_name (format: "org_id.runner_name")
                    runner_name = worker_queue_name.split(".")[-1] if "." in worker_queue_name else worker_queue_name
                    logger.info(
                        "extracted_runner_name_from_job",
                        job_id=request_data.job_id,
                        worker_queue_name=worker_queue_name,
                        runner_name=runner_name
                    )
            except Exception as e:
                logger.warning(
                    "failed_to_get_runner_name_from_job",
                    job_id=request_data.job_id,
                    error=str(e)
                )

        # If runner_name is still None, use a default value
        # This can happen for jobs with AUTO/ENVIRONMENT executor types
        if runner_name is None:
            runner_name = "auto"
            logger.info(
                "using_default_runner_name",
                execution_id=request_data.execution_id,
                job_id=request_data.job_id,
                runner_name=runner_name
            )

        # Map trigger_type to trigger_source
        trigger_source_map = {
            "manual": "job_manual",
            "cron": "job_cron",
            "webhook": "job_webhook",
        }
        trigger_source = trigger_source_map.get(request_data.trigger_type, "job_cron")

        # Determine execution_type
        execution_type_value = request_data.entity_type.upper() if request_data.entity_type else "AGENT"

        # Create execution record using SQLAlchemy
        execution = Execution(
            id=uuid_module.UUID(request_data.execution_id),
            organization_id=request_data.organization_id,
            execution_type=execution_type_value,
            entity_id=uuid_module.UUID(request_data.entity_id) if request_data.entity_id else None,
            entity_name=entity_name,
            runner_name=runner_name,
            trigger_source=trigger_source,
            trigger_metadata={
                "job_id": request_data.job_id,
                "job_name": request_data.trigger_metadata.get("job_name"),
                "trigger_type": request_data.trigger_type,
                **request_data.trigger_metadata,
            },
            user_id=request_data.trigger_metadata.get("user_id"),
            user_email=request_data.trigger_metadata.get("user_email"),
            user_name=request_data.trigger_metadata.get("user_name"),
            user_avatar=request_data.trigger_metadata.get("user_avatar"),
            status="pending",
            prompt=request_data.prompt,
            created_at=now,
            updated_at=now,
            execution_metadata={
                "job_id": request_data.job_id,
                "job_name": request_data.trigger_metadata.get("job_name"),
                "trigger_type": request_data.trigger_type,
                "scheduled_execution": True,
                **request_data.trigger_metadata,
            },
        )
        db.add(execution)
        db.commit()

        logger.info(
            "created_execution_record",
            execution_id=request_data.execution_id,
            job_id=request_data.job_id,
        )

        # Publish job_started event to Redis for real-time UI updates
        try:
            redis_client = get_redis_client()
            if redis_client:
                event_data = {
                    "event_type": "run_started",
                    "data": {
                        "job_id": request_data.job_id,
                        "execution_id": request_data.execution_id,
                        "status": "pending",
                        "trigger_type": request_data.trigger_type,
                        "message": f"Job execution started",
                        "entity_type": request_data.entity_type,
                        "entity_id": request_data.entity_id,
                    },
                    "timestamp": now,
                    "execution_id": request_data.execution_id,
                }

                # Push to Redis list
                redis_key = f"execution:{request_data.execution_id}:events"
                await redis_client.lpush(redis_key, json.dumps(event_data))
                await redis_client.ltrim(redis_key, 0, 999)
                await redis_client.expire(redis_key, 3600)

                # Publish to pub/sub for real-time streaming
                pubsub_channel = f"execution:{request_data.execution_id}:stream"
                await redis_client.publish(pubsub_channel, json.dumps(event_data))

                logger.info(
                    "job_started_event_published",
                    execution_id=request_data.execution_id[:8],
                    job_id=request_data.job_id[:8] if request_data.job_id else None,
                )
        except Exception as event_error:
            # Don't fail the request if event publishing fails
            logger.warning(
                "failed_to_publish_job_started_event",
                execution_id=request_data.execution_id,
                error=str(event_error),
            )

        # Create job_executions junction record if job_id provided
        if request_data.job_id:
            # VALIDATION: Ensure job exists and belongs to organization
            job = await validate_job_exists(
                db=db,
                job_id=request_data.job_id,
                organization_id=request_data.organization_id,
                logger_context={
                    "execution_id": request_data.execution_id,
                    "trigger_type": request_data.trigger_type,
                    "source": "create_execution_record",
                    "trigger_metadata": request_data.trigger_metadata,
                }
            )

            logger.info(
                "creating_job_execution_junction",
                job_id=request_data.job_id,
                job_name=job.get("name"),
                execution_id=request_data.execution_id,
                organization_id=request_data.organization_id,
                trigger_type=request_data.trigger_type,
            )

            try:
                job_execution = JobExecution(
                    id=str(uuid_module.uuid4()),
                    job_id=request_data.job_id,
                    execution_id=uuid_module.UUID(request_data.execution_id),
                    organization_id=request_data.organization_id,
                    trigger_type=request_data.trigger_type,
                    trigger_metadata=request_data.trigger_metadata,
                    execution_status="pending",
                    created_at=now,
                )
                db.add(job_execution)
                db.commit()
                logger.info(
                    "job_execution_junction_created",
                    job_id=request_data.job_id,
                    execution_id=request_data.execution_id,
                )
            except Exception as insert_error:
                db.rollback()
                logger.error(
                    "job_execution_junction_insert_failed",
                    job_id=request_data.job_id,
                    execution_id=request_data.execution_id,
                    error=str(insert_error),
                    error_type=type(insert_error).__name__,
                )
                # Don't raise - junction record is supplementary
                # Execution record already created successfully

            # Update job's last_execution_id and increment total_executions
            try:
                # Get job details to calculate next execution using SQLAlchemy
                job_obj = db.query(Job).filter(Job.id == request_data.job_id).first()

                if job_obj:
                    job_obj.last_execution_id = uuid_module.UUID(request_data.execution_id)
                    job_obj.last_execution_at = now
                    job_obj.total_executions = (job_obj.total_executions or 0) + 1

                    # Calculate next_execution_at for cron jobs
                    if job_obj.trigger_type == "cron" and job_obj.cron_schedule:
                        cron_iter = croniter(job_obj.cron_schedule, datetime.now(timezone.utc))
                        next_execution = cron_iter.get_next(datetime)
                        job_obj.next_execution_at = next_execution

                        logger.info(
                            "calculated_next_execution_time",
                            job_id=request_data.job_id,
                            next_execution_at=next_execution.isoformat(),
                        )

                    db.commit()
                    logger.info(
                        "updated_job_execution_counts",
                        job_id=request_data.job_id,
                        execution_id=request_data.execution_id,
                    )
                else:
                    logger.warning(
                        "job_update_failed_wrong_organization",
                        job_id=request_data.job_id,
                        organization_id=request_data.organization_id,
                    )
            except Exception as e:
                db.rollback()
                # Just log and continue - this is not critical
                logger.warning(
                    "failed_to_update_job_counts",
                    job_id=request_data.job_id,
                    error=str(e),
                )

        return {
            "execution_id": request_data.execution_id,
            "status": "created",
            "created_at": now.isoformat(),
        }

    except Exception as e:
        logger.error(
            "failed_to_create_job_execution_records",
            execution_id=request_data.execution_id,
            job_id=request_data.job_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create execution records: {str(e)}"
        )


@router.get("", response_model=List[ExecutionResponse])
async def list_executions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    status_filter: str | None = None,
    execution_type: str | None = None,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """List all executions for the organization with optional filtering"""
    try:
        # Build SQLAlchemy query with optional participants join
        query = db.query(Execution).options(
            joinedload(Execution.participants)
        ).filter(Execution.organization_id == organization["id"])

        if status_filter:
            query = query.filter(Execution.status == status_filter.lower())
        if execution_type:
            query = query.filter(Execution.execution_type == execution_type.upper())

        results = query.order_by(desc(Execution.created_at)).offset(skip).limit(limit).all()

        if not results:
            logger.info("no_executions_found", org_id=organization["id"])
            return []

        executions = []
        for execution in results:
            try:
                # Parse participants from SQLAlchemy relationship
                participants = []
                if hasattr(execution, 'participants') and execution.participants:
                    for p in execution.participants:
                        try:
                            participants.append(ParticipantResponse(
                                id=str(p.id),
                                user_id=p.user_id,
                                user_name=p.user_name,
                                user_email=p.user_email,
                                user_avatar=p.user_avatar,
                                role=p.role,
                                joined_at=p.joined_at.isoformat() if p.joined_at else "",
                                last_active_at=p.last_active_at.isoformat() if p.last_active_at else "",
                            ))
                        except Exception as participant_error:
                            logger.warning("failed_to_parse_participant", error=str(participant_error), execution_id=str(execution.id))
                            # Skip invalid participant, continue with others

                # Sanitize JSONB fields
                usage_data = sanitize_jsonb_field(
                    execution.usage,
                    field_name=f"usage[{execution.id}]"
                )
                metadata_data = sanitize_jsonb_field(
                    execution.execution_metadata,
                    field_name=f"execution_metadata[{execution.id}]"
                )

                executions.append(
                    ExecutionResponse(
                        id=str(execution.id),
                        organization_id=execution.organization_id,
                        execution_type=execution.execution_type,
                        entity_id=str(execution.entity_id) if execution.entity_id else "",
                        entity_name=execution.entity_name,
                        prompt=execution.prompt or "",
                        system_prompt=execution.system_prompt,
                        status=execution.status,
                        response=execution.response,
                        error_message=execution.error_message,
                        usage=usage_data,
                        execution_metadata=metadata_data,
                        runner_name=execution.runner_name,
                        user_id=execution.user_id,
                        user_name=execution.user_name,
                        user_email=execution.user_email,
                        user_avatar=execution.user_avatar,
                        created_at=execution.created_at.isoformat() if execution.created_at else "",
                        started_at=execution.started_at.isoformat() if execution.started_at else None,
                        completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
                        updated_at=execution.updated_at.isoformat() if execution.updated_at else "",
                        participants=participants,
                    )
                )
            except Exception as execution_error:
                logger.error("failed_to_parse_execution", error=str(execution_error), execution_id=str(execution.id))
                # Skip invalid execution, continue with others

        logger.info(
            "executions_listed_successfully",
            count=len(executions),
            org_id=organization["id"],
        )

        return executions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "executions_list_failed",
            error=str(e),
            error_type=type(e).__name__,
            org_id=organization["id"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list executions: {str(e)}"
        )


class CreateJobExecutionRequest(BaseModel):
    """Request to create a job execution record"""
    execution_id: str
    job_id: str | None = None
    entity_type: str  # "agent" or "team"
    entity_id: str | None = None
    prompt: str
    trigger_type: str  # "cron", "webhook", "manual"
    trigger_metadata: dict = Field(default_factory=dict)


@router.post("/job-executions", status_code=status.HTTP_201_CREATED)
async def create_job_execution(
    request_data: CreateJobExecutionRequest,
    http_request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Create execution and job_executions records for a scheduled job.

    This endpoint is used by workers to create execution records when jobs are triggered.
    It creates both:
    1. An execution record in the executions table
    2. A job_executions junction record linking the job to the execution

    Available at both /job-executions and /create for backwards compatibility.
    """
    try:
        now = datetime.now(timezone.utc)

        # Enhanced logging for debugging stale job_id sources
        logger.info(
            "execution_request_received",
            execution_id=request_data.execution_id,
            job_id=request_data.job_id,
            trigger_type=request_data.trigger_type,
            organization_id=organization["id"],
            endpoint=http_request.url.path,
            source_headers={
                "temporal_workflow": http_request.headers.get("X-Temporal-Workflow-Id"),
                "temporal_run": http_request.headers.get("X-Temporal-Run-Id"),
            },
        )

        # Fetch entity details (name and runner_name) using SQLAlchemy
        entity_name = None
        runner_name = None

        if request_data.entity_id and request_data.entity_type:
            try:
                if request_data.entity_type == "agent":
                    entity = db.query(Agent).filter(Agent.id == request_data.entity_id).first()
                elif request_data.entity_type == "team":
                    entity = db.query(Team).filter(Team.id == request_data.entity_id).first()
                else:
                    entity = None
                if entity:
                    entity_name = entity.name
                    runner_name = getattr(entity, 'runner_name', None)
            except Exception as e:
                logger.warning(
                    "failed_to_fetch_entity_details",
                    entity_type=request_data.entity_type,
                    entity_id=request_data.entity_id,
                    error=str(e)
                )

        # Fallback: Get runner_name from active worker_queues if not found
        if not runner_name:
            try:
                queue = db.query(WorkerQueue).filter(
                    WorkerQueue.organization_id == organization["id"],
                    WorkerQueue.status == "active",
                    WorkerQueue.ephemeral == False,  # Exclude ephemeral queues
                    ~WorkerQueue.name.startswith('local-exec')  # Exclude local-exec queues
                ).first()
                if queue:
                    worker_queue_name = queue.name
                    # Extract runner_name from queue name (format: "org_id.runner_name")
                    runner_name = worker_queue_name.split(".")[-1] if "." in worker_queue_name else worker_queue_name
            except Exception as e:
                logger.warning("failed_to_fetch_runner_name_from_worker_queues", error=str(e))

        # Final fallback for runner_name
        if not runner_name:
            runner_name = "default"

        # Map trigger_type to trigger_source
        trigger_source_map = {
            "manual": "job_manual",
            "cron": "job_cron",
            "webhook": "job_webhook",
        }
        trigger_source = trigger_source_map.get(request_data.trigger_type, "job_cron")

        # Check if execution already exists (might have been created as placeholder by jobs router)
        existing = db.query(Execution).filter(
            Execution.id == request_data.execution_id,
            Execution.organization_id == organization["id"]
        ).first()

        if existing:
            # Execution exists, update it with complete information
            logger.info(
                "updating_existing_execution_record",
                execution_id=request_data.execution_id,
            )
            existing.execution_type = request_data.entity_type.upper()
            existing.entity_id = uuid_module.UUID(request_data.entity_id) if request_data.entity_id else None
            existing.entity_name = entity_name
            existing.runner_name = runner_name
            existing.trigger_source = trigger_source
            existing.trigger_metadata = {
                "job_id": request_data.job_id,
                "job_name": request_data.trigger_metadata.get("job_name"),
                "trigger_type": request_data.trigger_type,
                **request_data.trigger_metadata,
            }
            existing.user_id = request_data.trigger_metadata.get("user_id")
            existing.user_email = request_data.trigger_metadata.get("triggered_by") or request_data.trigger_metadata.get("user_email")
            existing.user_name = request_data.trigger_metadata.get("user_name")
            existing.user_avatar = request_data.trigger_metadata.get("user_avatar")
            existing.prompt = request_data.prompt
            existing.status = "pending"
            existing.usage = {}
            existing.execution_metadata = {
                "job_id": request_data.job_id,
                "job_name": request_data.trigger_metadata.get("job_name"),
                "trigger_type": request_data.trigger_type,
                "scheduled_execution": True,
                **request_data.trigger_metadata,
            }
            existing.updated_at = now
            db.commit()
        else:
            # Execution doesn't exist, create it
            logger.info(
                "creating_new_execution_record",
                execution_id=request_data.execution_id,
            )
            execution = Execution(
                id=uuid_module.UUID(request_data.execution_id),
                organization_id=organization["id"],
                execution_type=request_data.entity_type.upper(),
                entity_id=uuid_module.UUID(request_data.entity_id) if request_data.entity_id else None,
                entity_name=entity_name,
                runner_name=runner_name,
                trigger_source=trigger_source,
                trigger_metadata={
                    "job_id": request_data.job_id,
                    "job_name": request_data.trigger_metadata.get("job_name"),
                    "trigger_type": request_data.trigger_type,
                    **request_data.trigger_metadata,
                },
                user_id=request_data.trigger_metadata.get("user_id"),
                user_email=request_data.trigger_metadata.get("triggered_by") or request_data.trigger_metadata.get("user_email"),
                user_name=request_data.trigger_metadata.get("user_name"),
                user_avatar=request_data.trigger_metadata.get("user_avatar"),
                prompt=request_data.prompt,
                status="pending",
                usage={},
                execution_metadata={
                    "job_id": request_data.job_id,
                    "job_name": request_data.trigger_metadata.get("job_name"),
                    "trigger_type": request_data.trigger_type,
                    "scheduled_execution": True,
                    **request_data.trigger_metadata,
                },
                created_at=now,
                updated_at=now,
            )
            db.add(execution)
            db.commit()

        # Create job_executions junction record if job_id is provided
        if request_data.job_id:
            # VALIDATION: Ensure job exists and belongs to organization
            job = await validate_job_exists(
                db=db,
                job_id=request_data.job_id,
                organization_id=organization["id"],
                logger_context={
                    "execution_id": request_data.execution_id,
                    "trigger_type": request_data.trigger_type,
                    "source": "create_job_execution",
                }
            )

            logger.info(
                "checking_job_execution_junction",
                job_id=request_data.job_id,
                job_name=job.get("name"),
                execution_id=request_data.execution_id,
            )

            # Check if junction record already exists (with org_id for security)
            existing_junction = db.query(JobExecution).filter(
                JobExecution.job_id == request_data.job_id,
                JobExecution.execution_id == request_data.execution_id,
                JobExecution.organization_id == organization["id"]
            ).first()

            if not existing_junction:
                # Only create if it doesn't exist
                try:
                    job_execution = JobExecution(
                        id=str(uuid_module.uuid4()),
                        job_id=request_data.job_id,
                        execution_id=uuid_module.UUID(request_data.execution_id),
                        organization_id=organization["id"],
                        trigger_type=request_data.trigger_type,
                        trigger_metadata=request_data.trigger_metadata,
                        execution_status="pending",
                        created_at=now,
                    )
                    db.add(job_execution)
                    db.commit()
                    logger.info(
                        "job_execution_junction_created",
                        job_id=request_data.job_id,
                        execution_id=request_data.execution_id,
                    )
                except Exception as insert_error:
                    db.rollback()
                    logger.error(
                        "job_execution_junction_insert_failed",
                        job_id=request_data.job_id,
                        execution_id=request_data.execution_id,
                        error=str(insert_error),
                    )
                    # Continue - don't fail the whole request
            else:
                logger.info(
                    "job_execution_junction_already_exists",
                    job_id=request_data.job_id,
                    execution_id=request_data.execution_id,
                )

        logger.info(
            "created_job_execution_records",
            execution_id=request_data.execution_id,
            job_id=request_data.job_id,
            trigger_type=request_data.trigger_type,
        )

        return {
            "execution_id": request_data.execution_id,
            "status": "created",
            "message": "Job execution records created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "failed_to_create_job_execution",
            error=str(e),
            execution_id=request_data.execution_id,
            job_id=request_data.job_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job execution: {str(e)}"
        )


class UpdateJobExecutionStatusRequest(BaseModel):
    """Request to update job execution status"""
    status: str
    duration_ms: int | None = None
    error_message: str | None = None


# ============================================================================
# BATCH ENDPOINTS - Must be defined BEFORE any /{execution_id}/... routes
# to ensure FastAPI matches them correctly (routes are matched in order)
# ============================================================================

@router.post("/batch/terminate", response_model=BatchTerminateResponse)
async def batch_terminate_executions(
    request: Request,
    batch_request: BatchTerminateRequest,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Terminate multiple executions in a single request.

    This endpoint allows terminating multiple running executions at once.
    Each execution is processed independently, so some may succeed while others fail.

    Args:
        request: FastAPI request object (contains kubiya_token in state)
        batch_request: Request body with list of execution IDs and termination reason
        organization: Current organization from auth
        db: Database session

    Returns:
        BatchTerminateResponse with results for each execution

    Note:
        - Maximum 100 executions per request
        - Each execution is terminated independently
        - Failed terminations don't affect other executions in the batch
    """
    org_id = organization["id"]

    logger.info(
        "batch_terminate_executions_start",
        org_id=org_id,
        execution_count=len(batch_request.execution_ids),
        reason=batch_request.reason
    )

    # Get kubiya token from request state for Temporal credentials
    token = getattr(request.state, "kubiya_token", None)
    if not token:
        logger.error("kubiya_token_missing", org_id=org_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication token not available"
        )

    workflow_service = WorkflowOperationsService(db)
    results: List[BatchTerminateResult] = []
    succeeded = 0
    failed = 0

    for exec_id in batch_request.execution_ids:
        try:
            # Find execution
            execution = db.query(Execution).filter(
                ((Execution.id == exec_id) | (Execution.temporal_workflow_id == exec_id)),
                Execution.organization_id == org_id
            ).first()

            if not execution:
                results.append(BatchTerminateResult(
                    execution_id=exec_id,
                    success=False,
                    error="Execution not found"
                ))
                failed += 1
                continue

            # Derive workflow ID
            workflow_id = execution.temporal_workflow_id
            if not workflow_id:
                exec_type = execution.execution_type.lower() if execution.execution_type else "agent"
                if exec_type == "team":
                    workflow_id = f"team-execution-{execution.id}"
                else:
                    workflow_id = f"agent-execution-{execution.id}"

            # Terminate the workflow
            result = await workflow_service.terminate_workflow(
                workflow_id=workflow_id,
                organization_id=org_id,
                token=token,
                reason=batch_request.reason
            )

            results.append(BatchTerminateResult(
                execution_id=exec_id,
                success=True,
                workflow_id=result.workflow_id,
                terminated_at=result.terminated_at
            ))
            succeeded += 1

        except ValueError as e:
            error_msg = str(e)
            results.append(BatchTerminateResult(
                execution_id=exec_id,
                success=False,
                error=error_msg
            ))
            failed += 1

        except Exception as e:
            logger.error(
                "batch_terminate_execution_error",
                error=str(e),
                execution_id=exec_id,
                org_id=org_id
            )
            results.append(BatchTerminateResult(
                execution_id=exec_id,
                success=False,
                error=f"Unexpected error: {str(e)}"
            ))
            failed += 1

    logger.info(
        "batch_terminate_executions_complete",
        org_id=org_id,
        total_requested=len(batch_request.execution_ids),
        succeeded=succeeded,
        failed=failed
    )

    return BatchTerminateResponse(
        total_requested=len(batch_request.execution_ids),
        total_succeeded=succeeded,
        total_failed=failed,
        results=results
    )


# ============================================================================
# PARAMETERIZED ROUTES - /{execution_id}/... routes below
# ============================================================================

@router.post("/{execution_id}/job/{job_id}/status", status_code=status.HTTP_202_ACCEPTED)
async def update_job_execution_status(
    execution_id: str,
    job_id: str,
    request: UpdateJobExecutionStatusRequest,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Update job execution status after completion.

    This endpoint is called by workers to update the job_executions junction record
    when a job execution completes or fails.
    """
    try:
        now = datetime.now(timezone.utc)

        # Update job_executions record using SQLAlchemy
        job_execution = db.query(JobExecution).filter(
            JobExecution.job_id == job_id,
            JobExecution.execution_id == execution_id,
            JobExecution.organization_id == organization["id"]
        ).first()

        if not job_execution:
            logger.warning(
                "job_execution_not_found_for_status_update",
                job_id=job_id,
                execution_id=execution_id,
            )
            # Don't fail - return success anyway
            return {
                "job_id": job_id,
                "execution_id": execution_id,
                "status": "not_found"
            }

        job_execution.execution_status = request.status
        job_execution.updated_at = now

        if request.duration_ms is not None:
            job_execution.execution_duration_ms = request.duration_ms

        db.commit()

        # Update job statistics based on status using SQLAlchemy
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == organization["id"]
        ).first()

        if job:
            if request.status == "completed":
                job.successful_executions = (job.successful_executions or 0) + 1
            elif request.status == "failed":
                job.failed_executions = (job.failed_executions or 0) + 1
            db.commit()

        logger.info(
            "updated_job_execution_status",
            job_id=job_id,
            execution_id=execution_id,
            status=request.status,
        )

        return {
            "job_id": job_id,
            "execution_id": execution_id,
            "status": "updated"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "failed_to_update_job_execution_status",
            error=str(e),
            job_id=job_id,
            execution_id=execution_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update job execution status: {str(e)}"
        )


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Get a specific execution by ID"""
    try:
        execution = db.query(Execution).filter(
            Execution.id == uuid_module.UUID(execution_id),
            Execution.organization_id == organization["id"]
        ).first()

        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")

        # Sanitize JSONB fields
        usage_data = sanitize_jsonb_field(
            execution.usage,
            field_name=f"usage[{execution_id}]"
        )
        metadata_data = sanitize_jsonb_field(
            execution.execution_metadata,
            field_name=f"execution_metadata[{execution_id}]"
        )

        return ExecutionResponse(
            id=str(execution.id),
            organization_id=execution.organization_id,
            execution_type=execution.execution_type,
            entity_id=str(execution.entity_id),
            entity_name=execution.entity_name,
            prompt=execution.prompt or "",
            system_prompt=execution.system_prompt,
            status=execution.status,
            response=execution.response,
            error_message=execution.error_message,
            usage=usage_data,
            execution_metadata=metadata_data,
            runner_name=execution.runner_name,
            user_id=execution.user_id,
            user_name=execution.user_name,
            user_email=execution.user_email,
            user_avatar=execution.user_avatar,
            created_at=execution.created_at.isoformat() if execution.created_at else None,
            started_at=execution.started_at.isoformat() if execution.started_at else None,
            completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
            updated_at=execution.updated_at.isoformat() if execution.updated_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("execution_get_failed", error=str(e), execution_id=execution_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution: {str(e)}"
        )


@router.delete("/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_execution(
    execution_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Delete an execution"""
    try:
        execution = db.query(Execution).filter(
            Execution.id == uuid_module.UUID(execution_id),
            Execution.organization_id == organization["id"]
        ).first()

        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")

        db.delete(execution)
        db.commit()

        logger.info("execution_deleted", execution_id=execution_id, org_id=organization["id"])

        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("execution_delete_failed", error=str(e), execution_id=execution_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete execution: {str(e)}"
        )


class ExecutionUpdate(BaseModel):
    """Update execution fields - used by workers to update execution status"""
    status: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    response: str | None = None
    error_message: str | None = None
    usage: dict | None = None
    execution_metadata: dict | None = None


@router.patch("/{execution_id}", response_model=ExecutionResponse)
async def update_execution(
    execution_id: str,
    execution_update: ExecutionUpdate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Update execution status and results.

    This endpoint is primarily used by workers to update execution status,
    results, usage metrics, and metadata during execution.
    """
    try:
        execution = db.query(Execution).filter(
            Execution.id == uuid_module.UUID(execution_id),
            Execution.organization_id == organization["id"]
        ).first()

        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")

        # Track fields that were updated
        updated_fields = []

        if execution_update.status is not None:
            execution.status = execution_update.status.lower()  # Normalize to lowercase
            updated_fields.append("status")

        if execution_update.started_at is not None:
            execution.started_at = datetime.fromisoformat(execution_update.started_at.replace('Z', '+00:00'))
            updated_fields.append("started_at")

        if execution_update.completed_at is not None:
            execution.completed_at = datetime.fromisoformat(execution_update.completed_at.replace('Z', '+00:00'))
            updated_fields.append("completed_at")

        if execution_update.response is not None:
            execution.response = execution_update.response
            updated_fields.append("response")

        if execution_update.error_message is not None:
            execution.error_message = execution_update.error_message
            updated_fields.append("error_message")

        if execution_update.usage is not None:
            execution.usage = execution_update.usage
            updated_fields.append("usage")

        if execution_update.execution_metadata is not None:
            execution.execution_metadata = execution_update.execution_metadata
            updated_fields.append("execution_metadata")

        # updated_at will be automatically set by onupdate
        updated_fields.append("updated_at")

        db.commit()
        db.refresh(execution)

        logger.info(
            "execution_updated",
            execution_id=execution_id,
            org_id=organization["id"],
            fields_updated=updated_fields,
        )

        # Sanitize JSONB fields before returning
        usage_data = sanitize_jsonb_field(
            execution.usage,
            field_name=f"usage[{execution_id}]"
        )
        metadata_data = sanitize_jsonb_field(
            execution.execution_metadata,
            field_name=f"execution_metadata[{execution_id}]"
        )

        return ExecutionResponse(
            id=str(execution.id),
            organization_id=execution.organization_id,
            execution_type=execution.execution_type,
            entity_id=str(execution.entity_id),
            entity_name=execution.entity_name,
            prompt=execution.prompt or "",
            system_prompt=execution.system_prompt,
            status=execution.status,
            response=execution.response,
            error_message=execution.error_message,
            usage=usage_data,
            execution_metadata=metadata_data,
            runner_name=execution.runner_name,
            user_id=execution.user_id,
            user_name=execution.user_name,
            user_email=execution.user_email,
            user_avatar=execution.user_avatar,
            created_at=execution.created_at.isoformat() if execution.created_at else None,
            started_at=execution.started_at.isoformat() if execution.started_at else None,
            completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
            updated_at=execution.updated_at.isoformat() if execution.updated_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("execution_update_failed", error=str(e), execution_id=execution_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update execution: {str(e)}"
        )


class SendMessageRequest(BaseModel):
    """Request to send a message to a running execution"""
    message: str
    role: str = "user"  # user, system, etc.


@router.post("/{execution_id}/message", status_code=status.HTTP_202_ACCEPTED)
async def send_message_to_execution(
    execution_id: str,
    request_body: SendMessageRequest,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Send a followup message to a running execution using Temporal signals.

    This sends a signal to the Temporal workflow, adding the message to the conversation.
    The workflow will process the message and respond accordingly.
    """
    try:
        # Get Temporal client
        temporal_client = await get_temporal_client()

        # Verify the execution belongs to this organization and get execution type
        execution = db.query(Execution).filter(
            Execution.id == uuid_module.UUID(execution_id),
            Execution.organization_id == organization["id"]
        ).first()

        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")

        # Construct workflow ID based on execution type
        execution_type = execution.execution_type or "AGENT"
        if execution_type == "TEAM":
            workflow_id = f"team-execution-{execution_id}"
        else:
            workflow_id = f"agent-execution-{execution_id}"

        workflow_handle = temporal_client.get_workflow_handle(workflow_id)

        # Import ChatMessage from workflow
        from control_plane_api.app.workflows.agent_execution import ChatMessage
        from datetime import datetime, timezone
        import time

        # Generate message_id FIRST so we can use it in both ChatMessage and Redis event
        message_id = f"{execution_id}_{int(time.time() * 1000000)}"

        # Create the message with user attribution from JWT token AND message_id
        message = ChatMessage(
            role=request_body.role,
            content=request_body.message,
            timestamp=datetime.now(timezone.utc).isoformat(),
            message_id=message_id,  # CRITICAL: Pass message_id to workflow for consistent deduplication
            user_id=organization.get("user_id"),
            user_name=organization.get("user_name"),
            user_email=organization.get("user_email"),
            user_avatar=organization.get("user_avatar"),  # Now available from JWT via auth middleware
        )

        # CRITICAL: Publish to Redis for immediate SSE streaming
        # The workflow will save to database - we just need instant UI update
        redis_client = get_redis_client()
        if redis_client:
            try:
                event_data = {
                    "event_type": "message",
                    "data": {
                        "role": message.role,
                        "content": message.content,
                        "timestamp": message.timestamp,
                        "message_id": message_id,
                        "user_id": message.user_id,
                        "user_name": message.user_name,
                        "user_email": message.user_email,
                        "user_avatar": message.user_avatar,
                    },
                    "timestamp": message.timestamp,
                    "execution_id": execution_id,
                }

                redis_key = f"execution:{execution_id}:events"
                await redis_client.lpush(redis_key, json.dumps(event_data))
                await redis_client.ltrim(redis_key, 0, 999)
                await redis_client.expire(redis_key, 3600)

                logger.info(
                    "user_message_published_to_redis",
                    execution_id=execution_id,
                    message_id=message_id,
                )
            except Exception as redis_error:
                logger.warning(
                    "failed_to_publish_user_message_to_redis",
                    error=str(redis_error),
                    execution_id=execution_id,
                )
                # Continue - not critical

        # IMMEDIATELY update status to "queued" before sending signal
        # This shows user that message was received and is waiting for worker to pick it up
        try:
            execution.status = "queued"
            execution.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(
                "execution_status_set_to_queued",
                execution_id=execution_id,
            )
        except Exception as db_error:
            db.rollback()
            logger.warning(
                "failed_to_set_queued_status",
                error=str(db_error),
                execution_id=execution_id,
            )
            # Continue - non-critical

        # Push "queued" status event to Redis for immediate UI update
        if redis_client:
            try:
                status_event = {
                    "event_type": "status",
                    "status": "queued",
                    "execution_id": execution_id,
                    "source": "message_endpoint",
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                }
                redis_key = f"execution:{execution_id}:events"
                await redis_client.lpush(redis_key, json.dumps(status_event))
                logger.info(
                    "queued_status_pushed_after_message",
                    execution_id=execution_id,
                )
            except Exception as status_push_error:
                logger.warning(
                    "failed_to_push_queued_status",
                    error=str(status_push_error),
                    execution_id=execution_id,
                )
                # Non-critical - worker will push "running" when it starts

        # Send signal to workflow - worker will change status to "running" when it picks this up
        await workflow_handle.signal(AgentExecutionWorkflow.add_message, message)

        # Add user as participant if not already added (multiplayer support)
        user_id = organization.get("user_id")
        if user_id:
            try:
                # Check if participant already exists
                existing = db.query(ExecutionParticipant).filter(
                    ExecutionParticipant.execution_id == uuid_module.UUID(execution_id),
                    ExecutionParticipant.user_id == user_id
                ).first()

                if not existing:
                    # Add as new participant (collaborator role)
                    import uuid
                    new_participant = ExecutionParticipant(
                        id=uuid.uuid4(),
                        execution_id=uuid_module.UUID(execution_id),
                        organization_id=organization["id"],
                        user_id=user_id,
                        user_name=organization.get("user_name"),
                        user_email=organization.get("user_email"),
                        user_avatar=organization.get("user_avatar"),
                        role="collaborator",
                    )
                    db.add(new_participant)
                    db.commit()
                    logger.info(
                        "participant_added",
                        execution_id=execution_id,
                        user_id=user_id,
                    )
                else:
                    # Update last_active_at for existing participant
                    from datetime import timezone
                    existing.last_active_at = datetime.now(timezone.utc)
                    db.commit()
            except Exception as participant_error:
                db.rollback()
                logger.warning(
                    "failed_to_add_participant",
                    error=str(participant_error),
                    execution_id=execution_id,
                )
                # Don't fail the whole request if participant tracking fails

        logger.info(
            "message_sent_to_execution",
            execution_id=execution_id,
            org_id=organization["id"],
            role=request_body.role,
        )

        return {
            "success": True,
            "execution_id": execution_id,
            "message": "Message sent to workflow",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "send_message_failed",
            error=str(e),
            execution_id=execution_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@router.post("/{execution_id}/pause")
async def pause_execution(
    execution_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Pause an active execution by sending a signal to the Temporal workflow.

    This is triggered when the user clicks the PAUSE button in the UI.
    The workflow will stop processing but remain active and can be resumed.
    """
    try:
        logger.info(
            "pause_execution_requested",
            execution_id=execution_id,
            org_id=organization["id"]
        )

        # Get execution from database
        execution = db.query(Execution).filter(
            Execution.id == uuid_module.UUID(execution_id),
            Execution.organization_id == organization["id"]
        ).first()

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )

        current_status = execution.status

        # Check if execution can be paused
        if current_status not in ["running", "waiting_for_input"]:
            logger.warning(
                "pause_execution_invalid_status",
                execution_id=execution_id,
                status=current_status
            )
            return {
                "success": False,
                "error": f"Execution cannot be paused (status: {current_status})",
                "execution_id": execution_id,
                "status": current_status,
            }

        # Get Temporal client
        temporal_client = await get_temporal_client()

        # Determine workflow ID based on execution type
        execution_type = execution.execution_type or "AGENT"
        workflow_id = f"team-execution-{execution_id}" if execution_type == "TEAM" else f"agent-execution-{execution_id}"

        workflow_handle = temporal_client.get_workflow_handle(workflow_id)

        # Send pause signal to workflow
        await workflow_handle.signal(AgentExecutionWorkflow.pause_execution)

        # Update execution status to paused
        execution.status = "paused"
        db.commit()

        # Emit system message to Redis for UI display
        redis_client = get_redis_client()
        if redis_client:
            try:
                import time
                user_name = organization.get("user_name", "User")
                current_timestamp = datetime.now(timezone.utc).isoformat()
                message_id = f"{execution_id}_pause_{int(time.time() * 1000000)}"

                # Create message event - format matches what streaming endpoint expects
                pause_message_event = {
                    "event_type": "message",
                    "data": {
                        "role": "system",
                        "content": f"⏸️ Execution paused by {user_name}",
                        "timestamp": current_timestamp,
                        "message_id": message_id,
                    },
                    "timestamp": current_timestamp,
                    "execution_id": execution_id,
                }

                redis_key = f"execution:{execution_id}:events"
                await redis_client.lpush(redis_key, json.dumps(pause_message_event))
                await redis_client.ltrim(redis_key, 0, 999)
                await redis_client.expire(redis_key, 3600)

                # Also update status event
                status_event = {
                    "event_type": "status",
                    "data": {"status": "paused", "execution_id": execution_id},
                    "timestamp": current_timestamp,
                    "execution_id": execution_id,
                }
                await redis_client.lpush(redis_key, json.dumps(status_event))

                logger.debug("pause_event_published_to_redis", execution_id=execution_id)
            except Exception as redis_error:
                logger.warning("failed_to_publish_pause_event", error=str(redis_error), execution_id=execution_id)

        logger.info(
            "execution_paused_successfully",
            execution_id=execution_id,
            workflow_id=workflow_id
        )

        return {
            "success": True,
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "message": "Execution paused successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "pause_execution_error",
            execution_id=execution_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause execution: {str(e)}"
        )


@router.post("/{execution_id}/resume")
async def resume_execution(
    execution_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Resume a paused execution by sending a signal to the Temporal workflow.

    This is triggered when the user clicks the RESUME button in the UI.
    The workflow will continue processing from where it was paused.
    """
    try:
        logger.info(
            "resume_execution_requested",
            execution_id=execution_id,
            org_id=organization["id"]
        )

        # Get execution from database
        execution = db.query(Execution).filter(
            Execution.id == uuid_module.UUID(execution_id),
            Execution.organization_id == organization["id"]
        ).first()

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )

        current_status = execution.status

        # Check if execution is paused
        if current_status != "paused":
            logger.warning(
                "resume_execution_not_paused",
                execution_id=execution_id,
                status=current_status
            )
            return {
                "success": False,
                "error": f"Execution is not paused (status: {current_status})",
                "execution_id": execution_id,
                "status": current_status,
            }

        # Get Temporal client
        temporal_client = await get_temporal_client()

        # Determine workflow ID based on execution type
        execution_type = execution.execution_type or "AGENT"
        workflow_id = f"team-execution-{execution_id}" if execution_type == "TEAM" else f"agent-execution-{execution_id}"

        workflow_handle = temporal_client.get_workflow_handle(workflow_id)

        # Send resume signal to workflow
        await workflow_handle.signal(AgentExecutionWorkflow.resume_execution)

        # Update execution status back to running/waiting
        # The workflow will determine the correct status
        execution.status = "running"
        db.commit()

        # Emit system message to Redis for UI display
        redis_client = get_redis_client()
        if redis_client:
            try:
                import time
                user_name = organization.get("user_name", "User")
                current_timestamp = datetime.now(timezone.utc).isoformat()
                message_id = f"{execution_id}_resume_{int(time.time() * 1000000)}"

                # Create message event - format matches what streaming endpoint expects
                resume_message_event = {
                    "event_type": "message",
                    "data": {
                        "role": "system",
                        "content": f"▶️ Execution resumed by {user_name}",
                        "timestamp": current_timestamp,
                        "message_id": message_id,
                    },
                    "timestamp": current_timestamp,
                    "execution_id": execution_id,
                }

                redis_key = f"execution:{execution_id}:events"
                await redis_client.lpush(redis_key, json.dumps(resume_message_event))
                await redis_client.ltrim(redis_key, 0, 999)
                await redis_client.expire(redis_key, 3600)

                # Also update status event
                status_event = {
                    "event_type": "status",
                    "data": {"status": "running", "execution_id": execution_id},
                    "timestamp": current_timestamp,
                    "execution_id": execution_id,
                }
                await redis_client.lpush(redis_key, json.dumps(status_event))

                logger.debug("resume_event_published_to_redis", execution_id=execution_id)
            except Exception as redis_error:
                logger.warning("failed_to_publish_resume_event", error=str(redis_error), execution_id=execution_id)

        logger.info(
            "execution_resumed_successfully",
            execution_id=execution_id,
            workflow_id=workflow_id
        )

        return {
            "success": True,
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "message": "Execution resumed successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "resume_execution_error",
            execution_id=execution_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume execution: {str(e)}"
        )


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Cancel an active execution by calling Temporal's workflow cancellation.

    This is triggered when the user clicks the STOP button in the UI.
    It uses Temporal's built-in cancellation which is fast and returns immediately.
    """
    try:
        from temporalio.client import WorkflowHandle

        logger.info(
            "cancel_execution_requested",
            execution_id=execution_id,
            org_id=organization["id"]
        )

        # Get execution from database
        execution = db.query(Execution).filter(
            Execution.id == uuid_module.UUID(execution_id),
            Execution.organization_id == organization["id"]
        ).first()

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )

        current_status = execution.status

        # Check if execution is still running
        if current_status not in ["running", "waiting_for_input"]:
            logger.warning(
                "cancel_execution_not_running",
                execution_id=execution_id,
                status=current_status
            )
            return {
                "success": False,
                "error": f"Execution is not running (status: {current_status})",
                "execution_id": execution_id,
                "status": current_status,
            }

        # Get Temporal client
        temporal_client = await get_temporal_client()

        # Determine workflow ID based on execution type
        execution_type = execution.execution_type or "AGENT"
        workflow_id = f"team-execution-{execution_id}" if execution_type == "TEAM" else f"agent-execution-{execution_id}"

        workflow_handle: WorkflowHandle = temporal_client.get_workflow_handle(
            workflow_id=workflow_id
        )

        # Use Temporal's built-in workflow cancellation
        # This is fast and returns immediately
        try:
            # Send cancel signal to the workflow
            # This returns immediately - it doesn't wait for the workflow to finish
            await workflow_handle.cancel()

            # Update execution status to cancelled
            execution.status = "cancelled"
            execution.completed_at = datetime.now(timezone.utc)
            execution.error_message = "Cancelled by user"
            db.commit()

            # Emit system message to Redis for UI display
            redis_client = get_redis_client()
            if redis_client:
                try:
                    import time
                    user_name = organization.get("user_name", "User")
                    current_timestamp = datetime.now(timezone.utc).isoformat()
                    message_id = f"{execution_id}_cancel_{int(time.time() * 1000000)}"

                    # Create message event - format matches what streaming endpoint expects
                    cancel_message_event = {
                        "event_type": "message",
                        "data": {
                            "role": "system",
                            "content": f"🛑 Execution stopped by {user_name}",
                            "timestamp": current_timestamp,
                            "message_id": message_id,
                        },
                        "timestamp": current_timestamp,
                        "execution_id": execution_id,
                    }

                    redis_key = f"execution:{execution_id}:events"
                    await redis_client.lpush(redis_key, json.dumps(cancel_message_event))
                    await redis_client.ltrim(redis_key, 0, 999)
                    await redis_client.expire(redis_key, 3600)

                    # Also update status event
                    status_event = {
                        "event_type": "status",
                        "data": {"status": "cancelled", "execution_id": execution_id},
                        "timestamp": current_timestamp,
                        "execution_id": execution_id,
                    }
                    await redis_client.lpush(redis_key, json.dumps(status_event))

                    logger.debug("cancel_event_published_to_redis", execution_id=execution_id)
                except Exception as redis_error:
                    logger.warning("failed_to_publish_cancel_event", error=str(redis_error), execution_id=execution_id)

            logger.info(
                "execution_cancelled_successfully",
                execution_id=execution_id,
                workflow_id=workflow_id
            )

            return {
                "success": True,
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "message": "Execution cancelled successfully",
            }

        except Exception as cancel_error:
            logger.error(
                "cancel_workflow_error",
                execution_id=execution_id,
                error=str(cancel_error)
            )

            # Mark as cancelled in database anyway (user intent matters)
            execution.status = "cancelled"
            execution.completed_at = datetime.now(timezone.utc)
            execution.error_message = f"Cancelled: {str(cancel_error)}"
            db.commit()

            return {
                "success": True,  # User intent succeeded
                "execution_id": execution_id,
                "message": "Execution marked as cancelled",
                "warning": str(cancel_error),
            }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "cancel_execution_error",
            execution_id=execution_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel execution: {str(e)}"
        )


class CancelWorkflowRequest(BaseModel):
    """Request to cancel a specific workflow"""
    workflow_message_id: str


@router.post("/{execution_id}/cancel_workflow")
async def cancel_workflow(
    execution_id: str,
    cancel_request: CancelWorkflowRequest,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Cancel a specific workflow tool call within an execution.

    This cancels only the workflow, allowing the agent to continue running
    and respond to the user about the cancellation. This is different from
    /cancel which stops the entire execution.

    Args:
        execution_id: The agent execution ID
        workflow_message_id: The unique workflow message ID to cancel
    """
    workflow_message_id = None  # Initialize to avoid UnboundLocalError
    try:
        from control_plane_api.app.services.workflow_cancellation_manager import workflow_cancellation_manager

        workflow_message_id = cancel_request.workflow_message_id

        logger.info(
            "cancel_workflow_requested",
            execution_id=execution_id,
            workflow_message_id=workflow_message_id,
            org_id=organization["id"]
        )

        # Get execution from database to verify it exists and is running
        execution = db.query(Execution).filter(
            Execution.id == uuid_module.UUID(execution_id),
            Execution.organization_id == organization["id"]
        ).first()

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )

        current_status = execution.status

        # Check if execution is still running
        if current_status not in ["running", "waiting_for_input"]:
            logger.warning(
                "cancel_workflow_execution_not_running",
                execution_id=execution_id,
                status=current_status
            )
            return {
                "success": False,
                "error": f"Execution is not running (status: {current_status})",
                "execution_id": execution_id,
                "workflow_message_id": workflow_message_id,
                "status": current_status,
            }

        # Request cancellation via the workflow cancellation manager
        # The workflow executor will check this flag and stop gracefully
        workflow_cancellation_manager.request_cancellation(execution_id, workflow_message_id)

        logger.info(
            "workflow_cancellation_flag_set",
            execution_id=execution_id,
            workflow_message_id=workflow_message_id
        )

        # Publish a workflow_cancelled event to update the UI immediately
        redis_client = get_redis_client()
        if redis_client:
            try:
                import time
                current_timestamp = datetime.now(timezone.utc).isoformat()

                # Create workflow_cancelled event for immediate UI feedback
                cancel_event = {
                    "event_type": "workflow_cancelled",
                    "data": {
                        "workflow_name": "Workflow",  # Will be updated by executor with actual name
                        "status": "cancelled",
                        "finished_at": current_timestamp,
                        "message": "Workflow cancellation requested",
                        "source": "workflow",
                        "message_id": workflow_message_id,
                    },
                    "timestamp": current_timestamp,
                }

                redis_key = f"execution:{execution_id}:events"
                redis_client.rpush(redis_key, json.dumps(cancel_event))
                redis_client.expire(redis_key, 3600)  # 1 hour TTL

                logger.info(
                    "workflow_cancel_event_published",
                    execution_id=execution_id,
                    workflow_message_id=workflow_message_id
                )
            except Exception as e:
                logger.warning(
                    "failed_to_publish_workflow_cancel_event",
                    error=str(e),
                    execution_id=execution_id
                )

        return {
            "success": True,
            "execution_id": execution_id,
            "workflow_message_id": workflow_message_id,
            "message": "Workflow cancellation requested. The workflow will stop at the next check point.",
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "cancel_workflow_error",
            execution_id=execution_id,
            workflow_message_id=workflow_message_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel workflow: {str(e)}"
        )


@router.get("/{execution_id}/session")
async def get_session_history(
    execution_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Retrieve session history with Redis caching for hot loading.

    Workers GET session messages before each run to restore conversation context.

    Performance strategy:
    1. Check Redis cache first (hot path - milliseconds)
    2. Fall back to database if not cached (cold path - ~50ms)
    3. Cache the result in Redis for next access
    """
    import json
    try:
        session_id = execution_id
        redis_key = f"session:{session_id}"

        # Try Redis first for hot loading
        redis_client = get_redis_client()
        if redis_client:
            try:
                cached_session = await redis_client.get(redis_key)
                if cached_session:
                    session_data = json.loads(cached_session)

                    # CRITICAL: Deduplicate and sort messages to ensure consistency
                    # Apply to cached data as well to guarantee no duplicates
                    if "messages" in session_data and session_data["messages"]:
                        # Two-level deduplication: message_id + content signature
                        seen_message_ids = {}
                        seen_content_sigs = {}  # Track content signatures for assistant messages
                        deduplicated_messages = []

                        for msg in session_data["messages"]:
                            msg_id = msg.get("message_id")

                            # Level 1: Deduplicate by message_id
                            if msg_id and msg_id in seen_message_ids:
                                continue
                            if msg_id:
                                seen_message_ids[msg_id] = True

                            # Level 2: Deduplicate by content signature (assistant messages only)
                            if msg.get("role") == "assistant":
                                content = msg.get("content", "")
                                timestamp = msg.get("timestamp", "")
                                content_normalized = content.strip().lower()[:200]

                                if content_normalized and content_normalized in seen_content_sigs:
                                    prev_msg = seen_content_sigs[content_normalized]
                                    prev_timestamp = prev_msg.get("timestamp", "")

                                    # Check timestamp proximity (within 5 seconds)
                                    try:
                                        from datetime import datetime
                                        t1 = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                        t2 = datetime.fromisoformat(prev_timestamp.replace('Z', '+00:00'))
                                        diff = abs((t1 - t2).total_seconds())

                                        if diff <= 5:
                                            logger.info(
                                                "duplicate_content_filtered_redis_cache",
                                                message_id=msg_id,
                                                prev_message_id=prev_msg.get("message_id"),
                                                content_preview=content[:50]
                                            )
                                            continue  # Skip duplicate content
                                    except:
                                        pass  # If can't parse timestamps, don't skip

                                if content_normalized:
                                    seen_content_sigs[content_normalized] = msg

                            deduplicated_messages.append(msg)

                        # Sort by timestamp (use far future date for missing timestamps to put them last)
                        session_data["messages"] = sorted(
                            deduplicated_messages,
                            key=lambda msg: msg.get("timestamp", "9999-12-31T23:59:59Z")
                        )
                        session_data["message_count"] = len(session_data["messages"])

                    logger.info(
                        "session_cache_hit",
                        execution_id=execution_id,
                        message_count=session_data.get("message_count", 0)
                    )
                    return session_data
            except Exception as redis_error:
                logger.warning("session_cache_error", error=str(redis_error))
                # Continue to DB fallback

        # Redis miss or unavailable - load from database
        session_record = db.query(SessionModel).filter(
            SessionModel.execution_id == execution_id,
            SessionModel.organization_id == organization["id"]
        ).first()

        if not session_record:
            raise HTTPException(status_code=404, detail="Session not found")

        messages = session_record.messages or []

        # CRITICAL: Deduplicate messages by message_id AND content to prevent duplicates
        # This handles any duplicates that may have been persisted in the database
        # Two-level deduplication: message_id + content signature
        seen_message_ids = {}
        seen_content_sigs = {}  # Track content signatures for assistant messages
        deduplicated_messages = []

        for msg in messages:
            msg_id = msg.get("message_id")

            # Level 1: Deduplicate by message_id
            if msg_id and msg_id in seen_message_ids:
                # Skip duplicate message
                continue
            if msg_id:
                seen_message_ids[msg_id] = True

            # Level 2: Deduplicate by content signature (assistant messages only)
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                content_normalized = content.strip().lower()[:200]

                if content_normalized and content_normalized in seen_content_sigs:
                    prev_msg = seen_content_sigs[content_normalized]
                    prev_timestamp = prev_msg.get("timestamp", "")

                    # Check timestamp proximity (within 5 seconds)
                    try:
                        from datetime import datetime
                        t1 = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        t2 = datetime.fromisoformat(prev_timestamp.replace('Z', '+00:00'))
                        diff = abs((t1 - t2).total_seconds())

                        if diff <= 5:
                            logger.info(
                                "duplicate_content_filtered_database",
                                message_id=msg_id,
                                prev_message_id=prev_msg.get("message_id"),
                                content_preview=content[:50]
                            )
                            continue  # Skip duplicate content
                    except:
                        pass  # If can't parse timestamps, don't skip

                if content_normalized:
                    seen_content_sigs[content_normalized] = msg

            deduplicated_messages.append(msg)

        # CRITICAL: Sort messages by timestamp to ensure chronological order
        # This guarantees consistent ordering regardless of how they're stored in JSONB
        # Use far future date for missing timestamps to put them last
        messages_sorted = sorted(deduplicated_messages, key=lambda msg: msg.get("timestamp", "9999-12-31T23:59:59Z"))

        session_data = {
            "session_id": session_record.session_id or execution_id,
            "execution_id": execution_id,
            "messages": messages_sorted,
            "message_count": len(messages_sorted),
            "metadata": session_record.metadata_ or {},
        }

        # Cache in Redis for next access (TTL: 1 hour)
        if redis_client:
            try:
                await redis_client.setex(
                    redis_key,
                    3600,  # 1 hour TTL
                    json.dumps(session_data)
                )
                logger.info(
                    "session_cached",
                    execution_id=execution_id,
                    message_count=len(messages)
                )
            except Exception as cache_error:
                logger.warning("session_cache_write_error", error=str(cache_error))

        logger.info(
            "session_history_retrieved_from_database",
            execution_id=execution_id,
            session_id=session_record.session_id,
            message_count=len(messages)
        )

        return session_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "failed_to_retrieve_session_history",
            execution_id=execution_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session history: {str(e)}"
        )


@router.post("/{execution_id}/session", status_code=status.HTTP_201_CREATED)
async def persist_session_history(
    execution_id: str,
    session_data: dict,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Persist session history from worker to Control Plane database.

    Worker POSTs session messages after each run completion.
    This ensures history is available even when worker is offline.

    Sessions are stored in database for fast loading by the UI streaming endpoint.
    """
    try:
        session_id = session_data.get("session_id", execution_id)
        user_id = session_data.get("user_id")
        messages = session_data.get("messages", [])
        metadata = session_data.get("metadata", {})

        logger.info(
            "persisting_session_history",
            execution_id=execution_id,
            session_id=session_id,
            user_id=user_id,
            message_count=len(messages),
            org_id=organization["id"],
        )

        # CRITICAL: Ensure all messages have message_id before persisting
        # Without message_id, messages cannot be properly sent via SSE stream
        messages_with_ids = []
        for msg in messages:
            if not msg.get("message_id"):
                # Generate stable message_id from timestamp and role
                timestamp_str = msg.get("timestamp")
                role = msg.get("role", "unknown")

                if timestamp_str:
                    try:
                        timestamp_micros = int(datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).timestamp() * 1000000)
                    except Exception:
                        timestamp_micros = int(datetime.now(timezone.utc).timestamp() * 1000000)
                else:
                    timestamp_micros = int(datetime.now(timezone.utc).timestamp() * 1000000)

                msg["message_id"] = f"{execution_id}_{role}_{timestamp_micros}"
                logger.info(
                    "generated_missing_message_id",
                    execution_id=execution_id,
                    role=role,
                    message_id=msg["message_id"]
                )

            messages_with_ids.append(msg)

        # DEFENSIVE: Deduplicate messages at API level (defense-in-depth)
        # This prevents duplicates even if worker didn't deduplicate properly
        # Two-level deduplication: message_id + content signature
        original_count = len(messages_with_ids)
        seen_ids = set()
        seen_content_sigs = {}  # Track content signatures for assistant messages
        deduplicated_messages = []
        duplicates_by_id = 0
        duplicates_by_content = 0

        for msg in messages_with_ids:
            msg_id = msg.get("message_id")

            # Level 1: Deduplicate by message_id
            if msg_id and msg_id in seen_ids:
                logger.debug(
                    "api_deduplication_skipped_duplicate_id",
                    execution_id=execution_id,
                    message_id=msg_id,
                    role=msg.get("role")
                )
                duplicates_by_id += 1
                continue

            if msg_id:
                seen_ids.add(msg_id)

            # Level 2: Deduplicate by content signature (assistant messages only)
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                content_normalized = content.strip().lower()[:200]

                if content_normalized and content_normalized in seen_content_sigs:
                    prev_msg = seen_content_sigs[content_normalized]
                    prev_timestamp = prev_msg.get("timestamp", "")

                    # Check timestamp proximity (within 5 seconds)
                    try:
                        t1 = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        t2 = datetime.fromisoformat(prev_timestamp.replace('Z', '+00:00'))
                        diff = abs((t1 - t2).total_seconds())

                        if diff <= 5:
                            logger.info(
                                "api_deduplication_skipped_duplicate_content",
                                execution_id=execution_id,
                                message_id=msg_id,
                                prev_message_id=prev_msg.get("message_id"),
                                content_preview=content[:50]
                            )
                            duplicates_by_content += 1
                            continue  # Skip duplicate content
                    except:
                        pass  # If can't parse timestamps, don't skip

                if content_normalized:
                    seen_content_sigs[content_normalized] = msg

            deduplicated_messages.append(msg)

        messages_with_ids = deduplicated_messages

        if len(messages_with_ids) < original_count:
            logger.info(
                "api_defensive_deduplication_applied",
                execution_id=execution_id,
                original_count=original_count,
                deduplicated_count=len(messages_with_ids),
                removed=original_count - len(messages_with_ids),
                duplicates_by_id=duplicates_by_id,
                duplicates_by_content=duplicates_by_content
            )

        # Upsert to sessions table using SQLAlchemy
        # This matches what the streaming endpoint expects to load
        existing_session = db.query(SessionModel).filter(
            SessionModel.execution_id == execution_id
        ).first()

        if existing_session:
            # Update existing session
            existing_session.session_id = session_id
            existing_session.organization_id = organization["id"]
            existing_session.user_id = user_id
            existing_session.messages = messages_with_ids
            existing_session.metadata_ = metadata
        else:
            # Create new session
            new_session = SessionModel(
                execution_id=execution_id,
                session_id=session_id,
                organization_id=organization["id"],
                user_id=user_id,
                messages=messages_with_ids,
                metadata_=metadata,
            )
            db.add(new_session)

        db.commit()

        logger.info(
            "session_persisted_to_database",
            execution_id=execution_id,
            session_id=session_id,
            message_count=len(messages),
        )

        # Cache in Redis for hot loading on next access
        import json

        redis_client = get_redis_client()
        if redis_client:
            try:
                redis_key = f"session:{session_id}"
                cache_data = {
                    "session_id": session_id,
                    "execution_id": execution_id,
                    "messages": messages,
                    "message_count": len(messages),
                }
                await redis_client.setex(
                    redis_key,
                    3600,  # 1 hour TTL
                    json.dumps(cache_data)
                )
                logger.info(
                    "session_cached_on_write",
                    execution_id=execution_id,
                    message_count=len(messages)
                )
            except Exception as cache_error:
                logger.warning("session_cache_write_error_on_persist", error=str(cache_error))
                # Don't fail persistence if caching fails

        return {
            "success": True,
            "execution_id": execution_id,
            "session_id": session_id,
            "persisted_messages": len(messages),
        }

    except Exception as e:
        db.rollback()
        logger.error(
            "session_persistence_failed",
            error=str(e),
            execution_id=execution_id,
        )
        return {
            "success": False,
            "error": str(e),
        }


@router.post("/{execution_id}/mark-done", status_code=status.HTTP_202_ACCEPTED)
async def mark_execution_as_done(
    execution_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Mark an execution as done, signaling the workflow to complete.

    This sends a signal to the Temporal workflow to indicate the user is finished
    with the conversation. The workflow will complete gracefully after this signal.
    """
    try:
        # Get Temporal client
        temporal_client = await get_temporal_client()

        # Verify the execution belongs to this organization and get execution type
        execution = db.query(Execution).filter(
            Execution.id == uuid_module.UUID(execution_id),
            Execution.organization_id == organization["id"]
        ).first()

        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")

        # Construct workflow ID based on execution type
        execution_type = execution.execution_type or "AGENT"
        if execution_type == "TEAM":
            workflow_id = f"team-execution-{execution_id}"
        else:
            workflow_id = f"agent-execution-{execution_id}"

        workflow_handle = temporal_client.get_workflow_handle(workflow_id)

        # Send mark_as_done signal to workflow
        await workflow_handle.signal(AgentExecutionWorkflow.mark_as_done)

        logger.info(
            "execution_marked_as_done",
            execution_id=execution_id,
            org_id=organization["id"],
        )

        return {
            "success": True,
            "execution_id": execution_id,
            "message": "Execution marked as done, workflow will complete",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "mark_as_done_failed",
            error=str(e),
            execution_id=execution_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark execution as done: {str(e)}"
        )


class StreamingEventRequest(BaseModel):
    """Request to publish a streaming event to Redis for real-time UI updates"""
    event_type: str  # "status", "message", "tool_started", "tool_completed", "error"
    data: dict  # Event payload
    timestamp: str | None = None


@router.post("/{execution_id}/events", status_code=status.HTTP_202_ACCEPTED)
async def publish_execution_event(
    execution_id: str,
    event: StreamingEventRequest,
    request: Request,
    organization: dict = Depends(get_current_organization),
):
    """
    Publish a streaming event via event bus (multi-provider support).

    This endpoint is used by workers to send real-time events (tool execution, status updates, etc.)
    that are streamed to the UI via SSE without waiting for Temporal workflow completion.

    Supports multiple providers:
    - Redis: List storage + pub/sub for SSE streaming
    - HTTP: Webhook notifications
    - WebSocket: Real-time push to connected clients
    - NATS: High-performance message streaming

    Events are stored in Redis list: execution:{execution_id}:events
    TTL: 1 hour (events are temporary, final state persists in database)
    """
    try:
        # Build event payload
        event_data = {
            "event_type": event.event_type,
            "data": event.data,
            "timestamp": event.timestamp or datetime.now(timezone.utc).isoformat(),
            "execution_id": execution_id,
        }

        metadata = {
            "organization_id": organization.get("id"),
            "organization_name": organization.get("name"),
        }

        # Try to use event bus if available
        event_bus = getattr(request.app.state, 'event_bus', None)
        if event_bus:
            # Use event bus (multi-provider)
            logger.debug(
                "publishing_via_event_bus",
                execution_id=execution_id[:8],
                event_type=event.event_type,
                providers=event_bus.get_provider_names()
            )

            results = await event_bus.publish_event(
                execution_id=execution_id,
                event_type=event.event_type,
                data=event.data,
                metadata=metadata
            )

            # Log results per provider
            success_count = sum(1 for success in results.values() if success)
            logger.info(
                "execution_event_published_via_event_bus",
                execution_id=execution_id[:8],
                event_type=event.event_type,
                providers=list(results.keys()),
                success_count=success_count,
                total_providers=len(results),
                results=results
            )

            return {
                "success": success_count > 0,
                "execution_id": execution_id,
                "event_type": event.event_type,
                "providers": results
            }
        else:
            # Fallback to direct Redis (backwards compatibility)
            logger.debug(
                "event_bus_not_available_using_redis_fallback",
                execution_id=execution_id[:8],
                event_type=event.event_type
            )

            redis_client = get_redis_client()
            if not redis_client:
                # Redis not configured - skip streaming but don't fail
                logger.warning("redis_not_configured_for_streaming", execution_id=execution_id)
                return {"success": True, "message": "Redis not configured, event skipped"}

            # Push event to Redis list (most recent at head) - this must be FAST
            redis_key = f"execution:{execution_id}:events"
            await redis_client.lpush(redis_key, json.dumps(event_data))

            # Keep only last 1000 events (prevent memory issues)
            await redis_client.ltrim(redis_key, 0, 999)

            # Set TTL: 1 hour (events are temporary)
            await redis_client.expire(redis_key, 3600)

            # Also publish to pub/sub channel for real-time streaming
            # This allows connected SSE clients to receive updates instantly
            pubsub_channel = f"execution:{execution_id}:stream"
            try:
                await redis_client.publish(pubsub_channel, json.dumps(event_data))
            except Exception as pubsub_error:
                # Don't fail if pub/sub fails - the list storage is the primary mechanism
                logger.debug("pubsub_publish_failed", error=str(pubsub_error), execution_id=execution_id[:8])

            logger.info(
                "execution_event_published_via_redis_fallback",
                execution_id=execution_id[:8],
                event_type=event.event_type,
            )

            return {
                "success": True,
                "execution_id": execution_id,
                "event_type": event.event_type,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "publish_event_failed",
            error=str(e),
            execution_id=execution_id,
            event_type=event.event_type,
        )
        # Don't fail the worker if streaming fails - it's not critical
        return {
            "success": False,
            "error": str(e),
            "message": "Event publishing failed but execution continues"
        }


# ============================================================================
# LEGACY STREAMING IMPLEMENTATION - REPLACED BY NEW MODULAR ARCHITECTURE
# ============================================================================
# The following ~1,400 line streaming implementation has been replaced by the
# new ExecutionStreamer architecture (Tasks 5-15).
#
# The new implementation is now the DEFAULT and is automatically included via:
#   router.include_router(new_streaming_router.router, tags=["executions"])
#
# This legacy code is kept commented out for emergency rollback purposes.
# If you need to rollback, comment out the include_router line above and
# uncomment this endpoint.
#
# NEW IMPLEMENTATION:
#   - File: control_plane_api/app/routers/executions/router.py
#   - Architecture: Modular with ExecutionStreamer orchestrator
#   - Performance: <50ms to first event (vs 2-5s in legacy)
#   - Code size: ~300 lines (vs ~1,400 lines here)
#   - Testability: High (modular components)
#   - Maintenance: Easy (separated concerns)
#
# For more details, see:
#   control_plane_api/app/routers/executions/TASK_15_INTEGRATION.md
# ============================================================================


@router.post("/{execution_id}/job/{job_id}/status")
async def update_job_execution_status_v2(
    execution_id: str,
    job_id: str,
    request_data: UpdateJobExecutionStatusRequest,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Update job_executions record with execution results.

    This endpoint is used by workers to update job execution status via HTTP
    instead of directly accessing the database.
    """
    try:
        from datetime import timezone

        now = datetime.now(timezone.utc).isoformat()

        logger.info(
            "updating_job_execution_status",
            job_id=job_id,
            execution_id=execution_id,
            status=request_data.status,
        )

        # Update job_executions record
        job_execution = db.query(JobExecution).filter(
            JobExecution.job_id == job_id,
            JobExecution.execution_id == uuid_module.UUID(execution_id)
        ).first()

        if job_execution:
            job_execution.execution_status = request_data.status
            job_execution.execution_duration_ms = request_data.duration_ms
            db.commit()

        # Update job success/failure counts
        if request_data.status == "completed":
            # Increment successful_executions - SECURITY: Add org_id filter
            try:
                job = db.query(Job).filter(
                    Job.id == job_id,
                    Job.organization_id == organization["id"]
                ).first()
                if job:
                    job.successful_executions = (job.successful_executions or 0) + 1
                    db.commit()
            except Exception as e:
                db.rollback()
                logger.warning("failed_to_increment_success_count", job_id=job_id, error=str(e))

        elif request_data.status == "failed":
            # Increment failed_executions - SECURITY: Add org_id filter
            try:
                job = db.query(Job).filter(
                    Job.id == job_id,
                    Job.organization_id == organization["id"]
                ).first()
                if job:
                    job.failed_executions = (job.failed_executions or 0) + 1
                    db.commit()
            except Exception as e:
                db.rollback()
                logger.warning("failed_to_increment_failure_count", job_id=job_id, error=str(e))

        logger.info(
            "updated_job_execution_status",
            job_id=job_id,
            execution_id=execution_id,
            status=request_data.status,
        )

        # Publish event to Redis for real-time UI updates
        try:
            redis_client = get_redis_client()
            if redis_client:
                event_type = "done" if request_data.status == "completed" else "error"
                event_data = {
                    "event_type": event_type,
                    "data": {
                        "job_id": job_id,
                        "execution_id": execution_id,
                        "status": request_data.status,
                        "duration_ms": request_data.duration_ms,
                        "error_message": request_data.error_message,
                        "message": f"Job execution {request_data.status}",
                    },
                    "timestamp": now,
                    "execution_id": execution_id,
                }

                # Push to Redis list
                redis_key = f"execution:{execution_id}:events"
                await redis_client.lpush(redis_key, json.dumps(event_data))
                await redis_client.ltrim(redis_key, 0, 999)
                await redis_client.expire(redis_key, 3600)

                # Publish to pub/sub for real-time streaming
                pubsub_channel = f"execution:{execution_id}:stream"
                await redis_client.publish(pubsub_channel, json.dumps(event_data))

                logger.info(
                    "job_status_event_published",
                    execution_id=execution_id[:8],
                    job_id=job_id[:8],
                    event_type=event_type,
                )
        except Exception as event_error:
            # Don't fail the request if event publishing fails
            logger.warning(
                "failed_to_publish_job_status_event",
                job_id=job_id,
                execution_id=execution_id,
                error=str(event_error),
            )

        return {
            "job_id": job_id,
            "execution_id": execution_id,
            "status": "updated",
        }

    except Exception as e:
        db.rollback()
        logger.error(
            "failed_to_update_job_execution_status",
            job_id=job_id,
            execution_id=execution_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update job execution status: {str(e)}"
        )


# ============================================================================
# State Transition Endpoints
# ============================================================================


class StateOverrideRequest(BaseModel):
    """Request to manually override execution state"""
    state: str = Field(..., description="New state (running, waiting_for_input, completed, failed)")
    reasoning: str = Field(..., description="Reason for manual override")


@router.get("/{execution_id}/transitions")
async def get_execution_transitions(
    execution_id: str,
    organization: dict = Depends(get_current_organization),
):
    """
    Get transition history for an execution

    Returns all state transitions with AI reasoning for the specified execution.
    """
    try:
        client = get_supabase()

        # Verify execution belongs to organization
        exec_result = safe_execute_query(
            client.table("executions")
            .select("id")
            .eq("id", execution_id)
            .eq("organization_id", organization["id"])
        )

        if not exec_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )

        # Get all transitions for this execution
        transitions_result = safe_execute_query(
            client.table("execution_transitions")
            .select("*")
            .eq("execution_id", execution_id)
            .order("created_at", desc=False)
        )

        transitions = transitions_result if transitions_result else []

        logger.info(
            "execution_transitions_fetched",
            execution_id=execution_id,
            transition_count=len(transitions),
        )

        return {
            "execution_id": execution_id,
            "transition_count": len(transitions),
            "transitions": transitions,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_transitions_failed",
            execution_id=execution_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transitions: {str(e)}"
        )


@router.post("/{execution_id}/transitions/override")
async def override_execution_state(
    execution_id: str,
    override: StateOverrideRequest,
    organization: dict = Depends(get_current_organization),
    request: Request = None,
):
    """
    Manually override execution state (admin/debug)

    Allows manual state transitions with reasoning. Records the override
    in the transitions table for audit purposes.
    """
    try:
        # Validate state
        valid_states = ["running", "waiting_for_input", "completed", "failed", "cancelled"]
        if override.state.lower() not in valid_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state. Must be one of: {', '.join(valid_states)}"
            )

        client = get_supabase()

        # Verify execution belongs to organization
        exec_result = safe_execute_query(
            client.table("executions")
            .select("id, status")
            .eq("id", execution_id)
            .eq("organization_id", organization["id"])
        )

        if not exec_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )

        current_execution = exec_result[0]
        from_state = current_execution.get("status", "unknown")
        to_state = override.state.lower()

        # Update execution status
        update_data = {"status": to_state}

        if to_state in ["completed", "failed"]:
            update_data["completed_at"] = datetime.now(timezone.utc).isoformat()

        update_result = safe_execute_query(
            client.table("executions")
            .update(update_data)
            .eq("id", execution_id)
            .eq("organization_id", organization["id"])
        )

        if not update_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update execution status"
            )

        # Get user info from request headers or auth
        user_id = organization.get("user_id", "admin")
        override_user_email = organization.get("email", "unknown")

        # Record manual override in transitions table
        transition_record = {
            "organization_id": organization["id"],
            "execution_id": execution_id,
            "turn_number": 0,  # Manual overrides don't have a turn number
            "from_state": from_state,
            "to_state": to_state,
            "reasoning": f"MANUAL OVERRIDE by {override_user_email}: {override.reasoning}",
            "confidence": "high",  # Manual overrides are definitive
            "decision_factors": {
                "manual_override": True,
                "override_by": override_user_email,
                "override_user_id": user_id,
                "original_reasoning": override.reasoning,
            },
            "ai_model": "manual",
            "decision_time_ms": 0,
            "is_manual_override": True,
            "override_user_id": user_id,
            "override_reasoning": override.reasoning,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        transition_result = safe_execute_query(
            client.table("execution_transitions")
            .insert(transition_record)
        )

        logger.info(
            "execution_state_overridden",
            execution_id=execution_id,
            from_state=from_state,
            to_state=to_state,
            user=override_user_email,
            reasoning=override.reasoning[:100],
        )

        return {
            "success": True,
            "execution_id": execution_id,
            "from_state": from_state,
            "to_state": to_state,
            "override_by": override_user_email,
            "transition_id": transition_result[0]["id"] if transition_result else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "override_state_failed",
            execution_id=execution_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to override state: {str(e)}"
        )


@router.get("/{execution_id}/details", response_model=WorkflowDetailsResponse)
async def get_execution_details(
    execution_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about an execution including activity trace.

    This endpoint retrieves comprehensive execution details including:
    - Execution status and timing
    - Activity execution trace with timeline
    - Recent workflow events
    - Link to Temporal Web UI

    Args:
        execution_id: Execution UUID or Temporal workflow ID
        request: FastAPI request object (contains kubiya_token in state)
        organization: Current organization from auth
        db: Database session

    Returns:
        WorkflowDetailsResponse with full execution details and activity trace

    Raises:
        404: Execution not found
        403: Access denied (execution doesn't belong to organization)
        500: Failed to fetch execution details from Temporal
    """
    try:
        org_id = organization["id"]

        # Find execution by ID or temporal_workflow_id
        execution = db.query(Execution).filter(
            ((Execution.id == execution_id) | (Execution.temporal_workflow_id == execution_id)),
            Execution.organization_id == org_id
        ).first()

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )

        # Get workflow ID for Temporal query
        # If stored in DB, use it; otherwise derive from execution type and ID
        workflow_id = execution.temporal_workflow_id
        if not workflow_id:
            # Derive workflow ID based on execution type
            exec_type = execution.execution_type.lower() if execution.execution_type else "agent"
            if exec_type == "team":
                workflow_id = f"team-execution-{execution.id}"
            else:
                # Default to agent execution pattern
                workflow_id = f"agent-execution-{execution.id}"

        # Get kubiya token from request state for Temporal credentials
        token = getattr(request.state, "kubiya_token", None)
        if not token:
            logger.error("kubiya_token_missing", execution_id=execution_id, org_id=org_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication token not available"
            )

        workflow_service = WorkflowOperationsService(db)
        details = await workflow_service.get_workflow_details(
            workflow_id=workflow_id,
            organization_id=org_id,
            token=token
        )

        logger.info(
            "execution_details_retrieved",
            execution_id=execution_id,
            workflow_id=workflow_id,
            org_id=org_id
        )

        return details

    except HTTPException:
        raise
    except ValueError as e:
        # ValueError is raised for "not found" or "access denied"
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        elif "access denied" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except RuntimeError as e:
        # RuntimeError is raised for Temporal client errors
        logger.error("execution_details_error", error=str(e), execution_id=execution_id, org_id=org_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "execution_details_unexpected_error",
            error=str(e),
            execution_id=execution_id,
            org_id=org_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching execution details"
        )


@router.post("/{execution_id}/terminate", response_model=TerminateWorkflowResponse)
async def terminate_execution(
    execution_id: str,
    request: Request,
    terminate_request: TerminateWorkflowRequest,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Terminate a running execution.

    This endpoint forcefully terminates a running execution. The execution will be
    cancelled and its status will be updated to 'cancelled' in the database.

    Args:
        execution_id: Execution UUID or Temporal workflow ID to terminate
        request: FastAPI request object (contains kubiya_token in state)
        terminate_request: Request body with termination reason
        organization: Current organization from auth
        db: Database session

    Returns:
        TerminateWorkflowResponse with success status and termination timestamp

    Raises:
        404: Execution not found
        403: Access denied (execution doesn't belong to organization)
        400: Cannot terminate execution (invalid status)
        500: Failed to terminate execution via Temporal
    """
    try:
        org_id = organization["id"]

        # Find execution by ID or temporal_workflow_id
        execution = db.query(Execution).filter(
            ((Execution.id == execution_id) | (Execution.temporal_workflow_id == execution_id)),
            Execution.organization_id == org_id
        ).first()

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )

        # Get workflow ID for Temporal query
        # If stored in DB, use it; otherwise derive from execution type and ID
        workflow_id = execution.temporal_workflow_id
        if not workflow_id:
            # Derive workflow ID based on execution type
            exec_type = execution.execution_type.lower() if execution.execution_type else "agent"
            if exec_type == "team":
                workflow_id = f"team-execution-{execution.id}"
            else:
                # Default to agent execution pattern
                workflow_id = f"agent-execution-{execution.id}"

        # Get kubiya token from request state for Temporal credentials
        token = getattr(request.state, "kubiya_token", None)
        if not token:
            logger.error("kubiya_token_missing", execution_id=execution_id, org_id=org_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication token not available"
            )

        workflow_service = WorkflowOperationsService(db)
        result = await workflow_service.terminate_workflow(
            workflow_id=workflow_id,
            organization_id=org_id,
            token=token,
            reason=terminate_request.reason
        )

        logger.info(
            "execution_terminated_via_api",
            execution_id=execution_id,
            workflow_id=workflow_id,
            org_id=org_id,
            reason=terminate_request.reason
        )

        return result

    except HTTPException:
        raise
    except ValueError as e:
        # ValueError is raised for "not found", "access denied", or "invalid status"
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        elif "access denied" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg)
        else:
            # Invalid status for termination
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except RuntimeError as e:
        # RuntimeError is raised for Temporal client errors
        logger.error("execution_termination_error", error=str(e), execution_id=execution_id, org_id=org_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "execution_termination_unexpected_error",
            error=str(e),
            execution_id=execution_id,
            org_id=org_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while terminating execution"
        )
