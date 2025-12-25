"""
Pydantic schemas for Worker Queue Observability API.

This module defines request/response schemas for worker queue metrics,
workflow tracking, and activity tracing.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class WorkerQueueMetricsResponse(BaseModel):
    """Comprehensive metrics for a worker queue"""
    queue_id: str = Field(..., description="Worker queue UUID")

    # Worker Health
    active_workers: int = Field(..., description="Number of active workers")
    idle_workers: int = Field(..., description="Number of idle workers")
    busy_workers: int = Field(..., description="Number of busy workers")
    total_workers: int = Field(..., description="Total number of workers")

    # Task Metrics (24h window)
    tasks_processed_24h: int = Field(..., description="Tasks completed in last 24 hours")
    tasks_failed_24h: int = Field(..., description="Tasks failed in last 24 hours")
    tasks_pending: int = Field(..., description="Tasks currently pending")
    avg_task_duration_ms: float = Field(..., description="Average task duration in milliseconds")

    # Error Tracking
    error_rate_percent: float = Field(..., description="Error rate percentage")
    last_error_at: Optional[datetime] = Field(None, description="Timestamp of last error")

    # Temporal Queue Metrics
    task_queue_backlog: int = Field(0, description="Number of tasks in backlog")
    task_queue_pollers: int = Field(0, description="Number of active pollers")

    # Timing
    last_activity_at: Optional[datetime] = Field(None, description="Last activity timestamp")
    updated_at: datetime = Field(..., description="Metrics update timestamp")


class WorkflowListItem(BaseModel):
    """Workflow list item for queue workflows"""
    workflow_id: str = Field(..., description="Temporal workflow ID")
    run_id: str = Field(..., description="Temporal run ID")
    task_queue: str = Field(..., description="Task queue name")
    worker_id: Optional[str] = Field(None, description="Worker ID processing this workflow")
    status: str = Field(..., description="Workflow status")
    execution_id: str = Field(..., description="Execution entity ID")
    started_at: Optional[datetime] = Field(None, description="Workflow start time")
    close_time: Optional[datetime] = Field(None, description="Workflow completion time")
    workflow_type: str = Field(..., description="Workflow type")
    attempt: int = Field(1, description="Execution attempt number")
    history_length: int = Field(0, description="Workflow history event count")


class WorkflowsListResponse(BaseModel):
    """Response for list queue workflows"""
    workflows: List[WorkflowListItem] = Field(..., description="List of workflows")
    total: int = Field(..., description="Total number of workflows")
    pending_count: int = Field(0, description="Number of pending workflows")
    running_count: int = Field(0, description="Number of running workflows")
    completed_count: int = Field(0, description="Number of completed workflows")
    failed_count: int = Field(0, description="Number of failed workflows")


class WorkflowEvent(BaseModel):
    """Individual workflow history event"""
    event_id: int = Field(..., description="Event ID")
    event_type: str = Field(..., description="Event type")
    event_time: datetime = Field(..., description="Event timestamp")
    details: Dict[str, Any] = Field(default_factory=dict, description="Event details")


class ActivityExecution(BaseModel):
    """Individual activity execution within a workflow"""
    activity_id: str = Field(..., description="Activity ID")
    activity_type: str = Field(..., description="Activity type/name")
    status: str = Field(..., description="Activity status: scheduled, started, completed, failed, timed_out")
    scheduled_time: datetime = Field(..., description="Activity scheduled timestamp")
    started_time: Optional[datetime] = Field(None, description="Activity start timestamp")
    completed_time: Optional[datetime] = Field(None, description="Activity completion timestamp")
    duration_ms: Optional[float] = Field(None, description="Activity duration in milliseconds")
    attempt: int = Field(1, description="Attempt number")
    worker_identity: Optional[str] = Field(None, description="Worker that executed this activity")
    failure_message: Optional[str] = Field(None, description="Failure message if activity failed")
    input: Optional[Dict[str, Any]] = Field(None, description="Activity input data")
    result: Optional[Dict[str, Any]] = Field(None, description="Activity result data")


class WorkflowTrace(BaseModel):
    """Execution trace with activities and timeline"""
    activities: List[ActivityExecution] = Field(..., description="List of activity executions")
    timeline: List[Dict[str, Any]] = Field(..., description="Timeline events for visualization")
    total_activities: int = Field(..., description="Total number of activities")
    completed_activities: int = Field(0, description="Number of completed activities")
    failed_activities: int = Field(0, description="Number of failed activities")


class WorkflowDetailsResponse(BaseModel):
    """Detailed workflow information"""
    workflow_id: str = Field(..., description="Temporal workflow ID")
    run_id: str = Field(..., description="Temporal run ID")
    status: str = Field(..., description="Workflow status")

    # Execution Info
    execution_id: str = Field(..., description="Execution entity ID")
    execution_status: str = Field(..., description="Execution status from DB")

    # Timing
    start_time: Optional[datetime] = Field(None, description="Workflow start time")
    close_time: Optional[datetime] = Field(None, description="Workflow close time")
    execution_duration_ms: float = Field(0, description="Execution duration in milliseconds")

    # Temporal Details
    task_queue: str = Field(..., description="Task queue name")
    workflow_type: str = Field(..., description="Workflow type")
    attempt: int = Field(1, description="Execution attempt number")
    history_length: int = Field(0, description="History event count")
    history_size_bytes: int = Field(0, description="History size in bytes")

    # Input
    input: Optional[Dict[str, Any]] = Field(None, description="Workflow input data")

    # Links
    temporal_web_url: str = Field(..., description="Temporal Web UI URL")

    # Events and Trace
    recent_events: List[WorkflowEvent] = Field(default_factory=list, description="Recent workflow events")
    trace: WorkflowTrace = Field(..., description="Workflow execution trace")


class TerminateWorkflowRequest(BaseModel):
    """Request to terminate a running workflow"""
    reason: str = Field(..., min_length=1, max_length=500, description="Termination reason")


class TerminateWorkflowResponse(BaseModel):
    """Response after terminating a workflow"""
    success: bool = Field(..., description="Whether termination was successful")
    workflow_id: str = Field(..., description="Workflow ID that was terminated")
    terminated_at: datetime = Field(..., description="Termination timestamp")


class BatchTerminateRequest(BaseModel):
    """Request to terminate multiple executions"""
    execution_ids: List[str] = Field(..., min_length=1, max_length=100, description="List of execution IDs to terminate")
    reason: str = Field(..., min_length=1, max_length=500, description="Termination reason")


class BatchTerminateResult(BaseModel):
    """Result for a single execution in batch termination"""
    execution_id: str = Field(..., description="Execution ID")
    success: bool = Field(..., description="Whether termination was successful")
    workflow_id: Optional[str] = Field(None, description="Workflow ID if successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    terminated_at: Optional[datetime] = Field(None, description="Termination timestamp if successful")


class BatchTerminateResponse(BaseModel):
    """Response after batch terminating executions"""
    total_requested: int = Field(..., description="Total number of executions requested for termination")
    total_succeeded: int = Field(..., description="Number of successfully terminated executions")
    total_failed: int = Field(..., description="Number of failed terminations")
    results: List[BatchTerminateResult] = Field(..., description="Results for each execution")
