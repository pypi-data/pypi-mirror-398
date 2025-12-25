"""
Activities for job execution tracking.

These activities handle creating execution records for scheduled jobs via HTTP API.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from temporalio import activity
from temporalio.exceptions import ApplicationError
import structlog

logger = structlog.get_logger()


@dataclass
class ActivityCreateJobExecutionInput:
    """Input for creating job execution records"""
    execution_id: str
    job_id: Optional[str]
    organization_id: str
    entity_type: str  # "agent" or "team"
    entity_id: Optional[str]
    prompt: str
    trigger_type: str  # "cron", "webhook", "manual"
    trigger_metadata: Dict[str, Any]


@activity.defn
async def create_job_execution_record(input: ActivityCreateJobExecutionInput) -> dict:
    """
    Create execution and job_executions records for a scheduled job via HTTP API.

    This activity calls the Control Plane API (not Supabase directly) to:
    1. Create execution record in executions table
    2. Create job_executions junction record
    3. Update job execution tracking

    Args:
        input: Execution creation input

    Returns:
        Dict with execution_id and status
    """
    from control_plane_api.worker.control_plane_client import get_control_plane_client
    import httpx

    client = get_control_plane_client()

    logger.info(
        "creating_job_execution_records_via_http",
        execution_id=input.execution_id,
        job_id=input.job_id,
        trigger_type=input.trigger_type,
    )

    try:
        # Prepare request payload
        payload = {
            "execution_id": input.execution_id,
            "job_id": input.job_id,
            "entity_type": input.entity_type,
            "entity_id": input.entity_id,
            "prompt": input.prompt,
            "trigger_type": input.trigger_type,
            "trigger_metadata": input.trigger_metadata,
        }

        # Call Control Plane API
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                f"{client.base_url}/api/v1/executions/job-executions",
                json=payload,
                headers={"Authorization": f"Bearer {client.api_key}"},
                timeout=30.0,
            )

        if response.status_code == 201:
            result = response.json()
            logger.info(
                "created_job_execution_records_via_http",
                execution_id=input.execution_id,
                job_id=input.job_id,
            )
            return result
        else:
            logger.error(
                "failed_to_create_job_execution_records_via_http",
                status_code=response.status_code,
                execution_id=input.execution_id,
                job_id=input.job_id,
                response=response.text[:500],
            )

            # Don't retry for 404 (not found) or 410 (gone) - job was deleted
            if response.status_code in [404, 410]:
                raise ApplicationError(
                    f"Job not found or deleted: HTTP {response.status_code}",
                    non_retryable=True,
                )

            # Retry for other errors (500, network issues, etc.)
            raise Exception(f"Failed to create execution record: HTTP {response.status_code}")

    except ApplicationError:
        # Re-raise ApplicationError without additional logging (already logged above)
        raise
    except Exception as e:
        logger.error(
            "error_creating_job_execution_records_via_http",
            execution_id=input.execution_id,
            job_id=input.job_id,
            error=str(e),
            exc_info=True,
        )
        raise


@activity.defn
async def update_job_execution_status(
    job_id: str,
    execution_id: str,
    status: str,
    duration_ms: Optional[int] = None,
    error_message: Optional[str] = None,
) -> dict:
    """
    Update job_executions record with execution results via HTTP API.

    This activity uses HTTP to communicate with the control plane API
    instead of directly accessing Supabase.

    Args:
        job_id: Job ID
        execution_id: Execution ID
        status: Final status (completed/failed)
        duration_ms: Execution duration in milliseconds
        error_message: Error message if failed

    Returns:
        Dict with update status
    """
    from control_plane_api.worker.control_plane_client import get_control_plane_client
    import httpx

    client = get_control_plane_client()

    logger.info(
        "updating_job_execution_status_via_http",
        job_id=job_id,
        execution_id=execution_id,
        status=status,
    )

    try:
        # Prepare request payload
        payload = {
            "status": status,
            "duration_ms": duration_ms,
            "error_message": error_message,
        }

        # Call Control Plane API
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                f"{client.base_url}/api/v1/executions/{execution_id}/job/{job_id}/status",
                json=payload,
                headers={"Authorization": f"Bearer {client.api_key}"},
                timeout=30.0,
            )

        if response.status_code in [200, 202]:
            logger.info(
                "updated_job_execution_status_via_http",
                job_id=job_id,
                execution_id=execution_id,
                status=status,
            )
            return {"job_id": job_id, "execution_id": execution_id, "status": "updated"}
        else:
            logger.error(
                "failed_to_update_job_execution_status_via_http",
                status_code=response.status_code,
                execution_id=execution_id,
                job_id=job_id,
                response=response.text[:500],
            )
            raise Exception(f"Failed to update job execution status: HTTP {response.status_code}")

    except Exception as e:
        logger.error(
            "error_updating_job_execution_status_via_http",
            job_id=job_id,
            execution_id=execution_id,
            error=str(e),
            exc_info=True,
        )
        raise
