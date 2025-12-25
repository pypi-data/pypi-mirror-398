"""
Hook system for Claude Code runtime tool execution monitoring.

This module provides pre-tool and post-tool hooks for real-time event
publishing and monitoring of tool execution.

Hooks Implemented:
- PreToolUse: Called before tool execution (can block/modify)
- PostToolUse: Called after tool execution completes
- SubagentStop: Called when subagent (Task tool) completes

Why SubagentStop is Needed:
According to Claude SDK documentation, Task tools spawn subagents that execute
in separate contexts. PostToolUse hooks don't fire for subagent tools because
they run in isolated sessions. SubagentStop captures these completions.

Built-in Tool Behavior:
Some built-in tools (TodoWrite, Bash, Read, Write, Edit, Glob, Grep) may execute
through optimized SDK paths that skip hooks. This is expected behavior. The runtime's
fallback mechanism (runtime.py lines 1032-1105) publishes synthetic completion events
for these tools to ensure the frontend receives proper notifications.

Includes policy enforcement for tool executions.

BUG FIX #2: Replaced all print() statements with structured logging.
BUG FIX #8: Added SubagentStop hook to capture Task tool completions.
"""

from typing import Dict, Any, Callable, Optional, TYPE_CHECKING
import structlog
import os

if TYPE_CHECKING:
    from control_plane_api.worker.services.tool_enforcement import ToolEnforcementService

logger = structlog.get_logger(__name__)

# Check if verbose debug logging is enabled
# Support legacy CLAUDE_CODE_DEBUG for backward compatibility
if os.getenv("CLAUDE_CODE_DEBUG"):
    logger.warning(
        "deprecated_env_var",
        old_var="CLAUDE_CODE_DEBUG",
        new_var="KUBIYA_CLI_LOG_LEVEL",
        message="CLAUDE_CODE_DEBUG is deprecated. Please use KUBIYA_CLI_LOG_LEVEL=DEBUG instead."
    )
    DEBUG_MODE = os.getenv("CLAUDE_CODE_DEBUG", "false").lower() == "true"
else:
    DEBUG_MODE = os.getenv("KUBIYA_CLI_LOG_LEVEL", "INFO").upper() == "DEBUG"


