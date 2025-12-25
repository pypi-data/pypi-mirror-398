"""
Message history loader for streaming execution data.

This module provides a HistoryLoader class that retrieves historical messages from
the database (PostgreSQL Session table) with Temporal workflow state as fallback.
Messages are streamed progressively using an async generator for non-blocking
rendering in the UI.

Key Features:
- Primary source: PostgreSQL Session table (fast, reliable)
- Fallback source: Temporal workflow state (when DB is empty)
- Progressive streaming: yields messages one-at-a-time for instant UI rendering
- Message deduplication: integrates with MessageDeduplicator
- Message limiting: caps at last 200 messages for performance
- Chronological sorting: ensures proper conversation flow
- Timeout protection: 3-second timeout for Temporal queries

Architecture:
This class is part of the Resumable Execution Stream Architecture:
1. HistoryLoader: Loads and streams historical messages (this module)
2. MessageDeduplicator: Prevents duplicate messages across history/live streams
3. LiveStreamProcessor: Handles real-time Redis stream events (future)

Test Strategy:
- Unit test database loading with various message counts (0, 1, 100, 300)
- Test Temporal fallback when DB empty
- Test yielding behavior (progressive, not batched)
- Test timeout handling for Temporal queries (3s limit)
- Test message sorting and chronological order
- Test message limit enforcement (200 cap)
- Test edge cases: no messages, DB errors, empty session record
- Integration test with MessageDeduplicator
"""

import asyncio
import hashlib
import time
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

import structlog
from sqlalchemy.orm import Session as SQLAlchemySession

from control_plane_api.app.models.session import Session as SessionModel
from control_plane_api.app.workflows.agent_execution import (
    AgentExecutionWorkflow,
    ChatMessage,
)
from .deduplication import MessageDeduplicator

logger = structlog.get_logger(__name__)


# Message limit for performance optimization
# Loading >200 messages can slow down initial rendering
# Most conversations don't exceed 100 messages
MAX_HISTORY_MESSAGES = 200


