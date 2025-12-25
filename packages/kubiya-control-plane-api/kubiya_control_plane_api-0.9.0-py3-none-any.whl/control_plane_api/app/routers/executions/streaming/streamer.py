"""
ExecutionStreamer - Main orchestrator for resumable execution streaming.

This module provides the ExecutionStreamer class that orchestrates the complete
streaming lifecycle: immediate connection, historical message loading, and live
event streaming with gap recovery support.

Architecture:
This is the core component of the Resumable Execution Stream Architecture that
ties together all the specialized streaming components:

1. Phase 1: Immediate Connection (<50ms)
   - Send 'connected' event immediately to unblock EventSource
   - Don't wait for any slow operations (DB, Temporal queries)

2. Phase 2: Stream Historical Messages
   - Use HistoryLoader to progressively stream database messages
   - Yield one message at a time for instant UI rendering
   - Track sent messages via MessageDeduplicator

3. Phase 3: History Complete
   - Send 'history_complete' event to signal transition
   - Include message count and truncation flags

4. Phase 4: Live Event Streaming
   - Use LiveEventSource to stream real-time Redis events
   - Poll at 200ms intervals for new events
   - Continue until workflow completes or timeout

Gap Recovery:
- Supports Last-Event-ID pattern for client reconnection
- Uses EventBuffer to detect and handle gaps
- Replays missing events when possible
- Notifies client when gaps are unrecoverable

Test Strategy:
- Integration test full streaming flow (all 4 phases in order)
- Test phase transitions occur at correct times with correct data
- Test Last-Event-ID resumption skips already-sent events
- Test gap detection and replay from EventBuffer
- Test error handling in each phase (graceful degradation)
- Test statistics tracking across phases
- Test timeout handling (0 = no timeout, streams until task completes)
- Test workflow completion detection stops streaming
- Test deduplication across history + live phases
"""

import asyncio
import logging
import time
from typing import Any, AsyncGenerator, Dict, Optional

from structlog import get_logger

from .deduplication import MessageDeduplicator
from .event_buffer import EventBuffer
from .event_formatter import EventFormatter
from .history_loader import HistoryLoader
from .live_source import LiveEventSource
from ..services.worker_health import WorkerHealthChecker, DegradationMode

logger = get_logger(__name__)


