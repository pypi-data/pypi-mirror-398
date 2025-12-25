"""
Pydantic models for workflow executor.

This module defines type-safe models for workflow configurations,
execution context, and streaming events.
"""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class WorkflowConfig(BaseModel):
    """Configuration for a workflow execution."""

    model_config = ConfigDict(extra='forbid')

    name: str = Field(..., description="Workflow name")
    type: Literal["json", "python_dsl"] = Field(..., description="Workflow type")
    definition: Dict[str, Any] = Field(..., description="Workflow definition")
    runner: Optional[str] = Field(None, description="Runner/environment name")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Workflow parameters")
    timeout: int = Field(default=3600, description="Execution timeout in seconds")


class WorkflowExecutionContext(BaseModel):
    """Context for workflow execution."""

    model_config = ConfigDict(extra='allow')

    execution_id: str = Field(..., description="Agent execution ID")
    workflow_message_id: str = Field(..., description="Unique workflow message ID")
    workflow_config: WorkflowConfig = Field(..., description="Workflow configuration")
    kubiya_api_key: str = Field(..., description="Kubiya API key")
    kubiya_api_base: str = Field(default="https://api.kubiya.ai", description="Kubiya API base URL")


class WorkflowStepStatus(BaseModel):
    """Status of a workflow step."""

    model_config = ConfigDict(extra='allow')

    name: str = Field(..., description="Step name")
    status: Literal["pending", "running", "completed", "failed", "skipped"] = Field(..., description="Step status")
    output: Optional[str] = Field(None, description="Step output")
    error: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[datetime] = Field(None, description="Step start time")
    finished_at: Optional[datetime] = Field(None, description="Step finish time")
    duration: Optional[float] = Field(None, description="Step duration in seconds")


class WorkflowEvent(BaseModel):
    """Base workflow event model."""

    model_config = ConfigDict(extra='allow')

    event_type: str = Field(..., description="Event type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    workflow_name: str = Field(..., description="Workflow name")
    message_id: str = Field(..., description="Workflow message ID")
    source: Literal["workflow"] = Field(default="workflow", description="Event source")


class WorkflowStartedEvent(WorkflowEvent):
    """Workflow started event."""

    event_type: Literal["workflow_started"] = "workflow_started"
    workflow_type: str = Field(..., description="Workflow type")
    runner: str = Field(..., description="Runner name")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Workflow parameters")
    message: str = Field(..., description="Start message")


class WorkflowStepRunningEvent(WorkflowEvent):
    """Workflow step started running event."""

    event_type: Literal["workflow_step_running"] = "workflow_step_running"
    step_name: str = Field(..., description="Step name")
    step_status: Literal["running"] = "running"


class WorkflowStepOutputEvent(WorkflowEvent):
    """Workflow step output event."""

    event_type: Literal["workflow_step_output"] = "workflow_step_output"
    step_name: str = Field(..., description="Step name")
    output: str = Field(..., description="Step output")


class WorkflowStepCompleteEvent(WorkflowEvent):
    """Workflow step completed event."""

    event_type: Literal["workflow_step_complete"] = "workflow_step_complete"
    step_name: str = Field(..., description="Step name")
    status: Literal["completed", "failed"] = Field(..., description="Completion status")
    output: Optional[str] = Field(None, description="Final output")
    error: Optional[str] = Field(None, description="Error if failed")
    duration: Optional[float] = Field(None, description="Step duration")
    finished_at: datetime = Field(default_factory=datetime.utcnow, description="Completion time")


class WorkflowCompletedEvent(WorkflowEvent):
    """Workflow completed event."""

    event_type: Literal["workflow_completed"] = "workflow_completed"
    status: Literal["completed"] = "completed"
    duration: float = Field(..., description="Total duration in seconds")
    steps_completed: int = Field(..., description="Number of steps completed")
    finished_at: datetime = Field(default_factory=datetime.utcnow, description="Completion time")


class WorkflowFailedEvent(WorkflowEvent):
    """Workflow failed event."""

    event_type: Literal["workflow_failed"] = "workflow_failed"
    status: Literal["failed"] = "failed"
    error: str = Field(..., description="Error message")
    duration: Optional[float] = Field(None, description="Duration before failure")
    finished_at: datetime = Field(default_factory=datetime.utcnow, description="Failure time")


class WorkflowCancelledEvent(WorkflowEvent):
    """Workflow cancelled event."""

    event_type: Literal["workflow_cancelled"] = "workflow_cancelled"
    status: Literal["cancelled"] = "cancelled"
    message: str = Field(..., description="Cancellation message")
    finished_at: datetime = Field(default_factory=datetime.utcnow, description="Cancellation time")


class WorkflowResult(BaseModel):
    """Result of workflow execution."""

    model_config = ConfigDict(extra='allow')

    workflow_name: str = Field(..., description="Workflow name")
    status: Literal["completed", "failed", "cancelled"] = Field(..., description="Final status")
    duration: float = Field(..., description="Total duration in seconds")
    output: str = Field(..., description="Complete workflow output")
    error: Optional[str] = Field(None, description="Error message if failed")
    steps: List[WorkflowStepStatus] = Field(default_factory=list, description="Step statuses")
    event_count: int = Field(default=0, description="Number of events processed")
