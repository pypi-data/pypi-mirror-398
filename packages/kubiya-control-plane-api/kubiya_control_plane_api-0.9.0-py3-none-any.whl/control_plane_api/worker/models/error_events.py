"""
Error event models for standardized error handling and streaming.

This module provides consistent error event structures for publishing
errors from worker components to the Control Plane and UI.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone


class ErrorSeverity(Enum):
    """Error severity levels for categorization and UI display."""
    CRITICAL = "critical"  # Execution completely failed
    ERROR = "error"        # Operation failed but execution may continue
    WARNING = "warning"    # Issue detected but non-fatal
    INFO = "info"          # Informational, not an error


class ErrorCategory(Enum):
    """Error categories for filtering and analytics."""
    RUNTIME_INIT = "runtime_initialization"
    SKILL_LOADING = "skill_loading"
    MCP_CONNECTION = "mcp_connection"
    TOOL_EXECUTION = "tool_execution"
    API_COMMUNICATION = "api_communication"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    MODEL_ERROR = "llm_model_error"
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Contextual information about where/when error occurred."""
    execution_id: str
    timestamp: str
    stage: str  # "initialization", "skill_loading", "execution", "cleanup"
    component: str  # "runtime", "skill_factory", "mcp_server", "workflow"
    operation: Optional[str] = None  # Specific operation that failed
    retry_count: Optional[int] = None


@dataclass
class ErrorDetails:
    """Detailed error information."""
    error_type: str  # Exception class name
    error_message: str  # User-friendly message
    technical_message: str  # Full exception message
    stack_trace: Optional[str] = None  # Stack trace (truncated)
    code_location: Optional[str] = None  # File:line where error occurred


@dataclass
class ErrorRecovery:
    """Recovery and remediation information."""
    is_retryable: bool
    retry_suggested: bool
    recovery_actions: List[str]  # User-actionable steps
    documentation_url: Optional[str] = None


@dataclass
class ErrorEvent:
    """Complete error event structure."""
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    details: ErrorDetails
    recovery: ErrorRecovery
    metadata: Optional[Dict[str, Any]] = None

    def to_event_data(self) -> Dict[str, Any]:
        """Convert to event data dict for publishing."""
        return {
            "severity": self.severity.value,
            "category": self.category.value,
            "context": {
                "execution_id": self.context.execution_id,
                "timestamp": self.context.timestamp,
                "stage": self.context.stage,
                "component": self.context.component,
                "operation": self.context.operation,
                "retry_count": self.context.retry_count,
            },
            "details": {
                "error_type": self.details.error_type,
                "error_message": self.details.error_message,
                "technical_message": self.details.technical_message,
                "stack_trace": self.details.stack_trace,
                "code_location": self.details.code_location,
            },
            "recovery": {
                "is_retryable": self.recovery.is_retryable,
                "retry_suggested": self.recovery.retry_suggested,
                "recovery_actions": self.recovery.recovery_actions,
                "documentation_url": self.recovery.documentation_url,
            },
            "metadata": self.metadata or {},
        }
