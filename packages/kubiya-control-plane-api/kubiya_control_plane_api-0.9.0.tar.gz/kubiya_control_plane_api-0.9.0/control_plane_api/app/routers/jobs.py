"""
Jobs router for scheduled and webhook-triggered executions.

This router handles:
- CRUD operations for jobs
- Manual job triggering
- Webhook URL generation and triggering
- Cron schedule management with Temporal
- Job execution history

Uses SQLAlchemy ORM for all database operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import structlog
import uuid as uuid_module
import hmac
import hashlib
import secrets
import json

from sqlalchemy.orm import Session
from sqlalchemy import desc

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.database import get_db
from control_plane_api.app.lib.sqlalchemy_utils import model_to_dict
from control_plane_api.app.lib.temporal_client import get_temporal_client
from control_plane_api.app.lib.job_executor import select_worker_queue, substitute_prompt_parameters
from control_plane_api.app.workflows.agent_execution import AgentExecutionWorkflow
from control_plane_api.app.workflows.team_execution import TeamExecutionWorkflow
from control_plane_api.app.routers.executions import validate_job_exists
from control_plane_api.app.routers.execution_environment import resolve_agent_execution_environment_internal
from control_plane_api.app.schemas.job_schemas import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobTriggerRequest,
    JobTriggerResponse,
    JobExecutionHistoryResponse,
    JobExecutionHistoryItem,
    WebhookPayload,
    ExecutionEnvironment,
)
from control_plane_api.app.models.job import Job, JobExecution
from control_plane_api.app.models.execution import Execution
from control_plane_api.app.models.agent import Agent
from control_plane_api.app.models.team import Team
from temporalio.client import Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec, SchedulePolicy, ScheduleOverlapPolicy
from croniter import croniter

logger = structlog.get_logger()

router = APIRouter()


def generate_webhook_secret() -> str:
    """Generate a secure random webhook secret"""
    return secrets.token_urlsafe(32)


def generate_webhook_path() -> str:
    """Generate a unique webhook URL path"""
    return secrets.token_urlsafe(16)


async def start_job_execution(
    job: dict,
    organization_id: str,
    trigger_type: str,
    trigger_metadata: dict,
    db: Session,
    token: str,
    parameters: Optional[dict] = None,
) -> tuple[str, str]:
    """
    Start a job execution by directly triggering the appropriate workflow.

    Args:
        job: Job data as dict
        organization_id: Organization ID
        trigger_type: Type of trigger (manual, cron, webhook)
        trigger_metadata: Metadata about the trigger
        db: SQLAlchemy database session
        token: Authentication token for fetching Temporal credentials
        parameters: Optional parameters for prompt substitution

    Returns:
        Tuple of (workflow_id, execution_id)
    """
    # Get org-specific Temporal credentials and client
    from control_plane_api.app.lib.temporal_credentials_service import get_temporal_credentials_for_org
    from control_plane_api.app.lib.temporal_client import get_temporal_client_for_org

    temporal_credentials = await get_temporal_credentials_for_org(
        org_id=organization_id,
        token=token,
        use_fallback=True  # Enable fallback during migration
    )

    temporal_client = await get_temporal_client_for_org(
        namespace=temporal_credentials["namespace"],
        api_key=temporal_credentials["api_key"],
        host=temporal_credentials["host"],
    )

    planning_mode = job.get("planning_mode")
    entity_type = job.get("entity_type")
    entity_id = job.get("entity_id")

    # Get the appropriate worker queue based on job configuration
    worker_queue_name, _ = await select_worker_queue(
        organization_id=organization_id,
        executor_type=job.get("executor_type", "auto"),
        worker_queue_name=job.get("worker_queue_name"),
        environment_name=job.get("environment_name"),
    )

    if not worker_queue_name:
        raise ValueError("No workers are currently running for your organization. Please start a worker to execute jobs.")

    # Extract runner_name from worker_queue_name (format: "org_id.runner_name")
    runner_name = worker_queue_name.split(".")[-1] if "." in worker_queue_name else worker_queue_name

    # Get entity name for display
    entity_name = job.get("entity_name")
    if not entity_name and entity_id and entity_type:
        # Try to get entity name from database using SQLAlchemy
        try:
            if entity_type == "agent":
                entity_obj = db.query(Agent).filter(Agent.id == entity_id).first()
            elif entity_type == "team":
                entity_obj = db.query(Team).filter(Team.id == entity_id).first()
            else:
                entity_obj = None
            if entity_obj:
                entity_name = entity_obj.name
        except Exception as e:
            logger.warning("failed_to_get_entity_name", entity_type=entity_type, entity_id=entity_id, error=str(e))

    # Substitute parameters in prompt template
    prompt = job.get("prompt_template", "")
    if parameters:
        prompt = substitute_prompt_parameters(prompt, parameters)

    # For webhook triggers, append webhook context to the prompt
    if trigger_type == "webhook" and (parameters or trigger_metadata.get("metadata")):
        webhook_context = "\n\n---\nWebhook Context:\n"
        if parameters:
            webhook_context += f"Parameters: {json.dumps(parameters, indent=2)}\n"
        if trigger_metadata.get("metadata"):
            webhook_context += f"Metadata: {json.dumps(trigger_metadata.get('metadata'), indent=2)}\n"
        prompt = prompt + webhook_context

    # Generate execution ID
    execution_id = str(uuid_module.uuid4())
    execution_uuid = uuid_module.UUID(execution_id)

    # Determine execution_type based on entity_type
    execution_type_value = entity_type.upper() if entity_type else "AGENT"

    # Map trigger_type to trigger_source
    trigger_source_map = {
        "manual": "job_manual",
        "cron": "job_cron",
        "webhook": "job_webhook",
    }
    trigger_source = trigger_source_map.get(trigger_type, "job_manual")

    now = datetime.now(timezone.utc)

    # Create placeholder execution record using SQLAlchemy
    execution = Execution(
        id=execution_uuid,
        organization_id=organization_id,
        execution_type=execution_type_value,
        entity_id=uuid_module.UUID(entity_id) if entity_id else None,
        entity_name=entity_name,
        runner_name=runner_name,
        trigger_source=trigger_source,
        trigger_metadata={
            "job_id": job["id"],
            "job_name": job.get("name"),
            "trigger_type": trigger_type,
            **trigger_metadata,
        },
        user_id=trigger_metadata.get("user_id"),
        user_email=trigger_metadata.get("triggered_by") or trigger_metadata.get("user_email"),
        user_name=trigger_metadata.get("user_name"),
        user_avatar=trigger_metadata.get("user_avatar"),
        status="pending",
        prompt=prompt if parameters else job.get("prompt_template", ""),
        execution_metadata={
            "job_id": job["id"],
            "job_name": job.get("name"),
            "trigger_type": trigger_type,
            **trigger_metadata,
        },
        created_at=now,
        updated_at=now,
    )

    db.add(execution)
    db.commit()

    logger.info(
        "created_placeholder_execution",
        execution_id=execution_id,
        job_id=job["id"],
        organization_id=organization_id,
    )

    # VALIDATION: Verify job still exists before creating junction record
    # This prevents foreign key constraint violations if job was deleted
    try:
        await validate_job_exists(
            db=db,
            job_id=job["id"],
            organization_id=organization_id,
            logger_context={
                "execution_id": execution_id,
                "trigger_type": trigger_type,
                "source": "start_job_execution",
            }
        )
    except HTTPException as validation_error:
        logger.error(
            "job_validation_failed_during_execution_start",
            job_id=job["id"],
            execution_id=execution_id,
            error_code=validation_error.status_code,
            error_detail=validation_error.detail,
        )
        # Clean up the execution record we just created
        db.query(Execution).filter(Execution.id == execution_uuid).delete()
        db.commit()
        logger.info("cleaned_up_orphaned_execution", execution_id=execution_id)
        raise

    # Create job_executions junction record to track this execution was triggered by a job
    job_execution = JobExecution(
        id=f"jobexec_{uuid_module.uuid4()}",
        job_id=job["id"],
        execution_id=execution_uuid,
        organization_id=organization_id,
        trigger_type=trigger_type,
        trigger_metadata=trigger_metadata,
        execution_status="pending",
        created_at=now,
    )

    try:
        db.add(job_execution)
        db.commit()
        logger.info(
            "job_execution_junction_created",
            job_id=job["id"],
            execution_id=execution_id,
        )
    except Exception as e:
        logger.error(
            "failed_to_create_job_execution_junction",
            error=str(e),
            execution_id=execution_id,
            job_id=job["id"],
        )
        db.rollback()
        # Clean up the execution record if junction record creation fails
        db.query(Execution).filter(Execution.id == execution_uuid).delete()
        db.commit()
        logger.info("cleaned_up_orphaned_execution_after_junction_failure", execution_id=execution_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job execution record: {str(e)}"
        )

    # Prepare workflow input based on entity type
    workflow_class = None
    workflow_input = None

    if planning_mode == "predefined_agent" and entity_type == "agent":
        # Start AgentExecutionWorkflow
        workflow_class = AgentExecutionWorkflow

        # Get agent details using SQLAlchemy
        agent_obj = db.query(Agent).filter(Agent.id == entity_id).first()
        if not agent_obj:
            raise ValueError(f"Agent {entity_id} not found")

        agent = model_to_dict(agent_obj)
        agent_config = agent.get("configuration", {}) or {}

        # Resolve execution environment properly (same as regular agent executions)
        # Token is None for job executions (no user context)
        try:
            resolved_env = await resolve_agent_execution_environment_internal(
                agent_id=entity_id,
                org_id=organization_id,
                db=db,
                token=None  # No user token for job executions
            )
        except Exception as e:
            logger.error(
                "failed_to_resolve_execution_environment_for_job",
                agent_id=entity_id,
                job_id=job["id"],
                error=str(e)
            )
            # Fallback to empty if resolution fails
            resolved_env = {"mcp_servers": {}}

        workflow_input = {
            "execution_id": execution_id,
            "agent_id": entity_id,
            "organization_id": organization_id,
            "prompt": prompt,
            "system_prompt": job.get("system_prompt") or agent_config.get("system_prompt"),
            "model_id": agent.get("model_id"),
            "model_config": agent.get("model_config", {}) or {},
            "agent_config": {**agent_config, **(job.get("config", {}) or {})},
            "mcp_servers": resolved_env.get("mcp_servers", {}),
            "user_metadata": {
                "job_id": job["id"],
                "job_name": job.get("name"),
                "trigger_type": trigger_type,
                **trigger_metadata,
            },
            "runtime_type": agent.get("runtime") or agent_config.get("runtime") or "default",
        }

    elif planning_mode == "predefined_team" and entity_type == "team":
        # Start TeamExecutionWorkflow
        workflow_class = TeamExecutionWorkflow

        # Get team details using SQLAlchemy
        team_obj = db.query(Team).filter(Team.id == entity_id).first()
        team = model_to_dict(team_obj) if team_obj else {}
        team_config = team.get("configuration", {}) or {}

        workflow_input = {
            "execution_id": execution_id,
            "team_id": entity_id,
            "organization_id": organization_id,
            "prompt": prompt,
            "system_prompt": job.get("system_prompt"),
            "config": job.get("config", {}) or {},
            "user_metadata": {
                "job_id": job["id"],
                "job_name": job.get("name"),
                "trigger_type": trigger_type,
                **trigger_metadata,
            },
            "runtime_type": team.get("runtime") or team_config.get("runtime") or "default",
        }
    else:
        raise ValueError(f"Unsupported planning_mode '{planning_mode}' or entity_type '{entity_type}'")

    # Start the workflow
    # Use standard workflow ID format for consistency with direct agent/team executions
    if entity_type == "agent":
        workflow_id = f"agent-execution-{execution_id}"
    elif entity_type == "team":
        workflow_id = f"team-execution-{execution_id}"
    else:
        # Fallback for other entity types
        workflow_id = f"job-{job['id']}-{trigger_type}-{uuid_module.uuid4()}"

    await temporal_client.start_workflow(
        workflow_class.run,
        workflow_input,
        id=workflow_id,
        task_queue=worker_queue_name,
    )

    logger.info(
        "job_execution_started",
        job_id=job["id"],
        workflow_id=workflow_id,
        execution_id=execution_id,
        trigger_type=trigger_type,
        workflow_name=workflow_class.__name__,
        worker_queue=worker_queue_name,
    )

    return workflow_id, execution_id


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify HMAC signature for webhook payload.

    Args:
        payload: Raw request body bytes
        signature: Signature from X-Webhook-Signature header
        secret: Webhook secret from database

    Returns:
        True if signature is valid
    """
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)


