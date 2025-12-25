"""
Shared validation module for runtime and model validation.

This module is shared between the API and worker to avoid circular dependencies.
It provides validation logic without depending on worker-specific types.
"""

from .runtime_validation import (
    validate_agent_for_runtime,
    validate_agent_for_runtime_with_litellm,
    validate_model_against_litellm,
    get_runtime_requirements_info,
    list_all_runtime_requirements,
    RUNTIME_REQUIREMENTS,
)

__all__ = [
    "validate_agent_for_runtime",
    "validate_agent_for_runtime_with_litellm",
    "validate_model_against_litellm",
    "get_runtime_requirements_info",
    "list_all_runtime_requirements",
    "RUNTIME_REQUIREMENTS",
]
