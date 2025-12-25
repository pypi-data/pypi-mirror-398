"""
StatusService for cached workflow status queries.

This module provides the StatusService class that caches Temporal workflow status
queries to reduce API load during high-frequency polling operations.

Key Features:
- 1-second TTL cache for status queries
- Reduces Temporal API load during SSE polling (typically 200ms intervals)
- Handles Temporal timeouts gracefully (2 second timeout)
- Thread-safe for concurrent access
- Per-execution_id cache keys
- Terminal state detection

Cache Strategy:
- Cache hit: Return cached status if within 1 second TTL
- Cache miss: Query Temporal, cache result, return status
- Cache invalidation: Automatic on TTL expiration or manual invalidation
- Terminal states cached indefinitely (no need to re-query completed workflows)

Test Strategy:
- Test cache hit behavior (query within 1 second returns cached value)
- Test cache miss behavior (query after TTL returns fresh value)
- Test TTL expiration (cache becomes invalid after 1 second)
- Test timeout handling (2 second Temporal timeout)
- Test terminal state detection (COMPLETED, FAILED, etc.)
- Test cache invalidation (manual and automatic)
- Test concurrent access (asyncio lock prevents race conditions)
- Test workflow_handle None handling
- Test Temporal unavailable handling
"""

import asyncio
import time
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger()