async def create_temporal_schedule(
    job_id: str,
    organization_id: str,
    job_data: dict,
    cron_schedule: str,
    cron_timezone: str,
    db: Session,
    token: str = "",
) -> str:
    """
    Create Temporal Schedule for cron-based job.

    The schedule directly triggers AgentExecutionWorkflow or TeamExecutionWorkflow
    based on the job's planning_mode and entity configuration.

    Args:
        job_id: Job ID
        organization_id: Organization ID
        job_data: Complete job data including entity info, prompt, config
        cron_schedule: Cron expression
        cron_timezone: Timezone for schedule
        db: SQLAlchemy database session
        token: Authentication token for fetching Temporal credentials (defaults to empty/fallback)

    Returns:
        Temporal Schedule ID
    """
    # Get org-specific Temporal credentials and client
    from control_plane_api.app.lib.temporal_credentials_service import get_temporal_credentials_for_org
    from control_plane_api.app.lib.temporal_client import get_temporal_client_for_org

    temporal_credentials = await get_temporal_credentials_for_org(
        org_id=organization_id,
        token=token,
        use_fallback=True  # Enable fallback for schedule operations
    )

    client = await get_temporal_client_for_org(
        namespace=temporal_credentials["namespace"],
        api_key=temporal_credentials["api_key"],
        host=temporal_credentials["host"],
    )
    schedule_id = f"job-{job_id}"

    try:
        # Determine execution type from planning_mode
        planning_mode = job_data.get("planning_mode")
        entity_type = job_data.get("entity_type")
        entity_id = job_data.get("entity_id")

        # Get the appropriate worker queue based on job configuration
        executor_type = job_data.get("executor_type", "auto")
        requested_queue = job_data.get("worker_queue_name")
        requested_env = job_data.get("environment_name")

        logger.info(
            "resolving_worker_queue_for_job",
            job_id=job_id,
            executor_type=executor_type,
            requested_queue=requested_queue,
            requested_env=requested_env,
        )

        worker_queue_name, _ = await select_worker_queue(
            organization_id=organization_id,
            executor_type=executor_type,
            worker_queue_name=requested_queue,
            environment_name=requested_env,
        )

        if not worker_queue_name:
            # Provide detailed error message based on executor type
            if executor_type == "specific_queue":
                error_detail = (
                    f"Requested worker queue '{requested_queue}' has no active workers. "
                    f"Please start workers on this queue before creating the job."
                )
            elif executor_type == "environment" and requested_env:
                error_detail = (
                    f"No active workers found in environment '{requested_env}'. "
                    f"Please start workers in this environment before creating the job."
                )
            else:
                error_detail = (
                    f"No workers are currently running in your organization. "
                    f"Please start at least one worker before creating scheduled jobs."
                )

            logger.error(
                "no_workers_available_for_job",
                job_id=job_id,
                executor_type=executor_type,
                requested_queue=requested_queue,
                requested_env=requested_env,
            )
            raise ValueError(error_detail)

        logger.info(
            "resolved_worker_queue_for_cron_job",
            job_id=job_id,
            worker_queue=worker_queue_name,
            planning_mode=planning_mode,
            entity_type=entity_type,
        )

        # Prepare workflow input based on entity type
        # Use ScheduledJobWrapperWorkflow which handles execution_id generation
        workflow_name = "ScheduledJobWrapperWorkflow"
        workflow_input = None

        if planning_mode == "predefined_agent" and entity_type == "agent":
            # Get agent details using SQLAlchemy
            agent_obj = db.query(Agent).filter(Agent.id == entity_id).first()
            if not agent_obj:
                raise ValueError(f"Agent {entity_id} not found")

            agent = model_to_dict(agent_obj)
            agent_config = agent.get("configuration", {}) or {}

            # Resolve execution environment properly (same as regular agent executions)
            # Token is None for cron job schedules (no user context)
            try:
                resolved_env = await resolve_agent_execution_environment_internal(
                    agent_id=entity_id,
                    org_id=organization_id,
                    db=db,
                    token=None  # No user token for cron schedules
                )
            except Exception as e:
                logger.error(
                    "failed_to_resolve_execution_environment_for_cron_job",
                    agent_id=entity_id,
                    job_id=job_id,
                    error=str(e)
                )
                # Fallback to empty if resolution fails
                resolved_env = {"mcp_servers": {}}

            workflow_input = {
                "execution_id": None,  # Will be generated by wrapper workflow
                "agent_id": entity_id,
                "organization_id": organization_id,
                "prompt": job_data.get("prompt_template", ""),
                "system_prompt": job_data.get("system_prompt") or agent_config.get("system_prompt"),
                "model_id": agent.get("model_id"),
                "model_config": agent.get("model_config", {}) or {},
                "agent_config": {**agent_config, **(job_data.get("config", {}) or {})},
                "mcp_servers": resolved_env.get("mcp_servers", {}),
                "user_metadata": {
                    "job_id": job_id,
                    "job_name": job_data.get("name"),
                    "trigger_type": "cron",
                    "user_id": job_data.get("created_by"),
                    "user_email": job_data.get("created_by_email"),
                    "user_name": job_data.get("created_by_name"),
                },
                "runtime_type": agent.get("runtime") or agent_config.get("runtime") or "default",
            }

        elif planning_mode == "predefined_team" and entity_type == "team":
            # Get team details using SQLAlchemy
            team_obj = db.query(Team).filter(Team.id == entity_id).first()
            team = model_to_dict(team_obj) if team_obj else {}
            team_config = team.get("configuration", {}) or {}

            workflow_input = {
                "execution_id": None,  # Will be generated by wrapper workflow
                "team_id": entity_id,
                "organization_id": organization_id,
                "prompt": job_data.get("prompt_template", ""),
                "system_prompt": job_data.get("system_prompt"),
                "model_config": {},
                "team_config": {**team_config, **(job_data.get("config", {}) or {})},
                "mcp_servers": {},
                "user_metadata": {
                    "job_id": job_id,
                    "job_name": job_data.get("name"),
                    "trigger_type": "cron",
                    "user_id": job_data.get("created_by"),
                    "user_email": job_data.get("created_by_email"),
                    "user_name": job_data.get("created_by_name"),
                },
                "runtime_type": team.get("runtime") or team_config.get("runtime") or "default",
            }
        else:
            raise ValueError(f"Unsupported planning_mode '{planning_mode}' or entity_type '{entity_type}' for cron jobs")

        # Create schedule action
        action = ScheduleActionStartWorkflow(
            workflow_name,
            workflow_input,
            id=f"job-{job_id}-{{{{SCHEDULE_ID}}}}",
            task_queue=worker_queue_name,
        )

        # Parse cron expression for schedule spec
        # Temporal accepts standard 5-field cron format: minute hour day month day_of_week
        # No need to add seconds field - Temporal handles it automatically
        temporal_cron = cron_schedule

        schedule_spec = ScheduleSpec(
            cron_expressions=[temporal_cron],
            time_zone_name=cron_timezone,
        )

        # Create schedule with enhanced error handling
        try:
            logger.info(
                "creating_temporal_schedule",
                schedule_id=schedule_id,
                workflow_name=workflow_name,
                worker_queue=worker_queue_name,
                cron_expression=temporal_cron,
                timezone=cron_timezone,
                job_id=job_id,
            )

            await client.create_schedule(
                schedule_id,
                Schedule(
                    action=action,
                    spec=schedule_spec,
                    policy=SchedulePolicy(
                        overlap=ScheduleOverlapPolicy.ALLOW_ALL,
                        catchup_window=timedelta(seconds=60),  # Only catch up for recent misses
                    ),
                ),
            )

            logger.info(
                "temporal_schedule_created_successfully",
                schedule_id=schedule_id,
                job_id=job_id,
                cron_schedule=cron_schedule,
                worker_queue=worker_queue_name,
            )

            return schedule_id

        except Exception as temporal_error:
            # Enhanced error reporting for Temporal schedule creation failures
            error_msg = str(temporal_error)
            error_type = type(temporal_error).__name__

            logger.error(
                "temporal_schedule_creation_failed",
                error=error_msg,
                error_type=error_type,
                schedule_id=schedule_id,
                job_id=job_id,
                worker_queue=worker_queue_name,
                workflow_name=workflow_name,
                cron_expression=temporal_cron,
            )

            # Provide actionable error messages
            if "connection" in error_msg.lower() or "unavailable" in error_msg.lower():
                detail = (
                    f"Cannot connect to Temporal server. "
                    f"Please verify TEMPORAL_HOST and TEMPORAL_NAMESPACE are correctly configured. "
                    f"Error: {error_msg}"
                )
            elif "permission" in error_msg.lower() or "unauthorized" in error_msg.lower():
                detail = (
                    f"Insufficient permissions to create Temporal schedule. "
                    f"Please verify Temporal API key or certificate authentication. "
                    f"Error: {error_msg}"
                )
            elif "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                detail = (
                    f"Schedule '{schedule_id}' already exists. "
                    f"Please check if this job was already scheduled. "
                    f"Error: {error_msg}"
                )
            elif "invalid cron" in error_msg.lower():
                detail = (
                    f"Invalid cron expression '{cron_schedule}'. "
                    f"Please verify the cron format is correct. "
                    f"Error: {error_msg}"
                )
            else:
                detail = f"Failed to create Temporal schedule: {error_msg}"

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=detail
            )

    except Exception as e:
        logger.error(
            "failed_to_create_temporal_schedule",
            error=str(e),
            job_id=job_id,
            cron_schedule=cron_schedule,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Temporal schedule: {str(e)}"
        )


