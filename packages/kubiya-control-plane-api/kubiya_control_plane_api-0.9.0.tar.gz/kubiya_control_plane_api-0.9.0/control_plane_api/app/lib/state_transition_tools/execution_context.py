"""
Execution context tools for state transition decisions

Provides tools for the AI agent to gather context about executions,
turns, conversations, and tool usage patterns.
"""

from typing import Optional, Dict, Any, List
import structlog
import httpx
from agno.tools.toolkit import Toolkit

logger = structlog.get_logger()


class ExecutionContextTools(Toolkit):
    """
    Tools for gathering execution context to inform state transition decisions
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        organization_id: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize execution context tools

        Args:
            base_url: Base URL for the control plane API
            organization_id: Organization context for filtering
            timeout: HTTP request timeout in seconds
        """
        super().__init__(name="execution_context_tools")
        self.base_url = base_url.rstrip("/")
        self.organization_id = organization_id
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the control plane API"""
        client = await self._get_client()
        response = await client.request(
            method=method,
            url=endpoint,
            params=params,
            json=json,
        )
        response.raise_for_status()
        return response.json()

    async def get_execution_details(self, execution_id: str) -> str:
        """
        Get detailed information about an execution

        Args:
            execution_id: The execution ID to fetch

        Returns:
            Formatted string with execution details including status, metadata, timestamps
        """
        try:
            logger.info("fetching_execution_details", execution_id=execution_id)

            result = await self._make_request(
                method="GET",
                endpoint=f"/api/v1/executions/{execution_id}",
            )

            execution = result.get("execution", result)

            # Format key information
            output = [
                f"Execution Details (ID: {execution_id}):",
                f"  Status: {execution.get('status', 'unknown')}",
                f"  Prompt: {execution.get('prompt', 'N/A')[:200]}...",
                f"  Started: {execution.get('started_at', 'N/A')}",
                f"  Completed: {execution.get('completed_at', 'N/A')}",
                f"  Response Preview: {execution.get('response', '')[:300]}...",
                f"  Error Message: {execution.get('error_message', 'None')}",
                f"  Agent ID: {execution.get('agent_id', 'N/A')}",
                f"  Team ID: {execution.get('team_id', 'N/A')}",
            ]

            # Add metadata if available
            if execution.get('execution_metadata'):
                output.append(f"  Metadata: {execution['execution_metadata']}")

            return "\n".join(output)

        except Exception as e:
            logger.error(
                "get_execution_details_failed",
                execution_id=execution_id,
                error=str(e),
            )
            return f"Error fetching execution details: {str(e)}"

    async def get_recent_turns(self, execution_id: str, limit: int = 5) -> str:
        """
        Get recent turns for an execution with metrics

        Args:
            execution_id: The execution ID
            limit: Maximum number of recent turns to fetch (default: 5)

        Returns:
            Formatted string with turn information including tokens, costs, finish reasons, tools called
        """
        try:
            logger.info(
                "fetching_recent_turns",
                execution_id=execution_id,
                limit=limit,
            )

            result = await self._make_request(
                method="GET",
                endpoint="/api/v1/analytics/turns",
                params={"execution_id": execution_id, "limit": limit},
            )

            turns = result.get("turns", [])

            if not turns:
                return f"No turns found for execution {execution_id}"

            output = [f"Recent Turns ({len(turns)} total, showing last {min(len(turns), limit)}):"]

            for turn in turns[-limit:]:
                turn_num = turn.get("turn_number", "?")
                output.append(f"\n--- Turn {turn_num} ---")
                output.append(f"  Model: {turn.get('model', 'N/A')}")
                output.append(f"  Finish Reason: {turn.get('finish_reason', 'N/A')}")
                output.append(f"  Duration: {turn.get('duration_ms', 0)}ms")
                output.append(f"  Tokens (in/out): {turn.get('input_tokens', 0)}/{turn.get('output_tokens', 0)}")
                output.append(f"  Tools Called: {turn.get('tools_called_count', 0)}")

                if turn.get('tools_called_names'):
                    output.append(f"  Tool Names: {', '.join(turn['tools_called_names'])}")

                if turn.get('response_preview'):
                    output.append(f"  Response: {turn['response_preview'][:150]}...")

                if turn.get('error_message'):
                    output.append(f"  Error: {turn['error_message'][:200]}")

            return "\n".join(output)

        except Exception as e:
            logger.error(
                "get_recent_turns_failed",
                execution_id=execution_id,
                error=str(e),
            )
            return f"Error fetching recent turns: {str(e)}"

    async def get_conversation_messages(self, execution_id: str, limit: int = 10) -> str:
        """
        Get conversation message history for an execution

        Args:
            execution_id: The execution ID
            limit: Maximum number of recent messages (default: 10)

        Returns:
            Formatted string with conversation messages
        """
        try:
            logger.info(
                "fetching_conversation_messages",
                execution_id=execution_id,
                limit=limit,
            )

            result = await self._make_request(
                method="GET",
                endpoint=f"/api/v1/executions/{execution_id}/messages",
                params={"limit": limit},
            )

            messages = result.get("messages", [])

            if not messages:
                return f"No conversation messages found for execution {execution_id}"

            output = [f"Conversation Messages ({len(messages)} total, showing last {limit}):"]

            for idx, msg in enumerate(messages[-limit:], 1):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "N/A")

                output.append(f"\n{idx}. [{role.upper()}] at {timestamp}:")
                output.append(f"   {content[:300]}...")

            return "\n".join(output)

        except Exception as e:
            logger.error(
                "get_conversation_messages_failed",
                execution_id=execution_id,
                error=str(e),
            )
            # Return empty conversation if endpoint doesn't exist yet
            return f"Conversation history not available: {str(e)}"

    async def get_tool_call_patterns(self, execution_id: str) -> str:
        """
        Analyze tool call patterns for an execution

        Args:
            execution_id: The execution ID

        Returns:
            Formatted string with tool usage statistics and patterns
        """
        try:
            logger.info(
                "analyzing_tool_call_patterns",
                execution_id=execution_id,
            )

            result = await self._make_request(
                method="GET",
                endpoint="/api/v1/analytics/tool-calls",
                params={"execution_id": execution_id},
            )

            tool_calls = result.get("tool_calls", [])

            if not tool_calls:
                return f"No tool calls found for execution {execution_id}"

            # Analyze patterns
            total_calls = len(tool_calls)
            successful_calls = sum(1 for tc in tool_calls if tc.get("success", False))
            failed_calls = total_calls - successful_calls

            # Count by tool name
            tool_counts: Dict[str, int] = {}
            tool_failures: Dict[str, int] = {}

            for tc in tool_calls:
                tool_name = tc.get("tool_name", "unknown")
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
                if not tc.get("success", False):
                    tool_failures[tool_name] = tool_failures.get(tool_name, 0) + 1

            output = [
                f"Tool Call Analysis:",
                f"  Total Calls: {total_calls}",
                f"  Successful: {successful_calls} ({100*successful_calls//total_calls if total_calls > 0 else 0}%)",
                f"  Failed: {failed_calls} ({100*failed_calls//total_calls if total_calls > 0 else 0}%)",
                f"\nMost Used Tools:",
            ]

            for tool_name, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                failures = tool_failures.get(tool_name, 0)
                output.append(f"  - {tool_name}: {count} calls ({failures} failed)")

            return "\n".join(output)

        except Exception as e:
            logger.error(
                "get_tool_call_patterns_failed",
                execution_id=execution_id,
                error=str(e),
            )
            return f"Tool call analysis not available: {str(e)}"

    async def check_error_recoverability(self, execution_id: str, error_message: Optional[str]) -> str:
        """
        Determine if an error is recoverable or requires user intervention

        Args:
            execution_id: The execution ID
            error_message: The error message to analyze

        Returns:
            Assessment of error recoverability
        """
        try:
            if not error_message:
                return "No error detected - execution appears healthy"

            error_lower = error_message.lower()

            # Unrecoverable errors (need user intervention)
            unrecoverable_patterns = [
                "authentication failed",
                "unauthorized",
                "forbidden",
                "access denied",
                "invalid credentials",
                "permission denied",
                "quota exceeded",
                "rate limit exceeded",
                "timeout",
                "network unreachable",
                "connection refused",
                "not found",
                "does not exist",
            ]

            # Recoverable errors (can retry)
            recoverable_patterns = [
                "temporary",
                "retry",
                "throttled",
                "busy",
                "unavailable",
            ]

            is_unrecoverable = any(pattern in error_lower for pattern in unrecoverable_patterns)
            is_recoverable = any(pattern in error_lower for pattern in recoverable_patterns)

            if is_unrecoverable:
                return (
                    f"Error Assessment: UNRECOVERABLE\n"
                    f"  Error: {error_message[:200]}\n"
                    f"  Recommendation: Requires user intervention. Execution should be marked as FAILED."
                )
            elif is_recoverable:
                return (
                    f"Error Assessment: RECOVERABLE\n"
                    f"  Error: {error_message[:200]}\n"
                    f"  Recommendation: Can be retried. Execution can continue or wait for retry."
                )
            else:
                return (
                    f"Error Assessment: UNCERTAIN\n"
                    f"  Error: {error_message[:200]}\n"
                    f"  Recommendation: Use caution. Consider context and turn history to decide."
                )

        except Exception as e:
            logger.error(
                "check_error_recoverability_failed",
                execution_id=execution_id,
                error=str(e),
            )
            return f"Error recoverability check failed: {str(e)}"

    async def get_current_state(self, execution_id: str) -> str:
        """
        Get the current state of an execution

        Args:
            execution_id: The execution ID

        Returns:
            Current execution state
        """
        try:
            result = await self._make_request(
                method="GET",
                endpoint=f"/api/v1/executions/{execution_id}",
            )

            execution = result.get("execution", result)
            current_status = execution.get("status", "unknown")

            return f"Current State: {current_status}"

        except Exception as e:
            logger.error(
                "get_current_state_failed",
                execution_id=execution_id,
                error=str(e),
            )
            return f"Unable to determine current state: {str(e)}"
