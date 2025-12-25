"""
Utility functions for Claude Code runtime.

This module provides helper functions for prompt building, session management,
and SDK version checking.
"""

from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


def build_prompt_with_history(context: any) -> str:
    """
    Build prompt with conversation history.

    Since ClaudeSDKClient maintains session continuity, we include
    the conversation history as context in the prompt.

    Args:
        context: RuntimeExecutionContext

    Returns:
        Prompt string with history context
    """
    if not context.conversation_history:
        return context.prompt

    # Build context from history
    history_context = "Previous conversation:\n"
    for msg in context.conversation_history[-10:]:  # Last 10 messages
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if len(content) > 200:
            history_context += f"{role.capitalize()}: {content[:200]}...\n"
        else:
            history_context += f"{role.capitalize()}: {content}\n"

    return f"{history_context}\n\nCurrent request:\n{context.prompt}"


def get_sdk_version() -> str:
    """
    Get Claude Code SDK version.

    Returns:
        SDK version string or "unknown"
    """
    try:
        import claude_agent_sdk

        return getattr(claude_agent_sdk, "__version__", "unknown")
    except Exception:
        return "unknown"


def extract_usage_from_result_message(message: any) -> dict:
    """
    Extract usage metrics from ResultMessage.

    Args:
        message: ResultMessage object

    Returns:
        Usage dict with token counts
    """
    if not hasattr(message, "usage") or not message.usage:
        logger.warning("result_message_has_no_usage")
        return {}

    # ResultMessage.usage is a dict, not an object - use .get() instead of getattr()
    usage_dict = message.usage

    # Handle both dict and object usage formats
    if isinstance(usage_dict, dict):
        input_tokens = usage_dict.get("input_tokens", 0)
        output_tokens = usage_dict.get("output_tokens", 0)
        cache_read_tokens = usage_dict.get("cache_read_input_tokens", 0)
        cache_creation_tokens = usage_dict.get("cache_creation_input_tokens", 0)
    else:
        # Fallback for object-style usage
        input_tokens = getattr(usage_dict, "input_tokens", 0)
        output_tokens = getattr(usage_dict, "output_tokens", 0)
        cache_read_tokens = getattr(usage_dict, "cache_read_input_tokens", 0)
        cache_creation_tokens = getattr(usage_dict, "cache_creation_input_tokens", 0)

    # Use Anthropic field names for consistency with analytics
    usage = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_creation_tokens": cache_creation_tokens,
    }

    logger.info(
        "usage_extracted_from_claude_code",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=usage["total_tokens"],
    )

    return usage


def extract_session_id_from_result_message(
    message: any, execution_id: str
) -> Optional[str]:
    """
    Extract and validate session_id from ResultMessage.

    BUG FIX #4: Validates session_id before returning.

    Args:
        message: ResultMessage object
        execution_id: Execution ID for logging

    Returns:
        Valid session_id or None
    """
    session_id = getattr(message, "session_id", None)

    if not session_id:
        logger.warning(
            "no_session_id_in_result_message",
            execution_id=execution_id[:8],
            message="Multi-turn conversations may not work without session_id",
        )
        return None

    # Validate format
    if not isinstance(session_id, str) or len(session_id) < 10:
        logger.warning(
            "invalid_session_id_format_in_result_message",
            execution_id=execution_id[:8],
            session_id_type=type(session_id).__name__,
            session_id_length=len(session_id) if isinstance(session_id, str) else 0,
        )
        return None

    logger.info(
        "session_id_captured_for_conversation_continuity",
        execution_id=execution_id[:8],
        session_id_prefix=session_id[:16],
        message="This session_id will enable multi-turn conversations",
    )

    return session_id
