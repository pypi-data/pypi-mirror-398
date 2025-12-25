"""
Error event publisher for standardized error handling.

This module provides utilities for publishing error events to the Control Plane
with consistent structure, user-friendly messages, and recovery suggestions.
"""

import structlog
import traceback
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from control_plane_api.worker.models.error_events import (
    ErrorEvent, ErrorSeverity, ErrorCategory, ErrorContext,
    ErrorDetails, ErrorRecovery
)
from control_plane_api.worker.control_plane_client import ControlPlaneClient

logger = structlog.get_logger()


class ErrorEventPublisher:
    """Helper class for publishing standardized error events."""

    def __init__(self, control_plane: ControlPlaneClient):
        self.control_plane = control_plane

    async def publish_error(
        self,
        execution_id: str,
        exception: Exception,
        severity: ErrorSeverity,
        category: ErrorCategory,
        stage: str,
        component: str,
        operation: Optional[str] = None,
        recovery_actions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        include_stack_trace: bool = True,
    ) -> bool:
        """
        Publish a standardized error event to Control Plane.

        Args:
            execution_id: Execution ID
            exception: The exception that occurred
            severity: Error severity level
            category: Error category
            stage: Execution stage where error occurred
            component: Component that generated error
            operation: Specific operation that failed
            recovery_actions: List of user-actionable recovery steps
            metadata: Additional metadata
            include_stack_trace: Whether to include stack trace

        Returns:
            True if published successfully
        """
        try:
            # Extract stack trace
            stack_trace = None
            code_location = None
            if include_stack_trace:
                tb_lines = traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                )
                stack_trace = ''.join(tb_lines)[-2000:]  # Last 2000 chars

                # Extract code location from traceback
                tb = exception.__traceback__
                if tb:
                    frame = traceback.extract_tb(tb)[-1]
                    code_location = f"{frame.filename}:{frame.lineno}"

            # Create user-friendly error message
            user_message = self._create_user_friendly_message(
                exception, category, component
            )

            # Determine if retryable
            is_retryable = self._is_retryable_error(exception, category)

            # Get default recovery actions if none provided
            if not recovery_actions:
                recovery_actions = self._get_default_recovery_actions(
                    category, is_retryable
                )

            # Get documentation URL
            doc_url = self._get_documentation_url(category)

            # Build error event
            error_event = ErrorEvent(
                severity=severity,
                category=category,
                context=ErrorContext(
                    execution_id=execution_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    stage=stage,
                    component=component,
                    operation=operation,
                ),
                details=ErrorDetails(
                    error_type=type(exception).__name__,
                    error_message=user_message,
                    technical_message=str(exception),
                    stack_trace=stack_trace,
                    code_location=code_location,
                ),
                recovery=ErrorRecovery(
                    is_retryable=is_retryable,
                    retry_suggested=is_retryable and severity != ErrorSeverity.CRITICAL,
                    recovery_actions=recovery_actions,
                    documentation_url=doc_url,
                ),
                metadata=metadata,
            )

            # Publish error event
            success = await self.control_plane.publish_event_async(
                execution_id=execution_id,
                event_type="error",
                data=error_event.to_event_data(),
            )

            if success:
                logger.info(
                    "error_event_published",
                    execution_id=execution_id[:8] if len(execution_id) >= 8 else execution_id,
                    severity=severity.value,
                    category=category.value,
                    error_type=type(exception).__name__,
                )
            else:
                logger.warning(
                    "error_event_publish_failed",
                    execution_id=execution_id[:8] if len(execution_id) >= 8 else execution_id,
                    error=str(exception)[:200],
                )

            return success

        except Exception as publish_error:
            # Never let error publishing break the main execution
            logger.error(
                "failed_to_publish_error_event",
                execution_id=execution_id[:8] if len(execution_id) >= 8 else execution_id,
                error=str(publish_error),
            )
            return False

    def _create_user_friendly_message(
        self, exception: Exception, category: ErrorCategory, component: str
    ) -> str:
        """Create user-friendly error message."""

        messages = {
            ErrorCategory.RUNTIME_INIT: f"Failed to initialize {component}",
            ErrorCategory.SKILL_LOADING: f"Could not load skill: {str(exception)[:100]}",
            ErrorCategory.MCP_CONNECTION: f"Failed to connect to MCP server",
            ErrorCategory.TOOL_EXECUTION: f"Tool execution failed: {str(exception)[:100]}",
            ErrorCategory.TIMEOUT: f"Operation timed out in {component}",
            ErrorCategory.MODEL_ERROR: f"LLM model error: {str(exception)[:100]}",
            ErrorCategory.AUTHENTICATION: "Authentication failed - please check credentials",
            ErrorCategory.NETWORK: "Network connection error",
            ErrorCategory.VALIDATION: f"Validation error: {str(exception)[:100]}",
        }

        return messages.get(category, str(exception)[:200])

    def _is_retryable_error(
        self, exception: Exception, category: ErrorCategory
    ) -> bool:
        """Determine if error is retryable."""

        # Network and timeout errors are generally retryable
        if category in [ErrorCategory.NETWORK, ErrorCategory.TIMEOUT]:
            return True

        # Authentication errors not retryable without credential changes
        if category == ErrorCategory.AUTHENTICATION:
            return False

        # Validation errors not retryable without input changes
        if category == ErrorCategory.VALIDATION:
            return False

        # Check exception type
        retryable_types = [
            "TimeoutError",
            "ConnectionError",
            "HTTPError",
            "TemporaryFailure",
        ]

        return type(exception).__name__ in retryable_types

    def _get_default_recovery_actions(
        self, category: ErrorCategory, is_retryable: bool
    ) -> List[str]:
        """Get default recovery actions for error category."""

        actions = {
            ErrorCategory.RUNTIME_INIT: [
                "Check that all required dependencies are installed",
                "Verify runtime configuration is correct",
                "Check worker logs for detailed error information",
            ],
            ErrorCategory.SKILL_LOADING: [
                "Verify skill configuration is correct",
                "Check that skill dependencies are available",
                "Review skill permissions and access",
            ],
            ErrorCategory.MCP_CONNECTION: [
                "Verify MCP server is running and accessible",
                "Check network connectivity",
                "Review MCP server configuration and credentials",
            ],
            ErrorCategory.TIMEOUT: [
                "Consider increasing timeout settings",
                "Check system resources and load",
                "Simplify the operation if possible",
            ],
            ErrorCategory.MODEL_ERROR: [
                "Verify API credentials are valid",
                "Check API rate limits and quotas",
                "Try a different model if available",
            ],
            ErrorCategory.AUTHENTICATION: [
                "Verify API credentials are correct",
                "Check that credentials have required permissions",
                "Regenerate credentials if expired",
            ],
        }

        default_actions = actions.get(category, [
            "Review error details above",
            "Check system logs for more information",
            "Contact support if issue persists",
        ])

        if is_retryable:
            default_actions.insert(0, "Retry the operation")

        return default_actions

    def _get_documentation_url(self, category: ErrorCategory) -> Optional[str]:
        """Get documentation URL for error category."""

        base_url = "https://docs.kubiya.ai/troubleshooting"

        urls = {
            ErrorCategory.RUNTIME_INIT: f"{base_url}/runtime-initialization",
            ErrorCategory.SKILL_LOADING: f"{base_url}/skill-configuration",
            ErrorCategory.MCP_CONNECTION: f"{base_url}/mcp-servers",
            ErrorCategory.MODEL_ERROR: f"{base_url}/llm-configuration",
            ErrorCategory.AUTHENTICATION: f"{base_url}/authentication",
        }

        return urls.get(category, base_url)
