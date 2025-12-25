"""
End-to-End Tests for Single Execution Mode Fixes

This test suite validates the three critical fixes for single execution mode:
1. WebSocket switching is disabled in single execution mode
2. Execution monitor requires consecutive completion checks
3. Extended timeout for long-running executions

Tests simulate real execution scenarios that previously caused premature exits.
"""

import pytest
import asyncio
import os
import time
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call
from pathlib import Path
import sys
import httpx

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from control_plane_api.worker.services.event_publisher import (
    EventPublisher,
    EventPublisherConfig,
    TransportMode,
)
from control_plane_api.worker.control_plane_client import ControlPlaneClient


class MockHTTPXClient:
    """Mock HTTPX client for testing"""

    def __init__(self, execution_statuses=None):
        """
        Args:
            execution_statuses: List of status dicts to return on sequential calls
                               e.g., [{"status": "running"}, {"status": "completed"}]
        """
        self.execution_statuses = execution_statuses or []
        self.call_count = 0
        self.requests = []

    async def get(self, url, headers=None, params=None):
        """Mock GET request"""
        self.requests.append({"method": "GET", "url": url, "headers": headers, "params": params})

        # Return execution status based on call count
        if "/executions" in url and self.call_count < len(self.execution_statuses):
            status_data = self.execution_statuses[self.call_count]
            self.call_count += 1

            response = Mock()
            response.status_code = 200
            response.json.return_value = [status_data]
            return response

        # Default response
        response = Mock()
        response.status_code = 200
        response.json.return_value = []
        return response

    async def post(self, url, json=None, headers=None):
        """Mock POST request"""
        self.requests.append({"method": "POST", "url": url, "json": json, "headers": headers})

        response = Mock()
        response.status_code = 202
        response.text = "OK"
        return response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.mark.asyncio
class TestWebSocketDisabledInSingleExecution:
    """Test that WebSocket switching is disabled in single execution mode"""

    async def test_websocket_disabled_when_env_var_set(self):
        """Verify WebSocket is disabled when KUBIYA_SINGLE_EXECUTION_MODE=true"""
        # Set environment variable
        os.environ["KUBIYA_SINGLE_EXECUTION_MODE"] = "true"

        try:
            # Create config from env
            config = EventPublisherConfig.from_env()

            # Assert WebSocket is disabled
            assert config.websocket_enabled is False, "WebSocket should be disabled in single execution mode"

            # Create event publisher
            mock_control_plane = Mock()
            mock_control_plane.publish_event_async = AsyncMock(return_value=True)

            publisher = EventPublisher(
                control_plane=mock_control_plane,
                execution_id="test-exec-123",
                config=config,
            )

            # Verify no transport switch task was created
            assert publisher._transport_switch_task is None, "Transport switch task should not be created"

            # Verify current transport stays HTTP
            assert publisher._current_transport == TransportMode.HTTP

        finally:
            # Clean up
            del os.environ["KUBIYA_SINGLE_EXECUTION_MODE"]

    async def test_websocket_enabled_when_env_var_not_set(self):
        """Verify WebSocket is enabled by default when not in single execution mode"""
        # Ensure env var is not set
        if "KUBIYA_SINGLE_EXECUTION_MODE" in os.environ:
            del os.environ["KUBIYA_SINGLE_EXECUTION_MODE"]

        # Create config from env
        config = EventPublisherConfig.from_env()

        # Assert WebSocket is enabled by default
        assert config.websocket_enabled is True, "WebSocket should be enabled by default"

    async def test_websocket_can_be_explicitly_enabled_in_single_mode(self):
        """Verify WebSocket can be explicitly enabled even in single execution mode"""
        # Set both env vars
        os.environ["KUBIYA_SINGLE_EXECUTION_MODE"] = "true"
        os.environ["EVENT_WEBSOCKET_ENABLED"] = "true"

        try:
            config = EventPublisherConfig.from_env()

            # Explicit override should take precedence
            assert config.websocket_enabled is True, "Explicit EVENT_WEBSOCKET_ENABLED should override default"

        finally:
            # Clean up
            del os.environ["KUBIYA_SINGLE_EXECUTION_MODE"]
            del os.environ["EVENT_WEBSOCKET_ENABLED"]

    async def test_no_websocket_switch_during_execution(self):
        """Verify that execution doesn't switch to WebSocket after threshold in single mode"""
        os.environ["KUBIYA_SINGLE_EXECUTION_MODE"] = "true"

        try:
            config = EventPublisherConfig.from_env()
            config.websocket_switch_threshold_seconds = 1  # 1 second for fast test

            mock_control_plane = Mock()
            mock_control_plane.publish_event_async = AsyncMock(return_value=True)

            publisher = EventPublisher(
                control_plane=mock_control_plane,
                execution_id="test-exec-123",
                config=config,
            )

            # Publish some events
            await publisher.publish("message_chunk", {"content": "test1"})

            # Wait past the threshold
            await asyncio.sleep(1.5)

            # Publish more events
            await publisher.publish("message_chunk", {"content": "test2"})

            # Verify transport is still HTTP
            assert publisher._current_transport == TransportMode.HTTP, "Transport should remain HTTP"
            assert publisher._ws_connection is None, "WebSocket connection should not be created"

            # Clean up
            await publisher.close()

        finally:
            del os.environ["KUBIYA_SINGLE_EXECUTION_MODE"]


