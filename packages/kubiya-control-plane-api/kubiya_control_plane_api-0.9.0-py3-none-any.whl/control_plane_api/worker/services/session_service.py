"""Session management service - handles loading and persisting conversation history"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import structlog
import httpx

from control_plane_api.worker.control_plane_client import ControlPlaneClient
from control_plane_api.worker.utils.retry_utils import retry_with_backoff

logger = structlog.get_logger()


def _safe_timestamp_to_iso(timestamp: Any) -> str:
    """
    Safely convert a timestamp (int, float, datetime, or str) to ISO format string.

    Args:
        timestamp: Can be Unix timestamp (int/float), datetime object, or ISO string

    Returns:
        ISO format timestamp string
    """
    if isinstance(timestamp, str):
        # Already a string, return as-is
        return timestamp
    elif isinstance(timestamp, datetime):
        # datetime object, call isoformat()
        return timestamp.isoformat()
    elif isinstance(timestamp, (int, float)):
        # Unix timestamp, convert to datetime first
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
    else:
        # Fallback to current time
        return datetime.now(timezone.utc).isoformat()


class SessionService:
    """
    Manages session history loading and persistence via Control Plane API.

    Workers don't have database access, so all session operations go through
    the Control Plane which provides Redis caching for hot loads.
    """

    def __init__(self, control_plane: ControlPlaneClient):
        self.control_plane = control_plane

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def load_session(
        self,
        execution_id: str,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Load session history from Control Plane (with retry).

        Returns:
            List of message dicts with role, content, timestamp, etc.
            Empty list if session not found or on error.
        """
        if not session_id:
            return []

        try:
            session_data = self.control_plane.get_session(
                execution_id=execution_id,
                session_id=session_id
            )

            if session_data and session_data.get("messages"):
                messages = session_data["messages"]
                logger.info(
                    "session_loaded",
                    execution_id=execution_id[:8],
                    message_count=len(messages)
                )
                return messages

            return []

        except httpx.TimeoutException:
            logger.warning(
                "session_load_timeout",
                execution_id=execution_id[:8]
            )
            raise  # Let retry decorator handle it
        except Exception as e:
            logger.warning(
                "session_load_error",
                execution_id=execution_id[:8],
                error=str(e)
            )
            return []  # Don't retry on non-timeout errors

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def persist_session(
        self,
        execution_id: str,
        session_id: str,
        user_id: Optional[str],
        messages: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Persist session history to Control Plane (with retry).

        IMPORTANT: Applies defensive deduplication before persisting to prevent
        duplicate messages from reaching the database, even if caller didn't deduplicate.

        Returns:
            True if successful, False otherwise
        """
        if not messages:
            logger.info("session_persist_skipped_no_messages", execution_id=execution_id[:8])
            return True

        # DEFENSIVE: Apply deduplication before persisting (defense-in-depth)
        # This ensures duplicates never reach the database, even if callers forget to deduplicate
        original_count = len(messages)
        messages = self.deduplicate_messages(messages)

        if len(messages) < original_count:
            logger.info(
                "defensive_deduplication_applied",
                execution_id=execution_id[:8],
                original_count=original_count,
                deduplicated_count=len(messages),
                removed=original_count - len(messages)
            )

        try:
            success = self.control_plane.persist_session(
                execution_id=execution_id,
                session_id=session_id or execution_id,
                user_id=user_id,
                messages=messages,
                metadata=metadata or {}
            )

            if success:
                logger.info(
                    "session_persisted",
                    execution_id=execution_id[:8],
                    message_count=len(messages)
                )

            return success

        except Exception as e:
            logger.error(
                "session_persist_error",
                execution_id=execution_id[:8],
                error=str(e)
            )
            return False

    def build_conversation_context(
        self,
        session_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Convert Control Plane session messages to Agno format.

        Args:
            session_messages: Messages from Control Plane

        Returns:
            List of dicts with 'role' and 'content' for Agno
        """
        context = []
        for msg in session_messages:
            context.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })
        return context

    def extract_messages_from_result(
        self,
        result: Any,
        user_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        message_ids: Optional[Dict[int, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract messages from Agno Agent/Team result.

        Args:
            result: Agno RunResponse object
            user_id: Optional user ID to attach
            execution_id: Optional execution ID for generating message_ids
            message_ids: Optional dict mapping message index to message_id.
                        Format: {0: "exec_123_user_1", 1: "exec_123_assistant_1"}
                        When provided, these deterministic IDs are used instead of
                        generating new ones, ensuring streaming and persisted messages
                        have the SAME message_id (fixes duplicate message issue).

        Returns:
            List of message dicts ready for persistence
        """
        messages = []

        if hasattr(result, "messages") and result.messages:
            for idx, msg in enumerate(result.messages):
                # IMPORTANT: Skip Agno's internal "tool" role messages
                # These are empty placeholders that Agno uses for tool calls
                # We use StreamingHelper's tool messages instead (role="system" with complete data)
                if msg.role == "tool":
                    continue

                # Use provided message_id if available, otherwise generate
                message_id = None
                if message_ids and idx in message_ids:
                    # Use pre-generated deterministic ID (preferred - prevents duplicates)
                    message_id = message_ids[idx]
                elif execution_id:
                    # Fallback: Generate ID (for backward compatibility)
                    message_id = f"{execution_id}_{msg.role}_{idx}"

                messages.append({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": (
                        _safe_timestamp_to_iso(msg.created_at)
                        if hasattr(msg, "created_at") and msg.created_at is not None
                        else datetime.now(timezone.utc).isoformat()
                    ),
                    "message_id": message_id,
                    "user_id": getattr(msg, "user_id", user_id),
                    "user_name": getattr(msg, "user_name", None),
                    "user_email": getattr(msg, "user_email", None),
                })

        return messages

    def deduplicate_messages(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate messages based on message_id AND content.
        Keeps first occurrence of each unique message.

        Two-level deduplication:
        1. Primary: message_id uniqueness
        2. Fallback: Content signature (role + normalized content + timestamp proximity)

        This is a defense-in-depth measure to prevent duplicate messages
        from appearing in the UI, even if they slip through earlier checks.

        Args:
            messages: List of message dicts to deduplicate

        Returns:
            Deduplicated list of messages (preserves order, keeps first occurrence)
        """
        seen_ids = set()
        seen_content_sigs = {}  # Track content signatures for assistant messages
        deduplicated = []
        duplicates_by_id = 0
        duplicates_by_content = 0

        for msg in messages:
            msg_id = msg.get("message_id")
            if not msg_id:
                # No ID - include it (shouldn't happen in normal flow)
                deduplicated.append(msg)
                logger.warning(
                    "message_without_id_in_deduplication",
                    role=msg.get("role"),
                    content_preview=(msg.get("content", "") or "")[:50]
                )
                continue

            # Level 1: Check message_id (existing logic)
            if msg_id in seen_ids:
                # Log duplicate for monitoring
                logger.debug(
                    "duplicate_message_id_filtered",
                    message_id=msg_id,
                    role=msg.get("role")
                )
                duplicates_by_id += 1
                continue

            # Level 2: Check content signature (NEW - for assistant messages only)
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")

                # Create content signature from first 200 chars of normalized content
                content_normalized = content.strip().lower()[:200]

                # Check if similar content exists recently
                if content_normalized and content_normalized in seen_content_sigs:
                    prev_msg = seen_content_sigs[content_normalized]
                    prev_timestamp = prev_msg.get("timestamp", "")

                    # Check timestamp proximity (within 5 seconds = likely duplicate)
                    if self._timestamps_close(timestamp, prev_timestamp, threshold_seconds=5):
                        logger.info(
                            "duplicate_content_filtered",
                            message_id=msg_id,
                            prev_message_id=prev_msg.get("message_id"),
                            content_preview=content[:50],
                            timestamp=timestamp,
                            prev_timestamp=prev_timestamp
                        )
                        duplicates_by_content += 1
                        continue  # Skip duplicate content

                # Store content signature for future checks
                if content_normalized:
                    seen_content_sigs[content_normalized] = msg

            # Message is unique - add it
            seen_ids.add(msg_id)
            deduplicated.append(msg)

        if len(deduplicated) < len(messages):
            logger.info(
                "messages_deduplicated",
                original_count=len(messages),
                deduplicated_count=len(deduplicated),
                duplicates_removed=len(messages) - len(deduplicated),
                duplicates_by_id=duplicates_by_id,
                duplicates_by_content=duplicates_by_content
            )

        return deduplicated

    def _timestamps_close(self, ts1: str, ts2: str, threshold_seconds: int = 5) -> bool:
        """
        Check if two timestamps are within threshold_seconds of each other.

        Args:
            ts1: First timestamp (ISO format string)
            ts2: Second timestamp (ISO format string)
            threshold_seconds: Maximum difference in seconds to consider timestamps close

        Returns:
            True if timestamps are within threshold, False otherwise
        """
        if not ts1 or not ts2:
            return False

        try:
            # Parse timestamps (handle both with and without 'Z' suffix)
            t1 = datetime.fromisoformat(ts1.replace('Z', '+00:00'))
            t2 = datetime.fromisoformat(ts2.replace('Z', '+00:00'))

            # Calculate absolute difference in seconds
            diff = abs((t1 - t2).total_seconds())

            return diff <= threshold_seconds
        except Exception as e:
            # If can't parse timestamps, assume they're not close
            logger.debug(
                "timestamp_comparison_failed",
                ts1=ts1,
                ts2=ts2,
                error=str(e)
            )
            return False
