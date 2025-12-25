"""Parameter validation for tool execution.

This module provides validation to ensure tool parameters match function signatures,
preventing parameter mismatch errors that can occur due to schema corruption or
other issues.
"""
import inspect
from typing import Callable, Dict
import structlog

logger = structlog.get_logger(__name__)


class ParameterValidationError(Exception):
    """Raised when tool parameters don't match function signature."""
    pass


def validate_tool_parameters(
    func: Callable,
    provided_args: Dict,
    tool_name: str,
    execution_id: str = None
) -> None:
    """
    Validate that provided arguments match function signature.

    This validator checks that:
    1. All required parameters are provided
    2. No unexpected parameters are passed
    3. Parameter names match the function signature

    Args:
        func: The function to validate against
        provided_args: Arguments provided by the LLM
        tool_name: Name of the tool for error messages
        execution_id: Optional execution ID for logging

    Raises:
        ParameterValidationError: If parameters don't match

    Example:
        >>> def my_tool(arg1: str, arg2: int, optional: bool = True):
        ...     pass
        >>> validate_tool_parameters(my_tool, {"arg1": "test", "arg2": 42}, "my_tool")
        # No error - all required params provided
        >>> validate_tool_parameters(my_tool, {"arg1": "test"}, "my_tool")
        # Raises ParameterValidationError - missing arg2
    """
    try:
        sig = inspect.signature(func)

        # Get expected parameters (exclude 'self')
        expected_params = {
            name for name, param in sig.parameters.items()
            if name != 'self'
        }

        # Get required parameters (no default value)
        required_params = {
            name for name, param in sig.parameters.items()
            if name != 'self' and param.default == inspect.Parameter.empty
        }

        provided_params = set(provided_args.keys())

        # Check for missing required parameters
        missing = required_params - provided_params
        if missing:
            error_msg = (
                f"Tool '{tool_name}' missing required parameters: {sorted(missing)}. "
                f"Expected: {sorted(expected_params)}, Got: {sorted(provided_params)}"
            )
            logger.error(
                "tool_parameter_validation_failed",
                tool_name=tool_name,
                execution_id=execution_id,
                missing_params=sorted(missing),
                expected_params=sorted(expected_params),
                provided_params=sorted(provided_params),
            )
            raise ParameterValidationError(error_msg)

        # Check for unexpected parameters
        unexpected = provided_params - expected_params
        if unexpected:
            error_msg = (
                f"Tool '{tool_name}' received unexpected parameters: {sorted(unexpected)}. "
                f"Expected: {sorted(expected_params)}, Got: {sorted(provided_params)}"
            )
            logger.error(
                "tool_parameter_validation_failed",
                tool_name=tool_name,
                execution_id=execution_id,
                unexpected_params=sorted(unexpected),
                expected_params=sorted(expected_params),
                provided_params=sorted(provided_params),
            )
            raise ParameterValidationError(error_msg)

        logger.debug(
            "tool_parameters_validated",
            tool_name=tool_name,
            execution_id=execution_id,
            provided_params=sorted(provided_params),
        )

    except ParameterValidationError:
        # Re-raise validation errors
        raise
    except Exception as e:
        # Don't block execution if validation itself fails
        # This prevents the validator from becoming a failure point
        logger.warning(
            "parameter_validation_error",
            tool_name=tool_name,
            execution_id=execution_id,
            error=str(e),
            error_type=type(e).__name__,
        )