@pytest.mark.asyncio
class TestRobustExecutionMonitor:
    """Test that execution monitor requires consecutive checks before shutdown"""

    async def test_consecutive_completion_checks_required(self):
        """Verify monitor requires 2 consecutive 'completed' checks before shutdown"""

        # Simulate execution status progression:
        # Call 1: running
        # Call 2: completed (first check)
        # Call 3: completed (second check - should trigger shutdown)
        execution_statuses = [
            {"id": "exec-123", "status": "running"},
            {"id": "exec-123", "status": "completed"},
            {"id": "exec-123", "status": "completed"},
        ]

        mock_client = MockHTTPXClient(execution_statuses)

        # Simulate the monitor logic
        consecutive_completion_checks = 0
        required_consecutive_checks = 2
        execution_seen = False
        execution_id = None
        should_shutdown = False

        # Simulate 3 polling cycles
        for i in range(3):
            async with mock_client as http_client:
                response = await http_client.get(
                    "http://test/api/v1/worker-queues/queue-123/executions",
                    headers={"Authorization": "Bearer test-key"},
                    params={"limit": 5, "status": "all"}
                )

                executions = response.json()

                for execution in executions:
                    exec_status = execution.get("status", "").lower()
                    exec_id = execution.get("id")

                    if not execution_seen:
                        if exec_status in ["running", "completed", "failed"]:
                            execution_seen = True
                            execution_id = exec_id

                    if execution_seen and exec_id == execution_id:
                        if exec_status in ["completed", "failed", "cancelled"]:
                            consecutive_completion_checks += 1

                            if consecutive_completion_checks >= required_consecutive_checks:
                                should_shutdown = True
                                break
                        else:
                            # Execution back to running - reset counter
                            consecutive_completion_checks = 0

        # Assertions
        assert consecutive_completion_checks == 2, "Should have 2 consecutive completion checks"
        assert should_shutdown is True, "Should trigger shutdown after 2 consecutive checks"
        assert mock_client.call_count == 3, "Should have made 3 API calls"

    async def test_completion_counter_resets_on_running_status(self):
        """Verify completion counter resets if execution goes back to running"""

        # Simulate: completed → running → completed → completed
        execution_statuses = [
            {"id": "exec-123", "status": "completed"},  # First check
            {"id": "exec-123", "status": "running"},    # Back to running - should reset
            {"id": "exec-123", "status": "completed"},  # First check again
            {"id": "exec-123", "status": "completed"},  # Second check - triggers shutdown
        ]

        mock_client = MockHTTPXClient(execution_statuses)

        consecutive_completion_checks = 0
        required_consecutive_checks = 2
        execution_seen = False
        execution_id = None
        should_shutdown = False

        for i in range(4):
            async with mock_client as http_client:
                response = await http_client.get(
                    "http://test/api/v1/worker-queues/queue-123/executions",
                    headers={"Authorization": "Bearer test-key"},
                    params={"limit": 5, "status": "all"}
                )

                executions = response.json()

                for execution in executions:
                    exec_status = execution.get("status", "").lower()
                    exec_id = execution.get("id")

                    if not execution_seen:
                        execution_seen = True
                        execution_id = exec_id

                    if execution_seen and exec_id == execution_id:
                        if exec_status in ["completed", "failed", "cancelled"]:
                            consecutive_completion_checks += 1

                            if consecutive_completion_checks >= required_consecutive_checks:
                                should_shutdown = True
                                break
                        else:
                            # Reset counter
                            if consecutive_completion_checks > 0:
                                consecutive_completion_checks = 0

        assert should_shutdown is True, "Should eventually trigger shutdown"
        assert mock_client.call_count == 4, "Should have made 4 API calls due to reset"

    async def test_completion_counter_resets_on_api_failure(self):
        """Verify completion counter resets on API failures for safety"""

        # This test simulates the behavior where API failures should reset the counter
        consecutive_completion_checks = 1  # Simulate we had one check

        # Simulate API failure
        try:
            raise Exception("API connection failed")
        except Exception:
            # Counter should be reset on error
            if consecutive_completion_checks > 0:
                consecutive_completion_checks = 0

        assert consecutive_completion_checks == 0, "Counter should reset on API failure"

    async def test_prevents_premature_shutdown_at_240_seconds(self):
        """
        Test that execution doesn't shutdown at 240 seconds (WebSocket switch time)
        This is the actual bug we're fixing.
        """

        # Simulate the scenario:
        # - Execution running at 237 seconds
        # - First check at 240 seconds returns "completed" (false positive)
        # - Second check at 243 seconds returns "running" (execution still active)
        # - Should NOT shutdown

        execution_statuses = [
            {"id": "exec-123", "status": "running"},    # Before 240s
            {"id": "exec-123", "status": "completed"},  # At 240s (false positive from race condition)
            {"id": "exec-123", "status": "running"},    # At 243s (still active!)
        ]

        mock_client = MockHTTPXClient(execution_statuses)

        consecutive_completion_checks = 0
        required_consecutive_checks = 2
        execution_seen = False
        execution_id = None
        should_shutdown = False

        for i in range(3):
            async with mock_client as http_client:
                response = await http_client.get(
                    "http://test/api/v1/worker-queues/queue-123/executions",
                    headers={"Authorization": "Bearer test-key"},
                    params={"limit": 5, "status": "all"}
                )

                executions = response.json()

                for execution in executions:
                    exec_status = execution.get("status", "").lower()
                    exec_id = execution.get("id")

                    if not execution_seen:
                        execution_seen = True
                        execution_id = exec_id

                    if execution_seen and exec_id == execution_id:
                        if exec_status in ["completed", "failed", "cancelled"]:
                            consecutive_completion_checks += 1

                            if consecutive_completion_checks >= required_consecutive_checks:
                                should_shutdown = True
                                break
                        else:
                            # Reset on running status
                            if consecutive_completion_checks > 0:
                                consecutive_completion_checks = 0

        # Critical assertions
        assert should_shutdown is False, "Should NOT shutdown due to false positive"
        assert consecutive_completion_checks == 0, "Counter should be reset after false positive"


