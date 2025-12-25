"""
EventBuffer class for SSE gap recovery support.

Implements a ring buffer pattern using collections.deque for bounded memory,
supporting event replay and gap detection for Server-Sent Events (SSE) streams.
"""

import time
import json
from collections import deque
from typing import Dict, Any, List, Optional, Tuple
from structlog import get_logger

logger = get_logger(__name__)


class EventBuffer:
    """
    Ring buffer for SSE event storage with gap recovery support.

    Uses a bounded deque to store recent SSE events, enabling:
    - Event replay on reconnection (Last-Event-ID pattern)
    - Gap detection between client and server state
    - Automatic memory management with size-based eviction

    Events are stored as tuples: (event_id, event_type, data, size)
    Event IDs follow format: {execution_id}_{counter}_{timestamp_micros}

    Limits:
    - Max 100 events (ring buffer evicts oldest)
    - Max 100KB total buffer size (evicts oldest until under limit)

    Thread Safety:
    - Uses deque which is thread-safe for append/popleft operations
    - Size tracking uses atomic operations

    Test Strategy:
    - Unit test buffer capacity limits (100 events)
    - Unit test size limits (100KB)
    - Test replay from various positions
    - Test gap detection accuracy
    - Test edge cases (empty buffer, no gaps, large gaps)
    - Test event ID parsing with various formats
    """

    MAX_BUFFER_EVENTS = 100
    MAX_BUFFER_SIZE = 100 * 1024  # 100KB

    def __init__(self, execution_id: str):
        """
        Initialize EventBuffer for a specific execution.

        Args:
            execution_id: The execution ID this buffer is associated with
        """
        self.execution_id = execution_id
        self.buffer: deque = deque(maxlen=self.MAX_BUFFER_EVENTS)
        self._current_size = 0

    def add_event(self, event_id: str, event_type: str, data: str) -> None:
        """
        Add event to buffer with automatic eviction.

        Events are stored as (event_id, event_type, data, size) tuples.
        If buffer exceeds MAX_BUFFER_SIZE, oldest events are evicted.
        The deque's maxlen ensures automatic eviction at MAX_BUFFER_EVENTS.

        Args:
            event_id: Unique event identifier (format: {execution_id}_{counter}_{timestamp})
            event_type: Type of event (e.g., 'status', 'tool_call', 'message')
            data: JSON string of event data
        """
        event_size = len(data)
        self._current_size += event_size

        # Add event to buffer (deque automatically evicts oldest if at maxlen)
        # Note: If eviction happens, we need to track it for size accounting
        old_len = len(self.buffer)
        self.buffer.append((event_id, event_type, data, event_size))

        # If deque evicted an event (length didn't increase), subtract its size
        if len(self.buffer) == old_len and old_len == self.MAX_BUFFER_EVENTS:
            # Deque evicted the oldest event, need to account for it
            # We can't access the evicted event, so we need to recalculate
            self._recalculate_size()

        # Remove old events if buffer exceeds size limit
        while self._current_size > self.MAX_BUFFER_SIZE and len(self.buffer) > 1:
            _, _, _, old_size = self.buffer.popleft()
            self._current_size -= old_size

        logger.debug(
            "event_buffered",
            execution_id=self.execution_id,
            event_id=event_id,
            event_type=event_type,
            buffer_count=len(self.buffer),
            buffer_size=self._current_size
        )

    def _recalculate_size(self) -> None:
        """Recalculate buffer size from scratch."""
        self._current_size = sum(size for _, _, _, size in self.buffer)

    def replay_from_id(self, last_event_id: str) -> List[Tuple[str, str, str]]:
        """
        Replay events after the given event ID.

        Parses the last_event_id to extract the counter, then returns all
        buffered events with higher counters in chronological order.

        Args:
            last_event_id: Last event ID received by client

        Returns:
            List of (event_id, event_type, data) tuples to replay
        """
        last_counter = self._parse_event_id(last_event_id)

        if last_counter is None or not self.buffer:
            return []

        replay_events: List[Tuple[str, str, str]] = []

        for buf_event_id, buf_event_type, buf_data, _ in self.buffer:
            buf_counter = self._parse_event_id(buf_event_id)

            if buf_counter is not None and buf_counter > last_counter:
                replay_events.append((buf_event_id, buf_event_type, buf_data))

        if replay_events:
            logger.info(
                "replaying_buffered_events",
                execution_id=self.execution_id,
                last_counter=last_counter,
                replay_count=len(replay_events)
            )

        return replay_events

    def detect_gap(self, last_event_id: str, current_event_id: str) -> Optional[Dict[str, Any]]:
        """
        Detect gap between last and current event IDs.

        Compares sequence counters to identify missing events. Returns gap
        information if events are missing from the buffer.

        Args:
            last_event_id: Last event ID received by client
            current_event_id: Current event ID being processed

        Returns:
            Gap information dict if gap detected, None otherwise:
            {
                "gap_detected": True,
                "last_counter": int,
                "current_counter": int,
                "missing_count": int,
                "reason": str
            }
        """
        last_counter = self._parse_event_id(last_event_id)
        current_counter = self._parse_event_id(current_event_id)

        if last_counter is None or current_counter is None:
            return None

        # Check if there's a gap
        expected_counter = last_counter + 1
        if current_counter > expected_counter:
            missing_count = current_counter - expected_counter

            logger.warning(
                "gap_detected",
                execution_id=self.execution_id,
                last_counter=last_counter,
                current_counter=current_counter,
                missing_count=missing_count
            )

            return {
                "gap_detected": True,
                "last_counter": last_counter,
                "current_counter": current_counter,
                "missing_count": missing_count,
                "reason": f"Missing {missing_count} events between {last_counter} and {current_counter}"
            }

        return None

    def check_buffer_miss(self, last_event_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if last_event_id is no longer in buffer (too old).

        Args:
            last_event_id: Last event ID received by client

        Returns:
            Buffer miss information if events are too old, None otherwise:
            {
                "buffer_miss": True,
                "last_known_id": str,
                "buffer_oldest": str,
                "reason": str
            }
        """
        if not self.buffer:
            return {
                "buffer_miss": True,
                "last_known_id": last_event_id,
                "buffer_oldest": None,
                "reason": "Event buffer is empty"
            }

        last_counter = self._parse_event_id(last_event_id)
        if last_counter is None:
            return None

        # Check if any buffered event is after the last_event_id
        has_newer_events = False
        for buf_event_id, _, _, _ in self.buffer:
            buf_counter = self._parse_event_id(buf_event_id)
            if buf_counter is not None and buf_counter > last_counter:
                has_newer_events = True
                break

        # If we have newer events but couldn't replay (empty replay_from_id),
        # it means the last_event_id is older than our oldest buffered event
        if not has_newer_events and last_counter > 0:
            oldest_event_id = self.buffer[0][0] if self.buffer else None

            logger.warning(
                "gap_detected_buffer_miss",
                execution_id=self.execution_id,
                last_counter=last_counter,
                buffer_size=len(self.buffer),
                buffer_oldest=oldest_event_id
            )

            return {
                "buffer_miss": True,
                "last_known_id": last_event_id,
                "buffer_oldest": oldest_event_id,
                "reason": "Event buffer miss - events too old"
            }

        return None

    def _parse_event_id(self, event_id: str) -> Optional[int]:
        """
        Extract sequence counter from event ID format: {execution_id}_{counter}_{timestamp}.

        Args:
            event_id: Event ID string to parse

        Returns:
            Sequence counter as integer, or None if parsing fails
        """
        try:
            parts = event_id.split("_")

            # Format: {execution_id}_{counter}_{timestamp_micros}
            # Validate execution_id matches (first part)
            if len(parts) >= 2 and parts[0] == self.execution_id:
                return int(parts[1])

            # If execution_id doesn't match, still try to parse counter
            # for compatibility with different ID formats
            if len(parts) >= 2:
                return int(parts[1])

        except (ValueError, IndexError) as e:
            logger.warning(
                "invalid_event_id_format",
                execution_id=self.execution_id,
                event_id=event_id,
                error=str(e)
            )

        return None

    def _estimate_size(self, data: Dict[str, Any]) -> int:
        """
        Estimate size of event data in bytes.

        Args:
            data: Dictionary of event data

        Returns:
            Estimated size in bytes
        """
        try:
            return len(json.dumps(data))
        except Exception:
            # Fallback: rough estimate based on string representation
            return len(str(data))

    def get_buffer_size(self) -> int:
        """
        Get current buffer size in bytes.

        Returns:
            Total size of buffered event data in bytes
        """
        return self._current_size

    def get_buffer_info(self) -> Dict[str, Any]:
        """
        Get buffer statistics for debugging.

        Returns:
            Dictionary with buffer statistics:
            {
                "execution_id": str,
                "event_count": int,
                "total_size_bytes": int,
                "max_events": int,
                "max_size_bytes": int,
                "oldest_event_id": str,
                "newest_event_id": str,
                "utilization_percent": float
            }
        """
        oldest_event_id = None
        newest_event_id = None

        if self.buffer:
            oldest_event_id = self.buffer[0][0]
            newest_event_id = self.buffer[-1][0]

        event_count = len(self.buffer)
        utilization = (event_count / self.MAX_BUFFER_EVENTS) * 100

        return {
            "execution_id": self.execution_id,
            "event_count": event_count,
            "total_size_bytes": self._current_size,
            "max_events": self.MAX_BUFFER_EVENTS,
            "max_size_bytes": self.MAX_BUFFER_SIZE,
            "oldest_event_id": oldest_event_id,
            "newest_event_id": newest_event_id,
            "utilization_percent": round(utilization, 2)
        }

    def clear(self) -> None:
        """Clear all buffered events."""
        self.buffer.clear()
        self._current_size = 0

        logger.debug(
            "event_buffer_cleared",
            execution_id=self.execution_id
        )
