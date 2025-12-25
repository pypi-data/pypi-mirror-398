"""
LiveEventSource for real-time event streaming from Redis.

This module provides the LiveEventSource class that handles real-time event streaming
from Redis with proper polling, deduplication, and workflow completion detection.

Key Features:
- Redis polling with explicit 200ms sleep interval to prevent CPU spinning
- Integration with MessageDeduplicator to filter duplicate events
- Workflow completion detection via Temporal status monitoring
- Graceful degradation when Redis or Temporal unavailable
- Keepalive and timeout handling for long-running streams
- Support for both Upstash REST API and standard redis-py clients

Test Strategy:
- Test Redis polling with mock events at 200ms intervals
- Test deduplication of overlapping events (history + live)
- Test completion detection stops streaming when workflow reaches terminal state
- Test timeout behavior (0 = no timeout, streams until task completes)
- Test keepalive events sent every 15 seconds
- Test graceful degradation when Redis unavailable
- Test graceful degradation when Temporal unavailable
- Test various event types: message, status, tool_started, tool_completed, etc.
- Test Redis LLEN and LRANGE operations with both client types
- Test terminal states: COMPLETED, FAILED, TERMINATED, CANCELLED
"""

import asyncio
import json
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

import structlog

from .deduplication import MessageDeduplicator

logger = structlog.get_logger(__name__)