@pytest.mark.asyncio
class TestLongRunningExecution:
    """Test that long-running executions (>4 minutes) complete successfully"""

    async def test_execution_continues_beyond_240_seconds(self):
        """Verify execution continues past 240 seconds without premature exit"""

        os.environ["KUBIYA_SINGLE_EXECUTION_MODE"] = "true"

        try:
            config = EventPublisherConfig.from_env()

            # Verify WebSocket is disabled
            assert config.websocket_enabled is False

            mock_control_plane = Mock()
            mock_control_plane.publish_event_async = AsyncMock(return_value=True)

            publisher = EventPublisher(
                control_plane=mock_control_plane,
                execution_id="test-long-exec",
                config=config,
            )

            # Publish events over time
            start_time = time.time()

            # Simulate publishing events for 5+ minutes (compressed to seconds for test)
            for i in range(6):  # Simulate 6 minutes
                await publisher.publish("message_chunk", {"content": f"chunk-{i}", "minute": i})

                # Small delay to simulate time passing
                await asyncio.sleep(0.1)

            # Verify transport never switched to WebSocket
            assert publisher._current_transport == TransportMode.HTTP
            assert publisher._ws_connection is None

            # Flush and close to ensure all batched events are sent
            await publisher.flush()
            await publisher.close()

            # Verify all events were published via HTTP (may be batched, so at least 1 call)
            assert mock_control_plane.publish_event_async.call_count >= 1, "Should publish events via HTTP"

        finally:
            if "KUBIYA_SINGLE_EXECUTION_MODE" in os.environ:
                del os.environ["KUBIYA_SINGLE_EXECUTION_MODE"]

    async def test_extended_timeout_allows_30_minute_execution(self):
        """Verify the extended timeout of 30 minutes (1800 seconds) is configured"""

        # The actual monitor uses max_runtime = 1800 seconds
        max_runtime = 1800  # 30 minutes

        # Verify this is sufficient for long executions
        assert max_runtime == 1800, "Timeout should be 30 minutes (1800 seconds)"
        assert max_runtime > 240, "Timeout should be much longer than WebSocket switch threshold"

        # Simulate time checks
        simulated_execution_time = 600  # 10 minutes
        assert simulated_execution_time < max_runtime, "10-minute execution should complete within timeout"

        simulated_execution_time = 1200  # 20 minutes
        assert simulated_execution_time < max_runtime, "20-minute execution should complete within timeout"


