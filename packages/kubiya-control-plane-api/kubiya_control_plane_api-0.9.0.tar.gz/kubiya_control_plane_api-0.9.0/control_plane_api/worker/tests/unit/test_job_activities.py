"""
Unit tests for refactored job activities.

Tests that job activities properly use ControlPlaneClient instead of direct Supabase access.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from control_plane_api.worker.activities.job_activities import (
    create_job_execution_record,
    update_job_execution_status,
    ActivityCreateJobExecutionInput,
)


@pytest.fixture
def mock_control_plane_client():
    """Mock ControlPlaneClient for testing."""
    mock_client = Mock()
    mock_client.create_job_execution_record = AsyncMock()
    mock_client.update_job_execution_status = AsyncMock()
    return mock_client


@pytest.mark.asyncio
class TestCreateJobExecutionRecordActivity:
    """Test create_job_execution_record activity."""

    async def test_create_job_execution_record_with_job(
        self, mock_control_plane_client
    ):
        """Test creating job execution record with job_id."""
        # Mock successful response
        mock_control_plane_client.create_job_execution_record.return_value = {
            "execution_id": "exec_test_123",
            "status": "created",
            "created_at": "2024-01-01T00:00:00Z"
        }

        # Create input
        input_data = ActivityCreateJobExecutionInput(
            execution_id="exec_test_123",
            job_id="job_test_456",
            organization_id="org_test_789",
            entity_type="agent",
            entity_id="agent_test_111",
            prompt="Test scheduled prompt",
            trigger_type="cron",
            trigger_metadata={
                "job_name": "Test Job",
                "user_id": "user_test_456",
            }
        )

        # Patch get_control_plane_client
        with patch(
            "control_plane_api.worker.control_plane_client.get_control_plane_client",
            return_value=mock_control_plane_client
        ):
            result = await create_job_execution_record(input_data)

        # Verify client method was called
        mock_control_plane_client.create_job_execution_record.assert_called_once_with(
            execution_id="exec_test_123",
            job_id="job_test_456",
            organization_id="org_test_789",
            entity_type="agent",
            entity_id="agent_test_111",
            prompt="Test scheduled prompt",
            trigger_type="cron",
            trigger_metadata={
                "job_name": "Test Job",
                "user_id": "user_test_456",
            }
        )

        # Verify result
        assert result["execution_id"] == "exec_test_123"
        assert result["status"] == "created"

    async def test_create_job_execution_record_without_job(
        self, mock_control_plane_client
    ):
        """Test creating execution record without job_id."""
        mock_control_plane_client.create_job_execution_record.return_value = {
            "execution_id": "exec_test_456",
            "status": "created",
            "created_at": "2024-01-01T00:00:00Z"
        }

        input_data = ActivityCreateJobExecutionInput(
            execution_id="exec_test_456",
            job_id=None,
            organization_id="org_test_789",
            entity_type="team",
            entity_id="team_test_222",
            prompt="Manual execution",
            trigger_type="manual",
            trigger_metadata={"user_id": "user_test_456"}
        )

        with patch(
            "control_plane_api.worker.control_plane_client.get_control_plane_client",
            return_value=mock_control_plane_client
        ):
            result = await create_job_execution_record(input_data)

        # Verify call
        call_args = mock_control_plane_client.create_job_execution_record.call_args
        assert call_args.kwargs["job_id"] is None
        assert call_args.kwargs["entity_type"] == "team"
        assert call_args.kwargs["trigger_type"] == "manual"

        assert result["execution_id"] == "exec_test_456"

    async def test_create_job_execution_record_webhook_trigger(
        self, mock_control_plane_client
    ):
        """Test creating execution record for webhook trigger."""
        mock_control_plane_client.create_job_execution_record.return_value = {
            "execution_id": "exec_webhook_123",
            "status": "created",
            "created_at": "2024-01-01T00:00:00Z"
        }

        input_data = ActivityCreateJobExecutionInput(
            execution_id="exec_webhook_123",
            job_id="job_webhook_456",
            organization_id="org_test_789",
            entity_type="agent",
            entity_id="agent_webhook_111",
            prompt="Handle webhook {{payload}}",
            trigger_type="webhook",
            trigger_metadata={
                "job_name": "Webhook Job",
                "webhook_payload": {"alert": "test"},
                "webhook_headers": {"x-source": "test"}
            }
        )

        with patch(
            "control_plane_api.worker.control_plane_client.get_control_plane_client",
            return_value=mock_control_plane_client
        ):
            result = await create_job_execution_record(input_data)

        # Verify webhook metadata was passed
        call_args = mock_control_plane_client.create_job_execution_record.call_args
        metadata = call_args.kwargs["trigger_metadata"]
        assert metadata["job_name"] == "Webhook Job"
        assert metadata["webhook_payload"]["alert"] == "test"
        assert metadata["webhook_headers"]["x-source"] == "test"

    async def test_create_job_execution_record_error_handling(
        self, mock_control_plane_client
    ):
        """Test error handling when client call fails."""
        # Mock error
        mock_control_plane_client.create_job_execution_record.side_effect = Exception(
            "HTTP 500 error"
        )

        input_data = ActivityCreateJobExecutionInput(
            execution_id="exec_error",
            job_id="job_error",
            organization_id="org_test",
            entity_type="agent",
            entity_id="agent_error",
            prompt="Test",
            trigger_type="cron",
            trigger_metadata={}
        )

        with patch(
            "control_plane_api.worker.control_plane_client.get_control_plane_client",
            return_value=mock_control_plane_client
        ):
            with pytest.raises(Exception) as exc_info:
                await create_job_execution_record(input_data)

        assert "HTTP 500 error" in str(exc_info.value)


@pytest.mark.asyncio
class TestUpdateJobExecutionStatusActivity:
    """Test update_job_execution_status activity."""

    async def test_update_job_execution_status_completed(
        self, mock_control_plane_client
    ):
        """Test updating job execution status to completed."""
        mock_control_plane_client.update_job_execution_status.return_value = {
            "job_id": "job_test_456",
            "execution_id": "exec_test_123",
            "status": "updated"
        }

        with patch(
            "control_plane_api.worker.control_plane_client.get_control_plane_client",
            return_value=mock_control_plane_client
        ):
            result = await update_job_execution_status(
                job_id="job_test_456",
                execution_id="exec_test_123",
                status="completed",
                duration_ms=5000,
                error_message=None
            )

        # Verify client method was called
        mock_control_plane_client.update_job_execution_status.assert_called_once_with(
            execution_id="exec_test_123",
            job_id="job_test_456",
            status="completed",
            duration_ms=5000,
            error_message=None
        )

        # Verify result
        assert result["job_id"] == "job_test_456"
        assert result["execution_id"] == "exec_test_123"
        assert result["status"] == "updated"

    async def test_update_job_execution_status_failed(
        self, mock_control_plane_client
    ):
        """Test updating job execution status to failed."""
        mock_control_plane_client.update_job_execution_status.return_value = {
            "job_id": "job_test_789",
            "execution_id": "exec_test_456",
            "status": "updated"
        }

        with patch(
            "control_plane_api.worker.control_plane_client.get_control_plane_client",
            return_value=mock_control_plane_client
        ):
            result = await update_job_execution_status(
                job_id="job_test_789",
                execution_id="exec_test_456",
                status="failed",
                duration_ms=1500,
                error_message="Test error occurred"
            )

        # Verify call includes error message
        call_args = mock_control_plane_client.update_job_execution_status.call_args
        assert call_args.kwargs["status"] == "failed"
        assert call_args.kwargs["duration_ms"] == 1500
        assert call_args.kwargs["error_message"] == "Test error occurred"

    async def test_update_job_execution_status_without_duration(
        self, mock_control_plane_client
    ):
        """Test updating status without duration_ms."""
        mock_control_plane_client.update_job_execution_status.return_value = {
            "job_id": "job_test",
            "execution_id": "exec_test",
            "status": "updated"
        }

        with patch(
            "control_plane_api.worker.control_plane_client.get_control_plane_client",
            return_value=mock_control_plane_client
        ):
            result = await update_job_execution_status(
                job_id="job_test",
                execution_id="exec_test",
                status="completed"
            )

        # Verify call with None values
        call_args = mock_control_plane_client.update_job_execution_status.call_args
        assert call_args.kwargs["duration_ms"] is None
        assert call_args.kwargs["error_message"] is None

    async def test_update_job_execution_status_error_handling(
        self, mock_control_plane_client
    ):
        """Test error handling when client call fails."""
        mock_control_plane_client.update_job_execution_status.side_effect = Exception(
            "HTTP 404 error"
        )

        with patch(
            "control_plane_api.worker.control_plane_client.get_control_plane_client",
            return_value=mock_control_plane_client
        ):
            with pytest.raises(Exception) as exc_info:
                await update_job_execution_status(
                    job_id="job_notfound",
                    execution_id="exec_notfound",
                    status="completed"
                )

        assert "HTTP 404 error" in str(exc_info.value)


@pytest.mark.asyncio
class TestJobActivitiesIntegration:
    """Integration tests for job activities workflow."""

    async def test_full_activity_lifecycle(
        self, mock_control_plane_client
    ):
        """Test complete lifecycle: create -> update."""
        # Mock create response
        mock_control_plane_client.create_job_execution_record.return_value = {
            "execution_id": "exec_lifecycle_123",
            "status": "created",
            "created_at": "2024-01-01T00:00:00Z"
        }

        # Mock update response
        mock_control_plane_client.update_job_execution_status.return_value = {
            "job_id": "job_lifecycle_456",
            "execution_id": "exec_lifecycle_123",
            "status": "updated"
        }

        with patch(
            "control_plane_api.worker.control_plane_client.get_control_plane_client",
            return_value=mock_control_plane_client
        ):
            # 1. Create execution record
            input_data = ActivityCreateJobExecutionInput(
                execution_id="exec_lifecycle_123",
                job_id="job_lifecycle_456",
                organization_id="org_test",
                entity_type="agent",
                entity_id="agent_test",
                prompt="Lifecycle test",
                trigger_type="cron",
                trigger_metadata={"job_name": "Lifecycle Job"}
            )

            create_result = await create_job_execution_record(input_data)
            assert create_result["execution_id"] == "exec_lifecycle_123"
            assert create_result["status"] == "created"

            # 2. Update execution status
            update_result = await update_job_execution_status(
                job_id="job_lifecycle_456",
                execution_id="exec_lifecycle_123",
                status="completed",
                duration_ms=3000
            )

            assert update_result["execution_id"] == "exec_lifecycle_123"
            assert update_result["status"] == "updated"

        # Verify both methods were called
        assert mock_control_plane_client.create_job_execution_record.call_count == 1
        assert mock_control_plane_client.update_job_execution_status.call_count == 1
