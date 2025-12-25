"""
Workflow Cancellation Manager - handles workflow-specific cancellation without affecting the agent execution.

This allows cancelling individual workflow tool calls while the agent continues to run.
"""

from typing import Dict, Set, Any, Optional
from datetime import datetime, timezone
import structlog
import threading

logger = structlog.get_logger()


class WorkflowCancellationManager:
    """
    Manages cancellation flags for active workflow executions.

    Workflow tool calls check these flags periodically to see if they should stop,
    without affecting the parent agent/team execution.
    """

    def __init__(self):
        # Key: workflow_execution_key (execution_id + workflow_message_id), Value: cancellation time
        self._cancelled_workflows: Dict[str, str] = {}
        # Key: workflow_execution_key, Value: threading.Event for immediate cancellation
        self._cancellation_events: Dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def _make_key(self, execution_id: str, workflow_message_id: str) -> str:
        """Create a unique key for a workflow execution."""
        return f"{execution_id}:{workflow_message_id}"

    def register_workflow(self, execution_id: str, workflow_message_id: str) -> threading.Event:
        """
        Register a workflow execution and get a cancellation event.

        Args:
            execution_id: The agent execution ID
            workflow_message_id: The unique workflow message ID

        Returns:
            threading.Event that will be set when cancellation is requested
        """
        with self._lock:
            key = self._make_key(execution_id, workflow_message_id)
            event = threading.Event()
            self._cancellation_events[key] = event

            logger.info(
                "workflow_registered",
                execution_id=execution_id[:8],
                workflow_message_id=workflow_message_id[-12:],
                key=key
            )

            return event

    def request_cancellation(self, execution_id: str, workflow_message_id: str) -> bool:
        """
        Request cancellation of a specific workflow.

        Args:
            execution_id: The agent execution ID
            workflow_message_id: The unique workflow message ID

        Returns:
            True if cancellation was requested, False if workflow not found
        """
        with self._lock:
            key = self._make_key(execution_id, workflow_message_id)
            self._cancelled_workflows[key] = datetime.now(timezone.utc).isoformat()

            # Signal the cancellation event immediately
            if key in self._cancellation_events:
                self._cancellation_events[key].set()
                logger.info(
                    "workflow_cancellation_event_signaled",
                    execution_id=execution_id[:8],
                    workflow_message_id=workflow_message_id[-12:],
                    key=key
                )

            logger.info(
                "workflow_cancellation_requested",
                execution_id=execution_id[:8],
                workflow_message_id=workflow_message_id[-12:],
                key=key
            )

            return True

    def is_cancelled(self, execution_id: str, workflow_message_id: str) -> bool:
        """
        Check if a workflow has been cancelled.

        Args:
            execution_id: The agent execution ID
            workflow_message_id: The unique workflow message ID

        Returns:
            True if the workflow has been cancelled
        """
        with self._lock:
            key = self._make_key(execution_id, workflow_message_id)
            return key in self._cancelled_workflows

    def clear_cancellation(self, execution_id: str, workflow_message_id: str) -> None:
        """
        Clear the cancellation flag for a workflow (called when workflow completes/fails).

        Args:
            execution_id: The agent execution ID
            workflow_message_id: The unique workflow message ID
        """
        with self._lock:
            key = self._make_key(execution_id, workflow_message_id)
            if key in self._cancelled_workflows:
                del self._cancelled_workflows[key]
            if key in self._cancellation_events:
                del self._cancellation_events[key]
            logger.info(
                "workflow_cancellation_cleared",
                execution_id=execution_id[:8],
                workflow_message_id=workflow_message_id[-12:]
            )

    def get_active_count(self) -> int:
        """Get number of workflows with pending cancellation."""
        with self._lock:
            return len(self._cancelled_workflows)


# Global singleton instance
workflow_cancellation_manager = WorkflowCancellationManager()