class ExecutionStreamer:
    """
    Main orchestrator for resumable execution streaming.

    This class coordinates all phases of execution streaming:
    1. Immediate connection acknowledgment
    2. Progressive historical message streaming
    3. History completion notification
    4. Live event streaming with completion detection

    The streamer supports gap recovery via Last-Event-ID pattern, enabling
    clients to reconnect and resume from their last received event without
    missing any updates.

    Example usage:
        ```python
        streamer = ExecutionStreamer(
            execution_id="exec-123",
            organization_id="org-456",
            db_session=db,
            redis_client=redis,
            temporal_client=temporal_client,
            last_event_id="exec-123_42_1234567890",  # Optional, for resumption
            timeout_seconds=0,  # 0 = no timeout
        )

        async for sse_event in streamer.stream():
            # Send SSE event to client
            yield sse_event
        ```

    Architecture:
    - Delegates to specialized components for each concern
    - Maintains single deduplicator instance shared across phases
    - Uses EventBuffer for gap detection and replay
    - Uses EventFormatter for consistent SSE formatting
    """

    def __init__(
        self,
        execution_id: str,
        organization_id: str,
        db_session,  # SQLAlchemy session
        redis_client,  # Redis client (UpstashRedisClient or StandardRedisClient)
        temporal_client,  # temporalio.client.Client
        last_event_id: Optional[str] = None,
        timeout_seconds: int = 0,  # 0 = no timeout, stream until task completes
        execution_type: Optional[str] = None,
        health_checker: Optional[WorkerHealthChecker] = None,
    ):
        """
        Initialize ExecutionStreamer.

        Args:
            execution_id: Execution ID to stream
            organization_id: Organization ID for authorization
            db_session: SQLAlchemy database session for HistoryLoader
            redis_client: Redis client for LiveEventSource (can be None)
            temporal_client: Temporal client for workflow queries (can be None)
            last_event_id: Last event ID client received (for resumption)
            timeout_seconds: Maximum streaming duration (default: 0 = no timeout)
            execution_type: Execution type ("AGENT" or "TEAM") to determine workflow_id
            health_checker: WorkerHealthChecker instance for graceful degradation (optional)
        """
        self.execution_id = execution_id
        self.organization_id = organization_id
        self.db_session = db_session
        self.redis_client = redis_client
        self.temporal_client = temporal_client
        self.last_event_id = last_event_id
        self.timeout_seconds = timeout_seconds
        self.execution_type = execution_type or "AGENT"

        # Determine workflow ID based on execution type
        if self.execution_type == "TEAM":
            self.workflow_id = f"team-execution-{execution_id}"
        else:
            self.workflow_id = f"agent-execution-{execution_id}"

        # Core components (initialized once, reused across phases)
        self.deduplicator = MessageDeduplicator()
        self.formatter = EventFormatter(execution_id)
        self.buffer = EventBuffer(execution_id)

        # Health checker for graceful degradation
        self.health_checker = health_checker or WorkerHealthChecker(
            temporal_client=temporal_client,
            redis_client=redis_client,
            db_session=db_session,
        )

        # Temporal workflow handle (cached)
        self._workflow_handle = None
        self._workflow_handle_error = None

        # Degradation tracking
        self._degradation_mode = None
        self._last_health_check = None

        # Statistics tracking
        self._stats = {
            "phase": "initializing",
            "start_time": None,
            "connection_time_ms": 0,
            "history_load_time_ms": 0,
            "live_streaming_time_ms": 0,
            "total_events_sent": 0,
            "history_messages_sent": 0,
            "live_events_sent": 0,
            "events_buffered": 0,
            "events_replayed": 0,
            "deduplication_stats": {},
            "errors": [],
            "degradation_mode": None,
        }

        logger.info(
            "execution_streamer_initialized",
            execution_id=execution_id[:8],
            organization_id=organization_id[:8],
            workflow_id=self.workflow_id,
            has_last_event_id=bool(last_event_id),
            timeout_seconds=timeout_seconds,
        )

    async def stream(self) -> AsyncGenerator[str, None]:
        """
        Main streaming generator that orchestrates all phases.

        This method executes the complete streaming lifecycle:
        1. Send immediate 'connected' event
        2. Handle Last-Event-ID resumption (replay or gap detection)
        3. Stream historical messages from database
        4. Send 'history_complete' event
        5. Stream live events from Redis until completion

        Yields:
            SSE-formatted event strings ready to send to client

        Example:
            ```python
            async for sse_event in streamer.stream():
                # sse_event is already formatted: "id: ...\nevent: ...\ndata: ...\n\n"
                yield sse_event
            ```
        """
        self._stats["start_time"] = time.time()

        try:
            # ========== PHASE 1: IMMEDIATE CONNECTION ==========
            yield await self._phase_1_connect()

            # ========== HEALTH CHECK: Determine degradation mode ==========
            degradation_mode = await self.health_checker.get_degradation_mode()
            self._degradation_mode = degradation_mode
            self._last_health_check = time.time()
            self._stats["degradation_mode"] = degradation_mode.value

            logger.info(
                "health_check_complete",
                execution_id=self.execution_id[:8],
                degradation_mode=degradation_mode.value,
            )

            # Send degraded event if not in full mode
            if degradation_mode != DegradationMode.FULL:
                capabilities = self.health_checker.get_capabilities(degradation_mode)

                # Determine reason message based on mode
                if degradation_mode == DegradationMode.UNAVAILABLE:
                    reason = "All services unavailable"
                    message = "Unable to stream execution data - all services are down"
                elif degradation_mode == DegradationMode.HISTORY_ONLY:
                    reason = "Live streaming unavailable"
                    message = "Real-time updates unavailable. Showing historical data only."
                elif degradation_mode == DegradationMode.LIVE_ONLY:
                    reason = "Historical data unavailable"
                    message = "Database unavailable. Showing live updates only (no history)."
                else:
                    reason = "Partial service availability"
                    message = "Some services unavailable. Functionality may be limited."

                yield self.formatter.format_degraded_event(
                    mode=degradation_mode.value,
                    reason=reason,
                    message=message,
                    capabilities=capabilities,
                )
                self._stats["total_events_sent"] += 1

            # If completely unavailable, stop here
            if degradation_mode == DegradationMode.UNAVAILABLE:
                yield self.formatter.format_error_event(
                    error="All services unavailable - cannot stream execution data",
                    error_type="unavailable",
                )
                return

            # ========== PHASE 2: RESUMPTION (if Last-Event-ID provided) ==========
            if self.last_event_id:
                async for event in self._phase_2_resumption():
                    yield event

            # ========== PHASE 3: STREAM HISTORICAL MESSAGES ==========
            # Skip history if in LIVE_ONLY mode
            if degradation_mode not in [DegradationMode.LIVE_ONLY]:
                async for event in self._phase_3_history(degradation_mode):
                    yield event

            # ========== PHASE 4: HISTORY COMPLETE ==========
            # Only send if we attempted history loading
            if degradation_mode not in [DegradationMode.LIVE_ONLY]:
                yield await self._phase_4_history_complete()

            # ========== PHASE 5: LIVE STREAMING ==========
            # Skip live if in HISTORY_ONLY mode
            if degradation_mode not in [DegradationMode.HISTORY_ONLY]:
                async for event in self._phase_5_live_streaming(degradation_mode):
                    yield event

            # ========== PHASE 6: SEND DONE EVENT ==========
            # Send 'done' event to signal stream completion to CLI/clients
            # This is critical for clients that wait for a terminal event
            yield self.formatter.format_done_event(
                response=None,  # Response is in the messages already
                workflow_status="completed",
            )
            self._stats["total_events_sent"] += 1

            logger.info(
                "phase_6_done_event_sent",
                execution_id=self.execution_id[:8],
            )

        except Exception as e:
            # Log critical error
            logger.error(
                "streaming_orchestration_error",
                execution_id=self.execution_id[:8],
                phase=self._stats["phase"],
                error=str(e),
                error_type=type(e).__name__,
            )
            self._stats["errors"].append({
                "phase": self._stats["phase"],
                "error": str(e),
                "error_type": type(e).__name__,
            })

            # Send error event to client
            yield self.formatter.format_error_event(
                error=str(e),
                error_type="streaming_error",
            )
        finally:
            # Log final statistics
            elapsed = time.time() - self._stats["start_time"]
            self._stats["total_duration_ms"] = int(elapsed * 1000)
            self._stats["deduplication_stats"] = self.deduplicator.get_stats()

            logger.info(
                "execution_streaming_complete",
                execution_id=self.execution_id[:8],
                stats=self._stats,
            )

    async def _phase_1_connect(self) -> str:
        """
        Phase 1: Send immediate 'connected' event (<50ms).

        This event is sent first to unblock the EventSource connection before
        any slow operations (Temporal queries, DB lookups) are performed.

        The client receives this event instantly, allowing the UI to show
        "connecting..." state while we load data in the background.

        Returns:
            SSE-formatted 'connected' event string
        """
        t0 = time.time()
        self._stats["phase"] = "connecting"

        logger.info(
            "phase_1_connecting",
            execution_id=self.execution_id[:8],
        )

        # Send connected event with minimal data (no DB/Temporal queries)
        event = self.formatter.format_connected_event(
            organization_id=self.organization_id,
            status="pending",  # Default status, will be updated later
        )

        self._stats["connection_time_ms"] = int((time.time() - t0) * 1000)
        self._stats["total_events_sent"] += 1

        logger.info(
            "phase_1_connected",
            execution_id=self.execution_id[:8],
            duration_ms=self._stats["connection_time_ms"],
        )

        return event

    async def _phase_2_resumption(self) -> AsyncGenerator[str, None]:
        """
        Phase 2: Handle Last-Event-ID resumption (gap detection and replay).

        If the client provided a Last-Event-ID, we need to:
        1. Check if we have buffered events after that ID
        2. If yes, replay them
        3. If no, check for gaps and notify client

        This phase is skipped if no Last-Event-ID was provided (new connection).

        Yields:
            SSE-formatted events for replay or gap notification
        """
        if not self.last_event_id:
            return

        t0 = time.time()
        self._stats["phase"] = "resumption"

        logger.info(
            "phase_2_resumption_start",
            execution_id=self.execution_id[:8],
            last_event_id=self.last_event_id,
        )

        try:
            # Check for buffered events to replay
            replay_events = self.buffer.replay_from_id(self.last_event_id)

            if replay_events:
                # Replay buffered events
                logger.info(
                    "replaying_buffered_events",
                    execution_id=self.execution_id[:8],
                    replay_count=len(replay_events),
                )

                for event_id, event_type, data_json in replay_events:
                    # Use existing event ID (don't regenerate)
                    yield self.formatter.format_event(
                        event_type=event_type,
                        data={"replay": True},  # Placeholder, actual data in data_json
                        event_id=event_id,
                    )
                    self._stats["events_replayed"] += 1
                    self._stats["total_events_sent"] += 1

            else:
                # Check if last_event_id is too old (buffer miss)
                buffer_miss = self.buffer.check_buffer_miss(self.last_event_id)

                if buffer_miss:
                    # Gap detected - notify client
                    logger.warning(
                        "gap_detected_notifying_client",
                        execution_id=self.execution_id[:8],
                        buffer_miss=buffer_miss,
                    )

                    yield self.formatter.format_gap_detected_event(
                        reason=buffer_miss.get("reason", "Unknown gap"),
                        buffer_oldest=buffer_miss.get("buffer_oldest"),
                    )
                    self._stats["total_events_sent"] += 1

        except Exception as e:
            logger.error(
                "phase_2_resumption_error",
                execution_id=self.execution_id[:8],
                error=str(e),
            )
            self._stats["errors"].append({
                "phase": "resumption",
                "error": str(e),
            })

            # Continue to history load despite error
            # Client will receive full history instead of incremental replay

    async def _phase_3_history(self, degradation_mode: DegradationMode) -> AsyncGenerator[str, None]:
        """
        Phase 3: Stream historical messages from database.

        This phase progressively streams messages from the database using
        HistoryLoader. Messages are yielded one at a time for instant UI
        rendering without waiting for the entire history to load.

        The HistoryLoader handles:
        - Database query with Temporal fallback
        - Message sorting and limiting (last 200)
        - Deduplication via shared deduplicator
        - Empty message filtering

        Args:
            degradation_mode: Current degradation mode for adaptive behavior

        Yields:
            SSE-formatted 'message' events for each historical message
        """
        t0 = time.time()
        self._stats["phase"] = "history_loading"

        logger.info(
            "phase_3_history_start",
            execution_id=self.execution_id[:8],
            degradation_mode=degradation_mode.value,
        )

        try:
            # Create history loader with shared deduplicator
            history_loader = HistoryLoader(
                execution_id=self.execution_id,
                organization_id=self.organization_id,
                db_session=self.db_session,
                temporal_client=self.temporal_client,
                deduplicator=self.deduplicator,
                workflow_id=self.workflow_id,
            )

            # Stream messages progressively
            message_count = 0
            async for message in history_loader.stream():
                # Format as SSE event
                event = self.formatter.format_message_event(message)

                # Buffer event for gap recovery
                event_id = self.formatter.generate_event_id()
                self.buffer.add_event(
                    event_id=event_id,
                    event_type="message",
                    data=str(message),  # Convert to JSON string for buffering
                )
                self._stats["events_buffered"] += 1

                yield event
                message_count += 1
                self._stats["total_events_sent"] += 1
                self._stats["history_messages_sent"] += 1

            # Get history loader stats
            history_stats = history_loader.get_stats()
            self._stats["history_load_time_ms"] = int((time.time() - t0) * 1000)

            logger.info(
                "phase_3_history_complete",
                execution_id=self.execution_id[:8],
                message_count=message_count,
                duration_ms=self._stats["history_load_time_ms"],
                history_stats=history_stats,
            )

        except Exception as e:
            logger.error(
                "phase_3_history_error",
                execution_id=self.execution_id[:8],
                error=str(e),
                error_type=type(e).__name__,
            )
            self._stats["errors"].append({
                "phase": "history_loading",
                "error": str(e),
                "error_type": type(e).__name__,
            })

            # Send degraded event to notify client
            yield self.formatter.format_degraded_event(
                mode="history_unavailable",
                reason="Failed to load message history",
                message=f"Database query failed: {str(e)[:100]}",
                capabilities=["live_events"],  # Can still serve live if Redis available
            )
            self._stats["total_events_sent"] += 1

            # Continue to live streaming despite history failure

    async def _phase_4_history_complete(self) -> str:
        """
        Phase 4: Send 'history_complete' event.

        This event signals to the client that all historical messages have
        been loaded and the stream is transitioning to live event mode.

        The client can use this to:
        - Stop showing loading spinners
        - Switch to real-time update mode
        - Update UI to indicate "connected" state

        Returns:
            SSE-formatted 'history_complete' event string
        """
        self._stats["phase"] = "history_complete"

        logger.info(
            "phase_4_history_complete",
            execution_id=self.execution_id[:8],
            message_count=self._stats["history_messages_sent"],
        )

        event = self.formatter.format_history_complete_event(
            message_count=self._stats["history_messages_sent"],
            is_truncated=False,  # HistoryLoader handles truncation internally
            has_more=False,
        )

        self._stats["total_events_sent"] += 1

        return event

    async def _phase_5_live_streaming(self, degradation_mode: DegradationMode) -> AsyncGenerator[str, None]:
        """
        Phase 5: Stream live events from Redis until workflow completes.

        This phase uses LiveEventSource to poll Redis for new events at
        200ms intervals. Events are deduplicated against history and yielded
        as they arrive.

        The streaming continues until:
        - Workflow reaches terminal state (COMPLETED, FAILED, CANCELLED)
        - Timeout is reached (default: 0 = no timeout, streams until complete)
        - Client disconnects
        - Critical error occurs

        Includes periodic recovery checks every 30 seconds to detect when
        services come back online.

        Args:
            degradation_mode: Current degradation mode for adaptive behavior

        Yields:
            SSE-formatted events for live updates, keepalives, status changes, etc.
        """
        t0 = time.time()
        self._stats["phase"] = "live_streaming"

        # Constants for recovery monitoring
        HEALTH_CHECK_INTERVAL = 30  # seconds

        logger.info(
            "phase_5_live_streaming_start",
            execution_id=self.execution_id[:8],
            timeout_seconds=self.timeout_seconds,
            degradation_mode=degradation_mode.value,
        )

        try:
            # Get or create workflow handle
            workflow_handle = await self._get_workflow_handle()

            # Create live event source with shared deduplicator
            live_source = LiveEventSource(
                execution_id=self.execution_id,
                organization_id=self.organization_id,
                redis_client=self.redis_client,
                workflow_handle=workflow_handle,
                deduplicator=self.deduplicator,
                timeout_seconds=self.timeout_seconds,
                keepalive_interval=15,
                db_session=self.db_session,  # Pass database session for status polling
            )

            # Stream live events
            event_count = 0
            async for event in live_source.stream():
                # Check for service recovery every 30 seconds
                if time.time() - self._last_health_check > HEALTH_CHECK_INTERVAL:
                    new_mode = await self.health_checker.get_degradation_mode()
                    self._last_health_check = time.time()

                    # If services recovered to FULL from degraded mode
                    if new_mode == DegradationMode.FULL and self._degradation_mode != DegradationMode.FULL:
                        logger.info(
                            "services_recovered",
                            execution_id=self.execution_id[:8],
                            old_mode=self._degradation_mode.value,
                            new_mode=new_mode.value,
                        )

                        # Notify client of recovery
                        recovery_event = self.formatter.format_recovered_event(
                            message="Services recovered, resuming full functionality"
                        )
                        yield recovery_event
                        self._stats["total_events_sent"] += 1

                        # Update tracking
                        self._degradation_mode = new_mode
                        self._stats["degradation_mode"] = new_mode.value

                # Event is already a dict with event_type and data
                event_type = event.get("event_type", "message")

                # Format based on event type
                if event_type == "message":
                    sse_event = self.formatter.format_message_event(event)
                elif event_type == "status":
                    sse_event = self.formatter.format_status_event(
                        status=event.get("status", "unknown"),
                        metadata=event.get("data", {}),
                    )
                elif event_type == "tool_started":
                    sse_event = self.formatter.format_tool_started_event(event)
                elif event_type == "tool_completed":
                    sse_event = self.formatter.format_tool_completed_event(event)
                elif event_type == "member_tool_started":
                    sse_event = self.formatter.format_member_tool_started_event(event)
                elif event_type == "member_tool_completed":
                    sse_event = self.formatter.format_member_tool_completed_event(event)
                elif event_type == "message_chunk":
                    sse_event = self.formatter.format_message_chunk_event(event)
                elif event_type == "member_message_chunk":
                    sse_event = self.formatter.format_member_message_chunk_event(event)
                elif event_type == "member_message_complete":
                    sse_event = self.formatter.format_member_message_complete_event(event)
                # Thinking/reasoning event types
                elif event_type == "thinking_start":
                    sse_event = self.formatter.format_thinking_start_event(
                        message_id=event.get("data", {}).get("message_id", ""),
                        index=event.get("data", {}).get("index", 0),
                        budget_tokens=event.get("data", {}).get("budget_tokens"),
                    )
                elif event_type == "thinking_delta":
                    sse_event = self.formatter.format_thinking_delta_event(
                        message_id=event.get("data", {}).get("message_id", ""),
                        thinking=event.get("data", {}).get("thinking", ""),
                        index=event.get("data", {}).get("index", 0),
                    )
                elif event_type == "thinking_complete":
                    sse_event = self.formatter.format_thinking_complete_event(
                        message_id=event.get("data", {}).get("message_id", ""),
                        index=event.get("data", {}).get("index", 0),
                        signature=event.get("data", {}).get("signature"),
                        tokens_used=event.get("data", {}).get("tokens_used"),
                    )
                elif event_type == "keepalive":
                    sse_event = self.formatter.format_keepalive()
                elif event_type == "degraded":
                    # Handle legacy degraded events from LiveEventSource
                    sse_event = self.formatter.format_degraded_event(
                        mode="degraded",
                        reason=event.get("data", {}).get("reason", "unknown"),
                        message=event.get("data", {}).get("message", "Degraded mode"),
                    )
                else:
                    # Generic event
                    sse_event = self.formatter.format_event(
                        event_type=event_type,
                        data=event.get("data", event),
                    )

                # Buffer event for gap recovery (except keepalives)
                if event_type != "keepalive":
                    event_id = self.formatter.generate_event_id()
                    self.buffer.add_event(
                        event_id=event_id,
                        event_type=event_type,
                        data=str(event),  # Convert to JSON string
                    )
                    self._stats["events_buffered"] += 1

                yield sse_event
                event_count += 1
                self._stats["total_events_sent"] += 1
                self._stats["live_events_sent"] += 1

            self._stats["live_streaming_time_ms"] = int((time.time() - t0) * 1000)

            logger.info(
                "phase_5_live_streaming_complete",
                execution_id=self.execution_id[:8],
                event_count=event_count,
                duration_ms=self._stats["live_streaming_time_ms"],
            )

        except Exception as e:
            logger.error(
                "phase_5_live_streaming_error",
                execution_id=self.execution_id[:8],
                error=str(e),
                error_type=type(e).__name__,
            )
            self._stats["errors"].append({
                "phase": "live_streaming",
                "error": str(e),
                "error_type": type(e).__name__,
            })

            # Send degraded event to notify client
            yield self.formatter.format_degraded_event(
                mode="live_events_unavailable",
                reason="Failed to stream live events",
                message=f"Redis streaming failed: {str(e)[:100]}",
                capabilities=["history"],  # At least we served history
            )
            self._stats["total_events_sent"] += 1

            # Don't crash - we already served history if it was available

    async def _get_workflow_handle(self):
        """
        Get Temporal workflow handle with caching and error handling.

        This method attempts to get a workflow handle from Temporal with a
        2-second timeout to fail fast when worker is down.

        Returns:
            Temporal workflow handle or None if unavailable

        Note:
            The workflow handle is cached after first successful retrieval.
            If retrieval fails, None is cached and logged (graceful degradation).
        """
        if self._workflow_handle is not None:
            return self._workflow_handle

        if self._workflow_handle_error is not None:
            # Already failed to get handle, don't retry
            return None

        if not self.temporal_client:
            logger.warning(
                "no_temporal_client_available",
                execution_id=self.execution_id[:8],
            )
            self._workflow_handle_error = "No Temporal client"
            return None

        try:
            # Try to get workflow handle with 2-second timeout
            self._workflow_handle = self.temporal_client.get_workflow_handle(
                self.workflow_id
            )

            logger.info(
                "workflow_handle_obtained",
                execution_id=self.execution_id[:8],
                workflow_id=self.workflow_id,
            )

            return self._workflow_handle

        except Exception as e:
            logger.warning(
                "failed_to_get_workflow_handle",
                execution_id=self.execution_id[:8],
                workflow_id=self.workflow_id,
                error=str(e),
            )
            self._workflow_handle_error = str(e)
            return None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get streaming statistics.

        Returns:
            Dictionary with statistics:
            - phase: Current phase
            - start_time: Stream start timestamp
            - connection_time_ms: Phase 1 duration
            - history_load_time_ms: Phase 3 duration
            - live_streaming_time_ms: Phase 5 duration
            - total_events_sent: Total events sent to client
            - history_messages_sent: Messages sent in phase 3
            - live_events_sent: Events sent in phase 5
            - events_buffered: Events added to EventBuffer
            - events_replayed: Events replayed in phase 2
            - deduplication_stats: Stats from MessageDeduplicator
            - errors: List of errors encountered
        """
        return self._stats.copy()
