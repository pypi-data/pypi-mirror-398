"""
Supabase utility functions with defensive error handling.

Provides wrappers around Supabase queries to handle common errors like:
- Code 556: JSON could not be generated (invalid JSONB data)
- Network timeouts
- Connection errors
"""

import structlog
from typing import Any, Optional, Callable
from supabase import Client

logger = structlog.get_logger()


def safe_execute_query(
    client: Client,
    query_builder: Callable,
    operation_name: str,
    fallback_query_builder: Optional[Callable] = None,
    **context
) -> Any:
    """
    Execute a Supabase query with defensive error handling.

    This wrapper handles common Supabase/PostgREST errors gracefully,
    including code 556 (JSON could not be generated) which occurs when
    JSONB columns contain invalid data.

    Args:
        client: Supabase client
        query_builder: Function that returns the query to execute
        operation_name: Name of the operation for logging
        fallback_query_builder: Optional fallback query if primary fails
        **context: Additional context for logging

    Returns:
        Query result or None if both queries fail

    Example:
        ```python
        result = safe_execute_query(
            client=get_supabase(),
            query_builder=lambda: client.table("executions")
                .select("*, execution_participants(*)")
                .eq("organization_id", org_id),
            fallback_query_builder=lambda: client.table("executions")
                .select("*")
                .eq("organization_id", org_id),
            operation_name="list_executions",
            org_id=org_id,
        )
        ```
    """
    try:
        # Try primary query
        query = query_builder()
        result = query.execute()
        return result

    except Exception as primary_error:
        error_str = str(primary_error)

        # Check if it's a JSON serialization error (code 556)
        is_json_error = (
            "JSON could not be generated" in error_str or
            "'code': 556" in error_str or
            "code\": 556" in error_str
        )

        if is_json_error:
            logger.warning(
                f"{operation_name}_json_error_using_fallback",
                error=error_str[:200],  # Truncate long errors
                **context
            )

            # Try fallback query if provided
            if fallback_query_builder:
                try:
                    fallback_query = fallback_query_builder()
                    result = fallback_query.execute()
                    logger.debug(
                        f"{operation_name}_fallback_succeeded",
                        **context
                    )
                    return result

                except Exception as fallback_error:
                    logger.error(
                        f"{operation_name}_fallback_query_failed",
                        error=str(fallback_error),
                        **context
                    )
                    raise fallback_error
            else:
                # No fallback provided, re-raise original error
                raise primary_error
        else:
            # Different error type - re-raise
            logger.error(
                f"{operation_name}_query_failed",
                error=error_str,
                error_type=type(primary_error).__name__,
                **context
            )
            raise primary_error


def sanitize_jsonb_field(value: Any, field_name: str, default: dict = None) -> dict:
    """
    Sanitize a JSONB field value to ensure it's a valid dict.

    Args:
        value: The value to sanitize
        field_name: Name of the field for logging
        default: Default value if sanitization fails

    Returns:
        Valid dict or default
    """
    if default is None:
        default = {}

    if value is None:
        return default

    if isinstance(value, dict):
        return value

    logger.debug(
        "invalid_jsonb_field_sanitized",
        field_name=field_name,
        type=type(value).__name__
    )

    return default
