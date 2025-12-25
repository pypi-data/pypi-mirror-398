"""Tests for WorkerHealthChecker service

Test Strategy:
1. Test each health check individually (Temporal, Redis, Database)
2. Test with service unavailable scenarios
3. Test timeout behavior
4. Test all degradation mode combinations
5. Test health check caching
6. Test concurrent health checks
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy import text

from control_plane_api.app.routers.executions.services.worker_health import (
    WorkerHealthChecker,
    DegradationMode,
    CAPABILITIES,
)


# Fixtures

@pytest.fixture
def mock_temporal_client():
    """Create mock Temporal client."""
    client = Mock()
    client.workflow_service = Mock()
    return client


@pytest.fixture
def mock_redis_client():
    """Create mock Redis client."""
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = Mock()
    session.execute = Mock(return_value=True)
    return session


# Test Temporal Health Checks

@pytest.mark.asyncio
async def test_temporal_health_check_success(mock_temporal_client):
    """Test Temporal health check with available service."""
    checker = WorkerHealthChecker(temporal_client=mock_temporal_client)

    result = await checker.check_temporal_connectivity()

    assert result is True


@pytest.mark.asyncio
async def test_temporal_health_check_no_client():
    """Test Temporal health check with no client."""
    checker = WorkerHealthChecker(temporal_client=None)

    result = await checker.check_temporal_connectivity()

    assert result is False


@pytest.mark.asyncio
async def test_temporal_health_check_timeout(mock_temporal_client):
    """Test Temporal health check timeout behavior."""
    checker = WorkerHealthChecker(temporal_client=mock_temporal_client)

    # Mock slow response that exceeds timeout
    with patch.object(
        checker,
        '_check_temporal_service',
        side_effect=asyncio.sleep(10)  # Longer than TEMPORAL_TIMEOUT
    ):
        result = await checker.check_temporal_connectivity()

    assert result is False


@pytest.mark.asyncio
async def test_temporal_health_check_exception(mock_temporal_client):
    """Test Temporal health check with connection error."""
    checker = WorkerHealthChecker(temporal_client=mock_temporal_client)

    with patch.object(
        checker,
        '_check_temporal_service',
        side_effect=Exception("Connection failed")
    ):
        result = await checker.check_temporal_connectivity()

    assert result is False


# Test Redis Health Checks

@pytest.mark.asyncio
async def test_redis_health_check_success(mock_redis_client):
    """Test Redis health check with available service."""
    checker = WorkerHealthChecker(redis_client=mock_redis_client)

    result = await checker.check_redis_connectivity()

    assert result is True
    mock_redis_client.ping.assert_awaited_once()


@pytest.mark.asyncio
async def test_redis_health_check_no_client():
    """Test Redis health check with no client."""
    checker = WorkerHealthChecker(redis_client=None)

    result = await checker.check_redis_connectivity()

    assert result is False


@pytest.mark.asyncio
async def test_redis_health_check_timeout(mock_redis_client):
    """Test Redis health check timeout behavior."""
    # Mock slow ping that exceeds timeout
    mock_redis_client.ping = AsyncMock(side_effect=asyncio.sleep(10))

    checker = WorkerHealthChecker(redis_client=mock_redis_client)

    result = await checker.check_redis_connectivity()

    assert result is False


@pytest.mark.asyncio
async def test_redis_health_check_connection_error(mock_redis_client):
    """Test Redis health check with connection error."""
    mock_redis_client.ping = AsyncMock(side_effect=Exception("Connection refused"))

    checker = WorkerHealthChecker(redis_client=mock_redis_client)

    result = await checker.check_redis_connectivity()

    assert result is False


# Test Database Health Checks

@pytest.mark.asyncio
async def test_database_health_check_success(mock_db_session):
    """Test database health check with available service."""
    checker = WorkerHealthChecker(db_session=mock_db_session)

    result = await checker.check_database_connectivity()

    assert result is True
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_database_health_check_no_session():
    """Test database health check with no session."""
    checker = WorkerHealthChecker(db_session=None)

    result = await checker.check_database_connectivity()

    assert result is False


@pytest.mark.asyncio
async def test_database_health_check_timeout(mock_db_session):
    """Test database health check timeout behavior."""
    checker = WorkerHealthChecker(db_session=mock_db_session)

    with patch.object(
        checker,
        '_check_database_query',
        side_effect=asyncio.sleep(10)  # Longer than DATABASE_TIMEOUT
    ):
        result = await checker.check_database_connectivity()

    assert result is False


@pytest.mark.asyncio
async def test_database_health_check_query_error(mock_db_session):
    """Test database health check with query error."""
    mock_db_session.execute = Mock(side_effect=Exception("Query failed"))

    checker = WorkerHealthChecker(db_session=mock_db_session)

    result = await checker.check_database_connectivity()

    assert result is False


# Test Check All

@pytest.mark.asyncio
async def test_check_all_services_available(
    mock_temporal_client,
    mock_redis_client,
    mock_db_session
):
    """Test check_all with all services available."""
    checker = WorkerHealthChecker(
        temporal_client=mock_temporal_client,
        redis_client=mock_redis_client,
        db_session=mock_db_session
    )

    results = await checker.check_all()

    assert results["temporal"] is True
    assert results["redis"] is True
    assert results["database"] is True


@pytest.mark.asyncio
async def test_check_all_services_unavailable():
    """Test check_all with all services unavailable."""
    checker = WorkerHealthChecker(
        temporal_client=None,
        redis_client=None,
        db_session=None
    )

    results = await checker.check_all()

    assert results["temporal"] is False
    assert results["redis"] is False
    assert results["database"] is False


@pytest.mark.asyncio
async def test_check_all_mixed_availability(mock_redis_client):
    """Test check_all with mixed service availability."""
    checker = WorkerHealthChecker(
        temporal_client=None,
        redis_client=mock_redis_client,
        db_session=None
    )

    results = await checker.check_all()

    assert results["temporal"] is False
    assert results["redis"] is True
    assert results["database"] is False


# Test Degradation Modes

@pytest.mark.asyncio
async def test_degradation_mode_full(
    mock_temporal_client,
    mock_redis_client,
    mock_db_session
):
    """Test FULL degradation mode with all services available."""
    checker = WorkerHealthChecker(
        temporal_client=mock_temporal_client,
        redis_client=mock_redis_client,
        db_session=mock_db_session
    )

    mode = await checker.get_degradation_mode()

    assert mode == DegradationMode.FULL


@pytest.mark.asyncio
async def test_degradation_mode_history_only(mock_db_session):
    """Test HISTORY_ONLY degradation mode with only database available."""
    checker = WorkerHealthChecker(
        temporal_client=None,
        redis_client=None,
        db_session=mock_db_session
    )

    mode = await checker.get_degradation_mode()

    assert mode == DegradationMode.HISTORY_ONLY


@pytest.mark.asyncio
async def test_degradation_mode_live_only(mock_redis_client):
    """Test LIVE_ONLY degradation mode with only Redis available."""
    checker = WorkerHealthChecker(
        temporal_client=None,
        redis_client=mock_redis_client,
        db_session=None
    )

    mode = await checker.get_degradation_mode()

    assert mode == DegradationMode.LIVE_ONLY


@pytest.mark.asyncio
async def test_degradation_mode_degraded(mock_temporal_client, mock_redis_client):
    """Test DEGRADED mode with partial availability."""
    checker = WorkerHealthChecker(
        temporal_client=mock_temporal_client,
        redis_client=mock_redis_client,
        db_session=None
    )

    mode = await checker.get_degradation_mode()

    assert mode == DegradationMode.DEGRADED


@pytest.mark.asyncio
async def test_degradation_mode_unavailable():
    """Test UNAVAILABLE mode with no services available."""
    checker = WorkerHealthChecker(
        temporal_client=None,
        redis_client=None,
        db_session=None
    )

    mode = await checker.get_degradation_mode()

    assert mode == DegradationMode.UNAVAILABLE


# Test Capabilities

def test_get_capabilities_full():
    """Test capabilities for FULL mode."""
    checker = WorkerHealthChecker()

    capabilities = checker.get_capabilities(DegradationMode.FULL)

    assert "history" in capabilities
    assert "live_events" in capabilities
    assert "status_updates" in capabilities
    assert "completion_detection" in capabilities
    assert "workflow_queries" in capabilities


def test_get_capabilities_history_only():
    """Test capabilities for HISTORY_ONLY mode."""
    checker = WorkerHealthChecker()

    capabilities = checker.get_capabilities(DegradationMode.HISTORY_ONLY)

    assert capabilities == ["history"]


def test_get_capabilities_live_only():
    """Test capabilities for LIVE_ONLY mode."""
    checker = WorkerHealthChecker()

    capabilities = checker.get_capabilities(DegradationMode.LIVE_ONLY)

    assert capabilities == ["live_events"]


def test_get_capabilities_unavailable():
    """Test capabilities for UNAVAILABLE mode."""
    checker = WorkerHealthChecker()

    capabilities = checker.get_capabilities(DegradationMode.UNAVAILABLE)

    assert capabilities == []


# Test Caching

@pytest.mark.asyncio
async def test_health_check_caching(mock_redis_client):
    """Test that health check results are cached."""
    checker = WorkerHealthChecker(
        redis_client=mock_redis_client,
        cache_ttl=10  # 10 second cache
    )

    # First check should call Redis
    result1 = await checker.check_redis_connectivity()
    assert result1 is True
    assert mock_redis_client.ping.call_count == 1

    # Second check should use cache (no additional Redis call)
    result2 = await checker.check_redis_connectivity()
    assert result2 is True
    assert mock_redis_client.ping.call_count == 1  # Still 1, not 2

    # Verify cache was used
    assert checker._is_cached("redis") is True


@pytest.mark.asyncio
async def test_health_check_cache_expiry(mock_redis_client):
    """Test that health check cache expires."""
    checker = WorkerHealthChecker(
        redis_client=mock_redis_client,
        cache_ttl=0.1  # 100ms cache
    )

    # First check
    result1 = await checker.check_redis_connectivity()
    assert result1 is True
    assert mock_redis_client.ping.call_count == 1

    # Wait for cache to expire
    await asyncio.sleep(0.2)

    # Second check should call Redis again
    result2 = await checker.check_redis_connectivity()
    assert result2 is True
    assert mock_redis_client.ping.call_count == 2  # Called again


@pytest.mark.asyncio
async def test_clear_cache(mock_redis_client):
    """Test clearing health check cache."""
    checker = WorkerHealthChecker(
        redis_client=mock_redis_client,
        cache_ttl=10
    )

    # First check
    result1 = await checker.check_redis_connectivity()
    assert result1 is True
    assert checker._is_cached("redis") is True

    # Clear cache
    checker.clear_cache()
    assert checker._is_cached("redis") is None

    # Next check should call Redis again
    result2 = await checker.check_redis_connectivity()
    assert result2 is True
    assert mock_redis_client.ping.call_count == 2


# Integration Test Examples (commented out - requires real services)

"""
@pytest.mark.asyncio
async def test_integration_with_real_services():
    # This test would require real Temporal, Redis, and Database instances
    # Uncomment and configure for integration testing

    from control_plane_api.app.lib.temporal_client import get_temporal_client
    from control_plane_api.app.lib.redis_client import get_redis_client
    from control_plane_api.app.database import get_session_local

    temporal_client = await get_temporal_client()
    redis_client = get_redis_client()
    SessionLocal = get_session_local()
    db_session = SessionLocal()

    try:
        checker = WorkerHealthChecker(
            temporal_client=temporal_client,
            redis_client=redis_client,
            db_session=db_session
        )

        # Test all health checks
        results = await checker.check_all()
        print(f"Health check results: {results}")

        # Test degradation mode
        mode = await checker.get_degradation_mode()
        print(f"Degradation mode: {mode}")

        # Test capabilities
        capabilities = checker.get_capabilities(mode)
        print(f"Available capabilities: {capabilities}")

    finally:
        db_session.close()
"""
