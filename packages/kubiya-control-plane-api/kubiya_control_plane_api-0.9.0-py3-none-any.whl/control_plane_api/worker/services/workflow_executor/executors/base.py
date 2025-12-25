"""
Base workflow executor.

This module defines the abstract base class for workflow executors,
implementing the strategy pattern for different workflow types.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import structlog
from typing import Any
import threading

from ..models import WorkflowExecutionContext, WorkflowResult
from ..event_publisher import WorkflowEventPublisher
from ..event_processor import WorkflowEventProcessor

logger = structlog.get_logger()


class BaseWorkflowExecutor(ABC):
    """
    Abstract base class for workflow executors.

    Implements the template method pattern for workflow execution,
    allowing subclasses to define workflow-type-specific logic.
    """

    def __init__(
        self,
        kubiya_client: Any,
        event_publisher: WorkflowEventPublisher,
        cancellation_manager: Any
    ):
        """
        Initialize workflow executor.

        Args:
            kubiya_client: Kubiya SDK client instance
            event_publisher: Event publisher for control plane communication
            cancellation_manager: Workflow cancellation manager
        """
        self.kubiya_client = kubiya_client
        self.event_publisher = event_publisher
        self.cancellation_manager = cancellation_manager

    def execute(self, context: WorkflowExecutionContext) -> WorkflowResult:
        """
        Execute workflow (template method).

        This method defines the overall execution flow:
        1. Register for cancellation
        2. Publish started event
        3. Execute workflow (subclass-specific)
        4. Process streaming events
        5. Publish completion/failure events
        6. Return result

        Args:
            context: Workflow execution context

        Returns:
            Workflow execution result

        Raises:
            Exception: If workflow execution fails
        """
        start_time = datetime.utcnow()

        # Register workflow for cancellation tracking
        cancellation_event = self.cancellation_manager.register_workflow(
            context.execution_id,
            context.workflow_message_id
        )

        logger.info(
            "workflow_execution_started",
            workflow_name=context.workflow_config.name,
            workflow_type=context.workflow_config.type,
            execution_id=context.execution_id[:8]
        )

        # Publish started event
        self.event_publisher.publish_started(
            workflow_name=context.workflow_config.name,
            workflow_type=context.workflow_config.type,
            runner=context.workflow_config.runner or "default",
            parameters=context.workflow_config.parameters,
            message_id=context.workflow_message_id
        )

        try:
            # Execute workflow (subclass implements this)
            response_stream = self._execute_workflow(context)

            # Process streaming events
            processor = WorkflowEventProcessor(
                event_publisher=self.event_publisher,
                workflow_name=context.workflow_config.name,
                message_id=context.workflow_message_id,
                stream_callback=None  # Can be passed from context if needed
            )

            # Process events from stream
            for event in response_stream:
                # Check for cancellation first
                if cancellation_event.is_set():
                    logger.warning(
                        "workflow_cancelled_by_user",
                        workflow_name=context.workflow_config.name,
                        execution_id=context.execution_id[:8]
                    )

                    self.cancellation_manager.clear_cancellation(
                        context.execution_id,
                        context.workflow_message_id
                    )

                    self.event_publisher.publish_cancelled(
                        workflow_name=context.workflow_config.name,
                        message=f"❌ Workflow '{context.workflow_config.name}' cancelled by user",
                        message_id=context.workflow_message_id
                    )

                    # Return cancellation result
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    return WorkflowResult(
                        workflow_name=context.workflow_config.name,
                        status="cancelled",
                        duration=duration,
                        output=f"❌ Workflow execution cancelled by user\n\nWorkflow: {context.workflow_config.name}\nCancelled at: {datetime.utcnow().isoformat()}",
                        event_count=processor.get_event_count()
                    )

                # Process event
                processor.process_event(event)

            # Calculate duration
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Build output from accumulated events
            accumulated_output = processor.get_accumulated_output()
            output = self._format_result(
                context=context,
                duration=duration,
                accumulated_output=accumulated_output,
                event_count=processor.get_event_count()
            )

            # Publish completion event
            self.event_publisher.publish_completed(
                workflow_name=context.workflow_config.name,
                duration=duration,
                steps_completed=len(accumulated_output),
                message_id=context.workflow_message_id
            )

            logger.info(
                "workflow_execution_completed",
                workflow_name=context.workflow_config.name,
                duration=duration,
                event_count=processor.get_event_count(),
                execution_id=context.execution_id[:8]
            )

            # Clear cancellation registration
            self.cancellation_manager.clear_cancellation(
                context.execution_id,
                context.workflow_message_id
            )

            return WorkflowResult(
                workflow_name=context.workflow_config.name,
                status="completed",
                duration=duration,
                output=output,
                event_count=processor.get_event_count()
            )

        except Exception as e:
            # Calculate duration before failure
            duration = (datetime.utcnow() - start_time).total_seconds()

            logger.error(
                "workflow_execution_failed",
                workflow_name=context.workflow_config.name,
                error=str(e),
                duration=duration,
                execution_id=context.execution_id[:8]
            )

            # Publish failure event
            self.event_publisher.publish_failed(
                workflow_name=context.workflow_config.name,
                error=str(e),
                message_id=context.workflow_message_id,
                duration=duration
            )

            # Clear cancellation registration
            self.cancellation_manager.clear_cancellation(
                context.execution_id,
                context.workflow_message_id
            )

            return WorkflowResult(
                workflow_name=context.workflow_config.name,
                status="failed",
                duration=duration,
                output="",
                error=str(e),
                event_count=0
            )

    @abstractmethod
    def _execute_workflow(self, context: WorkflowExecutionContext) -> Any:
        """
        Execute workflow and return event stream.

        Subclasses must implement this method to execute their specific
        workflow type and return an iterable event stream.

        Args:
            context: Workflow execution context

        Returns:
            Iterable event stream from Kubiya SDK

        Raises:
            Exception: If workflow execution fails
        """
        pass

    def _format_result(
        self,
        context: WorkflowExecutionContext,
        duration: float,
        accumulated_output: list,
        event_count: int
    ) -> str:
        """
        Format final workflow result for agent.

        Args:
            context: Workflow execution context
            duration: Total execution duration
            accumulated_output: List of output lines
            event_count: Number of events processed

        Returns:
            Formatted result string
        """
        result = f"\n{'='*60}\n"
        result += f"Workflow Execution: {context.workflow_config.name}\n"
        result += f"{'='*60}\n\n"
        result += f"Status: ✅ Completed\n"
        result += f"Duration: {duration:.2f}s\n"
        result += f"Runner: {context.workflow_config.runner or 'default'}\n"
        result += f"Total Events: {event_count}\n"

        if accumulated_output:
            result += f"\n{'='*60}\n"
            result += f"Workflow Output:\n"
            result += f"{'='*60}\n\n"
            result += "\n".join(accumulated_output)
        else:
            result += "\n⚠️  No output generated\n"

        return result
