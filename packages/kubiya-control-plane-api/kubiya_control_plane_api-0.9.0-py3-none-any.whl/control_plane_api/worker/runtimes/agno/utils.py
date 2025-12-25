"""
Utility functions for Agno runtime.

This module provides:
- Message formatting for conversation history
- Usage metrics extraction
- Tool message extraction
- Result processing helpers
"""

import structlog
from typing import Dict, Any, List

logger = structlog.get_logger(__name__)


def build_conversation_messages(conversation_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build conversation messages for Agno from history.

    Converts the standard conversation history format into Agno's
    expected message format.

    Args:
        conversation_history: List of conversation messages

    Returns:
        List of message dicts formatted for Agno
    """
    if not conversation_history:
        return []

    # Convert to Agno message format
    messages = []
    for msg in conversation_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        # Agno uses 'user' and 'assistant' roles
        if role in ["user", "assistant"]:
            messages.append({"role": role, "content": content})

    logger.debug(
        "conversation_messages_built",
        message_count=len(messages),
        original_count=len(conversation_history),
    )

    return messages


def extract_usage(result: Any) -> Dict[str, Any]:
    """
    Extract usage metrics from Agno result.

    Extracts comprehensive token usage information including:
    - Input/prompt tokens
    - Output/completion tokens
    - Total tokens
    - Cache tokens (Anthropic-specific)

    Args:
        result: Agno run result

    Returns:
        Usage metrics dict with comprehensive token breakdown
    """
    usage = {}

    if hasattr(result, "metrics") and result.metrics:
        metrics = result.metrics

        # Extract standard token counts
        input_tokens = getattr(metrics, "input_tokens", 0)
        output_tokens = getattr(metrics, "output_tokens", 0)
        total_tokens = getattr(metrics, "total_tokens", 0) or (input_tokens + output_tokens)

        usage = {
            # Standard fields (normalized for RuntimeAnalyticsExtractor)
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            # Legacy field names for backward compatibility
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
        }

        # Extract cache tokens (Anthropic-specific via Agno)
        # Agno exposes these in input_token_details for Anthropic models
        if hasattr(metrics, "input_token_details") and metrics.input_token_details:
            details = metrics.input_token_details
            if isinstance(details, dict):
                usage["cache_read_tokens"] = details.get("cache_read", 0)
                usage["cache_creation_tokens"] = details.get("cache_creation", 0)

                # Also add to prompt_tokens_details for LiteLLM compatibility
                usage["prompt_tokens_details"] = {
                    "cached_tokens": details.get("cache_read", 0),
                }

        # Log if metrics exist but no tokens were extracted
        if not input_tokens and not output_tokens:
            logger.warning(
                "agno_metrics_present_but_no_tokens",
                metrics_type=type(metrics).__name__,
                metrics_attrs=dir(metrics),
            )
    else:
        # Log when no metrics available
        logger.warning(
            "agno_result_missing_metrics",
            has_metrics=hasattr(result, "metrics"),
            result_type=type(result).__name__,
        )

    return usage


def extract_tool_messages(result: Any) -> List[Dict[str, Any]]:
    """
    Extract tool messages from Agno result.

    Args:
        result: Agno run result

    Returns:
        List of tool message dicts with execution metadata
    """
    tool_messages = []

    # Check if result has messages attribute
    if hasattr(result, "messages") and result.messages:
        for msg in result.messages:
            if hasattr(msg, "role") and msg.role == "tool":
                tool_messages.append(
                    {
                        "role": "tool",
                        "content": getattr(msg, "content", ""),
                        "tool_use_id": getattr(msg, "tool_use_id", None),
                    }
                )

    logger.debug(
        "tool_messages_extracted",
        tool_message_count=len(tool_messages),
    )

    return tool_messages


def extract_response_content(result: Any) -> str:
    """
    Extract response content from Agno result.

    Args:
        result: Agno run result

    Returns:
        Response content as string
    """
    if hasattr(result, "content"):
        return result.content
    return str(result)
