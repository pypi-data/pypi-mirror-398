"""
Workflow event publisher.

This module handles publishing workflow events to the control plane
with proper type safety and error handling.
"""

import structlog
from typing import Optional, Any
from .models import (
    WorkflowEvent,
    WorkflowStartedEvent,
    WorkflowStepRunningEvent,
    WorkflowStepOutputEvent,
    WorkflowStepCompleteEvent,
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
    WorkflowCancelledEvent,
)

logger = structlog.get_logger()


class WorkflowEventPublisher:
    """
    Publishes workflow events to the control plane.

    Handles event serialization, error handling, and control plane communication.
    """

    def __init__(self, control_plane: Any, execution_id: str):
        """
        Initialize event publisher.

        Args:
            control_plane: Control plane client instance
            execution_id: Agent execution ID
        """
        self.control_plane = control_plane
        self.execution_id = execution_id
        self.enabled = control_plane is not None and execution_id is not None

    def publish(self, event: WorkflowEvent) -> bool:
        """
        Publish a workflow event.

        Args:
            event: Workflow event to publish

        Returns:
            True if published successfully, False otherwise
        """
        if not self.enabled:
            logger.debug(
                "event_publisher_disabled",
                event_type=event.event_type,
                reason="control_plane_or_execution_id_missing"
            )
            return False

        try:
            # Convert Pydantic model to dict for control plane
            event_data = event.model_dump(mode='json', exclude_none=True)

            logger.debug(
                "publishing_workflow_event",
                event_type=event.event_type,
                execution_id=self.execution_id[:8],
                workflow_name=event.workflow_name
            )

            self.control_plane.publish_event(
                execution_id=self.execution_id,
                event_type=event.event_type,
                data=event_data
            )

            logger.debug(
                "workflow_event_published",
                event_type=event.event_type,
                execution_id=self.execution_id[:8]
            )

            return True

        except Exception as e:
            logger.error(
                "failed_to_publish_workflow_event",
                event_type=event.event_type,
                error=str(e),
                execution_id=self.execution_id[:8]
            )
            return False

    def publish_started(
        self,
        workflow_name: str,
        workflow_type: str,
        runner: str,
        parameters: dict,
        message_id: str
    ) -> bool:
        """Publish workflow started event."""
        event = WorkflowStartedEvent(
            workflow_name=workflow_name,
            workflow_type=workflow_type,
            runner=runner,
            parameters=parameters,
            message_id=message_id,
            message=f"🚀 Starting workflow: {workflow_name}"
        )
        return self.publish(event)

    def publish_step_running(
        self,
        workflow_name: str,
        step_name: str,
        message_id: str
    ) -> bool:
        """Publish step running event."""
        event = WorkflowStepRunningEvent(
            workflow_name=workflow_name,
            step_name=step_name,
            message_id=message_id
        )
        return self.publish(event)

    def publish_step_output(
        self,
        workflow_name: str,
        step_name: str,
        output: str,
        message_id: str
    ) -> bool:
        """Publish step output event."""
        event = WorkflowStepOutputEvent(
            workflow_name=workflow_name,
            step_name=step_name,
            output=output,
            message_id=message_id
        )
        return self.publish(event)

    def publish_step_complete(
        self,
        workflow_name: str,
        step_name: str,
        status: str,
        message_id: str,
        output: Optional[str] = None,
        error: Optional[str] = None,
        duration: Optional[float] = None
    ) -> bool:
        """Publish step complete event."""
        event = WorkflowStepCompleteEvent(
            workflow_name=workflow_name,
            step_name=step_name,
            status=status,  # type: ignore
            message_id=message_id,
            output=output,
            error=error,
            duration=duration
        )
        return self.publish(event)

    def publish_completed(
        self,
        workflow_name: str,
        duration: float,
        steps_completed: int,
        message_id: str
    ) -> bool:
        """Publish workflow completed event."""
        event = WorkflowCompletedEvent(
            workflow_name=workflow_name,
            duration=duration,
            steps_completed=steps_completed,
            message_id=message_id
        )
        return self.publish(event)

    def publish_failed(
        self,
        workflow_name: str,
        error: str,
        message_id: str,
        duration: Optional[float] = None
    ) -> bool:
        """Publish workflow failed event."""
        event = WorkflowFailedEvent(
            workflow_name=workflow_name,
            error=error,
            message_id=message_id,
            duration=duration
        )
        return self.publish(event)

    def publish_cancelled(
        self,
        workflow_name: str,
        message: str,
        message_id: str
    ) -> bool:
        """Publish workflow cancelled event."""
        event = WorkflowCancelledEvent(
            workflow_name=workflow_name,
            message=message,
            message_id=message_id
        )
        return self.publish(event)