def build_hooks(
    execution_id: str,
    event_callback: Optional[Callable[[Dict], None]],
    active_tools: Dict[str, str],
    completed_tools: set,
    started_tools: set,
    enforcement_context: Optional[Dict[str, Any]] = None,
    enforcement_service: Optional["ToolEnforcementService"] = None,
) -> Dict[str, Any]:
    """
    Build hooks for tool execution monitoring with policy enforcement.

    Hooks intercept events like PreToolUse and PostToolUse to provide
    real-time feedback and monitoring. Both hooks and ToolResultBlock
    can publish tool_complete events, so we use completed_tools set
    for deduplication. Uses started_tools set to prevent duplicate
    tool_start events. Includes policy enforcement checks.

    Args:
        execution_id: Execution ID for event tracking
        event_callback: Callback for publishing events
        active_tools: Shared dict mapping tool_use_id -> tool_name
        completed_tools: Shared set of tool_use_ids that completed
        started_tools: Shared set of tool_use_ids that started (prevents duplicate tool_start events)
        enforcement_context: Optional context for policy enforcement
        enforcement_service: Optional enforcement service for policy checks

    Returns:
        Dict of hook configurations
    """
    from claude_agent_sdk import HookMatcher

    async def pre_tool_hook(input_data, tool_use_id, tool_context):
        """
        Hook called before tool execution.

        BUG FIX #2: Uses logger.debug() instead of print().
        """
        # BUG FIX #2: Use structured logging instead of print
        if DEBUG_MODE:
            logger.debug(
                "pre_tool_hook_called",
                tool_use_id=tool_use_id,
                input_data_type=type(input_data).__name__,
                input_data_keys=(
                    list(input_data.keys()) if isinstance(input_data, dict) else None
                ),
                has_tool_context=bool(tool_context),
            )

        # Try to extract tool name from input_data
        tool_name = "unknown"
        tool_args = {}

        if isinstance(input_data, dict):
            # Check if input_data has tool_name like output_data does
            tool_name = input_data.get("tool_name", "unknown")
            tool_args = input_data.get("tool_input", {})

        # Always log MCP tool calls (not just in debug mode)
        if tool_name.startswith("mcp__"):
            logger.info(
                "🔧 mcp_tool_starting",
                tool_name=tool_name,
                tool_use_id=tool_use_id[:12],
                args=tool_args,
                message=f"▶️  Executing {tool_name}"
            )

            if DEBUG_MODE:
                if tool_name == "unknown":
                    logger.debug(
                        "pre_tool_hook_no_tool_name",
                        tool_use_id=tool_use_id,
                        input_data_keys=list(input_data.keys()),
                    )
                else:
                    logger.debug(
                        "pre_tool_hook_found_tool_name",
                        tool_use_id=tool_use_id,
                        tool_name=tool_name,
                    )

        # Enforcement check (non-blocking, async)
        enforcement_allowed = True
        enforcement_violation = None
        enforcement_metadata = {}

        if enforcement_service and enforcement_context and tool_name != "unknown":
            try:
                enforcement_allowed, enforcement_violation, enforcement_metadata = (
                    await enforcement_service.enforce_tool_execution(
                        tool_name=tool_name,
                        tool_args=tool_args,
                        enforcement_context={
                            **enforcement_context,
                            "execution_id": execution_id,
                            "tool_use_id": tool_use_id,
                        },
                    )
                )

                # Store enforcement result in tool context for post-hook
                if not enforcement_allowed:
                    tool_context["enforcement_violation"] = enforcement_violation
                    tool_context["enforcement_metadata"] = enforcement_metadata

            except Exception as e:
                logger.error(
                    "enforcement_check_failed",
                    tool_name=tool_name,
                    error=str(e),
                )
                # Fail open - allow execution
                enforcement_metadata = {"enforcer": "error", "error": str(e)}

        # Publish tool_start event with enforcement metadata (with deduplication)
        # Check if already started to prevent duplicate events
        if event_callback and tool_name != "unknown" and tool_use_id not in started_tools:
            try:
                event_callback(
                    {
                        "type": "tool_start",
                        "tool_name": tool_name,
                        "tool_args": tool_args,
                        "tool_execution_id": tool_use_id,
                        "execution_id": execution_id,
                        "enforcement": enforcement_metadata,  # Add enforcement metadata
                    }
                )
                # Mark as started to prevent duplicate events
                started_tools.add(tool_use_id)
                if DEBUG_MODE:
                    logger.debug(
                        "pre_tool_hook_published_tool_start",
                        tool_use_id=tool_use_id,
                        tool_name=tool_name,
                    )
            except Exception as e:
                logger.error(
                    "failed_to_publish_tool_start",
                    tool_name=tool_name,
                    tool_use_id=tool_use_id,
                    error=str(e),
                    exc_info=True,
                )
        elif tool_use_id in started_tools:
            if DEBUG_MODE:
                logger.debug(
                    "tool_start_already_published",
                    tool_use_id=tool_use_id,
                    tool_name=tool_name,
                )

        return {}

    async def post_tool_hook(output_data, tool_use_id, tool_context):
        """
        Hook called after tool execution.

        BUG FIX #2: Uses logger.debug() instead of print().
        """
        # Extract tool name from output_data (provided by Claude Code SDK)
        tool_name = "unknown"
        if isinstance(output_data, dict):
            # Claude SDK provides tool_name directly in output_data
            tool_name = output_data.get("tool_name", "unknown")

        # Check for errors from multiple sources:
        # 1. tool_context.is_error (set by SDK)
        # 2. output_data.isError (returned by tool wrapper when exception occurs)
        is_error = (
            (tool_context.get("is_error", False) if tool_context else False) or
            (output_data.get("isError", False) if isinstance(output_data, dict) else False)
        )

        # Check for enforcement violation and inject into output
        enforcement_violation = tool_context.get("enforcement_violation") if tool_context else None
        enforcement_metadata = tool_context.get("enforcement_metadata", {}) if tool_context else {}

        if enforcement_violation:
            # Inject violation into output_data
            violation_message = (
                f"\n{'='*60}\n"
                f"⛔ POLICY VIOLATION DETECTED\n"
                f"{'='*60}\n"
                f"{enforcement_violation}\n"
                f"{'='*60}\n\n"
            )

            if isinstance(output_data, dict):
                existing_output = output_data.get("output", "")
                output_data["output"] = violation_message + str(existing_output)
                output_data["enforcement_violated"] = True

            logger.warning(
                "tool_execution_policy_violation",
                tool_name=tool_name,
                tool_use_id=tool_use_id,
                enforcement_metadata=enforcement_metadata,
            )

        # Always log MCP tool results (not just in debug mode)
        if tool_name.startswith("mcp__"):
            # Extract result/error from output_data
            result_preview = None
            if isinstance(output_data, dict):
                result = output_data.get("result", output_data.get("output", output_data))
                result_str = str(result)
                result_preview = result_str[:500] + "..." if len(result_str) > 500 else result_str

            if is_error:
                logger.error(
                    "❌ mcp_tool_failed",
                    tool_name=tool_name,
                    tool_use_id=tool_use_id[:12],
                    error=result_preview,
                    message=f"Failed: {tool_name}"
                )
            else:
                logger.info(
                    "✅ mcp_tool_completed",
                    tool_name=tool_name,
                    tool_use_id=tool_use_id[:12],
                    result_preview=result_preview,
                    result_length=len(str(output_data)),
                    message=f"Completed: {tool_name}"
                )

        # BUG FIX #2: Use structured logging instead of print
        if DEBUG_MODE:
            logger.debug(
                "post_tool_hook_called",
                tool_use_id=tool_use_id,
                tool_name=tool_name,
                is_error=is_error,
                status="failed" if is_error else "success",
            )

        # Publish tool_complete event (with deduplication)
        # Both hooks and ToolResultBlock can publish, so check if already published
        if event_callback and tool_use_id not in completed_tools:
            try:
                event_callback(
                    {
                        "type": "tool_complete",
                        "tool_name": tool_name,
                        "tool_execution_id": tool_use_id,
                        "status": "failed" if is_error else "success",
                        "output": str(output_data)[:1000] if output_data else None,
                        "error": str(output_data) if is_error else None,
                        "execution_id": execution_id,
                        "enforcement": enforcement_metadata,  # Add enforcement metadata
                    }
                )
                # Mark as completed to prevent duplicate from ToolResultBlock
                completed_tools.add(tool_use_id)
                if DEBUG_MODE:
                    logger.debug(
                        "post_tool_hook_published_tool_complete",
                        tool_use_id=tool_use_id,
                        tool_name=tool_name,
                        is_error=is_error,
                    )
            except Exception as e:
                logger.error(
                    "failed_to_publish_tool_complete",
                    tool_name=tool_name,
                    tool_use_id=tool_use_id,
                    error=str(e),
                    exc_info=True,
                )
        elif tool_use_id in completed_tools:
            if DEBUG_MODE:
                logger.debug(
                    "tool_complete_already_published_via_stream",
                    tool_use_id=tool_use_id,
                    tool_name=tool_name,
                )

        return {}

    async def subagent_stop_hook(input_data, tool_use_id, tool_context):
        """
        Hook called when a subagent (Task tool) completes.

        This captures completions for Task tools that spawn subagents,
        which don't fire PostToolUse hooks. According to Claude SDK docs,
        subagent execution happens in separate contexts, so we need this
        dedicated hook to track their completion.

        Args:
            input_data: SubagentStopHookInput dict containing:
                - session_id: Session ID for the subagent
                - transcript_path: Path to subagent transcript
                - cwd: Working directory
                - stop_hook_active: Whether hook is active
                - hook_event_name: Name of the hook event
            tool_use_id: Unique identifier for this tool execution
            tool_context: Additional context from SDK

        Returns:
            Empty dict (SDK requirement)
        """
        tool_name = "Task"  # Subagents are spawned by Task tool

        # CRITICAL: Validate input_data is a dict (SDK passes SubagentStopHookInput)
        if not isinstance(input_data, dict):
            logger.error(
                "subagent_stop_hook_invalid_input_type",
                input_type=type(input_data).__name__,
                note="Expected dict with session_id, transcript_path, etc."
            )
            return {}

        # Defensive: Validate tool_use_id is present and valid
        if not tool_use_id:
            logger.error(
                "subagent_stop_hook_missing_tool_use_id",
                has_input_data=bool(input_data),
                note="Cannot track completion without tool_use_id"
            )
            return {}

        # Defensive: Ensure tool_use_id is string for string operations
        if not isinstance(tool_use_id, str):
            logger.warning(
                "subagent_stop_hook_invalid_tool_use_id_type",
                tool_use_id_type=type(tool_use_id).__name__,
                note="Converting to string for safety"
            )
            try:
                tool_use_id = str(tool_use_id)
            except Exception as e:
                logger.error(
                    "subagent_stop_hook_tool_use_id_conversion_failed",
                    error=str(e),
                    note="Cannot proceed without valid tool_use_id"
                )
                return {}

        # Safe slicing for logging (check length)
        tool_use_id_short = tool_use_id[:12] if len(tool_use_id) >= 12 else tool_use_id

        if DEBUG_MODE:
            logger.debug(
                "subagent_stop_hook_called",
                tool_use_id=tool_use_id_short,
                has_input_data=bool(input_data),
                input_data_type=type(input_data).__name__,
                input_data_keys=list(input_data.keys()) if isinstance(input_data, dict) else None,
            )

        # Always log subagent completions (not just in debug mode)
        logger.info(
            "subagent_completed",
            tool_use_id=tool_use_id_short,
            tool_name=tool_name,
            message=f"✅ Subagent (Task) completed: {tool_use_id_short}"
        )

        # Check if already completed (deduplicate with PostToolUse, though unlikely)
        if event_callback and tool_use_id not in completed_tools:
            try:
                # Extract meaningful info from SubagentStopHookInput
                output_str = None
                if input_data:
                    try:
                        session_id = input_data.get("session_id", "")
                        transcript_path = input_data.get("transcript_path", "")
                        output_str = f"Subagent completed (session: {session_id[:16] if session_id else 'unknown'})"

                        if transcript_path:
                            output_str += f" - transcript: {transcript_path}"
                    except Exception as conv_error:
                        logger.warning(
                            "subagent_input_extraction_failed",
                            tool_use_id=tool_use_id_short,
                            error=str(conv_error),
                            note="Using fallback output representation"
                        )
                        output_str = f"<Subagent completed - extraction failed: {type(input_data).__name__}>"

                event_callback(
                    {
                        "type": "tool_complete",
                        "tool_name": tool_name,
                        "tool_execution_id": tool_use_id,
                        "status": "success",  # Subagent completed successfully
                        "output": output_str,
                        "error": None,
                        "execution_id": execution_id,
                    }
                )
                completed_tools.add(tool_use_id)

                if DEBUG_MODE:
                    logger.debug(
                        "subagent_completion_published",
                        tool_use_id=tool_use_id_short,
                        tool_name=tool_name,
                    )
            except Exception as e:
                # Non-fatal: Log but don't crash if event publishing fails
                logger.error(
                    "failed_to_publish_subagent_completion",
                    tool_use_id=tool_use_id_short,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                    note="Completion tracking failed but execution succeeded"
                )
        elif tool_use_id in completed_tools:
            if DEBUG_MODE:
                logger.debug(
                    "subagent_completion_already_published",
                    tool_use_id=tool_use_id_short,
                    tool_name=tool_name,
                    note="Deduplicated - PostToolUse already published this"
                )

        return {}

    # Build hook configuration
    hooks = {
        "PreToolUse": [HookMatcher(hooks=[pre_tool_hook])],
        "PostToolUse": [HookMatcher(hooks=[post_tool_hook])],
        "SubagentStop": [HookMatcher(hooks=[subagent_stop_hook])],  # NEW: Track subagent (Task) completions
    }

    return hooks
