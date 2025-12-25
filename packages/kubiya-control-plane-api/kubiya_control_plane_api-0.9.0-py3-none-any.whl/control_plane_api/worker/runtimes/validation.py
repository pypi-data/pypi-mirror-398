"""
Runtime validation system with model compatibility and requirements checking.

This module re-exports validation functions from the shared validation module
and provides worker-specific validation helpers for RuntimeExecutionContext.
"""

from typing import List, Optional, Dict, Any
from control_plane_api.worker.runtimes.base import RuntimeType, RuntimeExecutionContext

# Import shared validation logic that both API and worker can use
from control_plane_api.app.lib.validation import (
    validate_agent_for_runtime as _validate_agent_for_runtime,
    get_runtime_requirements_info as _get_runtime_requirements_info,
    list_all_runtime_requirements as _list_all_runtime_requirements,
    RUNTIME_REQUIREMENTS as _RUNTIME_REQUIREMENTS,
)


# Re-export for backward compatibility
validate_agent_for_runtime = _validate_agent_for_runtime
get_runtime_requirements_info = _get_runtime_requirements_info
list_all_runtime_requirements = _list_all_runtime_requirements


class ValidationError(Exception):
    """Raised when validation fails."""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.field = field
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API responses."""
        result = {"error": self.message}
        if self.field:
            result["field"] = self.field
        if self.details:
            result["details"] = self.details
        return result


def validate_execution_context(context: RuntimeExecutionContext) -> tuple[bool, List[str]]:
    """
    Validate RuntimeExecutionContext for worker execution.

    This is a worker-specific helper that validates the full execution context
    including conversation history, skills, and runtime-specific requirements.

    Args:
        context: Runtime execution context

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Get runtime requirements from shared module
    runtime_type_str = context.runtime_type.value if isinstance(context.runtime_type, RuntimeType) else str(context.runtime_type)
    requirements = _RUNTIME_REQUIREMENTS.get(runtime_type_str)

    if not requirements:
        # No requirements registered - allow by default
        return True, []

    # Validate model
    is_valid, error = requirements.validate_model(context.model_id)
    if not is_valid:
        errors.append(error)

    # Validate config
    config_errors = requirements.validate_config(context.agent_config)
    errors.extend(config_errors)

    # Validate system prompt if required
    if requirements.requires_system_prompt and not context.system_prompt:
        errors.append("System prompt is required for this runtime")

    # Validate tools if required
    if requirements.requires_tools and not context.skills:
        errors.append("At least one skill is required for this runtime")

    # Validate history length
    if requirements.max_history_length and context.conversation_history:
        if len(context.conversation_history) > requirements.max_history_length:
            errors.append(
                f"Conversation history too long ({len(context.conversation_history)} messages). "
                f"Maximum: {requirements.max_history_length}"
            )

    return len(errors) == 0, errors
