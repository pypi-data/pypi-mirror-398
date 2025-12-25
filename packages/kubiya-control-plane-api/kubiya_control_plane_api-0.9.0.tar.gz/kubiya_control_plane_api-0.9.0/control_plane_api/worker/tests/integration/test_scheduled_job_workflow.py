"""
Integration test for ScheduledJobWrapperWorkflow.

This test verifies that the workflow correctly:
1. Creates execution records via activities
2. Executes child workflows (agent/team)
3. Calculates duration properly (tests the fix for float.total_seconds() bug)
4. Updates job execution status
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import timedelta
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio import activity

# Import the workflow and related classes
from control_plane_api.worker.workflows.scheduled_job_wrapper import (
    ScheduledJobWrapperWorkflow,
    ScheduledJobInput,
)
from control_plane_api.worker.workflows.agent_execution import (
    AgentExecutionWorkflow,
)
from control_plane_api.worker.activities.job_activities import (
    create_job_execution_record,
    update_job_execution_status,
)


@pytest.mark.asyncio
async def test_scheduled_job_wrapper_workflow_duration_calculation():
    """
    Test that ScheduledJobWrapperWorkflow correctly calculates duration.

    This specifically tests the fix for the bug where workflow.time() returns
    a float, not a datetime, so we can't call .total_seconds() on the difference.
    """

    # Mock the activities
    @activity.defn(name="create_job_execution_record")
    async def mock_create_job_execution_record(input_data):
        """Mock activity for creating job execution record"""
        # input_data can be a dict or ActivityCreateJobExecutionInput object
        execution_id = input_data.execution_id if hasattr(input_data, 'execution_id') else input_data.get('execution_id')
        return {
            "execution_id": execution_id,
            "status": "created",
            "created_at": "2024-01-01T00:00:00Z"
        }

    @activity.defn(name="update_job_execution_status")
    async def mock_update_job_execution_status(
        job_id: str,
        execution_id: str,
        status: str,
        duration_ms: int = None,
        error_message: str = None
    ):
        """Mock activity for updating job execution status"""
        # This is the key assertion - duration_ms should be an integer
        assert isinstance(duration_ms, int), f"duration_ms should be int, got {type(duration_ms)}"
        assert duration_ms >= 0, f"duration_ms should be non-negative, got {duration_ms}"

        return {
            "job_id": job_id,
            "execution_id": execution_id,
            "status": "updated"
        }

    # Mock the child workflow
    async def mock_agent_execution(input_data):
        """Mock AgentExecutionWorkflow.run"""
        # Simulate some execution time
        import asyncio
        await asyncio.sleep(0.1)  # 100ms execution

        return {
            "status": "completed",
            "execution_id": input_data.execution_id,
            "response": "Test response"
        }

    # Create test environment
    async with await WorkflowEnvironment.start_time_skipping() as env:
        # Create worker with our workflow and mocked activities
        worker = Worker(
            env.client,
            task_queue="test-task-queue",
            workflows=[ScheduledJobWrapperWorkflow, AgentExecutionWorkflow],
            activities=[
                mock_create_job_execution_record,
                mock_update_job_execution_status,
            ],
        )

        async with worker:
            # Prepare test input
            test_input = ScheduledJobInput(
                execution_id="test_exec_123",
                agent_id="test_agent_456",
                organization_id="test_org_789",
                prompt="Test scheduled job prompt",
                system_prompt="You are a test agent",
                model_id="claude-3-5-sonnet-20241022",
                model_config={},
                agent_config={},
                mcp_servers={},
                user_metadata={
                    "job_id": "test_job_123",
                    "job_name": "Test Job",
                    "trigger_type": "cron"
                },
                runtime_type="default"
            )

            # Mock the child workflow execution
            with patch.object(
                AgentExecutionWorkflow,
                'run',
                new=mock_agent_execution
            ):
                # Execute the workflow
                result = await env.client.execute_workflow(
                    ScheduledJobWrapperWorkflow.run,
                    test_input,
                    id=f"test-scheduled-job-{test_input.execution_id}",
                    task_queue="test-task-queue",
                )

            # Verify the result
            assert result["status"] == "completed"
            assert result["execution_id"] == "test_exec_123"

            print("✅ Test passed! Duration calculation works correctly.")


@pytest.mark.asyncio
async def test_scheduled_job_wrapper_workflow_with_failure():
    """
    Test that ScheduledJobWrapperWorkflow handles failures correctly
    and still calculates duration.
    """

    @activity.defn(name="create_job_execution_record")
    async def mock_create_job_execution_record(input_data):
        # input_data can be a dict or ActivityCreateJobExecutionInput object
        execution_id = input_data.execution_id if hasattr(input_data, 'execution_id') else input_data.get('execution_id')
        return {
            "execution_id": execution_id,
            "status": "created",
            "created_at": "2024-01-01T00:00:00Z"
        }

    @activity.defn(name="update_job_execution_status")
    async def mock_update_job_execution_status(
        job_id: str,
        execution_id: str,
        status: str,
        duration_ms: int = None,
        error_message: str = None
    ):
        # Verify we got duration even for failed execution
        assert isinstance(duration_ms, int)
        assert duration_ms >= 0
        assert status == "failed"
        assert error_message is not None

        return {
            "job_id": job_id,
            "execution_id": execution_id,
            "status": "updated"
        }

    async def mock_failing_agent_execution(input_data):
        """Mock failing AgentExecutionWorkflow.run"""
        import asyncio
        await asyncio.sleep(0.05)
        raise Exception("Test execution failure")

    async with await WorkflowEnvironment.start_time_skipping() as env:
        worker = Worker(
            env.client,
            task_queue="test-task-queue-fail",
            workflows=[ScheduledJobWrapperWorkflow, AgentExecutionWorkflow],
            activities=[
                mock_create_job_execution_record,
                mock_update_job_execution_status,
            ],
        )

        async with worker:
            test_input = ScheduledJobInput(
                execution_id="test_exec_fail_456",
                agent_id="test_agent_789",
                organization_id="test_org_789",
                prompt="Test failing job",
                user_metadata={
                    "job_id": "test_job_fail_456",
                    "job_name": "Failing Test Job",
                    "trigger_type": "cron"
                },
                runtime_type="default"
            )

            with patch.object(
                AgentExecutionWorkflow,
                'run',
                new=mock_failing_agent_execution
            ):
                result = await env.client.execute_workflow(
                    ScheduledJobWrapperWorkflow.run,
                    test_input,
                    id=f"test-scheduled-job-fail-{test_input.execution_id}",
                    task_queue="test-task-queue-fail",
                )

            # Verify the failure was handled
            assert result["status"] == "failed"
            assert "error" in result

            print("✅ Test passed! Duration calculation works correctly even on failure.")


if __name__ == "__main__":
    import asyncio

    print("Running ScheduledJobWrapperWorkflow integration tests...\n")

    print("Test 1: Duration calculation with successful execution")
    asyncio.run(test_scheduled_job_wrapper_workflow_duration_calculation())

    print("\nTest 2: Duration calculation with failed execution")
    asyncio.run(test_scheduled_job_wrapper_workflow_with_failure())

    print("\n✅ All tests passed!")