async def delete_temporal_schedule(schedule_id: str) -> None:
    """Delete Temporal Schedule"""
    client = await get_temporal_client()

    try:
        handle = client.get_schedule_handle(schedule_id)
        await handle.delete()

        logger.info("temporal_schedule_deleted", schedule_id=schedule_id)

    except Exception as e:
        logger.error(
            "failed_to_delete_temporal_schedule",
            error=str(e),
            schedule_id=schedule_id,
        )
        # Don't raise - schedule might not exist


async def pause_temporal_schedule(schedule_id: str) -> None:
    """Pause Temporal Schedule"""
    client = await get_temporal_client()

    try:
        handle = client.get_schedule_handle(schedule_id)
        await handle.pause()

        logger.info("temporal_schedule_paused", schedule_id=schedule_id)

    except Exception as e:
        logger.error(
            "failed_to_pause_temporal_schedule",
            error=str(e),
            schedule_id=schedule_id,
        )
        raise


async def unpause_temporal_schedule(schedule_id: str) -> None:
    """Unpause Temporal Schedule"""
    client = await get_temporal_client()

    try:
        handle = client.get_schedule_handle(schedule_id)
        await handle.unpause()

        logger.info("temporal_schedule_unpaused", schedule_id=schedule_id)

    except Exception as e:
        logger.error(
            "failed_to_unpause_temporal_schedule",
            error=str(e),
            schedule_id=schedule_id,
        )
        raise


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Create a new job.

    Jobs can be triggered via:
    - Cron schedule (requires cron_schedule parameter)
    - Webhook (generates unique webhook URL)
    - Manual API trigger

    **Request Body:**
    - name: Job name
    - trigger_type: "cron", "webhook", or "manual"
    - cron_schedule: Cron expression (required for cron trigger)
    - planning_mode: "on_the_fly", "predefined_agent", "predefined_team", or "predefined_workflow"
    - entity_id: Entity ID (required for predefined modes)
    - prompt_template: Prompt template with {{variable}} placeholders
    - executor_type: "auto", "specific_queue", or "environment"
    """
    organization_id = organization["id"]

    logger.info(
        "creating_job",
        organization_id=organization_id,
        name=job_data.name,
        trigger_type=job_data.trigger_type,
    )

    try:
        job_id = f"job_{uuid_module.uuid4()}"
        now = datetime.now(timezone.utc)

        # Generate webhook URL if trigger_type is webhook
        webhook_url_path = None
        webhook_secret = None
        if job_data.trigger_type == "webhook":
            webhook_url_path = f"/api/v1/jobs/webhook/{generate_webhook_path()}"
            webhook_secret = generate_webhook_secret()

        # If entity_id is provided, fetch entity name using SQLAlchemy
        entity_name = None
        if job_data.entity_id and job_data.entity_type:
            try:
                if job_data.entity_type == "agent":
                    entity_obj = db.query(Agent).filter(
                        Agent.id == job_data.entity_id,
                        Agent.organization_id == organization_id
                    ).first()
                elif job_data.entity_type == "team":
                    entity_obj = db.query(Team).filter(
                        Team.id == job_data.entity_id,
                        Team.organization_id == organization_id
                    ).first()
                else:
                    entity_obj = None
                if entity_obj:
                    entity_name = entity_obj.name
            except Exception as e:
                logger.warning("failed_to_get_entity_name", error=str(e))

        # Create Job model instance
        job = Job(
            id=job_id,
            organization_id=organization_id,
            name=job_data.name,
            description=job_data.description,
            enabled=job_data.enabled,
            status="active" if job_data.enabled else "disabled",
            trigger_type=job_data.trigger_type,
            cron_schedule=job_data.cron_schedule,
            cron_timezone=job_data.cron_timezone or "UTC",
            webhook_url_path=webhook_url_path,
            webhook_secret=webhook_secret,
            temporal_schedule_id=None,
            planning_mode=job_data.planning_mode,
            entity_type=job_data.entity_type,
            entity_id=job_data.entity_id,
            entity_name=entity_name,
            prompt_template=job_data.prompt_template,
            system_prompt=job_data.system_prompt,
            executor_type=job_data.executor_type,
            worker_queue_name=job_data.worker_queue_name,
            environment_name=job_data.environment_name,
            config=job_data.config or {},
            execution_environment=job_data.execution_environment.model_dump() if job_data.execution_environment else {},
            total_executions=0,
            successful_executions=0,
            failed_executions=0,
            execution_history=[],
            last_execution_id=None,
            last_execution_at=None,
            next_execution_at=None,
            last_triggered_at=None,
            created_by=organization.get("user_id"),
            updated_by=None,
            created_at=now,
            updated_at=now,
        )

        # Create Temporal Schedule for cron jobs (need job_record dict for schedule creation)
        if job_data.trigger_type == "cron" and job_data.enabled:
            job_record = model_to_dict(job)
            job_record["created_by_email"] = organization.get("user_email")
            job_record["created_by_name"] = organization.get("user_name")

            temporal_schedule_id = await create_temporal_schedule(
                job_id=job_id,
                organization_id=organization_id,
                job_data=job_record,
                cron_schedule=job_data.cron_schedule,
                cron_timezone=job_data.cron_timezone or "UTC",
                db=db,
            )
            job.temporal_schedule_id = temporal_schedule_id

            # Calculate next execution time
            cron_iter = croniter(job_data.cron_schedule, datetime.now(timezone.utc))
            next_execution = cron_iter.get_next(datetime)
            job.next_execution_at = next_execution

        # Insert job into database
        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(
            "job_created",
            job_id=job_id,
            name=job_data.name,
            trigger_type=job_data.trigger_type,
        )

        # Build response
        response_data = model_to_dict(job)
        response_data["created_by_email"] = organization.get("user_email")
        response_data["created_by_name"] = organization.get("user_name")

        # Add full webhook URL to response
        if webhook_url_path:
            response_data["webhook_url"] = f"{str(request.base_url).rstrip('/')}{webhook_url_path}"

        return JobResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "failed_to_create_job",
            error=str(e),
            organization_id=organization_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
    enabled: Optional[bool] = None,
    trigger_type: Optional[str] = None,
):
    """
    List all jobs for the organization.

    **Query Parameters:**
    - enabled: Filter by enabled status (true/false)
    - trigger_type: Filter by trigger type ("cron", "webhook", "manual")
    """
    organization_id = organization["id"]

    try:
        # Build query using SQLAlchemy
        query = db.query(Job).filter(Job.organization_id == organization_id)

        if enabled is not None:
            query = query.filter(Job.enabled == enabled)

        if trigger_type:
            query = query.filter(Job.trigger_type == trigger_type)

        job_objects = query.order_by(desc(Job.created_at)).all()

        # Build responses with full webhook URLs and enrich with user emails
        base_url = str(request.base_url).rstrip("/")

        # Collect unique user IDs
        user_ids = set()
        for job_obj in job_objects:
            if job_obj.created_by:
                user_ids.add(job_obj.created_by)
            if job_obj.updated_by:
                user_ids.add(job_obj.updated_by)

        # Fetch user details from Kubiya API
        user_emails = {}
        if user_ids:
            try:
                import httpx
                org_id = organization_id

                kubiya_url = "https://api.kubiya.ai/api/v2/users?limit=0&page=1&status=active"

                headers = {
                    "Accept": "application/json",
                    "X-Organization-ID": org_id,
                    "X-Kubiya-Client": "agentmesh-backend",
                }

                auth_header = request.headers.get("authorization")
                if auth_header:
                    headers["Authorization"] = auth_header

                async with httpx.AsyncClient() as http_client:
                    response = await http_client.get(kubiya_url, headers=headers, timeout=10.0)
                    if response.status_code == 200:
                        data = response.json()
                        users = data.get("items", [])
                        for user in users:
                            user_uuid = user.get("uuid") or user.get("_id") or user.get("id")
                            if user_uuid in user_ids:
                                user_emails[user_uuid] = user.get("email") or user.get("name") or user_uuid
                    else:
                        logger.warning("kubiya_api_users_fetch_failed", status_code=response.status_code)
            except Exception as e:
                logger.warning("failed_to_fetch_user_emails", error=str(e))

        jobs = []
        for job_obj in job_objects:
            job_data = model_to_dict(job_obj)
            if job_obj.webhook_url_path:
                job_data["webhook_url"] = f"{base_url}{job_obj.webhook_url_path}"

            # Enrich with user email if available
            if job_obj.created_by and job_obj.created_by in user_emails:
                job_data["created_by_email"] = user_emails[job_obj.created_by]
            if job_obj.updated_by and job_obj.updated_by in user_emails:
                job_data["updated_by_email"] = user_emails[job_obj.updated_by]

            jobs.append(JobResponse(**job_data))

        return jobs

    except Exception as e:
        logger.error(
            "failed_to_list_jobs",
            error=str(e),
            organization_id=organization_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}"
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Get job details by ID"""
    organization_id = organization["id"]

    try:
        job_obj = db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == organization_id
        ).first()

        if not job_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        job_data = model_to_dict(job_obj)

        # Add full webhook URL
        if job_obj.webhook_url_path:
            base_url = str(request.base_url).rstrip("/")
            job_data["webhook_url"] = f"{base_url}{job_obj.webhook_url_path}"

        return JobResponse(**job_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "failed_to_get_job",
            error=str(e),
            job_id=job_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job: {str(e)}"
        )


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_data: JobUpdate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Update job configuration.

    **Note:** Updating cron_schedule will recreate the Temporal Schedule.
    """
    organization_id = organization["id"]

    try:
        # Fetch existing job using SQLAlchemy
        job_obj = db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == organization_id
        ).first()

        if not job_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        existing_job = model_to_dict(job_obj)

        # Build update data
        update_data = {}
        for field, value in job_data.model_dump(exclude_unset=True).items():
            if value is not None:
                if field == "execution_environment" and isinstance(value, ExecutionEnvironment):
                    update_data[field] = value.model_dump()
                else:
                    update_data[field] = value

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        update_data["updated_by"] = organization.get("user_id")
        update_data["updated_at"] = datetime.now(timezone.utc)

        # If entity_id is being updated, fetch entity name using SQLAlchemy
        if "entity_id" in update_data:
            entity_type = update_data.get("entity_type", existing_job.get("entity_type"))
            entity_id = update_data["entity_id"]
            try:
                if entity_type == "agent":
                    entity_obj = db.query(Agent).filter(
                        Agent.id == entity_id,
                        Agent.organization_id == organization_id
                    ).first()
                elif entity_type == "team":
                    entity_obj = db.query(Team).filter(
                        Team.id == entity_id,
                        Team.organization_id == organization_id
                    ).first()
                else:
                    entity_obj = None
                if entity_obj:
                    update_data["entity_name"] = entity_obj.name
            except Exception as e:
                logger.warning("failed_to_get_entity_name_during_update", error=str(e))

        # Handle schedule updates - recreate if any workflow input fields change
        schedule_affecting_fields = {
            "cron_schedule", "cron_timezone", "entity_id", "entity_type",
            "prompt_template", "system_prompt", "config"
        }

        should_recreate_schedule = (
            existing_job.get("trigger_type") == "cron" and
            existing_job.get("enabled", True) and
            existing_job.get("temporal_schedule_id") and
            any(field in update_data for field in schedule_affecting_fields)
        )

        if should_recreate_schedule:
            logger.info(
                "recreating_temporal_schedule_due_to_updates",
                job_id=job_id,
                updated_fields=[f for f in update_data.keys() if f in schedule_affecting_fields],
            )

            # Delete existing schedule
            try:
                await delete_temporal_schedule(existing_job["temporal_schedule_id"])
            except Exception as delete_error:
                logger.error(
                    "failed_to_delete_schedule_during_update",
                    job_id=job_id,
                    schedule_id=existing_job["temporal_schedule_id"],
                    error=str(delete_error),
                )

            # Merge existing job data with updates for schedule
            updated_job_data = {**existing_job, **update_data}

            # Create new schedule
            try:
                temporal_schedule_id = await create_temporal_schedule(
                    job_id=job_id,
                    organization_id=organization_id,
                    job_data=updated_job_data,
                    cron_schedule=update_data.get("cron_schedule", existing_job.get("cron_schedule")),
                    cron_timezone=update_data.get("cron_timezone", existing_job.get("cron_timezone", "UTC")),
                    db=db,
                )
                update_data["temporal_schedule_id"] = temporal_schedule_id

                # Calculate next execution time if cron_schedule changed
                if "cron_schedule" in update_data:
                    cron_iter = croniter(update_data["cron_schedule"], datetime.now(timezone.utc))
                    next_execution = cron_iter.get_next(datetime)
                    update_data["next_execution_at"] = next_execution

                logger.info(
                    "temporal_schedule_recreated_successfully",
                    job_id=job_id,
                    new_schedule_id=temporal_schedule_id,
                )
            except Exception as create_error:
                logger.error(
                    "failed_to_recreate_schedule_during_update",
                    job_id=job_id,
                    error=str(create_error),
                )
                update_data["temporal_schedule_id"] = None
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to recreate Temporal schedule: {str(create_error)}"
                )

        # Update job using SQLAlchemy
        for key, value in update_data.items():
            if hasattr(job_obj, key):
                setattr(job_obj, key, value)

        db.commit()
        db.refresh(job_obj)

        logger.info(
            "job_updated",
            job_id=job_id,
            updated_fields=list(update_data.keys()),
        )

        job_data_response = model_to_dict(job_obj)

        # Add full webhook URL
        if job_obj.webhook_url_path:
            base_url = str(request.base_url).rstrip("/")
            job_data_response["webhook_url"] = f"{base_url}{job_obj.webhook_url_path}"

        return JobResponse(**job_data_response)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "failed_to_update_job",
            error=str(e),
            job_id=job_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update job: {str(e)}"
        )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Delete a job and its Temporal Schedule"""
    organization_id = organization["id"]

    try:
        # Fetch job details for audit logging using SQLAlchemy
        job_obj = db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == organization_id
        ).first()

        if not job_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        # Enhanced logging for job deletion audit trail
        logger.info(
            "job_deletion_initiated",
            job_id=job_id,
            job_name=job_obj.name,
            organization_id=organization_id,
            temporal_schedule_id=job_obj.temporal_schedule_id,
            enabled=job_obj.enabled,
            trigger_type=job_obj.trigger_type,
        )

        # Delete Temporal Schedule
        if job_obj.temporal_schedule_id:
            try:
                await delete_temporal_schedule(job_obj.temporal_schedule_id)
                logger.info(
                    "temporal_schedule_deleted",
                    job_id=job_id,
                    schedule_id=job_obj.temporal_schedule_id,
                )
            except Exception as temporal_error:
                # Log but don't fail - we still want to delete from DB
                logger.error(
                    "failed_to_delete_temporal_schedule",
                    job_id=job_id,
                    schedule_id=job_obj.temporal_schedule_id,
                    error=str(temporal_error),
                    note="Job will be deleted from DB anyway. Run cleanup script to remove orphaned schedule.",
                )

        # Delete job from database using SQLAlchemy
        job_name = job_obj.name  # Store before deletion
        db.delete(job_obj)
        db.commit()

        logger.info(
            "job_deleted_successfully",
            job_id=job_id,
            job_name=job_name,
            organization_id=organization_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "failed_to_delete_job",
            error=str(e),
            job_id=job_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job: {str(e)}"
        )