class StatusService:
    """
    Service for querying and caching Temporal workflow status.

    This service provides cached workflow status queries to reduce load on
    Temporal API during high-frequency polling operations (e.g., SSE streaming
    at 200ms intervals).

    The cache uses a 1-second TTL to balance freshness with API load reduction.
    Terminal states (COMPLETED, FAILED, etc.) are cached indefinitely since
    they won't change.

    Example:
        ```python
        status_service = StatusService(
            temporal_client=client,
            execution_id="exec-123",
            organization_id="org-456"
        )

        # First call queries Temporal
        status = await status_service.get_status()  # "RUNNING"

        # Second call within 1 second uses cache
        status = await status_service.get_status()  # "RUNNING" (cached)

        # Force refresh ignores cache
        status = await status_service.get_status(force_refresh=True)  # "COMPLETED" (fresh)

        # Check terminal state
        if await status_service.is_terminal():
            print("Workflow completed")
        ```
    """

    # Cache TTL in seconds - balances freshness with API load
    CACHE_TTL = 1.0

    # Terminal workflow states that won't change (cache indefinitely)
    TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED", "TERMINATED", "TIMED_OUT"}

    def __init__(
        self,
        workflow_handle: Optional[Any],
        execution_id: str,
        organization_id: str,
    ):
        """
        Initialize StatusService.

        Args:
            workflow_handle: Temporal workflow handle for status queries (can be None)
            execution_id: Execution ID for this workflow
            organization_id: Organization ID for authorization
        """
        self.workflow_handle = workflow_handle
        self.execution_id = execution_id
        self.organization_id = organization_id

        # Cache structure: {execution_id: {status, timestamp, workflow_info}}
        self._cache: Dict[str, Dict[str, Any]] = {}

        # Lock for thread-safe cache access
        self._lock = asyncio.Lock()

        logger.debug(
            "status_service_initialized",
            execution_id=execution_id[:8] if execution_id else "unknown",
            has_workflow_handle=workflow_handle is not None,
        )

    async def get_status(self, force_refresh: bool = False) -> Optional[str]:
        """
        Get workflow status with caching.

        This method checks the cache first and only queries Temporal if:
        1. Cache is empty (first call)
        2. Cache has expired (TTL exceeded)
        3. force_refresh is True

        Args:
            force_refresh: Skip cache and query Temporal directly

        Returns:
            Status string (RUNNING, COMPLETED, FAILED, CANCELLED, TERMINATED, TIMED_OUT)
            or None if workflow_handle is None or query fails

        Example:
            ```python
            # Normal cached query
            status = await service.get_status()

            # Force fresh query
            status = await service.get_status(force_refresh=True)
            ```
        """
        if not self.workflow_handle:
            logger.debug(
                "status_query_skipped_no_workflow_handle",
                execution_id=self.execution_id[:8],
            )
            return None

        async with self._lock:
            current_time = time.time()

            # Check cache validity
            if not force_refresh and self._is_cache_valid(self.execution_id):
                cached_entry = self._cache[self.execution_id]
                cached_status = cached_entry["status"]
                cache_age = current_time - cached_entry["timestamp"]

                logger.debug(
                    "status_cache_hit",
                    execution_id=self.execution_id[:8],
                    status=cached_status,
                    cache_age_ms=int(cache_age * 1000),
                )
                return cached_status

            # Cache miss or expired - query Temporal
            status = await self._query_temporal()

            if status:
                # Update cache
                self._cache[self.execution_id] = {
                    "status": status,
                    "timestamp": current_time,
                }

                cache_status = "refreshed" if force_refresh else "miss"
                logger.debug(
                    f"status_cache_{cache_status}",
                    execution_id=self.execution_id[:8],
                    status=status,
                )

            return status

    async def is_terminal(self) -> bool:
        """
        Check if workflow is in terminal state.

        Terminal states are: COMPLETED, FAILED, CANCELLED, TERMINATED, TIMED_OUT
        These states are final and won't change.

        Returns:
            True if workflow is in terminal state, False otherwise

        Example:
            ```python
            if await service.is_terminal():
                print("Workflow finished")
                # Stop polling
            ```
        """
        status = await self.get_status()
        if not status:
            return False

        is_terminal = status in self.TERMINAL_STATES

        logger.debug(
            "terminal_state_check",
            execution_id=self.execution_id[:8],
            status=status,
            is_terminal=is_terminal,
        )

        return is_terminal

    async def is_running(self) -> bool:
        """
        Check if workflow is currently running.

        Returns:
            True if workflow status is RUNNING, False otherwise

        Example:
            ```python
            if await service.is_running():
                print("Workflow is active")
                # Continue polling
            ```
        """
        status = await self.get_status()
        if not status:
            return False

        is_running = status == "RUNNING"

        logger.debug(
            "running_state_check",
            execution_id=self.execution_id[:8],
            status=status,
            is_running=is_running,
        )

        return is_running

    async def _query_temporal(self) -> Optional[str]:
        """
        Query Temporal for current workflow status with timeout.

        This method queries the Temporal workflow handle with a 2-second timeout
        to prevent hanging on slow/unavailable Temporal clusters.

        Returns:
            Status enum name (e.g., "RUNNING", "COMPLETED") or None on error

        Handles:
            - Timeout after 2 seconds
            - Temporal unavailable errors
            - Network errors
            - Invalid workflow handle
        """
        if not self.workflow_handle:
            return None

        try:
            t0 = time.time()

            # Query Temporal with 2 second timeout
            description = await asyncio.wait_for(
                self.workflow_handle.describe(),
                timeout=2.0,
            )

            # Extract status enum name (e.g., "RUNNING")
            # Temporal execution status enum values:
            # RUNNING, COMPLETED, FAILED, CANCELLED, TERMINATED, TIMED_OUT, CONTINUED_AS_NEW
            status = description.status.name

            query_duration = int((time.time() - t0) * 1000)

            logger.debug(
                "temporal_status_query_success",
                execution_id=self.execution_id[:8],
                status=status,
                duration_ms=query_duration,
            )

            # Log slow queries (>100ms)
            if query_duration > 100:
                logger.warning(
                    "slow_temporal_status_query",
                    execution_id=self.execution_id[:8],
                    duration_ms=query_duration,
                )

            return status

        except asyncio.TimeoutError:
            logger.warning(
                "temporal_status_query_timeout",
                execution_id=self.execution_id[:8],
                timeout_seconds=2.0,
            )
            return None

        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)

            logger.error(
                "temporal_status_query_error",
                execution_id=self.execution_id[:8],
                error_type=error_type,
                error=error_msg,
            )
            return None

    def _is_cache_valid(self, execution_id: str) -> bool:
        """
        Check if cached status is still valid (within TTL).

        For terminal states, cache is always valid (infinite TTL).
        For non-terminal states, cache is valid for CACHE_TTL seconds.

        Args:
            execution_id: Execution ID to check cache for

        Returns:
            True if cache exists and is valid, False otherwise
        """
        if execution_id not in self._cache:
            return False

        cached_entry = self._cache[execution_id]
        cached_status = cached_entry["status"]

        # Terminal states are cached indefinitely
        if cached_status in self.TERMINAL_STATES:
            logger.debug(
                "cache_valid_terminal_state",
                execution_id=execution_id[:8],
                status=cached_status,
            )
            return True

        # Non-terminal states use TTL
        current_time = time.time()
        cache_age = current_time - cached_entry["timestamp"]
        is_valid = cache_age < self.CACHE_TTL

        if not is_valid:
            logger.debug(
                "cache_expired",
                execution_id=execution_id[:8],
                cache_age_ms=int(cache_age * 1000),
                ttl_ms=int(self.CACHE_TTL * 1000),
            )

        return is_valid

    def invalidate_cache(self, execution_id: Optional[str] = None):
        """
        Invalidate cache for specific execution or all executions.

        Args:
            execution_id: Execution ID to invalidate, or None to invalidate all

        Example:
            ```python
            # Invalidate specific execution
            service.invalidate_cache("exec-123")

            # Invalidate all
            service.invalidate_cache()
            ```
        """
        if execution_id:
            if execution_id in self._cache:
                del self._cache[execution_id]
                logger.debug(
                    "cache_invalidated",
                    execution_id=execution_id[:8],
                )
        else:
            # Invalidate all
            cache_size = len(self._cache)
            self._cache.clear()
            logger.debug(
                "cache_cleared_all",
                cleared_entries=cache_size,
            )

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.

        Returns:
            Dictionary with cache statistics:
            - size: Number of cached entries
            - entries: List of cached execution IDs with status and age

        Example:
            ```python
            stats = service.get_cache_stats()
            print(f"Cache size: {stats['size']}")
            for entry in stats['entries']:
                print(f"  {entry['execution_id']}: {entry['status']} ({entry['age_ms']}ms old)")
            ```
        """
        current_time = time.time()
        entries = []

        for exec_id, cached_entry in self._cache.items():
            cache_age = current_time - cached_entry["timestamp"]
            entries.append({
                "execution_id": exec_id,
                "status": cached_entry["status"],
                "age_ms": int(cache_age * 1000),
                "is_valid": self._is_cache_valid(exec_id),
            })

        return {
            "size": len(self._cache),
            "entries": entries,
        }