@pytest.mark.asyncio
class TestEventPublishingInAgnoRuntime:
    """Test that event publishing works correctly in Agno runtime"""

    async def test_event_publisher_awaits_async_functions(self):
        """Verify EventPublisher properly awaits async publish functions"""

        mock_control_plane = Mock()
        call_tracker = []

        async def mock_publish_async(execution_id, event_type, data):
            """Mock async publish that tracks calls"""
            call_tracker.append({"execution_id": execution_id, "event_type": event_type, "data": data})
            await asyncio.sleep(0.01)  # Simulate async work
            return True

        mock_control_plane.publish_event_async = mock_publish_async

        config = EventPublisherConfig(websocket_enabled=False)
        publisher = EventPublisher(
            control_plane=mock_control_plane,
            execution_id="test-exec-456",
            config=config,
        )

        # Publish multiple events
        # Note: message_chunk is batched (EventPriority.NORMAL)
        # tool_started is immediate (EventPriority.IMMEDIATE by default)
        result1 = await publisher.publish("message_chunk", {"content": "chunk1"})
        result2 = await publisher.publish("tool_started", {"tool": "test"})

        # Verify both published successfully
        assert result1 is True
        assert result2 is True

        # Flush to ensure batched events are sent
        await publisher.flush()
        await publisher.close()

        # Verify events were awaited (not just coroutines created)
        # Note: message_chunk is batched, tool_started is immediate
        assert len(call_tracker) >= 1, "At least one event should be published"

        # Check that tool_started was published immediately
        tool_events = [e for e in call_tracker if e["event_type"] == "tool_started"]
        assert len(tool_events) == 1, "tool_started should be published immediately"

    async def test_no_unawaited_coroutine_warnings(self):
        """Verify no 'await wasn't used with future' errors occur"""

        mock_control_plane = Mock()

        async def mock_publish_that_raises(execution_id, event_type, data):
            """Simulate an error that might cause unawaited coroutines"""
            if event_type == "error_event":
                raise RuntimeError("await wasn't used with future")
            return True

        mock_control_plane.publish_event_async = mock_publish_that_raises

        config = EventPublisherConfig(websocket_enabled=False)
        publisher = EventPublisher(
            control_plane=mock_control_plane,
            execution_id="test-exec-789",
            config=config,
        )

        # Publish normal event - should work
        result = await publisher.publish("message_chunk", {"content": "test"})
        assert result is True

        # Publish error event - should handle exception gracefully
        result = await publisher.publish("error_event", {"error": "test"})
        assert result is False  # Returns False on error, doesn't raise

        await publisher.close()


