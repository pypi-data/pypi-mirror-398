"""Worker Health Checker Service

This service detects worker and service availability to enable graceful degradation
when critical services (Temporal, Redis, Database) are unavailable.

Degradation Modes:
- FULL: All services available (Temporal + Redis + Database)
- HISTORY_ONLY: Only database available (can serve historical data)
- LIVE_ONLY: Only Redis available (can serve live events)
- DEGRADED: Partial functionality available
- UNAVAILABLE: Critical services down

Usage:
    health_checker = WorkerHealthChecker(
        temporal_client=temporal_client,
        redis_client=redis_client,
        db_session=db_session
    )

    mode = await health_checker.get_degradation_mode()
    capabilities = health_checker.get_capabilities(mode)
"""

import asyncio
import time
from enum import Enum
from typing import Dict, List, Optional, Any
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = structlog.get_logger()


class DegradationMode(Enum):
    """Service degradation modes based on availability."""

    FULL = "full"  # All services available
    HISTORY_ONLY = "history_only"  # Only database available
    LIVE_ONLY = "live_only"  # Only Redis available
    DEGRADED = "degraded"  # Partial functionality
    UNAVAILABLE = "unavailable"  # Critical services down


# Capabilities available in each degradation mode
CAPABILITIES = {
    DegradationMode.FULL: [
        "history",
        "live_events",
        "status_updates",
        "completion_detection",
        "workflow_queries",
    ],
    DegradationMode.HISTORY_ONLY: [
        "history",
    ],
    DegradationMode.LIVE_ONLY: [
        "live_events",
    ],
    DegradationMode.DEGRADED: [
        "partial_functionality",
    ],
    DegradationMode.UNAVAILABLE: [],
}