class LiveEventSource:
    """
    Handles real-time event streaming from Redis with polling and completion detection.

    This class polls Redis for new events at 200ms intervals, deduplicates events
    against historical data, and monitors workflow status to detect completion.

    The streaming stops when:
    1. Workflow reaches terminal state (COMPLETED, FAILED, CANCELLED, TERMINATED)
    2. Timeout is reached (default 0 = no timeout, streams until task completes)
    3. An exception occurs that cannot be recovered

    Events are yielded as dictionaries with the following structure:
    {
        "event_type": "message" | "status" | "tool_started" | "tool_completed" | ...,
        "data": {...},  # Event-specific data
        "timestamp": "2024-01-15T10:30:00Z"
    }
    """

    # Terminal workflow states that indicate streaming should stop
    TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED", "TERMINATED"}

    # Terminal database execution states (lowercase, as stored in DB)
    TERMINAL_DB_STATES = {"completed", "failed", "cancelled", "terminated", "interrupted"}

    # Temporal status cache TTL (seconds) to reduce API load
    TEMPORAL_STATUS_CACHE_TTL = 1.0

    # Database status poll interval (seconds) - check for status changes
    DB_STATUS_POLL_INTERVAL = 2.0

    def __init__(
        self,
        execution_id: str,
        organization_id: str,
        redis_client,
        workflow_handle,
        deduplicator: MessageDeduplicator,
        timeout_seconds: int = 0,  # 0 = no timeout, stream until task completes
        keepalive_interval: int = 15,
        db_session=None,  # SQLAlchemy session for status polling
    ):
        """
        Initialize LiveEventSource.

        Args:
            execution_id: Execution ID to stream events for
            organization_id: Organization ID for authorization
            redis_client: Redis client instance (UpstashRedisClient or StandardRedisClient)
            workflow_handle: Temporal workflow handle for status checks (can be None)
            deduplicator: MessageDeduplicator instance for filtering duplicates
            timeout_seconds: Maximum streaming duration in seconds (default: 0 = no timeout)
            keepalive_interval: Seconds between keepalive messages (default: 15)
            db_session: Database session for polling execution status (optional)
        """
        self.execution_id = execution_id
        self.organization_id = organization_id
        self.redis_client = redis_client
        self.workflow_handle = workflow_handle
        self.deduplicator = deduplicator
        self.timeout_seconds = timeout_seconds
        self.keepalive_interval = keepalive_interval
        self.db_session = db_session

        # Streaming state
        self._start_time = None
        self._last_keepalive = None
        self._last_redis_index = -1  # Track last processed Redis event index
        self._stopped = False
        self._is_workflow_running = True  # Assume running until proven otherwise

        # Temporal status caching
        self._cached_temporal_status = None
        self._cached_workflow_description = None
        self._last_temporal_check = 0

        # Database status caching
        self._cached_db_status = None
        self._last_db_status_check = 0

        # Redis key for events
        self._redis_key = f"execution:{execution_id}:events"

        logger.info(
            "live_event_source_initialized",
            execution_id=execution_id[:8],
            timeout_seconds=timeout_seconds,
            keepalive_interval=keepalive_interval,
            has_workflow_handle=workflow_handle is not None,
            has_redis_client=redis_client is not None,
        )

    async def stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream live events from Redis until workflow completes or timeout.

        This is the main entry point for streaming. It polls Redis every 200ms
        for new events, deduplicates them, and yields them as dictionaries.

        Yields:
            Event dictionaries with event_type, data, and timestamp

        Example:
            ```python
            async for event in live_source.stream():
                print(f"Event: {event['event_type']}")
                # Process event...
            ```
        """
        self._start_time = time.time()
        self._last_keepalive = self._start_time

        logger.info(
            "live_streaming_started",
            execution_id=self.execution_id[:8],
            timeout_seconds=self.timeout_seconds,
        )

        try:
            while not self.should_stop:
                current_time = time.time()

                # Check timeout (skip if timeout_seconds is 0 = no timeout)
                elapsed = current_time - self._start_time
                if self.timeout_seconds > 0 and elapsed >= self.timeout_seconds:
                    logger.warning(
                        "live_streaming_timeout",
                        execution_id=self.execution_id[:8],
                        elapsed_seconds=int(elapsed),
                        timeout_seconds=self.timeout_seconds,
                    )
                    self._stopped = True
                    break

                # Send keepalive if needed
                if current_time - self._last_keepalive >= self.keepalive_interval:
                    yield self._create_keepalive_event()
                    self._last_keepalive = current_time

                # Check workflow completion (if handle available)
                if self.workflow_handle is not None:
                    try:
                        is_complete = await self._check_completion()
                        if is_complete:
                            logger.info(
                                "workflow_completed_stopping_stream",
                                execution_id=self.execution_id[:8],
                                status=self._cached_temporal_status,
                            )
                            self._stopped = True
                            break
                    except Exception as e:
                        # Don't fail streaming if status check fails
                        logger.warning(
                            "workflow_status_check_failed",
                            execution_id=self.execution_id[:8],
                            error=str(e),
                        )

                # Check database status for changes (every 2 seconds)
                db_status_event = await self._check_db_status()
                if db_status_event:
                    # Emit status change event
                    yield db_status_event

                # Poll Redis for new events
                if self.redis_client:
                    try:
                        new_events = await self._poll_redis(self._last_redis_index)
                        for event in new_events:
                            # Deduplicate event
                            if self.deduplicator.is_sent(event):
                                logger.debug(
                                    "duplicate_event_skipped",
                                    execution_id=self.execution_id[:8],
                                    event_type=event.get("event_type"),
                                    message_id=event.get("message_id"),
                                )
                                continue

                            # Mark as sent and yield
                            self.deduplicator.mark_sent(event)
                            yield event
                    except Exception as redis_error:
                        # Log error but don't fail streaming
                        logger.error(
                            "redis_poll_error",
                            execution_id=self.execution_id[:8],
                            error=str(redis_error),
                        )
                        # Yield degraded state notification
                        yield self._create_degraded_event(str(redis_error))

                # Sleep 200ms before next poll (prevent CPU spinning)
                await asyncio.sleep(0.2)

        except Exception as e:
            logger.error(
                "live_streaming_error",
                execution_id=self.execution_id[:8],
                error=str(e),
            )
            raise
        finally:
            elapsed = time.time() - self._start_time
            logger.info(
                "live_streaming_stopped",
                execution_id=self.execution_id[:8],
                elapsed_seconds=int(elapsed),
                events_processed=self._last_redis_index + 1,
            )

    async def _poll_redis(self, last_index: int) -> List[Dict[str, Any]]:
        """
        Poll Redis for new events since last_index.

        This method:
        1. Uses LLEN to get total event count
        2. Uses LRANGE to get new events since last index
        3. Parses events from JSON
        4. Reverses them to chronological order (Redis uses LPUSH, newest first)
        5. Extracts message_id for deduplication

        Args:
            last_index: Last processed event index (0-based)

        Returns:
            List of new event dictionaries in chronological order

        Note:
            Redis stores events in reverse chronological order (LPUSH adds to head).
            We reverse them here to get chronological order (oldest first).
        """
        if not self.redis_client:
            return []

        try:
            # Get total event count
            total_events = await self.redis_client.llen(self._redis_key)

            if total_events is None or total_events == 0:
                return []

            # Check if there are new events
            if total_events <= (last_index + 1):
                return []

            logger.debug(
                "redis_new_events_found",
                execution_id=self.execution_id[:8],
                total=total_events,
                last_index=last_index,
                new_count=total_events - (last_index + 1),
            )

            # Get all events (they're in reverse chronological order from LPUSH)
            all_redis_events = await self.redis_client.lrange(self._redis_key, 0, -1)

            if not all_redis_events:
                return []

            # Reverse to get chronological order (oldest first)
            chronological_events = list(reversed(all_redis_events))

            # Extract only NEW events we haven't processed yet
            new_events = []
            for i in range(last_index + 1, len(chronological_events)):
                event_json = chronological_events[i]

                try:
                    event_data = json.loads(event_json)
                    event_type = event_data.get("event_type", "message")

                    # Extract payload based on event structure
                    # Two formats:
                    # 1. Message events: flat structure {role, content, timestamp, message_id}
                    # 2. Other events: nested {event_type, data: {...}, timestamp}
                    if "data" in event_data and isinstance(event_data["data"], dict):
                        if event_type == "message" and "role" in event_data["data"]:
                            # Message events expect flat structure
                            payload = event_data["data"].copy()
                        else:
                            # Chunk events and others expect nested structure
                            payload = {
                                "data": event_data["data"],
                                "timestamp": event_data.get("timestamp"),
                            }
                    else:
                        # Fallback for legacy format
                        payload = event_data.copy()

                    # Ensure message_id exists for deduplication
                    if event_type == "message" and isinstance(payload, dict):
                        if not payload.get("message_id"):
                            # Generate stable message_id
                            timestamp = payload.get("timestamp") or event_data.get("timestamp")
                            role = payload.get("role", "unknown")
                            if timestamp:
                                try:
                                    from datetime import datetime
                                    timestamp_micros = int(
                                        datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp()
                                        * 1000000
                                    )
                                except Exception:
                                    timestamp_micros = int(time.time() * 1000000)
                            else:
                                timestamp_micros = int(time.time() * 1000000)

                            generated_id = f"{self.execution_id}_{role}_{timestamp_micros}"
                            payload["message_id"] = generated_id

                            logger.debug(
                                "generated_message_id_for_redis_event",
                                execution_id=self.execution_id[:8],
                                role=role,
                                generated_id=generated_id,
                            )

                    # Store event type and payload
                    event = {
                        "event_type": event_type,
                        **payload,  # Merge payload into event
                    }

                    new_events.append(event)

                    # Update last processed index
                    self._last_redis_index = i

                    logger.debug(
                        "redis_event_parsed",
                        execution_id=self.execution_id[:8],
                        event_type=event_type,
                        index=i,
                    )

                except json.JSONDecodeError as e:
                    logger.warning(
                        "invalid_redis_event_json",
                        execution_id=self.execution_id[:8],
                        event=event_json[:100],
                        error=str(e),
                    )
                    # Update index even for invalid events
                    self._last_redis_index = i
                    continue
                except Exception as e:
                    logger.error(
                        "redis_event_processing_error",
                        execution_id=self.execution_id[:8],
                        event=event_json[:100],
                        error=str(e),
                    )
                    # Update index even for failed events
                    self._last_redis_index = i
                    continue

            return new_events

        except Exception as e:
            logger.error(
                "redis_poll_failed",
                execution_id=self.execution_id[:8],
                error=str(e),
            )
            return []

    async def _check_completion(self) -> bool:
        """
        Check if workflow is in terminal state (completed, failed, cancelled).

        This method uses cached status if within TTL (1 second) to reduce
        Temporal API load. Fresh status is fetched if cache expired.

        Returns:
            True if workflow is in terminal state, False otherwise

        Note:
            Temporal execution status enum values:
            - RUNNING: Workflow is actively processing
            - COMPLETED: Workflow completed successfully
            - FAILED: Workflow failed with error
            - CANCELLED: Workflow was cancelled by user
            - TERMINATED: Workflow was terminated
            - TIMED_OUT: Workflow exceeded timeout
            - CONTINUED_AS_NEW: Workflow continued as new execution
        """
        if not self.workflow_handle:
            # No workflow handle - can't check completion
            return False

        try:
            current_time = time.time()

            # Use cached status if within TTL
            if (
                self._cached_temporal_status
                and (current_time - self._last_temporal_check) < self.TEMPORAL_STATUS_CACHE_TTL
            ):
                temporal_status = self._cached_temporal_status
                logger.debug(
                    "using_cached_temporal_status",
                    execution_id=self.execution_id[:8],
                    status=temporal_status,
                )
            else:
                # Cache expired or not set - fetch fresh status
                t0 = time.time()
                description = await self.workflow_handle.describe()
                temporal_status = description.status.name  # Get enum name (e.g., "RUNNING")
                describe_duration = int((time.time() - t0) * 1000)

                # Update cache
                self._cached_temporal_status = temporal_status
                self._cached_workflow_description = description
                self._last_temporal_check = t0

                logger.debug(
                    "temporal_status_fetched",
                    execution_id=self.execution_id[:8],
                    status=temporal_status,
                    duration_ms=describe_duration,
                )

                # Log slow describe calls (>100ms)
                if describe_duration > 100:
                    logger.warning(
                        "slow_temporal_describe",
                        execution_id=self.execution_id[:8],
                        duration_ms=describe_duration,
                    )

            # Update running state
            previous_running = self._is_workflow_running
            self._is_workflow_running = temporal_status == "RUNNING"

            # Log state changes
            if previous_running != self._is_workflow_running:
                logger.info(
                    "workflow_running_state_changed",
                    execution_id=self.execution_id[:8],
                    temporal_status=temporal_status,
                    is_running=self._is_workflow_running,
                )

            # Check if terminal state reached
            return temporal_status in self.TERMINAL_STATES

        except Exception as e:
            logger.warning(
                "temporal_status_check_error",
                execution_id=self.execution_id[:8],
                error=str(e),
            )
            # Don't treat errors as completion - keep streaming
            return False

    async def _check_db_status(self) -> Optional[Dict[str, Any]]:
        """
        Check database execution status and emit status event if changed.

        This polls the database every 2 seconds to detect status changes
        (running, waiting_for_input, completed, failed, etc.) and returns
        a status event if the status has changed since last check.

        Returns:
            Status event dict if status changed, None otherwise
        """
        if not self.db_session:
            return None

        try:
            current_time = time.time()

            # Check if we should poll (respect poll interval)
            if (current_time - self._last_db_status_check) < self.DB_STATUS_POLL_INTERVAL:
                return None

            # Query execution status from database
            from control_plane_api.app.models.execution import Execution
            import uuid as uuid_module

            execution = self.db_session.query(Execution).filter(
                Execution.id == uuid_module.UUID(self.execution_id),
                Execution.organization_id == self.organization_id
            ).first()

            if not execution:
                return None

            db_status = execution.status
            self._last_db_status_check = current_time

            # Check if status changed
            status_event = None
            if db_status != self._cached_db_status:
                logger.info(
                    "execution_status_changed",
                    execution_id=self.execution_id[:8],
                    old_status=self._cached_db_status,
                    new_status=db_status,
                )

                self._cached_db_status = db_status

                # Return status event
                status_event = {
                    "event_type": "status",
                    "status": db_status,
                    "data": {
                        "execution_id": self.execution_id,
                        "status": db_status,
                        "source": "database_poll",
                    }
                }

            # Check if DB status is a terminal state - signal completion
            # This is a fallback when Temporal workflow handle is unavailable
            if db_status in self.TERMINAL_DB_STATES:
                logger.info(
                    "db_terminal_state_detected",
                    execution_id=self.execution_id[:8],
                    db_status=db_status,
                )
                self._stopped = True

            return status_event

        except Exception as e:
            logger.warning(
                "db_status_check_error",
                execution_id=self.execution_id[:8],
                error=str(e),
            )
            return None

    @property
    def should_stop(self) -> bool:
        """
        Whether streaming should stop.

        Returns:
            True if streaming should stop (completed or timeout), False otherwise
        """
        return self._stopped

    def _create_keepalive_event(self) -> Dict[str, Any]:
        """
        Create a keepalive event.

        Keepalive events are sent periodically to prevent connection timeout
        and to inform the client that streaming is still active.

        Returns:
            Keepalive event dictionary
        """
        elapsed = time.time() - self._start_time
        remaining = max(0, self.timeout_seconds - elapsed)

        event = {
            "event_type": "keepalive",
            "data": {
                "execution_id": self.execution_id,
                "elapsed_seconds": int(elapsed),
                "remaining_seconds": int(remaining),
            },
            "timestamp": self._current_timestamp(),
        }

        logger.debug(
            "keepalive_sent",
            execution_id=self.execution_id[:8],
            elapsed_seconds=int(elapsed),
            remaining_seconds=int(remaining),
        )

        return event

    def _create_degraded_event(self, reason: str) -> Dict[str, Any]:
        """
        Create a degraded state event.

        Degraded events inform the client that streaming quality is reduced
        due to Redis unavailability or other issues.

        Args:
            reason: Reason for degraded state

        Returns:
            Degraded event dictionary
        """
        event = {
            "event_type": "degraded",
            "data": {
                "reason": "redis_unavailable",
                "fallback": "temporal_polling",
                "message": f"Real-time events unavailable: {reason}",
                "execution_id": self.execution_id,
            },
            "timestamp": self._current_timestamp(),
        }

        logger.warning(
            "degraded_state_notification",
            execution_id=self.execution_id[:8],
            reason=reason,
        )

        return event

    def _current_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.

        Returns:
            ISO format timestamp string (e.g., "2024-01-15T10:30:00Z")
        """
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