@router.post("/{job_id}/trigger", response_model=JobTriggerResponse)
async def trigger_job(
    job_id: str,
    trigger_data: JobTriggerRequest,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Manually trigger a job execution.

    **Request Body:**
    - parameters: Dictionary of parameters to substitute in prompt template
    - config_override: Optional config overrides for this execution
    """
    organization_id = organization["id"]

    try:
        # Validate job exists and is enabled using SQLAlchemy
        job_obj = db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == organization_id
        ).first()

        if not job_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        job = model_to_dict(job_obj)

        if not job.get("enabled"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job is disabled"
            )

        # Apply config overrides if provided
        if trigger_data.config_override:
            job = {**job, "config": {**(job.get("config") or {}), **trigger_data.config_override}}

        # Start the job execution directly (same as UI does)
        workflow_id, execution_id = await start_job_execution(
            job=job,
            organization_id=organization_id,
            trigger_type="manual",
            trigger_metadata={
                "triggered_by": organization.get("user_email"),
                "user_id": organization.get("user_id"),
                "user_email": organization.get("user_email"),
                "user_name": organization.get("user_name"),
            },
            db=db,
            token=request.state.kubiya_token,
            parameters=trigger_data.parameters,
        )

        return JobTriggerResponse(
            job_id=job_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            status="started",
            message="Job execution started successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "failed_to_trigger_job",
            error=str(e),
            job_id=job_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger job: {str(e)}"
        )


@router.post("/{job_id}/enable", response_model=JobResponse)
async def enable_job(
    job_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Enable a job and unpause its Temporal Schedule"""
    organization_id = organization["id"]

    try:
        # Fetch job using SQLAlchemy
        job_obj = db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == organization_id
        ).first()

        if not job_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        job = model_to_dict(job_obj)

        # Unpause Temporal Schedule if it exists
        if job_obj.temporal_schedule_id:
            try:
                await unpause_temporal_schedule(job_obj.temporal_schedule_id)
                logger.info(
                    "temporal_schedule_unpaused",
                    job_id=job_id,
                    schedule_id=job_obj.temporal_schedule_id,
                )
            except Exception as temporal_error:
                logger.error(
                    "failed_to_unpause_temporal_schedule",
                    job_id=job_id,
                    schedule_id=job_obj.temporal_schedule_id,
                    error=str(temporal_error),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to unpause Temporal schedule: {str(temporal_error)}"
                )

            # Update job status
            job_obj.enabled = True
            job_obj.status = "active"
            job_obj.updated_at = datetime.now(timezone.utc)

        elif job_obj.trigger_type == "cron":
            # Create schedule if it doesn't exist
            try:
                temporal_schedule_id = await create_temporal_schedule(
                    job_id=job_id,
                    organization_id=organization_id,
                    job_data=job,
                    cron_schedule=job_obj.cron_schedule,
                    cron_timezone=job_obj.cron_timezone or "UTC",
                    db=db,
                )
            except Exception as create_error:
                logger.error(
                    "failed_to_create_temporal_schedule_during_enable",
                    job_id=job_id,
                    error=str(create_error),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create Temporal schedule: {str(create_error)}"
                )

            # Update job with schedule ID
            job_obj.temporal_schedule_id = temporal_schedule_id
            job_obj.enabled = True
            job_obj.status = "active"
            job_obj.updated_at = datetime.now(timezone.utc)

            # Calculate next execution time
            cron_iter = croniter(job_obj.cron_schedule, datetime.now(timezone.utc))
            next_execution = cron_iter.get_next(datetime)
            job_obj.next_execution_at = next_execution
        else:
            # Just enable the job (non-cron jobs)
            job_obj.enabled = True
            job_obj.status = "active"
            job_obj.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(job_obj)

        logger.info("job_enabled", job_id=job_id)

        job_data = model_to_dict(job_obj)
        if job_obj.webhook_url_path:
            base_url = str(request.base_url).rstrip("/")
            job_data["webhook_url"] = f"{base_url}{job_obj.webhook_url_path}"

        return JobResponse(**job_data)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "failed_to_enable_job",
            error=str(e),
            job_id=job_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable job: {str(e)}"
        )


