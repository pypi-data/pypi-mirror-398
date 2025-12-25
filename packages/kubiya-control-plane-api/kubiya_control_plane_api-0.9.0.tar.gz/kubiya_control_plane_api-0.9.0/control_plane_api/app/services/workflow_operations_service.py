"""
Workflow Operations Service.

This service provides business logic for workflow/task operations including
listing workflows, getting workflow details, and terminating workflows.
"""

import structlog
from datetime import datetime, timezone
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from temporalio.client import Client
from temporalio.api.enums.v1 import EventType

from control_plane_api.app.models.worker import WorkerQueue
from control_plane_api.app.models.execution import Execution
from control_plane_api.app.models.orchestration import TemporalNamespace
from control_plane_api.app.lib.temporal_client import get_temporal_client_for_org
from control_plane_api.app.lib.temporal_credentials_service import get_temporal_credentials_for_org
from control_plane_api.app.schemas.worker_queue_observability_schemas import (
    WorkflowListItem,
    WorkflowsListResponse,
    WorkflowDetailsResponse,
    WorkflowTrace,
    ActivityExecution,
    WorkflowEvent,
    TerminateWorkflowResponse
)

logger = structlog.get_logger()


class WorkflowOperationsService:
    """Service for workflow/task operations"""

    def __init__(self, db: Session):
        self.db = db

    async def list_queue_workflows(
        self,
        queue_id: str,
        organization_id: str,
        status_filter: Optional[str] = None,
        limit: int = 100
    ) -> WorkflowsListResponse:
        """
        List workflows/tasks for a worker queue.

        Args:
            queue_id: Worker queue UUID
            organization_id: Organization ID
            status_filter: Optional status filter (running, completed, failed, cancelled)
            limit: Maximum number of workflows to return

        Returns:
            WorkflowsListResponse with workflow list and counts

        Raises:
            ValueError: If queue not found
        """
        # Verify queue exists
        queue = self.db.query(WorkerQueue).filter(
            WorkerQueue.id == queue_id,
            WorkerQueue.organization_id == organization_id
        ).first()

        if not queue:
            raise ValueError("Worker queue not found")

        # Query executions for this queue
        query = self.db.query(Execution).filter(
            Execution.worker_queue_id == queue_id
        )

        if status_filter:
            query = query.filter(Execution.status == status_filter)

        # Order by most recent first
        query = query.order_by(Execution.created_at.desc()).limit(limit)
        executions = query.all()

        # Get status counts
        pending_count = self.db.query(Execution).filter(
            Execution.worker_queue_id == queue_id,
            Execution.status == "pending"
        ).count()

        running_count = self.db.query(Execution).filter(
            Execution.worker_queue_id == queue_id,
            Execution.status == "running"
        ).count()

        completed_count = self.db.query(Execution).filter(
            Execution.worker_queue_id == queue_id,
            Execution.status == "completed"
        ).count()

        failed_count = self.db.query(Execution).filter(
            Execution.worker_queue_id == queue_id,
            Execution.status == "failed"
        ).count()

        # Convert to workflow list items
        workflows = []
        for execution in executions:
            workflows.append(WorkflowListItem(
                workflow_id=execution.temporal_workflow_id or "",
                run_id=execution.temporal_run_id or "",
                task_queue=execution.task_queue_name or "",
                worker_id=None,  # Worker ID not tracked at execution level
                status=execution.status or "unknown",
                execution_id=str(execution.id),
                started_at=execution.started_at,
                close_time=execution.completed_at,
                workflow_type="agent-execution-workflow",
                attempt=1,
                history_length=0
            ))

        logger.info(
            "workflows_listed",
            queue_id=queue_id,
            total=len(workflows),
            pending=pending_count,
            running=running_count,
            completed=completed_count,
            failed=failed_count
        )

        return WorkflowsListResponse(
            workflows=workflows,
            total=len(workflows),
            pending_count=pending_count,
            running_count=running_count,
            completed_count=completed_count,
            failed_count=failed_count
        )

    async def get_workflow_details(
        self,
        workflow_id: str,
        organization_id: str,
        token: str
    ) -> WorkflowDetailsResponse:
        """
        Get detailed information about a workflow execution.

        Args:
            workflow_id: Temporal workflow ID
            organization_id: Organization ID
            token: Kubiya auth token for Temporal credentials

        Returns:
            WorkflowDetailsResponse with full workflow details

        Raises:
            ValueError: If workflow not found or access denied
            RuntimeError: If Temporal client unavailable
        """
        # Find execution by temporal_workflow_id or derived from workflow_id pattern
        execution = self.db.query(Execution).filter(
            Execution.temporal_workflow_id == workflow_id
        ).first()

        if not execution:
            # Try to extract execution ID from derived workflow ID patterns
            # Pattern: agent-execution-{uuid} or team-execution-{uuid}
            execution_id = None
            if workflow_id.startswith("agent-execution-"):
                execution_id = workflow_id.replace("agent-execution-", "")
            elif workflow_id.startswith("team-execution-"):
                execution_id = workflow_id.replace("team-execution-", "")

            if execution_id:
                execution = self.db.query(Execution).filter(
                    Execution.id == execution_id
                ).first()

        if not execution:
            raise ValueError("Workflow not found")

        # Verify organization access
        if execution.organization_id != organization_id:
            raise ValueError("Access denied")

        # Get Temporal client
        temporal_credentials = await get_temporal_credentials_for_org(
            org_id=organization_id,
            token=token,
            use_fallback=True
        )

        temporal_client = await get_temporal_client_for_org(
            namespace=temporal_credentials["namespace"],
            api_key=temporal_credentials["api_key"],
            host=temporal_credentials["host"],
        )

        if not temporal_client:
            raise RuntimeError("Temporal client unavailable")

        try:
            # Get workflow handle
            workflow_handle = temporal_client.get_workflow_handle(
                workflow_id=workflow_id,
                run_id=execution.temporal_run_id
            )

            # Describe workflow
            description = await workflow_handle.describe()

            # Fetch workflow history and parse activities, input, and events
            trace, workflow_input, recent_events, history_length = await self._parse_workflow_history(workflow_handle)

            # Calculate duration
            if execution.started_at and execution.completed_at:
                duration_ms = (execution.completed_at - execution.started_at).total_seconds() * 1000
            elif execution.started_at:
                duration_ms = (datetime.now(timezone.utc) - execution.started_at).total_seconds() * 1000
            else:
                duration_ms = 0

            # Generate Temporal Web UI URL (internal use only, not exposed to UI)
            temporal_web_url = f"https://cloud.temporal.io/namespaces/{temporal_credentials['namespace']}/workflows/{workflow_id}/{execution.temporal_run_id}"

            logger.info(
                "workflow_details_retrieved",
                workflow_id=workflow_id,
                execution_id=str(execution.id),
                history_length=history_length,
                has_input=workflow_input is not None
            )

            return WorkflowDetailsResponse(
                workflow_id=workflow_id,
                run_id=execution.temporal_run_id or "",
                status=description.status.name,
                execution_id=str(execution.id),
                execution_status=execution.status or "unknown",
                start_time=execution.started_at,
                close_time=execution.completed_at,
                execution_duration_ms=duration_ms,
                task_queue=description.task_queue,
                workflow_type=description.workflow_type,
                attempt=1,
                history_length=history_length,
                history_size_bytes=0,
                input=workflow_input,
                temporal_web_url=temporal_web_url,
                recent_events=recent_events,
                trace=trace
            )

        except Exception as e:
            logger.error(
                "workflow_details_fetch_failed",
                error=str(e),
                workflow_id=workflow_id
            )
            raise RuntimeError(f"Failed to get workflow details: {str(e)}")

    async def terminate_workflow(
        self,
        workflow_id: str,
        organization_id: str,
        token: str,
        reason: str
    ) -> TerminateWorkflowResponse:
        """
        Terminate a running workflow.

        Args:
            workflow_id: Temporal workflow ID
            organization_id: Organization ID
            token: Kubiya auth token
            reason: Termination reason

        Returns:
            TerminateWorkflowResponse with success status

        Raises:
            ValueError: If workflow not found, access denied, or not running
            RuntimeError: If termination fails
        """
        # Find execution by temporal_workflow_id or derived from workflow_id pattern
        execution = self.db.query(Execution).filter(
            Execution.temporal_workflow_id == workflow_id
        ).first()

        if not execution:
            # Try to extract execution ID from derived workflow ID patterns
            # Pattern: agent-execution-{uuid} or team-execution-{uuid}
            execution_id = None
            if workflow_id.startswith("agent-execution-"):
                execution_id = workflow_id.replace("agent-execution-", "")
            elif workflow_id.startswith("team-execution-"):
                execution_id = workflow_id.replace("team-execution-", "")

            if execution_id:
                execution = self.db.query(Execution).filter(
                    Execution.id == execution_id
                ).first()

        if not execution:
            raise ValueError("Workflow not found")

        # Verify organization access
        if execution.organization_id != organization_id:
            raise ValueError("Access denied")

        # Check if workflow is running
        if execution.status not in ["running", "pending"]:
            raise ValueError(f"Cannot terminate workflow in status: {execution.status}")

        # Get Temporal client
        temporal_credentials = await get_temporal_credentials_for_org(
            org_id=organization_id,
            token=token,
            use_fallback=True
        )

        temporal_client = await get_temporal_client_for_org(
            namespace=temporal_credentials["namespace"],
            api_key=temporal_credentials["api_key"],
            host=temporal_credentials["host"],
        )

        if not temporal_client:
            raise RuntimeError("Temporal client unavailable")

        try:
            # Get workflow handle
            workflow_handle = temporal_client.get_workflow_handle(
                workflow_id=workflow_id,
                run_id=execution.temporal_run_id
            )

            # Cancel the workflow
            await workflow_handle.cancel()

            # Update execution status in DB
            now = datetime.now(timezone.utc)
            execution.status = "cancelled"
            execution.completed_at = now
            self.db.commit()

            logger.info(
                "workflow_terminated",
                workflow_id=workflow_id,
                execution_id=str(execution.id),
                reason=reason
            )

            return TerminateWorkflowResponse(
                success=True,
                workflow_id=workflow_id,
                terminated_at=now
            )

        except Exception as e:
            self.db.rollback()
            logger.error(
                "workflow_termination_failed",
                error=str(e),
                workflow_id=workflow_id
            )
            raise RuntimeError(f"Failed to terminate workflow: {str(e)}")

    async def _parse_workflow_history(self, workflow_handle) -> tuple:
        """
        Parse workflow history to extract activity executions, timeline, input, and events.

        Args:
            workflow_handle: Temporal workflow handle

        Returns:
            Tuple of (WorkflowTrace, input_data, recent_events, history_length)
        """
        activities_map: Dict[str, ActivityExecution] = {}
        timeline_events: List[Dict] = []
        recent_events: List[WorkflowEvent] = []
        workflow_input: Optional[Dict] = None
        history_length: int = 0

        # Map to track scheduled_event_id -> activity_id for linking events
        scheduled_event_map: Dict[int, str] = {}

        try:
            # Use fetch_history_events for async iteration
            async for event in workflow_handle.fetch_history_events():
                history_length += 1
                event_type = event.event_type
                event_time = event.event_time.ToDatetime() if hasattr(event.event_time, 'ToDatetime') else event.event_time

                # Capture recent events (last 20)
                event_type_name = str(event_type).replace("EVENT_TYPE_", "") if hasattr(event_type, 'name') else str(event_type)
                if len(recent_events) < 20:
                    recent_events.append(WorkflowEvent(
                        event_id=event.event_id,
                        event_type=event_type_name,
                        event_time=event_time,
                        details={}
                    ))

                # Parse WorkflowExecutionStarted to get input
                # Compare as integer since event.event_type might be int or enum
                if event_type == EventType.EVENT_TYPE_WORKFLOW_EXECUTION_STARTED or event_type == 1:
                    logger.debug("found_workflow_execution_started", event_type=str(event_type), event_id=event.event_id)
                    try:
                        attrs = event.workflow_execution_started_event_attributes
                        if attrs.input and attrs.input.payloads:
                            import json
                            logger.debug("workflow_input_payloads_found", count=len(attrs.input.payloads))
                            # Try to decode the first payload as JSON
                            for payload in attrs.input.payloads:
                                try:
                                    data = payload.data.decode('utf-8') if payload.data else None
                                    if data:
                                        workflow_input = json.loads(data)
                                        logger.info("workflow_input_parsed", has_input=True)
                                        break
                                except (json.JSONDecodeError, UnicodeDecodeError):
                                    # If not JSON, store as string
                                    workflow_input = {"raw": payload.data.decode('utf-8', errors='replace') if payload.data else None}
                                    logger.info("workflow_input_raw", has_input=True)
                        else:
                            logger.debug("workflow_input_not_found", has_input=attrs.input is not None)
                    except Exception as e:
                        logger.warning("failed_to_parse_workflow_input", error=str(e))

                # Parse activity scheduled events
                elif event_type == EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED:
                    attrs = event.activity_task_scheduled_event_attributes
                    activity_id = attrs.activity_id or str(event.event_id)

                    # Store mapping from event_id to activity_id for linking
                    scheduled_event_map[event.event_id] = activity_id

                    activities_map[activity_id] = ActivityExecution(
                        activity_id=activity_id,
                        activity_type=attrs.activity_type.name if attrs.activity_type else "unknown",
                        status="scheduled",
                        scheduled_time=event_time,
                        attempt=1
                    )

                    timeline_events.append({
                        "type": "activity_scheduled",
                        "event_id": event.event_id,
                        "activity_id": activity_id,
                        "activity_type": attrs.activity_type.name if attrs.activity_type else "unknown",
                        "timestamp": event_time.isoformat() if hasattr(event_time, 'isoformat') else str(event_time)
                    })

                # Parse activity started events
                elif event_type == EventType.EVENT_TYPE_ACTIVITY_TASK_STARTED:
                    attrs = event.activity_task_started_event_attributes
                    # Get activity_id from the scheduled_event_id reference
                    scheduled_event_id = attrs.scheduled_event_id
                    activity_id = scheduled_event_map.get(scheduled_event_id)

                    if activity_id and activity_id in activities_map:
                        activities_map[activity_id].status = "started"
                        activities_map[activity_id].started_time = event_time
                        activities_map[activity_id].worker_identity = attrs.identity
                        activities_map[activity_id].attempt = attrs.attempt

                        timeline_events.append({
                            "type": "activity_started",
                            "event_id": event.event_id,
                            "activity_id": activity_id,
                            "worker": attrs.identity,
                            "attempt": attrs.attempt,
                            "timestamp": event_time.isoformat() if hasattr(event_time, 'isoformat') else str(event_time)
                        })

                # Parse activity completed events
                elif event_type == EventType.EVENT_TYPE_ACTIVITY_TASK_COMPLETED:
                    attrs = event.activity_task_completed_event_attributes
                    scheduled_event_id = attrs.scheduled_event_id
                    activity_id = scheduled_event_map.get(scheduled_event_id)

                    if activity_id and activity_id in activities_map:
                        activity = activities_map[activity_id]
                        activity.status = "completed"
                        activity.completed_time = event_time

                        if activity.started_time:
                            started = activity.started_time
                            if hasattr(started, 'timestamp'):
                                started = started.timestamp()
                            elif hasattr(started, 'ToDatetime'):
                                started = started.ToDatetime().timestamp()
                            else:
                                started = started.timestamp() if hasattr(started, 'timestamp') else 0

                            completed = event_time
                            if hasattr(completed, 'timestamp'):
                                completed = completed.timestamp()
                            elif hasattr(completed, 'ToDatetime'):
                                completed = completed.ToDatetime().timestamp()
                            else:
                                completed = completed.timestamp() if hasattr(completed, 'timestamp') else 0

                            activity.duration_ms = (completed - started) * 1000

                        timeline_events.append({
                            "type": "activity_completed",
                            "event_id": event.event_id,
                            "activity_id": activity_id,
                            "duration_ms": activity.duration_ms,
                            "timestamp": event_time.isoformat() if hasattr(event_time, 'isoformat') else str(event_time)
                        })

                # Parse activity failed events
                elif event_type == EventType.EVENT_TYPE_ACTIVITY_TASK_FAILED:
                    attrs = event.activity_task_failed_event_attributes
                    scheduled_event_id = attrs.scheduled_event_id
                    activity_id = scheduled_event_map.get(scheduled_event_id)

                    if activity_id and activity_id in activities_map:
                        activity = activities_map[activity_id]
                        activity.status = "failed"
                        activity.completed_time = event_time

                        # Extract failure message
                        if attrs.failure:
                            activity.failure_message = attrs.failure.message

                        if activity.started_time:
                            started = activity.started_time
                            if hasattr(started, 'timestamp'):
                                started = started.timestamp()
                            elif hasattr(started, 'ToDatetime'):
                                started = started.ToDatetime().timestamp()
                            else:
                                started = 0

                            completed = event_time
                            if hasattr(completed, 'timestamp'):
                                completed = completed.timestamp()
                            elif hasattr(completed, 'ToDatetime'):
                                completed = completed.ToDatetime().timestamp()
                            else:
                                completed = 0

                            activity.duration_ms = (completed - started) * 1000

                        timeline_events.append({
                            "type": "activity_failed",
                            "event_id": event.event_id,
                            "activity_id": activity_id,
                            "error": activity.failure_message,
                            "retry_state": attrs.retry_state if hasattr(attrs, 'retry_state') else None,
                            "timestamp": event_time.isoformat() if hasattr(event_time, 'isoformat') else str(event_time)
                        })

                # Parse activity timed out events
                elif event_type == EventType.EVENT_TYPE_ACTIVITY_TASK_TIMED_OUT:
                    attrs = event.activity_task_timed_out_event_attributes
                    scheduled_event_id = attrs.scheduled_event_id
                    activity_id = scheduled_event_map.get(scheduled_event_id)

                    if activity_id and activity_id in activities_map:
                        activities_map[activity_id].status = "timed_out"
                        activities_map[activity_id].completed_time = event_time

                        timeline_events.append({
                            "type": "activity_timed_out",
                            "event_id": event.event_id,
                            "activity_id": activity_id,
                            "timestamp": event_time.isoformat() if hasattr(event_time, 'isoformat') else str(event_time)
                        })

                # Parse activity cancelled events
                elif event_type == EventType.EVENT_TYPE_ACTIVITY_TASK_CANCELED:
                    attrs = event.activity_task_canceled_event_attributes
                    scheduled_event_id = attrs.scheduled_event_id
                    activity_id = scheduled_event_map.get(scheduled_event_id)

                    if activity_id and activity_id in activities_map:
                        activities_map[activity_id].status = "cancelled"
                        activities_map[activity_id].completed_time = event_time

                        timeline_events.append({
                            "type": "activity_cancelled",
                            "event_id": event.event_id,
                            "activity_id": activity_id,
                            "timestamp": event_time.isoformat() if hasattr(event_time, 'isoformat') else str(event_time)
                        })

        except Exception as e:
            logger.warning(
                "workflow_history_parse_error",
                error=str(e),
                exc_info=True
            )
            # Continue with what we have

        # Build trace object
        activities_list = list(activities_map.values())

        trace = WorkflowTrace(
            activities=activities_list,
            timeline=timeline_events,
            total_activities=len(activities_list),
            completed_activities=sum(1 for a in activities_list if a.status == "completed"),
            failed_activities=sum(1 for a in activities_list if a.status == "failed")
        )

        return trace, workflow_input, recent_events, history_length
