"""
Event Batcher for efficient HTTP event publishing.

Batches multiple events into a single HTTP request to reduce overhead,
especially important for serverless deployments like Vercel where you
pay per request.

Features:
- Time-based flushing (default 50ms)
- Size-based flushing (default 10 events)
- Priority-based immediate flushing for critical events
- Automatic background flushing task
- Graceful shutdown with pending event flush

Usage:
    batcher = EventBatcher(
        flush_callback=send_batch_to_server,
        max_batch_size=10,
        max_batch_time_ms=50
    )

    await batcher.start()
    await batcher.add_event(event_data, priority="normal")
    await batcher.add_event(critical_event, priority="critical")  # Flushes immediately
    await batcher.stop()
"""

import asyncio
import time
from typing import Dict, Any, Callable, Literal, List, Optional
import structlog

logger = structlog.get_logger()


class EventBatcher:
    """
    Batches events for efficient HTTP publishing.

    Reduces HTTP request count by batching multiple events together,
    with smart flushing based on time, size, and priority.
    """

    def __init__(
        self,
        flush_callback: Callable[[List[Dict[str, Any]]], Any],
        max_batch_size: int = 10,
        max_batch_time_ms: int = 50,
        enabled: bool = True
    ):
        """
        Initialize event batcher.

        Args:
            flush_callback: Async callback to send batch (receives list of events)
            max_batch_size: Maximum events per batch before auto-flush
            max_batch_time_ms: Maximum milliseconds to wait before auto-flush
            enabled: Whether batching is enabled (if False, events flush immediately)
        """
        self.flush_callback = flush_callback
        self.max_batch_size = max_batch_size
        self.max_batch_time_ms = max_batch_time_ms
        self.enabled = enabled

        # Batch state
        self.batch: List[Dict[str, Any]] = []
        self.batch_lock = asyncio.Lock()
        self.last_flush_time = time.time()

        # Background flush task
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False

        # Statistics
        self.stats = {
            "total_events": 0,
            "total_batches": 0,
            "total_flushes": 0,
            "time_based_flushes": 0,
            "size_based_flushes": 0,
            "critical_flushes": 0,
            "events_per_batch_avg": 0.0
        }

    async def start(self):
        """Start the background flush task."""
        if not self.enabled:
            logger.info("event_batching_disabled")
            return

        if self._running:
            logger.warning("event_batcher_already_running")
            return

        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info(
            "event_batcher_started",
            max_batch_size=self.max_batch_size,
            max_batch_time_ms=self.max_batch_time_ms
        )

    async def stop(self):
        """Stop the batcher and flush any pending events."""
        self._running = False

        # Cancel background task
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Flush any remaining events
        await self._flush_batch("shutdown")

        logger.info(
            "event_batcher_stopped",
            stats=self.stats
        )

    async def add_event(
        self,
        event: Dict[str, Any],
        priority: Literal["normal", "critical"] = "normal"
    ) -> bool:
        """
        Add an event to the batch.

        Args:
            event: Event data to batch
            priority: "normal" for regular events, "critical" for immediate flush

        Returns:
            True if event was added successfully
        """
        if not self.enabled:
            # If batching disabled, send immediately
            try:
                result = self.flush_callback([event])
                if asyncio.iscoroutine(result):
                    await result
                return True
            except Exception as e:
                logger.error("event_send_failed", error=str(e))
                return False

        async with self.batch_lock:
            self.batch.append(event)
            self.stats["total_events"] += 1

            # Critical events flush immediately
            if priority == "critical":
                await self._flush_batch("critical")
                return True

            # Size-based flush
            if len(self.batch) >= self.max_batch_size:
                await self._flush_batch("size")
                return True

        return True

    async def _flush_loop(self):
        """Background task that flushes batches based on time."""
        while self._running:
            try:
                # Check every 10ms (more responsive than max_batch_time_ms)
                await asyncio.sleep(0.01)

                # Check if we need time-based flush
                async with self.batch_lock:
                    if not self.batch:
                        continue

                    elapsed_ms = (time.time() - self.last_flush_time) * 1000
                    if elapsed_ms >= self.max_batch_time_ms:
                        await self._flush_batch("time")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("flush_loop_error", error=str(e))
                # Continue running even if flush fails

    async def _flush_batch(self, reason: str):
        """
        Flush the current batch.

        Args:
            reason: Reason for flush (time/size/critical/shutdown)

        Note: Caller must hold batch_lock
        """
        if not self.batch:
            return

        batch_to_send = self.batch.copy()
        batch_size = len(batch_to_send)

        # Clear batch immediately (unlock for new events)
        self.batch.clear()
        self.last_flush_time = time.time()

        # Update statistics
        self.stats["total_batches"] += 1
        self.stats["total_flushes"] += 1

        if reason == "time":
            self.stats["time_based_flushes"] += 1
        elif reason == "size":
            self.stats["size_based_flushes"] += 1
        elif reason == "critical":
            self.stats["critical_flushes"] += 1

        # Calculate average batch size
        self.stats["events_per_batch_avg"] = (
            self.stats["total_events"] / self.stats["total_batches"]
        )

        # Send batch (outside lock)
        try:
            logger.debug(
                "flushing_event_batch",
                batch_size=batch_size,
                reason=reason,
                avg_batch_size=f"{self.stats['events_per_batch_avg']:.1f}"
            )

            result = self.flush_callback(batch_to_send)
            if asyncio.iscoroutine(result):
                await result

            logger.debug(
                "event_batch_flushed",
                batch_size=batch_size,
                reason=reason
            )

        except Exception as e:
            logger.error(
                "batch_flush_failed",
                error=str(e),
                batch_size=batch_size,
                reason=reason
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get batching statistics."""
        return self.stats.copy()

    async def force_flush(self):
        """Force flush any pending events (useful for testing or critical sections)."""
        async with self.batch_lock:
            await self._flush_batch("manual")