@router.post("/{job_id}/disable", response_model=JobResponse)
async def disable_job(
    job_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Disable a job and pause its Temporal Schedule"""
    organization_id = organization["id"]

    try:
        # Fetch job using SQLAlchemy
        job_obj = db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == organization_id
        ).first()

        if not job_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        # Pause Temporal Schedule if it exists
        if job_obj.temporal_schedule_id:
            try:
                await pause_temporal_schedule(job_obj.temporal_schedule_id)
                logger.info(
                    "temporal_schedule_paused",
                    job_id=job_id,
                    schedule_id=job_obj.temporal_schedule_id,
                )
            except Exception as temporal_error:
                logger.error(
                    "failed_to_pause_temporal_schedule",
                    job_id=job_id,
                    schedule_id=job_obj.temporal_schedule_id,
                    error=str(temporal_error),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to pause Temporal schedule: {str(temporal_error)}"
                )

        # Update job status using SQLAlchemy
        job_obj.enabled = False
        job_obj.status = "disabled"
        job_obj.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(job_obj)

        logger.info("job_disabled", job_id=job_id)

        job_data = model_to_dict(job_obj)
        if job_obj.webhook_url_path:
            base_url = str(request.base_url).rstrip("/")
            job_data["webhook_url"] = f"{base_url}{job_obj.webhook_url_path}"

        return JobResponse(**job_data)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "failed_to_disable_job",
            error=str(e),
            job_id=job_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable job: {str(e)}"
        )


@router.get("/{job_id}/executions", response_model=JobExecutionHistoryResponse)
async def get_job_executions(
    job_id: str,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """
    Get execution history for a job.

    **Query Parameters:**
    - limit: Maximum number of executions to return (default: 50)
    - offset: Number of executions to skip (default: 0)
    """
    from sqlalchemy.orm import joinedload
    from sqlalchemy import func

    organization_id = organization["id"]

    try:
        # Fetch job executions with joined execution data using SQLAlchemy
        job_execution_objects = db.query(JobExecution).options(
            joinedload(JobExecution.execution)
        ).filter(
            JobExecution.job_id == job_id,
            JobExecution.organization_id == organization_id
        ).order_by(desc(JobExecution.created_at)).offset(offset).limit(limit).all()

        # Count total executions
        total_count = db.query(func.count(JobExecution.id)).filter(
            JobExecution.job_id == job_id,
            JobExecution.organization_id == organization_id
        ).scalar() or 0

        executions = []
        for job_exec in job_execution_objects:
            execution = job_exec.execution
            execution_data = model_to_dict(execution) if execution else {}
            executions.append(
                JobExecutionHistoryItem(
                    execution_id=str(execution.id) if execution else None,
                    trigger_type=job_exec.trigger_type,
                    status=execution_data.get("status"),
                    started_at=execution_data.get("started_at"),
                    completed_at=execution_data.get("completed_at"),
                    duration_ms=job_exec.execution_duration_ms,
                    error_message=execution_data.get("error_message"),
                    trigger_metadata=execution_data.get("trigger_metadata"),
                )
            )

        return JobExecutionHistoryResponse(
            job_id=job_id,
            total_count=total_count,
            executions=executions,
        )

    except Exception as e:
        logger.error(
            "failed_to_get_job_executions",
            error=str(e),
            job_id=job_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job executions: {str(e)}"
        )


@router.post("/webhook/{webhook_path}", response_model=JobTriggerResponse)
async def trigger_webhook(
    webhook_path: str,
    payload: WebhookPayload,
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Trigger a job via webhook.

    **Security:**
    - Requires HMAC signature in X-Webhook-Signature header
    - Signature format: hex(HMAC-SHA256(secret, request_body))

    **Request Body:**
    - parameters: Dictionary of parameters to substitute in prompt template
    - config_override: Optional config overrides for this execution
    - metadata: Additional metadata for this trigger
    """
    try:
        # Fetch job by webhook path using SQLAlchemy
        webhook_url_path = f"/api/v1/jobs/webhook/{webhook_path}"
        job_obj = db.query(Job).filter(
            Job.webhook_url_path == webhook_url_path
        ).first()

        if not job_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )

        job = model_to_dict(job_obj)

        # Verify webhook signature
        if not x_webhook_signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-Webhook-Signature header"
            )

        # Get raw request body for signature verification
        body = await request.body()
        if not verify_webhook_signature(body, x_webhook_signature, job_obj.webhook_secret):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

        # Validate job is enabled
        if not job_obj.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job is disabled"
            )

        # Apply config overrides if provided
        if payload.config_override:
            job = {**job, "config": {**(job.get("config") or {}), **payload.config_override}}

        # Start the job execution directly (same as UI does)
        # Include webhook payload in trigger_metadata so agent can access it
        # Extract user info from metadata if provided, otherwise mark as external
        webhook_metadata = payload.metadata or {}

        # For webhooks, get a worker token from the organization's environment
        # This allows webhooks to use org-specific Temporal credentials
        from control_plane_api.app.models.environment import Environment
        env = db.query(Environment).filter(
            Environment.organization_id == job["organization_id"],
            Environment.status == "ready"
        ).first()

        # Use worker token if available, otherwise empty (will fallback to env vars)
        webhook_token = env.worker_token if env and env.worker_token else ""

        workflow_id, execution_id = await start_job_execution(
            job=job,
            organization_id=job["organization_id"],
            trigger_type="webhook",
            trigger_metadata={
                "webhook_path": webhook_path,
                "webhook_payload": {
                    "parameters": payload.parameters or {},
                    "config_override": payload.config_override or {},
                    "metadata": webhook_metadata,
                },
                "parameters": payload.parameters or {},
                "metadata": webhook_metadata,
                "triggered_by": webhook_metadata.get("user_email") or webhook_metadata.get("triggered_by") or "webhook",
                "user_id": webhook_metadata.get("user_id"),
                "user_email": webhook_metadata.get("user_email"),
                "user_name": webhook_metadata.get("user_name"),
            },
            db=db,
            token=webhook_token,  # Use org's worker token for authentication
            parameters=payload.parameters,
        )

        return JobTriggerResponse(
            job_id=job["id"],
            workflow_id=workflow_id,
            execution_id=execution_id,
            status="started",
            message="Job execution started successfully via webhook",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "failed_to_trigger_webhook",
            error=str(e),
            webhook_path=webhook_path,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger webhook: {str(e)}"
        )