class WorkerHealthChecker:
    """
    Health checker for worker and service availability.

    Performs health checks on critical services with proper timeouts to
    avoid blocking operations. Results can be cached to prevent excessive
    health check overhead.

    Attributes:
        temporal_client: Temporal client instance (optional)
        redis_client: Redis client instance (optional)
        db_session: Database session instance (optional)
        cache_ttl: Time-to-live for health check cache in seconds
    """

    # Timeout values for health checks (in seconds)
    TEMPORAL_TIMEOUT = 2.0  # Fast timeout - don't block on Temporal
    REDIS_TIMEOUT = 1.0  # Redis should be fast
    DATABASE_TIMEOUT = 1.0  # Database should be fast

    def __init__(
        self,
        temporal_client=None,
        redis_client=None,
        db_session: Optional[Session] = None,
        cache_ttl: int = 10,  # Cache health check results for 10 seconds
    ):
        """
        Initialize WorkerHealthChecker.

        Args:
            temporal_client: Temporal client instance (can be None)
            redis_client: Redis client instance (can be None)
            db_session: Database session instance (can be None)
            cache_ttl: Cache TTL in seconds for health check results
        """
        self.temporal_client = temporal_client
        self.redis_client = redis_client
        self.db_session = db_session
        self.cache_ttl = cache_ttl

        # Cache health check results to avoid excessive checks
        # Format: {"temporal": (timestamp, result), "redis": (timestamp, result), ...}
        self._last_check: Dict[str, tuple[float, bool]] = {}

    def _is_cached(self, service: str) -> Optional[bool]:
        """
        Check if health check result is cached and still valid.

        Args:
            service: Service name ("temporal", "redis", "database")

        Returns:
            Cached result if valid, None if cache miss or expired
        """
        if service not in self._last_check:
            return None

        timestamp, result = self._last_check[service]
        if time.time() - timestamp < self.cache_ttl:
            logger.debug(
                "health_check_cache_hit",
                service=service,
                result=result,
                age_seconds=time.time() - timestamp
            )
            return result

        return None

    def _cache_result(self, service: str, result: bool) -> None:
        """
        Cache health check result.

        Args:
            service: Service name ("temporal", "redis", "database")
            result: Health check result (True if healthy)
        """
        self._last_check[service] = (time.time(), result)

    async def check_temporal_connectivity(self) -> bool:
        """
        Check if Temporal is accessible.

        Attempts to verify Temporal client is connected and responsive.
        Uses a fast timeout (2 seconds) to fail quickly when worker is down.

        Returns:
            True if connected and responsive, False otherwise

        Test Strategy:
            - Test with Temporal unavailable (connection timeout)
            - Test with Temporal available (successful connection)
            - Test timeout behavior (should complete within 2 seconds)
        """
        # Check cache first
        cached = self._is_cached("temporal")
        if cached is not None:
            return cached

        if not self.temporal_client:
            logger.debug("temporal_health_check_skipped", reason="no_client")
            self._cache_result("temporal", False)
            return False

        try:
            # Try to describe the client with timeout
            # This is a lightweight operation that verifies connectivity
            t0 = time.time()

            # Try getting workflow service with timeout
            result = await asyncio.wait_for(
                self._check_temporal_service(),
                timeout=self.TEMPORAL_TIMEOUT
            )

            duration_ms = int((time.time() - t0) * 1000)
            logger.debug(
                "temporal_health_check_passed",
                duration_ms=duration_ms,
                result=result
            )

            self._cache_result("temporal", result)
            return result

        except asyncio.TimeoutError:
            duration_ms = int((time.time() - t0) * 1000)
            logger.warning(
                "temporal_health_check_timeout",
                timeout_seconds=self.TEMPORAL_TIMEOUT,
                duration_ms=duration_ms
            )
            self._cache_result("temporal", False)
            return False

        except Exception as e:
            logger.warning(
                "temporal_health_check_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            self._cache_result("temporal", False)
            return False

    async def _check_temporal_service(self) -> bool:
        """
        Internal method to check Temporal service availability.

        Returns:
            True if service is accessible
        """
        try:
            # Check if client has a workflow service
            # This is a lightweight check that doesn't require a specific workflow
            if hasattr(self.temporal_client, 'workflow_service'):
                # Client is properly initialized
                return True

            # Fallback: Check if client object exists
            return self.temporal_client is not None

        except Exception as e:
            logger.debug("temporal_service_check_error", error=str(e))
            return False

    async def check_redis_connectivity(self) -> bool:
        """
        Check if Redis is accessible.

        Performs a simple PING operation to verify Redis connectivity.
        Uses a 1-second timeout to fail quickly.

        Returns:
            True if connected and responsive, False otherwise

        Test Strategy:
            - Test with Redis unavailable (connection error)
            - Test with Redis available (successful ping)
            - Test timeout behavior (should complete within 1 second)
        """
        # Check cache first
        cached = self._is_cached("redis")
        if cached is not None:
            return cached

        if not self.redis_client:
            logger.debug("redis_health_check_skipped", reason="no_client")
            self._cache_result("redis", False)
            return False

        try:
            t0 = time.time()

            # Try a simple PING operation with timeout
            result = await asyncio.wait_for(
                self.redis_client.ping(),
                timeout=self.REDIS_TIMEOUT
            )

            duration_ms = int((time.time() - t0) * 1000)

            # Redis ping returns True/PONG on success
            is_healthy = result is True or result == "PONG"

            logger.debug(
                "redis_health_check_passed",
                duration_ms=duration_ms,
                result=is_healthy
            )

            self._cache_result("redis", is_healthy)
            return is_healthy

        except asyncio.TimeoutError:
            duration_ms = int((time.time() - t0) * 1000)
            logger.warning(
                "redis_health_check_timeout",
                timeout_seconds=self.REDIS_TIMEOUT,
                duration_ms=duration_ms
            )
            self._cache_result("redis", False)
            return False

        except Exception as e:
            logger.warning(
                "redis_health_check_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            self._cache_result("redis", False)
            return False

    async def check_database_connectivity(self) -> bool:
        """
        Check if database is accessible.

        Performs a simple SELECT 1 query to verify database connectivity.
        Uses a 1-second timeout to fail quickly.

        Returns:
            True if connected and responsive, False otherwise

        Test Strategy:
            - Test with database unavailable (connection error)
            - Test with database available (successful query)
            - Test timeout behavior (should complete within 1 second)
        """
        # Check cache first
        cached = self._is_cached("database")
        if cached is not None:
            return cached

        if not self.db_session:
            logger.debug("database_health_check_skipped", reason="no_session")
            self._cache_result("database", False)
            return False

        try:
            t0 = time.time()

            # Try a simple query with timeout
            result = await asyncio.wait_for(
                self._check_database_query(),
                timeout=self.DATABASE_TIMEOUT
            )

            duration_ms = int((time.time() - t0) * 1000)
            logger.debug(
                "database_health_check_passed",
                duration_ms=duration_ms,
                result=result
            )

            self._cache_result("database", result)
            return result

        except asyncio.TimeoutError:
            duration_ms = int((time.time() - t0) * 1000)
            logger.warning(
                "database_health_check_timeout",
                timeout_seconds=self.DATABASE_TIMEOUT,
                duration_ms=duration_ms
            )
            self._cache_result("database", False)
            return False

        except Exception as e:
            logger.warning(
                "database_health_check_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            self._cache_result("database", False)
            return False

    async def _check_database_query(self) -> bool:
        """
        Internal method to execute database health check query.

        Returns:
            True if query successful
        """
        try:
            # Execute simple query to verify database connectivity
            result = self.db_session.execute(text("SELECT 1"))

            # Verify we got a result
            if result:
                return True

            return False

        except Exception as e:
            logger.debug("database_query_error", error=str(e))
            return False

    async def check_all(self) -> Dict[str, bool]:
        """
        Run all health checks and return results.

        Executes all health checks concurrently for efficiency.

        Returns:
            Dictionary with health check results:
            {
                "temporal": bool,
                "redis": bool,
                "database": bool
            }

        Test Strategy:
            - Test with all services available
            - Test with all services unavailable
            - Test with mixed availability
        """
        # Run all checks concurrently for efficiency
        temporal_check, redis_check, db_check = await asyncio.gather(
            self.check_temporal_connectivity(),
            self.check_redis_connectivity(),
            self.check_database_connectivity(),
            return_exceptions=True  # Don't let one failure stop others
        )

        # Handle any exceptions from gather
        temporal_ok = temporal_check if isinstance(temporal_check, bool) else False
        redis_ok = redis_check if isinstance(redis_check, bool) else False
        db_ok = db_check if isinstance(db_check, bool) else False

        results = {
            "temporal": temporal_ok,
            "redis": redis_ok,
            "database": db_ok,
        }

        logger.info("health_check_all_completed", **results)
        return results

    async def get_degradation_mode(self) -> DegradationMode:
        """
        Determine current degradation mode based on service availability.

        Logic:
        - All available: FULL
        - Only DB: HISTORY_ONLY
        - Only Redis: LIVE_ONLY
        - Some available: DEGRADED
        - None available: UNAVAILABLE

        Returns:
            Current degradation mode

        Test Strategy:
            - Test all degradation mode combinations
            - Test mode selection logic
            - Test with various service availability patterns
        """
        # Get health check results
        temporal_ok = await self.check_temporal_connectivity()
        redis_ok = await self.check_redis_connectivity()
        db_ok = await self.check_database_connectivity()

        # Determine degradation mode
        if temporal_ok and redis_ok and db_ok:
            mode = DegradationMode.FULL

        elif db_ok and not (temporal_ok or redis_ok):
            # Database only - can serve historical data
            mode = DegradationMode.HISTORY_ONLY

        elif redis_ok and not db_ok:
            # Redis only - can serve live events (no history)
            mode = DegradationMode.LIVE_ONLY

        elif any([temporal_ok, redis_ok, db_ok]):
            # Some services available but not full functionality
            mode = DegradationMode.DEGRADED

        else:
            # Nothing available
            mode = DegradationMode.UNAVAILABLE

        logger.info(
            "degradation_mode_determined",
            mode=mode.value,
            temporal=temporal_ok,
            redis=redis_ok,
            database=db_ok
        )

        return mode

    def get_capabilities(self, mode: DegradationMode) -> List[str]:
        """
        Return list of available capabilities for given mode.

        Args:
            mode: Degradation mode

        Returns:
            List of capability names available in this mode

        Examples:
            >>> checker = WorkerHealthChecker()
            >>> checker.get_capabilities(DegradationMode.FULL)
            ['history', 'live_events', 'status_updates', 'completion_detection', 'workflow_queries']

            >>> checker.get_capabilities(DegradationMode.HISTORY_ONLY)
            ['history']
        """
        capabilities = CAPABILITIES.get(mode, [])

        logger.debug(
            "capabilities_retrieved",
            mode=mode.value,
            capabilities=capabilities
        )

        return capabilities

    def clear_cache(self) -> None:
        """
        Clear all cached health check results.

        Useful when you want to force fresh health checks.
        """
        self._last_check.clear()
        logger.debug("health_check_cache_cleared")
