"""
Wrapper workflow for scheduled (cron) jobs.

This workflow handles the execution_id generation and record creation
before delegating to the actual AgentExecutionWorkflow or TeamExecutionWorkflow.

This is necessary because Temporal schedules cannot dynamically generate IDs,
so we need a workflow that runs first to create the execution record.
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, Dict, Any
from temporalio import workflow
from temporalio.common import RetryPolicy
import uuid

with workflow.unsafe.imports_passed_through():
    from control_plane_api.worker.activities.agent_activities import (
        ActivityUpdateExecutionInput,
        update_execution_status,
    )
    from control_plane_api.worker.activities.job_activities import (
        create_job_execution_record,
        update_job_execution_status,
        ActivityCreateJobExecutionInput,
    )
    from control_plane_api.worker.workflows.agent_execution import (
        AgentExecutionWorkflow,
        AgentExecutionInput,
    )
    from control_plane_api.worker.workflows.team_execution import (
        TeamExecutionWorkflow,
        TeamExecutionInput,
    )


@dataclass
class ScheduledJobInput:
    """
    Input for scheduled job wrapper workflow.

    This matches the structure created by create_temporal_schedule()
    in jobs.py, but allows execution_id to be None.
    """
    execution_id: Optional[str]  # Will be generated if None
    agent_id: Optional[str] = None  # For agent jobs
    team_id: Optional[str] = None  # For team jobs
    organization_id: str = ""
    prompt: str = ""
    system_prompt: Optional[str] = None
    model_id: Optional[str] = None
    model_config: Optional[Dict[str, Any]] = None
    agent_config: Optional[Dict[str, Any]] = None
    team_config: Optional[Dict[str, Any]] = None
    mcp_servers: Optional[Dict[str, Any]] = None
    user_metadata: Optional[Dict[str, Any]] = None
    runtime_type: str = "default"

    def __post_init__(self):
        if self.model_config is None:
            self.model_config = {}
        if self.agent_config is None:
            self.agent_config = {}
        if self.team_config is None:
            self.team_config = {}
        if self.mcp_servers is None:
            self.mcp_servers = {}
        if self.user_metadata is None:
            self.user_metadata = {}


@workflow.defn
class ScheduledJobWrapperWorkflow:
    """
    Wrapper workflow that handles scheduled job execution.

    This workflow:
    1. Generates execution_id if not provided
    2. Creates execution and job_executions records via activity
    3. Delegates to AgentExecutionWorkflow or TeamExecutionWorkflow
    """

    @workflow.run
    async def run(self, input: ScheduledJobInput) -> dict:
        """
        Execute a scheduled job with proper record creation.

        Args:
            input: Scheduled job input (may have execution_id=None)

        Returns:
            Execution result dict
        """
        # Generate execution_id if not provided
        execution_id = input.execution_id
        if not execution_id:
            execution_id = workflow.uuid4()
            workflow.logger.info(
                f"Generated execution_id for scheduled job",
                extra={"execution_id": execution_id}
            )

        # Extract job metadata from user_metadata
        job_id = input.user_metadata.get("job_id") if input.user_metadata else None
        job_name = input.user_metadata.get("job_name") if input.user_metadata else None
        trigger_type = input.user_metadata.get("trigger_type", "cron") if input.user_metadata else "cron"

        workflow.logger.info(
            f"Starting scheduled job execution",
            extra={
                "execution_id": execution_id,
                "job_id": job_id,
                "job_name": job_name,
                "trigger_type": trigger_type,
                "agent_id": input.agent_id,
                "team_id": input.team_id,
                "organization_id": input.organization_id,
            }
        )

        # Create execution record via activity
        # This activity will:
        # 1. Create execution record in executions table
        # 2. Create job_executions junction record
        # 3. Update job execution counts
        try:
            await workflow.execute_activity(
                create_job_execution_record,
                ActivityCreateJobExecutionInput(
                    execution_id=execution_id,
                    job_id=job_id,
                    organization_id=input.organization_id,
                    entity_type="agent" if input.agent_id else "team",
                    entity_id=input.agent_id or input.team_id,
                    prompt=input.prompt,
                    trigger_type=trigger_type,
                    trigger_metadata=input.user_metadata or {},
                ),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            workflow.logger.info(
                f"Created execution records for scheduled job",
                extra={"execution_id": execution_id, "job_id": job_id}
            )
        except Exception as activity_error:
            error_str = str(activity_error).lower()
            workflow.logger.error(
                f"Failed to create execution records",
                extra={
                    "error": str(activity_error),
                    "execution_id": execution_id,
                    "job_id": job_id,
                }
            )

            # If job was deleted or not found, gracefully exit
            if "not found" in error_str or "deleted" in error_str or "404" in error_str or "410" in error_str:
                workflow.logger.warning(
                    f"Job deleted during scheduled execution",
                    extra={
                        "job_id": job_id,
                        "execution_id": execution_id,
                        "reason": "Job was deleted between schedule trigger and execution creation"
                    }
                )
                return {
                    "status": "cancelled",
                    "reason": "job_deleted",
                    "execution_id": execution_id,
                    "message": "Job was deleted before execution could start"
                }
            else:
                # Re-raise for other errors (will retry per RetryPolicy)
                raise

        # Now delegate to the appropriate workflow
        start_time = workflow.time()
        execution_error = None
        execution_status = "completed"

        try:
            if input.agent_id:
                # Execute as agent
                agent_input = AgentExecutionInput(
                    execution_id=execution_id,
                    agent_id=input.agent_id,
                    organization_id=input.organization_id,
                    prompt=input.prompt,
                    system_prompt=input.system_prompt,
                    model_id=input.model_id,
                    model_config=input.model_config or {},
                    agent_config=input.agent_config or {},
                    mcp_servers=input.mcp_servers or {},
                    user_metadata=input.user_metadata or {},
                    runtime_type=input.runtime_type,
                )

                # Execute as child workflow
                result = await workflow.execute_child_workflow(
                    AgentExecutionWorkflow.run,
                    agent_input,
                    id=f"agent-execution-{execution_id}",
                    task_queue=workflow.info().task_queue,
                )

            elif input.team_id:
                # Execute as team
                team_input = TeamExecutionInput(
                    execution_id=execution_id,
                    team_id=input.team_id,
                    organization_id=input.organization_id,
                    prompt=input.prompt,
                    system_prompt=input.system_prompt,
                    model_id=input.model_id,
                    model_config=input.model_config or {},
                    team_config=input.team_config or {},
                    mcp_servers=input.mcp_servers or {},
                    user_metadata=input.user_metadata or {},
                    runtime_type=input.runtime_type,
                )

                # Execute as child workflow
                result = await workflow.execute_child_workflow(
                    TeamExecutionWorkflow.run,
                    team_input,
                    id=f"team-execution-{execution_id}",
                    task_queue=workflow.info().task_queue,
                )
            else:
                raise ValueError("Either agent_id or team_id must be provided")

            workflow.logger.info(
                f"Scheduled job execution completed",
                extra={
                    "execution_id": execution_id,
                    "job_id": job_id,
                    "status": result.get("status", "unknown"),
                }
            )

        except Exception as e:
            execution_status = "failed"
            # Ensure error message is never empty
            execution_error = str(e) or repr(e) or f"{type(e).__name__}: No error details available"
            workflow.logger.error(
                f"Scheduled job execution failed",
                extra={
                    "execution_id": execution_id,
                    "job_id": job_id,
                    "error": execution_error,
                    "error_type": type(e).__name__,
                }
            )
            result = {
                "status": "failed",
                "error": execution_error,
                "execution_id": execution_id,
            }

            # Update job_executions record with failed status before re-raising
            if job_id:
                end_time = workflow.time()
                duration_ms = int((end_time - start_time) * 1000)

                try:
                    await workflow.execute_activity(
                        update_job_execution_status,
                        args=[job_id, execution_id, execution_status, duration_ms, execution_error],
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=RetryPolicy(maximum_attempts=3),
                    )

                    workflow.logger.info(
                        f"Updated job execution status to failed",
                        extra={
                            "execution_id": execution_id,
                            "job_id": job_id,
                            "status": execution_status,
                            "duration_ms": duration_ms,
                        }
                    )
                except Exception as status_update_error:
                    # Log but don't fail the workflow if status update fails
                    workflow.logger.warning(
                        f"Failed to update job execution status",
                        extra={
                            "execution_id": execution_id,
                            "job_id": job_id,
                            "error": str(status_update_error),
                        }
                    )

            # CRITICAL: Re-raise the exception so Temporal marks workflow as failed
            raise

        # Update job_executions record with final status (for successful executions)
        if job_id:
            end_time = workflow.time()
            duration_ms = int((end_time - start_time) * 1000)

            try:
                await workflow.execute_activity(
                    update_job_execution_status,
                    args=[job_id, execution_id, execution_status, duration_ms, execution_error],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=3),
                )

                workflow.logger.info(
                    f"Updated job execution status",
                    extra={
                        "execution_id": execution_id,
                        "job_id": job_id,
                        "status": execution_status,
                        "duration_ms": duration_ms,
                    }
                )
            except Exception as status_update_error:
                # Log but don't fail the workflow if status update fails
                workflow.logger.warning(
                    f"Failed to update job execution status",
                    extra={
                        "execution_id": execution_id,
                        "job_id": job_id,
                        "error": str(status_update_error),
                    }
                )

        return result