class HistoryLoader:
    """
    Handles loading historical messages from database with Temporal fallback.

    This class manages the initial message history load when a client connects
    to the streaming execution endpoint. It attempts to load messages from the
    PostgreSQL Session table first (fast, reliable), falling back to Temporal
    workflow state if the database has no messages (e.g., new execution, DB lag).

    The loader yields messages progressively as an async generator, allowing
    the UI to render messages immediately without waiting for the entire history
    to load. This provides instant feedback to users even for long conversations.

    Message deduplication is handled via the provided MessageDeduplicator instance,
    ensuring that messages aren't duplicated between history and live streams.

    Example usage:
        deduplicator = MessageDeduplicator()
        loader = HistoryLoader(
            execution_id="exec-123",
            organization_id="org-456",
            db_session=db,
            temporal_client=temporal_client,
            deduplicator=deduplicator,
        )

        async for message in loader.stream():
            # Send message to client
            yield format_sse_message(message)
    """

    def __init__(
        self,
        execution_id: str,
        organization_id: str,
        db_session: SQLAlchemySession,
        temporal_client: Any,  # temporalio.client.Client
        deduplicator: MessageDeduplicator,
        workflow_id: Optional[str] = None,
    ):
        """
        Initialize the history loader.

        Args:
            execution_id: Execution ID to load history for
            organization_id: Organization ID for security filtering
            db_session: SQLAlchemy database session
            temporal_client: Temporal client for workflow queries
            deduplicator: Message deduplicator instance
            workflow_id: Workflow ID for Temporal queries (defaults to agent-execution-{execution_id})
        """
        self.execution_id = execution_id
        self.organization_id = organization_id
        self.db_session = db_session
        self.temporal_client = temporal_client
        self.deduplicator = deduplicator
        self.workflow_id = workflow_id or f"agent-execution-{execution_id}"

        # Statistics for monitoring
        self._stats = {
            "db_messages_loaded": 0,
            "temporal_messages_loaded": 0,
            "messages_sent": 0,
            "messages_skipped_empty": 0,
            "messages_deduplicated": 0,
            "db_load_duration_ms": 0,
            "temporal_load_duration_ms": 0,
        }

    async def stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream historical messages progressively.

        This method loads messages from the database first, falling back to
        Temporal workflow state if no messages are found. Messages are yielded
        one at a time for non-blocking progressive rendering.

        The method performs the following steps:
        1. Load messages from database (PostgreSQL Session table)
        2. If no messages found, try Temporal workflow fallback
        3. Sort messages chronologically
        4. Limit to last 200 messages if needed
        5. Yield messages one at a time, checking deduplication

        Yields:
            Message dictionaries with keys:
            - message_id: Unique message identifier
            - role: Message role (user, assistant, system, tool)
            - content: Message content
            - timestamp: ISO format timestamp
            - tool_name, tool_input, tool_output: Tool data (if applicable)
            - workflow_name, workflow_steps, etc.: Workflow data (if applicable)
            - user_id, user_name, user_email, user_avatar: User attribution (if applicable)

        Raises:
            Exception: If both database and Temporal loading fail (logged but not raised)
        """
        import time

        # Step 1: Try loading from database
        t0 = time.time()
        messages = await self._load_from_database()
        self._stats["db_load_duration_ms"] = int((time.time() - t0) * 1000)
        self._stats["db_messages_loaded"] = len(messages)

        # Step 2: Fallback to Temporal if no messages in database
        if not messages:
            logger.info(
                "no_database_history_attempting_temporal_fallback",
                execution_id=self.execution_id,
            )
            t0 = time.time()
            messages = await self._load_from_temporal()
            self._stats["temporal_load_duration_ms"] = int((time.time() - t0) * 1000)
            self._stats["temporal_messages_loaded"] = len(messages)

        if not messages:
            logger.info(
                "no_history_messages_found",
                execution_id=self.execution_id,
                stats=self._stats,
            )
            return

        # Step 3: Sort messages chronologically
        # CRITICAL: Messages must be in exact order for proper conversation flow
        messages.sort(key=lambda m: self._parse_timestamp(m.get("timestamp", "")))

        logger.info(
            "history_messages_loaded_and_sorted",
            execution_id=self.execution_id,
            message_count=len(messages),
            first_timestamp=messages[0].get("timestamp") if messages else None,
            last_timestamp=messages[-1].get("timestamp") if messages else None,
            stats=self._stats,
        )

        # Step 4: Limit to last N messages for performance
        if len(messages) > MAX_HISTORY_MESSAGES:
            original_count = len(messages)
            messages = messages[-MAX_HISTORY_MESSAGES:]
            logger.info(
                "history_messages_limited_for_performance",
                execution_id=self.execution_id,
                original_count=original_count,
                limited_count=len(messages),
                limit=MAX_HISTORY_MESSAGES,
            )

        # Step 5: Stream messages one at a time
        for msg in messages:
            # Skip messages with empty content UNLESS they have tool/workflow data
            has_content = msg.get("content") and msg.get("content").strip()
            has_tool_data = bool(
                msg.get("tool_name")
                or msg.get("tool_input")
                or msg.get("tool_output")
                or msg.get("tool_error")
            )
            has_workflow_data = bool(
                msg.get("workflow_name")
                or msg.get("workflow_steps")
                or msg.get("workflow_status")
            )

            if not has_content and not has_tool_data and not has_workflow_data:
                self._stats["messages_skipped_empty"] += 1
                logger.debug(
                    "skipping_empty_message",
                    execution_id=self.execution_id,
                    message_id=msg.get("message_id"),
                    role=msg.get("role"),
                )
                continue

            # Check deduplication
            if self.deduplicator.is_sent(msg):
                self._stats["messages_deduplicated"] += 1
                logger.debug(
                    "skipping_duplicate_message",
                    execution_id=self.execution_id,
                    message_id=msg.get("message_id"),
                    role=msg.get("role"),
                )
                continue

            # Mark as sent for deduplication
            self.deduplicator.mark_sent(msg)
            self._stats["messages_sent"] += 1

            # Yield the message
            yield msg

        logger.info(
            "history_streaming_complete",
            execution_id=self.execution_id,
            stats=self._stats,
        )

    async def _load_from_database(self) -> List[Dict[str, Any]]:
        """
        Load messages from PostgreSQL Session table.

        This is the primary source for message history. The Session table stores
        messages as JSONB array, which is fast to query and doesn't require joins.

        The method queries the Session table by execution_id and organization_id,
        extracts the messages array, and converts to standard message dictionaries.

        Returns:
            List of message dictionaries, or empty list if no session found
        """
        try:
            # Query session record
            session_record = (
                self.db_session.query(SessionModel)
                .filter(
                    SessionModel.execution_id == self.execution_id,
                    SessionModel.organization_id == self.organization_id,
                )
                .first()
            )

            if not session_record:
                logger.warning(
                    "no_session_record_found_in_database",
                    execution_id=self.execution_id,
                    organization_id=self.organization_id,
                )
                return []

            # Extract messages from JSONB array
            messages_data = session_record.messages or []

            if not messages_data:
                logger.warning(
                    "session_record_found_but_no_messages",
                    execution_id=self.execution_id,
                    session_id=session_record.session_id,
                    created_at=str(session_record.created_at),
                )
                return []

            logger.info(
                "loaded_messages_from_database",
                execution_id=self.execution_id,
                message_count=len(messages_data),
            )

            # Convert to standard message dictionaries
            # Messages are already dicts in JSONB, so just ensure they have required fields
            messages = []
            for msg_data in messages_data:
                # Ensure message has required fields
                message = {
                    "message_id": msg_data.get("message_id"),
                    "role": msg_data.get("role"),
                    "content": msg_data.get("content"),
                    "timestamp": msg_data.get("timestamp"),
                }

                # Add optional fields if present
                optional_fields = [
                    "tool_name",
                    "tool_input",
                    "tool_output",
                    "tool_error",
                    "workflow_name",
                    "workflow_status",
                    "workflow_steps",
                    "workflow_runner",
                    "workflow_type",
                    "workflow_duration",
                    "workflow_error",
                    "user_id",
                    "user_name",
                    "user_email",
                    "user_avatar",
                    "metadata",
                ]
                for field in optional_fields:
                    if field in msg_data and msg_data[field] is not None:
                        message[field] = msg_data[field]

                messages.append(message)

            # Normalize old message ID formats for backward compatibility
            self._normalize_message_ids(messages)

            return messages

        except Exception as e:
            logger.error(
                "database_load_failed",
                execution_id=self.execution_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return []

    async def _load_from_temporal(self) -> List[Dict[str, Any]]:
        """
        Fallback: Load messages from Temporal workflow state.

        This method is used when the database has no messages, which can happen
        for new executions or if there's DB replication lag. It queries the
        Temporal workflow state to get the current message history.

        The method has a 3-second timeout to prevent blocking the stream if the
        Temporal worker is down or slow. If the timeout is exceeded, an empty
        list is returned and the stream continues without history.

        Returns:
            List of message dictionaries, or empty list if query fails/times out
        """
        try:
            # Get workflow handle
            workflow_handle = self.temporal_client.get_workflow_handle(
                self.workflow_id
            )

            # Query workflow state with 3-second timeout
            # This prevents 29-second hangs when worker is down
            try:
                state = await asyncio.wait_for(
                    workflow_handle.query(AgentExecutionWorkflow.get_state),
                    timeout=3.0,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "temporal_fallback_timeout",
                    execution_id=self.execution_id,
                    workflow_id=self.workflow_id,
                    timeout_seconds=3.0,
                )
                return []

            if not state or not state.messages or len(state.messages) == 0:
                logger.info(
                    "temporal_fallback_no_messages",
                    execution_id=self.execution_id,
                    workflow_id=self.workflow_id,
                )
                return []

            logger.info(
                "loaded_messages_from_temporal",
                execution_id=self.execution_id,
                workflow_id=self.workflow_id,
                message_count=len(state.messages),
            )

            # Convert ChatMessage objects to dictionaries
            messages = []
            for i, msg in enumerate(state.messages):
                # Generate message_id if missing
                message_id = getattr(msg, "message_id", None)
                if not message_id:
                    # Use index-based ID for temporal messages
                    message_id = f"{self.execution_id}_{msg.role}_{i}"

                message = {
                    "message_id": message_id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                }

                # Add optional fields if present
                if msg.tool_name:
                    message["tool_name"] = msg.tool_name
                if hasattr(msg, "tool_input") and msg.tool_input:
                    message["tool_input"] = msg.tool_input
                if hasattr(msg, "tool_output") and msg.tool_output:
                    message["tool_output"] = msg.tool_output

                # Add user attribution if present
                if hasattr(msg, "user_id") and msg.user_id:
                    message["user_id"] = msg.user_id
                if hasattr(msg, "user_name") and msg.user_name:
                    message["user_name"] = msg.user_name
                if hasattr(msg, "user_email") and msg.user_email:
                    message["user_email"] = msg.user_email
                if hasattr(msg, "user_avatar") and msg.user_avatar:
                    message["user_avatar"] = msg.user_avatar

                messages.append(message)

            # Normalize message IDs
            self._normalize_message_ids(messages)

            return messages

        except Exception as e:
            logger.error(
                "temporal_fallback_failed",
                execution_id=self.execution_id,
                workflow_id=self.workflow_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return []

    def _normalize_message_ids(self, messages: List[Dict[str, Any]]) -> None:
        """
        Normalize old message ID formats for backward compatibility.

        This method handles legacy message ID formats to ensure consistent IDs
        across database reloads. Old formats used timestamps or simple indices,
        which change on each load. New format uses turn-based numbering which
        is stable.

        Message ID formats:
        - New (turn-based): {execution_id}_{role}_{turn_number}
          Example: "exec123_assistant_5"
        - Old (timestamp-based): {execution_id}_{role}_{timestamp_micros}
          Example: "exec123_assistant_1234567890123456"
        - Old (index-based): {execution_id}_{role}_{idx}
          Example: "exec123_assistant_42" (ambiguous with turn-based)

        Detection heuristic:
        - If last part is < 10000, assume turn-based (new format) - keep as-is
        - If last part is >= 10000, assume timestamp-based (old format) - use content hash
        - If can't parse, use content hash

        Args:
            messages: List of message dictionaries to normalize in-place
        """
        normalized_count = 0

        for msg in messages:
            message_id = msg.get("message_id")
            if not message_id:
                continue

            parts = message_id.split("_")

            # Check if format is: {execution_id}_{role}_{number}
            if len(parts) >= 3 and parts[-2] in ["user", "assistant", "system"]:
                try:
                    last_part = int(parts[-1])

                    # Turn numbers are small (1-100), timestamps are huge (1e15)
                    if last_part < 10000:
                        # New format (turn-based) - keep as-is
                        continue

                    # Old format (timestamp-based) - normalize to content hash
                    normalized_count += 1

                except (ValueError, IndexError):
                    # Can't parse as number - might be hash or other format
                    normalized_count += 1

            # Generate stable ID based on content hash
            content = msg.get("content", "") or ""
            role = msg.get("role", "unknown")
            execution_id = parts[0] if parts else self.execution_id

            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            new_id = f"{execution_id}_{role}_{content_hash}"

            old_id = message_id
            msg["message_id"] = new_id

            logger.debug(
                "normalized_message_id",
                execution_id=self.execution_id,
                old_id=old_id,
                new_id=new_id,
                role=role,
            )

        if normalized_count > 0:
            logger.info(
                "normalized_message_ids_for_backward_compatibility",
                execution_id=self.execution_id,
                normalized_count=normalized_count,
                total_messages=len(messages),
            )

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse ISO format timestamp string.

        Handles both with and without 'Z' suffix. Returns datetime.min for
        invalid/missing timestamps to ensure they sort first.

        Args:
            timestamp_str: ISO format timestamp (e.g., "2024-01-15T10:30:00Z")

        Returns:
            datetime object, or datetime.min if parsing fails
        """
        if not timestamp_str:
            return datetime.min

        try:
            # Handle 'Z' suffix for UTC timestamps
            normalized = timestamp_str.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)
        except Exception as e:
            logger.warning(
                "failed_to_parse_timestamp",
                execution_id=self.execution_id,
                timestamp=timestamp_str,
                error=str(e),
            )
            return datetime.min

    def get_stats(self) -> Dict[str, Any]:
        """
        Get history loading statistics.

        Returns:
            Dictionary with statistics:
            - db_messages_loaded: Messages loaded from database
            - temporal_messages_loaded: Messages loaded from Temporal
            - messages_sent: Messages yielded to stream
            - messages_skipped_empty: Messages skipped due to empty content
            - messages_deduplicated: Messages skipped due to deduplication
            - db_load_duration_ms: Database query duration
            - temporal_load_duration_ms: Temporal query duration
        """
        return self._stats.copy()
