"""
EventFormatter - Centralized SSE event formatting for execution streaming.

This module provides a clean interface for formatting Server-Sent Events (SSE)
according to the SSE specification with proper event IDs for gap recovery.

SSE Format:
    id: {execution_id}_{counter}_{timestamp_micros}
    event: {event_type}
    data: {json_payload}
    {blank line}

Event Types:
    - connected: Initial connection confirmation
    - message: Chat messages (user, assistant, tool, system)
    - history_complete: History loading complete
    - status: Execution status updates
    - tool_started: Tool execution started
    - tool_completed: Tool execution completed
    - member_tool_started: Team member tool execution started
    - member_tool_completed: Team member tool execution completed
    - message_chunk: Streaming message chunks (for real-time token streaming)
    - member_message_chunk: Team member message chunks
    - member_message_complete: Team member message streaming complete
    - thinking_start: Beginning of thinking/reasoning block
    - thinking_delta: Incremental thinking content
    - thinking_complete: End of thinking block with signature
    - member_thinking_start: Team member thinking start
    - member_thinking_delta: Team member thinking content
    - member_thinking_complete: Team member thinking end
    - done: Execution completed successfully
    - error: Execution failed
    - degraded: Degraded mode notification (Redis down, worker down)
    - reconnect: Server requesting client reconnect
    - timeout_warning: Connection timeout warning
    - gap_detected: Event gap detected, client should reconnect

Test Strategy:
    - Unit test each format method for SSE compliance
    - Verify event ID generation uniqueness and format
    - Test JSON serialization edge cases (None, nested objects, special chars)
    - Test multi-line data handling
    - Verify all fields present (id, event, data, blank line)
    - Test thread-safety of counter increment
"""

import json
import time
from typing import Any, Dict, Optional


