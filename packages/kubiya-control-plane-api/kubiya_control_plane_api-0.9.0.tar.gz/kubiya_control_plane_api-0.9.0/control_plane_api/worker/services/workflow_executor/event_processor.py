"""
Workflow event processor.

This module processes streaming events from the Kubiya SDK,
handling deduplication, parsing, and state management.
"""

import json
import hashlib
import structlog
from typing import Dict, Any, Set, Optional, Callable
from .event_publisher import WorkflowEventPublisher

logger = structlog.get_logger()


class WorkflowEventProcessor:
    """
    Processes streaming events from workflow execution.

    Handles event parsing, deduplication, and publishes to control plane.
    """

    def __init__(
        self,
        event_publisher: WorkflowEventPublisher,
        workflow_name: str,
        message_id: str,
        stream_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize event processor.

        Args:
            event_publisher: Event publisher instance
            workflow_name: Name of the workflow being executed
            message_id: Unique workflow message ID
            stream_callback: Optional callback for streaming output
        """
        self.event_publisher = event_publisher
        self.workflow_name = workflow_name
        self.message_id = message_id
        self.stream_callback = stream_callback

        # State tracking
        self.event_count = 0
        self.accumulated_output: list[str] = []
        self.seen_events: Set[str] = set()
        self.current_step: Optional[str] = None
        self.step_outputs: Dict[str, str] = {}

    def process_event(self, event: Any) -> Optional[Dict[str, Any]]:
        """
        Process a single streaming event from the SDK.

        Args:
            event: Raw event from SDK (string, bytes, or dict)

        Returns:
            Parsed event data as dict, or None if event should be skipped
        """
        self.event_count += 1

        # Skip None/empty events
        if event is None:
            logger.debug("skipping_none_event", event_number=self.event_count)
            return None

        # Parse the event
        try:
            event_data = self._parse_event(event)
            if event_data is None:
                return None

            # Process based on event type
            event_type = event_data.get("type", "unknown")
            logger.debug(
                "processing_workflow_event",
                event_type=event_type,
                event_number=self.event_count
            )

            # Route to specific handler
            if event_type == "step_output":
                self._handle_step_output(event_data)
            elif event_type == "step_running":
                self._handle_step_running(event_data)
            elif event_type == "step_complete":
                self._handle_step_complete(event_data)
            elif event_type == "workflow_complete":
                self._handle_workflow_complete(event_data)
            elif event_type == "workflow_failed":
                self._handle_workflow_failed(event_data)
            else:
                logger.debug("unknown_event_type", event_type=event_type)

            return event_data

        except Exception as e:
            logger.error(
                "failed_to_process_event",
                error=str(e),
                event_number=self.event_count
            )
            return None

    def _parse_event(self, event: Any) -> Optional[Dict[str, Any]]:
        """Parse raw event into dict."""
        try:
            # Handle bytes
            if isinstance(event, bytes):
                if not event:
                    return None
                event = event.decode('utf-8')

            # Handle strings
            if isinstance(event, str):
                if not event.strip():
                    return None

                # Handle SSE format: "data: 2:{json}"
                if event.startswith("data: "):
                    event = event[6:]  # Remove "data: " prefix

                    # Strip message ID prefix like "2:"
                    if ":" in event and event.split(":", 1)[0].isdigit():
                        event = event.split(":", 1)[1]

                # Parse JSON
                return json.loads(event)

            # Already a dict
            elif isinstance(event, dict):
                return event

            # Unknown type
            else:
                logger.warning(
                    "unknown_event_type_treating_as_text",
                    type_name=type(event).__name__
                )
                event_str = str(event)
                if event_str.strip():
                    self.accumulated_output.append(event_str)
                    if self.stream_callback:
                        self.stream_callback(f"{event_str}\n")
                return None

        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning("failed_to_parse_event_treating_as_text", error=str(e))
            event_str = str(event)
            if event_str.strip():
                self.accumulated_output.append(event_str)
                if self.stream_callback:
                    self.stream_callback(f"{event_str}\n")
            return None

    def _handle_step_output(self, event_data: Dict[str, Any]) -> None:
        """Handle step_output event."""
        step = event_data.get("step", {})
        step_name = step.get("name", "unknown")
        step_status = step.get("status", "")
        output = step.get("output", "")

        if not output.strip():
            return

        # Deduplicate events - SDK sends same event twice
        event_hash = hashlib.md5(f"{step_name}:{output}".encode()).hexdigest()
        if event_hash in self.seen_events:
            logger.debug("skipping_duplicate_event", step_name=step_name)
            return
        self.seen_events.add(event_hash)

        logger.debug("step_output_received", step_name=step_name, output_length=len(output))

        # Store output
        self.accumulated_output.append(output)
        self.step_outputs[step_name] = output

        # Stream to callback
        if self.stream_callback:
            formatted_output = f"```\n{output}\n```\n"
            self.stream_callback(formatted_output)

        # Publish to control plane
        self.event_publisher.publish_step_output(
            workflow_name=self.workflow_name,
            step_name=step_name,
            output=output,
            message_id=self.message_id
        )

        # Check if step failed
        if step_status in ["error", "failed"]:
            logger.warning("step_failed_detected", step_name=step_name, status=step_status)
            self.event_publisher.publish_step_complete(
                workflow_name=self.workflow_name,
                step_name=step_name,
                status="failed",
                message_id=self.message_id,
                error=output
            )

    def _handle_step_running(self, event_data: Dict[str, Any]) -> None:
        """Handle step_running event."""
        step = event_data.get("step", {})
        step_name = step.get("name", "unknown")

        logger.debug("step_running", step_name=step_name)

        self.current_step = step_name
        formatted = f"\n▶️  Step: {step_name}"
        self.accumulated_output.append(formatted)

        if self.stream_callback:
            self.stream_callback(f"{formatted}\n")

        self.event_publisher.publish_step_running(
            workflow_name=self.workflow_name,
            step_name=step_name,
            message_id=self.message_id
        )

    def _handle_step_complete(self, event_data: Dict[str, Any]) -> None:
        """Handle step_complete event."""
        step = event_data.get("step", {})
        step_name = step.get("name", "unknown")
        status = step.get("status", "unknown")

        logger.debug("step_complete", step_name=step_name, status=status)

        icon = "✅" if status == "finished" else "❌"
        formatted = f"{icon} Step '{step_name}' {status}"
        self.accumulated_output.append(formatted)
        self.current_step = None

        if self.stream_callback:
            self.stream_callback(f"{formatted}\n")

        self.event_publisher.publish_step_complete(
            workflow_name=self.workflow_name,
            step_name=step_name,
            status="completed" if status == "finished" else "failed",
            message_id=self.message_id
        )

    def _handle_workflow_complete(self, event_data: Dict[str, Any]) -> None:
        """Handle workflow_complete event."""
        dag_name = event_data.get("dagName", "unknown")
        status = event_data.get("status", "unknown")
        success = event_data.get("success", False)

        logger.info("workflow_complete", dag_name=dag_name, status=status, success=success)

        icon = "✅" if success else "❌"
        formatted = f"\n{icon} Workflow '{dag_name}' {status}"
        self.accumulated_output.append(formatted)

        if self.stream_callback:
            self.stream_callback(f"{formatted}\n")

    def _handle_workflow_failed(self, event_data: Dict[str, Any]) -> None:
        """Handle workflow_failed event."""
        error = event_data.get("error", "Unknown error")

        logger.error("workflow_failed", error=error)

        formatted = f"\n❌ Workflow failed: {error}"
        self.accumulated_output.append(formatted)

        if self.stream_callback:
            self.stream_callback(f"{formatted}\n")

        self.event_publisher.publish_failed(
            workflow_name=self.workflow_name,
            error=error,
            message_id=self.message_id
        )

    def get_accumulated_output(self) -> list[str]:
        """Get all accumulated output lines."""
        return self.accumulated_output

    def get_event_count(self) -> int:
        """Get total number of events processed."""
        return self.event_count
