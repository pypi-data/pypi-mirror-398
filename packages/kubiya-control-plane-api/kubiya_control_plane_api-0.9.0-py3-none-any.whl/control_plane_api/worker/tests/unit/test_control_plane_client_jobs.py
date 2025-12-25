"""
Unit tests for ControlPlaneClient job execution methods.

Tests the HTTP client methods that workers use to create and update job executions.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx
from control_plane_api.worker.control_plane_client import ControlPlaneClient


@pytest.fixture
def mock_async_client():
    """Mock async HTTP client."""
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "execution_id": "exec_test_123",
        "status": "created",
        "created_at": "2024-01-01T00:00:00Z"
    }
    mock_client.post = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def control_plane_client(mock_async_client):
    """Create ControlPlaneClient with mocked HTTP client."""
    client = ControlPlaneClient(
        base_url="http://test-control-plane",
        api_key="test-api-key",
        websocket_enabled=False
    )
    # Replace the async client with our mock
    client._async_client = mock_async_client
    return client


@pytest.mark.asyncio
class TestCreateJobExecutionRecord:
    """Test create_job_execution_record method."""

    async def test_create_job_execution_record_success(
        self, control_plane_client, mock_async_client
    ):
        """Test successfully creating a job execution record."""
        result = await control_plane_client.create_job_execution_record(
            execution_id="exec_test_123",
            job_id="job_test_456",
            organization_id="org_test_789",
            entity_type="agent",
            entity_id="agent_test_111",
            prompt="Test prompt",
            trigger_type="cron",
            trigger_metadata={"job_name": "Test Job"}
        )

        # Verify the HTTP call was made
        mock_async_client.post.assert_called_once()
        call_args = mock_async_client.post.call_args

        # Verify URL
        assert call_args[0][0] == "http://test-control-plane/api/v1/executions/create"

        # Verify payload
        payload = call_args.kwargs["json"]
        assert payload["execution_id"] == "exec_test_123"
        assert payload["job_id"] == "job_test_456"
        assert payload["organization_id"] == "org_test_789"
        assert payload["entity_type"] == "agent"
        assert payload["entity_id"] == "agent_test_111"
        assert payload["prompt"] == "Test prompt"
        assert payload["trigger_type"] == "cron"
        assert payload["trigger_metadata"]["job_name"] == "Test Job"

        # Verify headers
        assert call_args.kwargs["headers"]["Authorization"] == "UserKey test-api-key"

        # Verify result
        assert result["execution_id"] == "exec_test_123"
        assert result["status"] == "created"

    async def test_create_job_execution_record_without_job_id(
        self, control_plane_client, mock_async_client
    ):
        """Test creating execution record without job_id."""
        result = await control_plane_client.create_job_execution_record(
            execution_id="exec_test_456",
            job_id=None,
            organization_id="org_test_789",
            entity_type="team",
            entity_id="team_test_222",
            prompt="Manual execution",
            trigger_type="manual",
            trigger_metadata={"user_id": "user_123"}
        )

        # Verify the call
        mock_async_client.post.assert_called_once()
        payload = mock_async_client.post.call_args.kwargs["json"]
        assert payload["job_id"] is None
        assert payload["entity_type"] == "team"
        assert payload["trigger_type"] == "manual"

    async def test_create_job_execution_record_http_error(
        self, control_plane_client, mock_async_client
    ):
        """Test handling HTTP error response."""
        # Mock error response
        error_response = Mock()
        error_response.status_code = 500
        error_response.text = "Internal server error"
        mock_async_client.post = AsyncMock(return_value=error_response)

        with pytest.raises(Exception) as exc_info:
            await control_plane_client.create_job_execution_record(
                execution_id="exec_error",
                job_id="job_error",
                organization_id="org_test",
                entity_type="agent",
                entity_id="agent_error",
                prompt="Test",
                trigger_type="cron",
                trigger_metadata={}
            )

        assert "Failed to create execution record" in str(exc_info.value)
        assert "HTTP 500" in str(exc_info.value)

    async def test_create_job_execution_record_network_error(
        self, control_plane_client, mock_async_client
    ):
        """Test handling network error."""
        # Mock network error
        mock_async_client.post = AsyncMock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        with pytest.raises(Exception):
            await control_plane_client.create_job_execution_record(
                execution_id="exec_network_error",
                job_id="job_test",
                organization_id="org_test",
                entity_type="agent",
                entity_id="agent_test",
                prompt="Test",
                trigger_type="cron",
                trigger_metadata={}
            )


@pytest.mark.asyncio
class TestUpdateJobExecutionStatus:
    """Test update_job_execution_status method."""

    async def test_update_job_execution_status_completed(
        self, control_plane_client, mock_async_client
    ):
        """Test updating job execution status to completed."""
        # Mock successful response
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "job_id": "job_test_456",
            "execution_id": "exec_test_123",
            "status": "updated"
        }
        mock_async_client.post = AsyncMock(return_value=success_response)

        result = await control_plane_client.update_job_execution_status(
            execution_id="exec_test_123",
            job_id="job_test_456",
            status="completed",
            duration_ms=5000,
            error_message=None
        )

        # Verify the HTTP call
        mock_async_client.post.assert_called_once()
        call_args = mock_async_client.post.call_args

        # Verify URL
        expected_url = "http://test-control-plane/api/v1/executions/exec_test_123/job/job_test_456/status"
        assert call_args[0][0] == expected_url

        # Verify payload
        payload = call_args.kwargs["json"]
        assert payload["status"] == "completed"
        assert payload["duration_ms"] == 5000
        assert payload["error_message"] is None

        # Verify result
        assert result["job_id"] == "job_test_456"
        assert result["execution_id"] == "exec_test_123"
        assert result["status"] == "updated"

    async def test_update_job_execution_status_failed(
        self, control_plane_client, mock_async_client
    ):
        """Test updating job execution status to failed."""
        # Mock successful response
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "job_id": "job_test_789",
            "execution_id": "exec_test_456",
            "status": "updated"
        }
        mock_async_client.post = AsyncMock(return_value=success_response)

        result = await control_plane_client.update_job_execution_status(
            execution_id="exec_test_456",
            job_id="job_test_789",
            status="failed",
            duration_ms=1500,
            error_message="Test error occurred"
        )

        # Verify payload includes error message
        payload = mock_async_client.post.call_args.kwargs["json"]
        assert payload["status"] == "failed"
        assert payload["duration_ms"] == 1500
        assert payload["error_message"] == "Test error occurred"

    async def test_update_job_execution_status_without_duration(
        self, control_plane_client, mock_async_client
    ):
        """Test updating status without duration_ms."""
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "job_id": "job_test",
            "execution_id": "exec_test",
            "status": "updated"
        }
        mock_async_client.post = AsyncMock(return_value=success_response)

        result = await control_plane_client.update_job_execution_status(
            execution_id="exec_test",
            job_id="job_test",
            status="completed"
        )

        # Verify payload
        payload = mock_async_client.post.call_args.kwargs["json"]
        assert payload["status"] == "completed"
        assert payload["duration_ms"] is None
        assert payload["error_message"] is None

    async def test_update_job_execution_status_http_error(
        self, control_plane_client, mock_async_client
    ):
        """Test handling HTTP error response."""
        error_response = Mock()
        error_response.status_code = 404
        error_response.text = "Job execution not found"
        mock_async_client.post = AsyncMock(return_value=error_response)

        with pytest.raises(Exception) as exc_info:
            await control_plane_client.update_job_execution_status(
                execution_id="exec_notfound",
                job_id="job_notfound",
                status="completed"
            )

        assert "Failed to update job execution status" in str(exc_info.value)
        assert "HTTP 404" in str(exc_info.value)

    async def test_update_job_execution_status_timeout(
        self, control_plane_client, mock_async_client
    ):
        """Test handling timeout error."""
        mock_async_client.post = AsyncMock(
            side_effect=httpx.TimeoutException("Request timeout")
        )

        with pytest.raises(Exception):
            await control_plane_client.update_job_execution_status(
                execution_id="exec_timeout",
                job_id="job_timeout",
                status="completed",
                duration_ms=10000
            )


@pytest.mark.asyncio
class TestControlPlaneClientIntegration:
    """Integration tests for ControlPlaneClient job methods."""

    async def test_full_job_execution_lifecycle(
        self, control_plane_client, mock_async_client
    ):
        """Test complete lifecycle: create -> update status."""
        # Mock create response
        create_response = Mock()
        create_response.status_code = 201
        create_response.json.return_value = {
            "execution_id": "exec_lifecycle_123",
            "status": "created",
            "created_at": "2024-01-01T00:00:00Z"
        }

        # Mock update response
        update_response = Mock()
        update_response.status_code = 200
        update_response.json.return_value = {
            "job_id": "job_lifecycle_456",
            "execution_id": "exec_lifecycle_123",
            "status": "updated"
        }

        # Configure mock to return different responses
        mock_async_client.post = AsyncMock(
            side_effect=[create_response, update_response]
        )

        # 1. Create execution record
        create_result = await control_plane_client.create_job_execution_record(
            execution_id="exec_lifecycle_123",
            job_id="job_lifecycle_456",
            organization_id="org_test",
            entity_type="agent",
            entity_id="agent_test",
            prompt="Lifecycle test",
            trigger_type="cron",
            trigger_metadata={"job_name": "Lifecycle Job"}
        )

        assert create_result["execution_id"] == "exec_lifecycle_123"
        assert create_result["status"] == "created"

        # 2. Update execution status
        update_result = await control_plane_client.update_job_execution_status(
            execution_id="exec_lifecycle_123",
            job_id="job_lifecycle_456",
            status="completed",
            duration_ms=3000
        )

        assert update_result["execution_id"] == "exec_lifecycle_123"
        assert update_result["status"] == "updated"

        # Verify both calls were made
        assert mock_async_client.post.call_count == 2