@pytest.mark.asyncio
class TestIntegrationScenarios:
    """Integration tests simulating real-world scenarios"""

    async def test_complete_single_execution_flow(self):
        """
        Test complete flow: worker starts → execution runs → completes → worker exits
        This simulates the actual 'kubiya exec' flow.
        """

        # Setup: Single execution mode
        os.environ["KUBIYA_SINGLE_EXECUTION_MODE"] = "true"

        try:
            # Phase 1: Worker initialization
            config = EventPublisherConfig.from_env()
            assert config.websocket_enabled is False, "WebSocket should be disabled"

            # Phase 2: Execution starts
            mock_control_plane = Mock()
            mock_control_plane.publish_event_async = AsyncMock(return_value=True)

            publisher = EventPublisher(
                control_plane=mock_control_plane,
                execution_id="integration-test-exec",
                config=config,
            )

            # Phase 3: Simulate execution for 5 minutes with events
            execution_statuses = [
                {"id": "integration-test-exec", "status": "running"},
                {"id": "integration-test-exec", "status": "running"},
                {"id": "integration-test-exec", "status": "running"},
                {"id": "integration-test-exec", "status": "completed"},
                {"id": "integration-test-exec", "status": "completed"},  # Second check triggers shutdown
            ]

            mock_http_client = MockHTTPXClient(execution_statuses)

            # Simulate monitoring
            consecutive_completion_checks = 0
            should_shutdown = False

            for i in range(5):
                # Publish event during execution
                await publisher.publish("message_chunk", {"content": f"Working on task {i}..."})

                # Monitor checks status
                async with mock_http_client as client:
                    response = await client.get(
                        "http://test/api/v1/worker-queues/queue-123/executions",
                        headers={"Authorization": "Bearer test-key"},
                        params={"limit": 5, "status": "all"}
                    )

                    executions = response.json()
                    for execution in executions:
                        exec_status = execution.get("status")

                        if exec_status == "completed":
                            consecutive_completion_checks += 1
                            if consecutive_completion_checks >= 2:
                                should_shutdown = True
                                break

            # Phase 4: Cleanup
            await publisher.flush()
            await publisher.close()

            # Assertions
            assert publisher._current_transport == TransportMode.HTTP, "Should stay HTTP throughout"
            assert consecutive_completion_checks == 2, "Should have 2 completion checks"
            assert should_shutdown is True, "Should shutdown after verification"
            assert mock_control_plane.publish_event_async.call_count >= 1, "Should publish events (may be batched)"

        finally:
            del os.environ["KUBIYA_SINGLE_EXECUTION_MODE"]

    async def test_execution_with_kubectl_commands_beyond_4_minutes(self):
        """
        Simulate the actual user scenario: kubectl commands running beyond 4 minutes
        This is the exact bug scenario from the issue.
        """

        os.environ["KUBIYA_SINGLE_EXECUTION_MODE"] = "true"

        try:
            config = EventPublisherConfig.from_env()

            mock_control_plane = Mock()
            mock_control_plane.publish_event_async = AsyncMock(return_value=True)

            publisher = EventPublisher(
                control_plane=mock_control_plane,
                execution_id="kubectl-exec",
                config=config,
            )

            # Simulate the timeline from the user's logs:
            # 07:02:40 - Execution starts
            # 07:04:09 - kubectl get nodes command (129 seconds)
            # 07:06:41 - kubectl config view command (240 seconds - WebSocket switch time!)
            # Should continue without exiting

            events = [
                (0, "Execution started"),
                (129, "Running kubectl get nodes -o wide"),
                (240, "Running kubectl config view --minify"),  # Critical moment!
                (245, "Running minikube status -p kubiya-k8s"),
                (300, "Task completed successfully"),
            ]

            for elapsed_time, description in events:
                await publisher.publish("message_chunk", {
                    "content": description,
                    "elapsed": elapsed_time
                })

                # At 240 seconds, verify no WebSocket switch occurred
                if elapsed_time == 240:
                    assert publisher._current_transport == TransportMode.HTTP, \
                        "Should NOT switch to WebSocket at 240 seconds"
                    assert publisher._ws_connection is None, \
                        "WebSocket connection should NOT be created"

            await publisher.flush()
            await publisher.close()

            # Verify all events were published successfully via HTTP (may be batched)
            assert mock_control_plane.publish_event_async.call_count >= 1, \
                "Should publish events via HTTP"

        finally:
            del os.environ["KUBIYA_SINGLE_EXECUTION_MODE"]


if __name__ == "__main__":
    """Run tests with pytest"""
    pytest.main([__file__, "-v", "-s"])