class EventFormatter:
    """
    Formats Server-Sent Events (SSE) for execution streaming.

    Handles:
    - Event ID generation with sequential counter
    - JSON serialization of payloads
    - Proper SSE format compliance
    - Multiple event types with specialized formatting

    Example:
        >>> formatter = EventFormatter("exec-123")
        >>> event = formatter.format_connected_event("org-456", "pending")
        >>> print(event)
        id: exec-123_1_1702938457123456
        event: connected
        data: {"execution_id": "exec-123", "organization_id": "org-456", "status": "pending", "connected_at": 1702938457.123456}

    """

    def __init__(self, execution_id: str):
        """
        Initialize event formatter for a specific execution.

        Args:
            execution_id: Unique execution identifier
        """
        self.execution_id = execution_id
        self._counter = 0

    def generate_event_id(self) -> str:
        """
        Generate unique event ID with sequential counter and microsecond timestamp.

        Format: {execution_id}_{counter}_{timestamp_micros}

        The counter ensures sequential ordering within a stream, while the
        microsecond timestamp provides global uniqueness across reconnections.

        Returns:
            str: Unique event ID

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> event_id1 = formatter.generate_event_id()
            >>> event_id2 = formatter.generate_event_id()
            >>> # event_id1: "exec-123_1_1702938457123456"
            >>> # event_id2: "exec-123_2_1702938457124789"
        """
        self._counter += 1
        timestamp_micros = int(time.time() * 1000000)
        return f"{self.execution_id}_{self._counter}_{timestamp_micros}"

    def format_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        event_id: Optional[str] = None
    ) -> str:
        """
        Generic SSE event formatter.

        Generates proper SSE format with id, event, data fields and blank line terminator.

        Args:
            event_type: Type of event (e.g., "message", "status", "done")
            data: Event payload to JSON-serialize
            event_id: Optional custom event ID (auto-generated if not provided)

        Returns:
            str: Formatted SSE event string

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> event = formatter.format_event("status", {"status": "running"})
            >>> print(event)
            id: exec-123_1_1702938457123456
            event: status
            data: {"status": "running"}

        """
        if event_id is None:
            event_id = self.generate_event_id()

        # JSON serialize data with proper error handling
        try:
            data_json = json.dumps(data)
        except (TypeError, ValueError) as e:
            # Fallback to error payload if serialization fails
            data_json = json.dumps({
                "error": "Failed to serialize event data",
                "error_type": "serialization_error",
                "details": str(e)
            })

        # SSE format: id, event, data, blank line
        return f"id: {event_id}\nevent: {event_type}\ndata: {data_json}\n\n"

    def format_connected_event(
        self,
        organization_id: str,
        status: str = "pending"
    ) -> str:
        """
        Format 'connected' event sent immediately on connection.

        This event is sent first to unblock the EventSource connection before
        any slow operations (Temporal queries, DB lookups) are performed.

        Args:
            organization_id: Organization ID for the execution
            status: Current execution status (default: "pending")

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> event = formatter.format_connected_event("org-456", "running")
            >>> print(event)
            id: exec-123_1_1702938457123456
            event: connected
            data: {"execution_id": "exec-123", "organization_id": "org-456", "status": "running", "connected_at": 1702938457.123456}

        """
        data = {
            "execution_id": self.execution_id,
            "organization_id": organization_id,
            "status": status,
            "connected_at": time.time()
        }
        return self.format_event("connected", data)

    def format_message_event(self, message: Dict[str, Any]) -> str:
        """
        Format 'message' event for chat messages.

        Handles user, assistant, tool, and system messages with all metadata.

        Args:
            message: Message dictionary with fields like role, content, timestamp, etc.

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> message = {
            ...     "role": "user",
            ...     "content": "Hello",
            ...     "timestamp": "2024-12-18T10:00:00Z",
            ...     "message_id": "msg-456"
            ... }
            >>> event = formatter.format_message_event(message)
        """
        return self.format_event("message", message)

    def format_history_complete_event(
        self,
        message_count: int,
        is_truncated: bool = False,
        has_more: bool = False
    ) -> str:
        """
        Format 'history_complete' event.

        Signals that historical messages have been fully loaded.

        Args:
            message_count: Number of messages loaded
            is_truncated: Whether history was truncated (default: False)
            has_more: Whether there are more messages available (default: False)

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> event = formatter.format_history_complete_event(42, is_truncated=True)
            >>> print(event)
            id: exec-123_1_1702938457123456
            event: history_complete
            data: {"execution_id": "exec-123", "message_count": 42, "is_truncated": true, "has_more": false}

        """
        data = {
            "execution_id": self.execution_id,
            "message_count": message_count,
            "is_truncated": is_truncated,
            "has_more": has_more
        }
        return self.format_event("history_complete", data)

    def format_status_event(
        self,
        status: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Format 'status' event for execution status changes.

        Args:
            status: New status (e.g., "pending", "running", "completed", "failed")
            metadata: Optional additional metadata (e.g., source="database")

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> event = formatter.format_status_event("running")
            >>> print(event)
            id: exec-123_1_1702938457123456
            event: status
            data: {"status": "running", "execution_id": "exec-123"}

        """
        data = {
            "status": status,
            "execution_id": self.execution_id
        }
        if metadata:
            data.update(metadata)
        return self.format_event("status", data)

    def format_tool_started_event(self, tool_data: Dict[str, Any]) -> str:
        """
        Format 'tool_started' event for tool execution started.

        Args:
            tool_data: Tool execution data with nested structure:
                {
                    "data": {
                        "tool_name": str,
                        "tool_execution_id": str,
                        "tool_input": dict,
                        ...
                    },
                    "timestamp": str
                }

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> tool_data = {
            ...     "data": {
            ...         "tool_name": "search",
            ...         "tool_execution_id": "tool-789",
            ...         "tool_input": {"query": "test"}
            ...     },
            ...     "timestamp": "2024-12-18T10:00:00Z"
            ... }
            >>> event = formatter.format_tool_started_event(tool_data)
        """
        return self.format_event("tool_started", tool_data)

    def format_tool_completed_event(self, tool_data: Dict[str, Any]) -> str:
        """
        Format 'tool_completed' event for tool execution completed.

        Args:
            tool_data: Tool execution data with nested structure:
                {
                    "data": {
                        "tool_name": str,
                        "tool_execution_id": str,
                        "tool_output": Any,
                        "tool_status": str,
                        ...
                    },
                    "timestamp": str
                }

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> tool_data = {
            ...     "data": {
            ...         "tool_name": "search",
            ...         "tool_execution_id": "tool-789",
            ...         "tool_output": {"results": [...]},
            ...         "tool_status": "completed"
            ...     },
            ...     "timestamp": "2024-12-18T10:00:01Z"
            ... }
            >>> event = formatter.format_tool_completed_event(tool_data)
        """
        return self.format_event("tool_completed", tool_data)

    def format_member_tool_started_event(self, tool_data: Dict[str, Any]) -> str:
        """
        Format 'member_tool_started' event for team member tool execution started.

        Used in multi-agent scenarios when a team member starts executing a tool.

        Args:
            tool_data: Tool execution data with nested structure:
                {
                    "data": {
                        "tool_name": str,
                        "tool_execution_id": str,
                        "member_name": str,
                        "parent_message_id": str,
                        "tool_arguments": dict,
                        ...
                    },
                    "timestamp": str
                }

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> tool_data = {
            ...     "data": {
            ...         "tool_name": "search",
            ...         "tool_execution_id": "tool-789",
            ...         "member_name": "Researcher",
            ...         "tool_arguments": {"query": "test"}
            ...     },
            ...     "timestamp": "2024-12-18T10:00:00Z"
            ... }
            >>> event = formatter.format_member_tool_started_event(tool_data)
        """
        return self.format_event("member_tool_started", tool_data)

    def format_member_tool_completed_event(self, tool_data: Dict[str, Any]) -> str:
        """
        Format 'member_tool_completed' event for team member tool execution completed.

        Used in multi-agent scenarios when a team member finishes executing a tool.

        Args:
            tool_data: Tool execution data with nested structure:
                {
                    "data": {
                        "tool_name": str,
                        "tool_execution_id": str,
                        "member_name": str,
                        "status": str,
                        "tool_output": Any,
                        "tool_error": Any,
                        ...
                    },
                    "timestamp": str
                }

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> tool_data = {
            ...     "data": {
            ...         "tool_name": "search",
            ...         "tool_execution_id": "tool-789",
            ...         "member_name": "Researcher",
            ...         "status": "success",
            ...         "tool_output": {"results": [...]}
            ...     },
            ...     "timestamp": "2024-12-18T10:00:01Z"
            ... }
            >>> event = formatter.format_member_tool_completed_event(tool_data)
        """
        return self.format_event("member_tool_completed", tool_data)

    def format_message_chunk_event(self, chunk_data: Dict[str, Any]) -> str:
        """
        Format 'message_chunk' event for streaming message chunks.

        Used for real-time token streaming of assistant responses.

        Args:
            chunk_data: Chunk data with nested structure:
                {
                    "data": {
                        "content": str,
                        "message_id": str,
                        "is_final": bool,
                        ...
                    },
                    "timestamp": str
                }

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> chunk_data = {
            ...     "data": {
            ...         "content": "Hello",
            ...         "message_id": "msg-456",
            ...         "is_final": False
            ...     },
            ...     "timestamp": "2024-12-18T10:00:00Z"
            ... }
            >>> event = formatter.format_message_chunk_event(chunk_data)
        """
        return self.format_event("message_chunk", chunk_data)

    def format_member_message_chunk_event(self, chunk_data: Dict[str, Any]) -> str:
        """
        Format 'member_message_chunk' event for team member message chunks.

        Used for streaming messages from team members in multi-agent scenarios.

        Args:
            chunk_data: Chunk data with nested structure similar to message_chunk

        Returns:
            str: Formatted SSE event
        """
        return self.format_event("member_message_chunk", chunk_data)

    def format_member_message_complete_event(self, data: Dict[str, Any]) -> str:
        """
        Format 'member_message_complete' event for end of team member message.

        Used to signal that a team member has finished streaming their message.

        Args:
            data: Event data with nested structure:
                {
                    "data": {
                        "message_id": str,
                        "member_name": str,
                        ...
                    },
                    "timestamp": str
                }

        Returns:
            str: Formatted SSE event
        """
        return self.format_event("member_message_complete", data)

    # =========================================================================
    # Thinking/Reasoning Event Methods (Extended Thinking Support)
    # =========================================================================

    def format_thinking_start_event(
        self,
        message_id: str,
        index: int = 0,
        budget_tokens: Optional[int] = None
    ) -> str:
        """
        Format 'thinking_start' event for beginning of thinking block.

        Sent when the model begins extended thinking/reasoning before generating
        a response. This event signals the UI to show a thinking indicator.

        Args:
            message_id: ID of the message being generated
            index: Content block index (default: 0)
            budget_tokens: Optional thinking token budget configured for this request

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> event = formatter.format_thinking_start_event("msg_abc", budget_tokens=10000)
            >>> print(event)
            id: exec-123_1_1702938457123456
            event: thinking_start
            data: {"execution_id": "exec-123", "message_id": "msg_abc", "index": 0, "budget_tokens": 10000}

        """
        data = {
            "execution_id": self.execution_id,
            "message_id": message_id,
            "index": index,
        }
        if budget_tokens is not None:
            data["budget_tokens"] = budget_tokens
        return self.format_event("thinking_start", data)

    def format_thinking_delta_event(
        self,
        message_id: str,
        thinking: str,
        index: int = 0
    ) -> str:
        """
        Format 'thinking_delta' event for incremental thinking content.

        Streams reasoning content as the model thinks through the problem.
        Clients should accumulate deltas for the same message_id + index.

        Args:
            message_id: ID of the message being generated
            thinking: Incremental thinking content (may be multiline with markdown)
            index: Content block index (default: 0)

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> event = formatter.format_thinking_delta_event(
            ...     "msg_abc",
            ...     "Step 1: Analyze the requirements\\n\\nFirst, I need to..."
            ... )

        """
        data = {
            "execution_id": self.execution_id,
            "message_id": message_id,
            "thinking": thinking,
            "index": index,
        }
        return self.format_event("thinking_delta", data)

    def format_thinking_complete_event(
        self,
        message_id: str,
        index: int = 0,
        signature: Optional[str] = None,
        tokens_used: Optional[int] = None
    ) -> str:
        """
        Format 'thinking_complete' event for end of thinking block.

        Sent when thinking is complete, includes optional signature for verification.
        The signature is opaque and should be stored/passed through unchanged.

        Args:
            message_id: ID of the message being generated
            index: Content block index (default: 0)
            signature: Optional verification signature from Anthropic API
            tokens_used: Optional actual tokens used for thinking

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> event = formatter.format_thinking_complete_event(
            ...     "msg_abc",
            ...     signature="EqQBCgIYAhIM...",
            ...     tokens_used=1024
            ... )

        """
        data = {
            "execution_id": self.execution_id,
            "message_id": message_id,
            "index": index,
        }
        if signature is not None:
            data["signature"] = signature
        if tokens_used is not None:
            data["tokens_used"] = tokens_used
        return self.format_event("thinking_complete", data)

    def format_member_thinking_start_event(
        self,
        member_name: str,
        index: int = 0,
        member_id: Optional[str] = None,
        budget_tokens: Optional[int] = None
    ) -> str:
        """
        Format 'member_thinking_start' event for team member thinking.

        Sent when a sub-agent/team member begins thinking.
        Note: Sub-agents currently don't support transparent thinking mode,
        this is reserved for future SDK enhancements.

        Args:
            member_name: Name of the team member/sub-agent
            index: Content block index (default: 0)
            member_id: Optional sub-agent ID
            budget_tokens: Optional thinking token budget

        Returns:
            str: Formatted SSE event
        """
        data = {
            "execution_id": self.execution_id,
            "member_name": member_name,
            "index": index,
        }
        if member_id is not None:
            data["member_id"] = member_id
        if budget_tokens is not None:
            data["budget_tokens"] = budget_tokens
        return self.format_event("member_thinking_start", data)

    def format_member_thinking_delta_event(
        self,
        member_name: str,
        thinking: str,
        index: int = 0,
        member_id: Optional[str] = None
    ) -> str:
        """
        Format 'member_thinking_delta' event for team member thinking content.

        Streams reasoning content from a sub-agent/team member.
        Note: Sub-agents currently don't support transparent thinking mode,
        this is reserved for future SDK enhancements.

        Args:
            member_name: Name of the team member/sub-agent
            thinking: Incremental thinking content
            index: Content block index (default: 0)
            member_id: Optional sub-agent ID

        Returns:
            str: Formatted SSE event
        """
        data = {
            "execution_id": self.execution_id,
            "member_name": member_name,
            "thinking": thinking,
            "index": index,
        }
        if member_id is not None:
            data["member_id"] = member_id
        return self.format_event("member_thinking_delta", data)

    def format_member_thinking_complete_event(
        self,
        member_name: str,
        index: int = 0,
        member_id: Optional[str] = None,
        signature: Optional[str] = None,
        tokens_used: Optional[int] = None
    ) -> str:
        """
        Format 'member_thinking_complete' event for end of member thinking.

        Sent when a sub-agent/team member completes thinking.
        Note: Sub-agents currently don't support transparent thinking mode,
        this is reserved for future SDK enhancements.

        Args:
            member_name: Name of the team member/sub-agent
            index: Content block index (default: 0)
            member_id: Optional sub-agent ID
            signature: Optional verification signature
            tokens_used: Optional actual tokens used

        Returns:
            str: Formatted SSE event
        """
        data = {
            "execution_id": self.execution_id,
            "member_name": member_name,
            "index": index,
        }
        if member_id is not None:
            data["member_id"] = member_id
        if signature is not None:
            data["signature"] = signature
        if tokens_used is not None:
            data["tokens_used"] = tokens_used
        return self.format_event("member_thinking_complete", data)

    def format_done_event(
        self,
        response: Any = None,
        usage: Optional[Dict] = None,
        workflow_status: Optional[str] = None
    ) -> str:
        """
        Format 'done' event for successful completion.

        Args:
            response: Optional response data
            usage: Optional usage statistics (tokens, cost, etc.)
            workflow_status: Optional Temporal workflow status

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> event = formatter.format_done_event(
            ...     response="Task completed",
            ...     usage={"tokens": 150, "cost": 0.003}
            ... )
            >>> print(event)
            id: exec-123_1_1702938457123456
            event: done
            data: {"execution_id": "exec-123", "response": "Task completed", "usage": {"tokens": 150, "cost": 0.003}}

        """
        data = {
            "execution_id": self.execution_id
        }
        if response is not None:
            data["response"] = response
        if usage is not None:
            data["usage"] = usage
        if workflow_status is not None:
            data["workflow_status"] = workflow_status
        return self.format_event("done", data)

    def format_error_event(
        self,
        error: str,
        error_type: str = "execution_error",
        status: str = "failed"
    ) -> str:
        """
        Format 'error' event for failures.

        Args:
            error: Error message
            error_type: Type of error (default: "execution_error")
            status: Execution status (default: "failed")

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> event = formatter.format_error_event(
            ...     "Connection timeout",
            ...     error_type="timeout_error"
            ... )
            >>> print(event)
            id: exec-123_1_1702938457123456
            event: error
            data: {"error": "Connection timeout", "error_type": "timeout_error", "execution_id": "exec-123", "status": "failed"}

        """
        data = {
            "error": error,
            "error_type": error_type,
            "execution_id": self.execution_id,
            "status": status
        }
        return self.format_event("error", data)

    def format_degraded_event(
        self,
        mode: str,
        reason: str,
        message: Optional[str] = None,
        capabilities: Optional[list] = None
    ) -> str:
        """
        Format 'degraded' event for degraded mode notification.

        Sent when the stream falls back to slower polling modes due to
        infrastructure issues (Redis down, Temporal worker down, etc.).

        Args:
            mode: Degradation mode (e.g., "history_only", "live_only", "degraded", "unavailable")
            reason: Reason for degraded mode (e.g., "redis_unavailable", "worker_down")
            message: User-friendly explanation (optional)
            capabilities: List of available capabilities in this mode (optional)

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> event = formatter.format_degraded_event(
            ...     mode="history_only",
            ...     reason="redis_unavailable",
            ...     message="Real-time events unavailable, using workflow polling (slower updates)",
            ...     capabilities=["history"]
            ... )
        """
        data = {
            "execution_id": self.execution_id,
            "mode": mode,
            "reason": reason,
        }
        if message:
            data["message"] = message
        if capabilities is not None:
            data["capabilities"] = capabilities
        return self.format_event("degraded", data)

    def format_recovered_event(
        self,
        message: str = "Services recovered, resuming full functionality"
    ) -> str:
        """
        Format 'recovered' event for service recovery notification.

        Sent when services recover from degraded mode back to full functionality.

        Args:
            message: Recovery notification message

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> event = formatter.format_recovered_event()
            >>> print(event)
            id: exec-123_1_1702938457123456
            event: recovered
            data: {"execution_id": "exec-123", "message": "Services recovered, resuming full functionality"}

        """
        data = {
            "execution_id": self.execution_id,
            "message": message
        }
        return self.format_event("recovered", data)

    def format_reconnect_event(
        self,
        reason: str,
        duration: Optional[float] = None
    ) -> str:
        """
        Format 'reconnect' event for server-requested reconnection.

        Tells the client to gracefully reconnect (won't count as failed attempt).

        Args:
            reason: Reason for reconnect (e.g., "timeout", "server_restart")
            duration: Optional duration in seconds before timeout

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> event = formatter.format_reconnect_event("timeout", duration=300.5)
            >>> print(event)
            id: exec-123_1_1702938457123456
            event: reconnect
            data: {"reason": "timeout", "duration": 300.5}

        """
        data = {"reason": reason}
        if duration is not None:
            data["duration"] = duration
        return self.format_event("reconnect", data)

    def format_timeout_warning_event(self, remaining_seconds: int) -> str:
        """
        Format 'timeout_warning' event for connection timeout warnings.

        Sent in the last 30 seconds before connection timeout.

        Args:
            remaining_seconds: Seconds remaining before timeout

        Returns:
            str: Formatted SSE event

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> event = formatter.format_timeout_warning_event(15)
        """
        data = {"remaining_seconds": remaining_seconds}
        return self.format_event("timeout_warning", data)

    def format_gap_detected_event(
        self,
        reason: str,
        buffer_oldest: Optional[str] = None
    ) -> str:
        """
        Format 'gap_detected' event when event buffer can't recover gaps.

        Signals client should reconnect to get missing events.

        Args:
            reason: Reason for gap (e.g., "Event buffer miss - events too old")
            buffer_oldest: Oldest event ID in buffer

        Returns:
            str: Formatted SSE event
        """
        data = {
            "execution_id": self.execution_id,
            "reason": reason
        }
        if buffer_oldest is not None:
            data["buffer_oldest"] = buffer_oldest
        return self.format_event("gap_detected", data)

    def format_keepalive(self) -> str:
        """
        Format keepalive comment (not an event).

        SSE comments start with ':' and don't have id/event/data fields.
        Prevents connection timeout during periods of no activity.

        Returns:
            str: SSE comment string

        Example:
            >>> formatter = EventFormatter("exec-123")
            >>> keepalive = formatter.format_keepalive()
            >>> print(keepalive)
            : keepalive

        """
        return ": keepalive\n\n"
