"""Integration tests for hook enforcement."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, MagicMock
from control_plane_api.worker.runtimes.agno.hooks import (
    create_tool_hook_for_streaming,
    create_tool_hook_with_callback,
)
from control_plane_api.worker.runtimes.claude_code.hooks import build_hooks
from control_plane_api.worker.services.tool_enforcement import ToolEnforcementService


@pytest.fixture
def mock_control_plane():
    """Mock control plane client."""
    client = Mock()
    client.publish_event = Mock()
    return client


@pytest.fixture
def mock_enforcer_client():
    """Mock enforcer client for integration tests."""
    client = AsyncMock()
    client.evaluation = AsyncMock()
    return client


@pytest.fixture
def enforcement_service(mock_enforcer_client):
    """Create enforcement service."""
    return ToolEnforcementService(mock_enforcer_client)


@pytest.fixture
def enforcement_context():
    """Sample enforcement context."""
    return {
        "organization_id": "org-123",
        "user_email": "test@example.com",
        "user_id": "user-456",
        "user_roles": ["developer"],
        "team_id": "team-789",
        "agent_id": "agent-abc",
        "environment": "test",
    }


class TestAgnoHookEnforcement:
    """Test Agno hook with enforcement integration."""

    def test_streaming_hook_with_allowed_tool(
        self, mock_control_plane, enforcement_service, enforcement_context, mock_enforcer_client
    ):
        """Test streaming hook when enforcement allows tool."""
        # Mock allowed response
        mock_enforcer_client.evaluation.enforce.return_value = {
            "allow": True,
            "id": "enf-123",
            "policies": ["test_policy"],
        }

        # Create hook
        hook = create_tool_hook_for_streaming(
            control_plane=mock_control_plane,
            execution_id="exec-123",
            message_id="msg-456",
            enforcement_context=enforcement_context,
            enforcement_service=enforcement_service,
        )

        # Mock tool function
        mock_tool = Mock(return_value="tool result")

        # Execute hook
        result = hook(name="Read", function=mock_tool, arguments={"file_path": "/tmp/test.txt"})

        # Verify tool was executed
        mock_tool.assert_called_once_with(file_path="/tmp/test.txt")
        assert result == "tool result"

        # Verify enforcement was called
        assert mock_enforcer_client.evaluation.enforce.called

        # Verify events were published
        assert mock_control_plane.publish_event.call_count == 2  # start + complete

        # Check that enforcement metadata is in events
        calls = mock_control_plane.publish_event.call_args_list
        start_event = calls[0][1]["data"]
        complete_event = calls[1][1]["data"]

        assert "enforcement" in start_event
        assert "enforcement" in complete_event
        assert complete_event["enforcement"]["enforcer"] == "allowed"

    def test_streaming_hook_with_blocked_tool(
        self, mock_control_plane, enforcement_service, enforcement_context, mock_enforcer_client
    ):
        """Test streaming hook when enforcement blocks tool."""
        # Mock blocked response
        mock_enforcer_client.evaluation.enforce.return_value = {
            "allow": False,
            "id": "enf-456",
            "policies": ["production_safeguards"],
        }

        # Create hook
        hook = create_tool_hook_for_streaming(
            control_plane=mock_control_plane,
            execution_id="exec-123",
            message_id="msg-456",
            enforcement_context=enforcement_context,
            enforcement_service=enforcement_service,
        )

        # Mock tool function
        mock_tool = Mock(return_value="original result")

        # Execute hook
        result = hook(name="Bash", function=mock_tool, arguments={"command": "rm -rf /"})

        # Verify tool was STILL executed (non-blocking)
        mock_tool.assert_called_once()

        # Verify result contains violation message
        assert "POLICY VIOLATION" in result
        assert "Bash" in result
        assert "original result" in result

        # Verify enforcement metadata shows blocked
        calls = mock_control_plane.publish_event.call_args_list
        complete_event = calls[1][1]["data"]
        assert complete_event["enforcement"]["enforcer"] == "blocked"

    def test_callback_hook_with_enforcement(
        self, enforcement_service, enforcement_context, mock_enforcer_client
    ):
        """Test callback hook with enforcement."""
        # Mock allowed response
        mock_enforcer_client.evaluation.enforce.return_value = {
            "allow": True,
            "id": "enf-789",
            "policies": [],
        }

        # Mock callback
        callback_events = []
        def event_callback(event):
            callback_events.append(event)

        # Create hook
        hook = create_tool_hook_with_callback(
            execution_id="exec-123",
            message_id="msg-456",
            event_callback=event_callback,
            enforcement_context=enforcement_context,
            enforcement_service=enforcement_service,
        )

        # Mock tool function
        mock_tool = Mock(return_value="result")

        # Execute hook
        result = hook(name="Read", function=mock_tool, arguments={"file_path": "/tmp/test"})

        # Verify events contain enforcement metadata
        assert len(callback_events) == 2  # start + complete
        assert "enforcement" in callback_events[0]
        assert "enforcement" in callback_events[1]

    def test_hook_without_enforcement_service(self, mock_control_plane):
        """Test hook works without enforcement service (disabled)."""
        # Create hook WITHOUT enforcement
        hook = create_tool_hook_for_streaming(
            control_plane=mock_control_plane,
            execution_id="exec-123",
            message_id="msg-456",
            enforcement_context=None,
            enforcement_service=None,
        )

        # Mock tool function
        mock_tool = Mock(return_value="result")

        # Execute hook
        result = hook(name="Read", function=mock_tool, arguments={"file_path": "/tmp/test"})

        # Should work normally
        assert result == "result"
        mock_tool.assert_called_once()


class TestClaudeCodeHookEnforcement:
    """Test Claude Code hooks with enforcement integration."""

    @pytest.mark.asyncio
    async def test_claude_hooks_with_allowed_tool(
        self, enforcement_service, enforcement_context, mock_enforcer_client
    ):
        """Test Claude Code hooks when enforcement allows tool."""
        # Mock allowed response
        mock_enforcer_client.evaluation.enforce.return_value = {
            "allow": True,
            "id": "enf-123",
            "policies": ["test_policy"],
        }

        # Mock callback
        callback_events = []
        def event_callback(event):
            callback_events.append(event)

        # Build hooks
        active_tools = {}
        started_tools = set()
        completed_tools = set()
        hooks = build_hooks(
            execution_id="exec-123",
            event_callback=event_callback,
            active_tools=active_tools,
            completed_tools=completed_tools,
            started_tools=started_tools,
            enforcement_context=enforcement_context,
            enforcement_service=enforcement_service,
        )

        # Get hooks
        pre_hook = hooks["PreToolUse"][0].hooks[0]
        post_hook = hooks["PostToolUse"][0].hooks[0]

        # Simulate tool execution
        input_data = {"tool_name": "Read", "tool_input": {"file_path": "/tmp/test"}}
        tool_use_id = "tool-123"
        tool_context = {}

        # Call pre-hook
        await pre_hook(input_data, tool_use_id, tool_context)

        # Verify enforcement was called
        assert mock_enforcer_client.evaluation.enforce.called

        # Verify no violation stored in context
        assert "enforcement_violation" not in tool_context

        # Simulate tool output
        output_data = {"tool_name": "Read", "output": "file contents"}

        # Call post-hook
        await post_hook(output_data, tool_use_id, tool_context)

        # Verify output is not modified
        assert output_data["output"] == "file contents"
        assert "enforcement_violated" not in output_data

    @pytest.mark.asyncio
    async def test_claude_hooks_with_blocked_tool(
        self, enforcement_service, enforcement_context, mock_enforcer_client
    ):
        """Test Claude Code hooks when enforcement blocks tool."""
        # Mock blocked response
        mock_enforcer_client.evaluation.enforce.return_value = {
            "allow": False,
            "id": "enf-456",
            "policies": ["bash_validation"],
        }

        # Mock callback
        callback_events = []
        def event_callback(event):
            callback_events.append(event)

        # Build hooks
        active_tools = {}
        started_tools = set()
        completed_tools = set()
        hooks = build_hooks(
            execution_id="exec-123",
            event_callback=event_callback,
            active_tools=active_tools,
            completed_tools=completed_tools,
            started_tools=started_tools,
            enforcement_context=enforcement_context,
            enforcement_service=enforcement_service,
        )

        # Get hooks
        pre_hook = hooks["PreToolUse"][0].hooks[0]
        post_hook = hooks["PostToolUse"][0].hooks[0]

        # Simulate tool execution
        input_data = {"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}
        tool_use_id = "tool-456"
        tool_context = {}

        # Call pre-hook
        await pre_hook(input_data, tool_use_id, tool_context)

        # Verify violation stored in context
        assert "enforcement_violation" in tool_context
        assert "enforcement_metadata" in tool_context

        # Simulate tool output
        output_data = {"tool_name": "Bash", "output": "command executed"}

        # Call post-hook
        await post_hook(output_data, tool_use_id, tool_context)

        # Verify violation injected into output
        assert "POLICY VIOLATION" in output_data["output"]
        assert "enforcement_violated" in output_data
        assert output_data["enforcement_violated"] is True
        assert "command executed" in output_data["output"]  # Original output preserved

    @pytest.mark.asyncio
    async def test_claude_hooks_without_enforcement(self):
        """Test Claude Code hooks work without enforcement service."""
        # Mock callback
        callback_events = []
        def event_callback(event):
            callback_events.append(event)

        # Build hooks WITHOUT enforcement
        active_tools = {}
        started_tools = set()
        completed_tools = set()
        hooks = build_hooks(
            execution_id="exec-123",
            event_callback=event_callback,
            active_tools=active_tools,
            completed_tools=completed_tools,
            started_tools=started_tools,
            enforcement_context=None,
            enforcement_service=None,
        )

        # Get hooks
        pre_hook = hooks["PreToolUse"][0].hooks[0]
        post_hook = hooks["PostToolUse"][0].hooks[0]

        # Simulate tool execution
        input_data = {"tool_name": "Read", "tool_input": {"file_path": "/tmp/test"}}
        tool_use_id = "tool-123"
        tool_context = {}

        # Call hooks
        await pre_hook(input_data, tool_use_id, tool_context)

        output_data = {"tool_name": "Read", "output": "file contents"}
        await post_hook(output_data, tool_use_id, tool_context)

        # Should work normally without violations
        assert output_data["output"] == "file contents"
        assert "enforcement_violated" not in output_data


class TestEnforcementFailOpen:
    """Test fail-open behavior on errors."""

    def test_agno_hook_fails_open_on_enforcer_error(
        self, mock_control_plane, enforcement_service, enforcement_context, mock_enforcer_client
    ):
        """Test Agno hook fails open when enforcer has error."""
        # Mock enforcer error
        mock_enforcer_client.evaluation.enforce.side_effect = Exception("Enforcer down")

        # Create hook
        hook = create_tool_hook_for_streaming(
            control_plane=mock_control_plane,
            execution_id="exec-123",
            message_id="msg-456",
            enforcement_context=enforcement_context,
            enforcement_service=enforcement_service,
        )

        # Mock tool function
        mock_tool = Mock(return_value="result")

        # Execute hook - should NOT raise exception
        result = hook(name="Read", function=mock_tool, arguments={"file_path": "/tmp/test"})

        # Verify tool was executed (fail open)
        mock_tool.assert_called_once()
        assert result == "result"

        # Verify enforcement metadata shows error
        calls = mock_control_plane.publish_event.call_args_list
        complete_event = calls[1][1]["data"]
        assert "enforcement" in complete_event
        assert complete_event["enforcement"]["enforcer"] == "error"

    @pytest.mark.asyncio
    async def test_claude_hook_fails_open_on_enforcer_error(
        self, enforcement_service, enforcement_context, mock_enforcer_client
    ):
        """Test Claude Code hook fails open when enforcer has error."""
        # Mock enforcer error
        mock_enforcer_client.evaluation.enforce.side_effect = Exception("Enforcer down")

        # Build hooks
        active_tools = {}
        started_tools = set()
        completed_tools = set()
        hooks = build_hooks(
            execution_id="exec-123",
            event_callback=lambda x: None,
            active_tools=active_tools,
            completed_tools=completed_tools,
            started_tools=started_tools,
            enforcement_context=enforcement_context,
            enforcement_service=enforcement_service,
        )

        # Get pre-hook
        pre_hook = hooks["PreToolUse"][0].hooks[0]

        # Simulate tool execution
        input_data = {"tool_name": "Bash", "tool_input": {"command": "ls"}}
        tool_use_id = "tool-123"
        tool_context = {}

        # Call pre-hook - should NOT raise exception
        await pre_hook(input_data, tool_use_id, tool_context)

        # Verify no violation stored (fail open)
        assert "enforcement_violation" not in tool_context


class TestToolEventDeduplication:
    """Test deduplication of tool start and complete events."""

    @pytest.mark.asyncio
    async def test_tool_start_deduplication(self):
        """Test that duplicate tool_start events are prevented."""
        # Track events
        callback_events = []
        def event_callback(event):
            callback_events.append(event)

        # Build hooks
        active_tools = {}
        started_tools = set()
        completed_tools = set()
        hooks = build_hooks(
            execution_id="exec-123",
            event_callback=event_callback,
            active_tools=active_tools,
            completed_tools=completed_tools,
            started_tools=started_tools,
            enforcement_context=None,
            enforcement_service=None,
        )

        # Get pre-hook
        pre_hook = hooks["PreToolUse"][0].hooks[0]

        # Simulate tool execution
        input_data = {"tool_name": "Bash", "tool_input": {"command": "echo 'hello world'"}}
        tool_use_id = "tool-123"
        tool_context = {}

        # Call pre-hook FIRST time
        await pre_hook(input_data, tool_use_id, tool_context)

        # Verify tool_start event was published
        assert len(callback_events) == 1
        assert callback_events[0]["type"] == "tool_start"
        assert callback_events[0]["tool_name"] == "Bash"
        assert callback_events[0]["tool_execution_id"] == tool_use_id

        # Verify tool_use_id added to started_tools
        assert tool_use_id in started_tools

        # Call pre-hook SECOND time with SAME tool_use_id (simulating duplicate)
        await pre_hook(input_data, tool_use_id, tool_context)

        # Verify NO additional event was published (deduplication works!)
        assert len(callback_events) == 1, "Duplicate tool_start event was published!"

    @pytest.mark.asyncio
    async def test_tool_complete_deduplication(self):
        """Test that duplicate tool_complete events are prevented."""
        # Track events
        callback_events = []
        def event_callback(event):
            callback_events.append(event)

        # Build hooks
        active_tools = {}
        started_tools = set()
        completed_tools = set()
        hooks = build_hooks(
            execution_id="exec-123",
            event_callback=event_callback,
            active_tools=active_tools,
            completed_tools=completed_tools,
            started_tools=started_tools,
            enforcement_context=None,
            enforcement_service=None,
        )

        # Get post-hook
        post_hook = hooks["PostToolUse"][0].hooks[0]

        # Simulate tool output
        output_data = {"tool_name": "Bash", "output": "hello world"}
        tool_use_id = "tool-456"
        tool_context = {}

        # Call post-hook FIRST time
        await post_hook(output_data, tool_use_id, tool_context)

        # Verify tool_complete event was published
        assert len(callback_events) == 1
        assert callback_events[0]["type"] == "tool_complete"
        assert callback_events[0]["tool_name"] == "Bash"
        assert callback_events[0]["tool_execution_id"] == tool_use_id

        # Verify tool_use_id added to completed_tools
        assert tool_use_id in completed_tools

        # Call post-hook SECOND time with SAME tool_use_id (simulating duplicate)
        await post_hook(output_data, tool_use_id, tool_context)

        # Verify NO additional event was published (deduplication works!)
        assert len(callback_events) == 1, "Duplicate tool_complete event was published!"

    @pytest.mark.asyncio
    async def test_multiple_different_tools(self):
        """Test that different tools each get their own events."""
        # Track events
        callback_events = []
        def event_callback(event):
            callback_events.append(event)

        # Build hooks
        active_tools = {}
        started_tools = set()
        completed_tools = set()
        hooks = build_hooks(
            execution_id="exec-123",
            event_callback=event_callback,
            active_tools=active_tools,
            completed_tools=completed_tools,
            started_tools=started_tools,
            enforcement_context=None,
            enforcement_service=None,
        )

        # Get pre-hook
        pre_hook = hooks["PreToolUse"][0].hooks[0]

        # Execute tool 1
        input_data_1 = {"tool_name": "Bash", "tool_input": {"command": "echo 'hello'"}}
        await pre_hook(input_data_1, "tool-1", {})

        # Execute tool 2
        input_data_2 = {"tool_name": "Read", "tool_input": {"file_path": "/tmp/test"}}
        await pre_hook(input_data_2, "tool-2", {})

        # Execute tool 3
        input_data_3 = {"tool_name": "Write", "tool_input": {"file_path": "/tmp/out"}}
        await pre_hook(input_data_3, "tool-3", {})

        # Verify all 3 events were published
        assert len(callback_events) == 3
        assert callback_events[0]["tool_name"] == "Bash"
        assert callback_events[1]["tool_name"] == "Read"
        assert callback_events[2]["tool_name"] == "Write"

        # Verify all 3 tool_use_ids are in started_tools
        assert "tool-1" in started_tools
        assert "tool-2" in started_tools
        assert "tool-3" in started_tools


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
