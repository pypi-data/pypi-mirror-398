"""
Planning Agent Streaming Hook

Captures agent execution events (tool calls, reasoning) during task planning
and publishes them for real-time UI streaming.
"""

from typing import Callable, Any, Optional
import time
import uuid
import structlog

logger = structlog.get_logger()


class PlanningStreamingHook:
    """
    Hook to capture and stream agent execution events during planning.

    Similar to worker execution streaming but optimized for planning agents.
    Captures:
    - Tool executions (start/complete)
    - Reasoning/thinking content
    - Agent state transitions
    """

    def __init__(self, event_publisher: Callable):
        """
        Initialize streaming hook.

        Args:
            event_publisher: Async function to publish events (yield SSE messages)
        """
        self.event_publisher = event_publisher
        self.active_tools = {}  # tool_id -> tool info
        self.tool_count = 0
        self.thinking_buffer = []  # Buffer for thinking content
        self.last_thinking_time = 0  # Debounce thinking events

    def create_tool_hook(self) -> Callable:
        """
        Create tool execution hook for Agno agent.

        This hook captures tool calls before execution and publishes events
        for real-time streaming to the UI.

        Returns:
            Tool hook function compatible with Agno agent
        """
        def tool_hook(
            name: str = None,
            function_name: str = None,
            function: Callable = None,
            arguments: dict = None,
            **kwargs,
        ) -> Any:
            """Hook called by Agno when tools are executed"""
            tool_name = name or function_name or "unknown_tool"
            tool_args = arguments or {}

            # Generate unique tool ID
            self.tool_count += 1
            tool_id = f"{tool_name}_{self.tool_count}_{uuid.uuid4().hex[:8]}"

            logger.info(
                "planning_tool_started",
                tool_name=tool_name,
                tool_id=tool_id,
                args_keys=list(tool_args.keys()) if isinstance(tool_args, dict) else None
            )

            # Track tool start time
            start_time = time.time()
            self.active_tools[tool_id] = {
                "name": tool_name,
                "start_time": start_time,
            }

            # Publish tool_started event
            try:
                logger.info("publishing_tool_started", tool_name=tool_name, tool_id=tool_id)
                self.event_publisher({
                    "event": "tool_call",
                    "data": {
                        "tool_name": tool_name,
                        "tool_id": tool_id,
                        "tool_arguments": tool_args,
                        "timestamp": start_time,
                    }
                })
                logger.info("tool_started_event_published", tool_name=tool_name)
            except Exception as e:
                logger.error("failed_to_publish_tool_started", error=str(e))

            # Execute the tool
            result = None
            error = None
            status = "success"

            try:
                if function and callable(function):
                    result = function(**tool_args) if tool_args else function()
                else:
                    raise ValueError(f"Function not callable: {function}")
            except Exception as e:
                error = e
                status = "failed"
                result = str(e)
                logger.error(
                    "planning_tool_failed",
                    tool_name=tool_name,
                    tool_id=tool_id,
                    error=str(e)
                )

            # Calculate duration
            end_time = time.time()
            duration = end_time - start_time

            # Format result for streaming with smart truncation
            result_str = str(result) if result else ""
            MAX_RESULT_SIZE = 5000  # Increased from 1000 to preserve more context

            if len(result_str) > MAX_RESULT_SIZE:
                # Smart truncation: keep start and end, truncate middle
                start_chunk = result_str[:2500]
                end_chunk = result_str[-2500:]
                result_str = f"{start_chunk}\n... ({len(result_str)} chars total, middle section truncated) ...\n{end_chunk}"

            # Publish tool_completed event
            try:
                self.event_publisher({
                    "event": "tool_result",
                    "data": {
                        "tool_name": tool_name,
                        "tool_id": tool_id,
                        "status": status,
                        "result": result_str,
                        "duration": duration,
                        "timestamp": end_time,
                    }
                })
            except Exception as e:
                logger.error("failed_to_publish_tool_completed", error=str(e))

            # Clean up tracking
            self.active_tools.pop(tool_id, None)

            logger.info(
                "planning_tool_completed",
                tool_name=tool_name,
                tool_id=tool_id,
                status=status,
                duration=f"{duration:.2f}s"
            )

            # Return result or raise error
            if error:
                raise error
            return result

        return tool_hook

    def create_thinking_hook(self) -> Callable:
        """
        Create thinking/reasoning hook for capturing LLM thoughts.

        This hook captures LLM reasoning content as it's generated
        and streams it in real-time to the UI with debouncing.

        Returns:
            Thinking hook function compatible with Agno agent
        """
        def thinking_hook(content: str, **kwargs):
            """Hook called when LLM generates reasoning content"""
            if not content or len(content.strip()) == 0:
                return

            # Debounce: Only publish every 200ms to avoid flooding
            current_time = time.time()
            if current_time - self.last_thinking_time < 0.2:
                self.thinking_buffer.append(content)
                return

            # Flush buffer if we have content
            if self.thinking_buffer:
                content = " ".join(self.thinking_buffer) + " " + content
                self.thinking_buffer = []

            self.last_thinking_time = current_time

            # Truncate very long thinking to avoid overwhelming the UI
            MAX_THINKING_LENGTH = 500
            if len(content) > MAX_THINKING_LENGTH:
                content = content[:MAX_THINKING_LENGTH] + "..."

            try:
                logger.debug("publishing_thinking", length=len(content))
                self.event_publisher({
                    "event": "thinking",
                    "data": {
                        "content": content,
                        "timestamp": current_time,
                    }
                })
            except Exception as e:
                logger.error("failed_to_publish_thinking", error=str(e))

        return thinking_hook

    def get_active_tools_count(self) -> int:
        """Get count of currently executing tools"""
        return len(self.active_tools)
