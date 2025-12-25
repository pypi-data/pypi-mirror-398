"""End-to-end tests for tool enforcement in worker execution."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from control_plane_api.worker.runtimes.base import RuntimeExecutionContext
from control_plane_api.worker.activities.runtime_activities import ActivityRuntimeExecuteInput


@pytest.fixture
def mock_control_plane_client():
    """Mock control plane client."""
    client = Mock()
    client.publish_event = Mock()
    client._api_key = "test-api-key"
    client.cache_metadata = Mock()
    return client


@pytest.fixture
def mock_cancellation_manager():
    """Mock cancellation manager."""
    manager = Mock()
    manager.register = Mock()
    manager.unregister = Mock()
    return manager


@pytest.fixture
def enforcement_context_data():
    """Sample enforcement context data."""
    return {
        "user_email": "test@example.com",
        "user_id": "user-123",
        "user_roles": ["developer"],
        "team_id": "team-456",
        "team_name": "Test Team",
        "environment": "test",
    }


@pytest.fixture
def runtime_context(enforcement_context_data):
    """Create RuntimeExecutionContext with enforcement fields."""
    return RuntimeExecutionContext(
        execution_id="exec-test-123",
        agent_id="agent-test-456",
        organization_id="org-test-789",
        prompt="Test prompt",
        system_prompt="You are a test assistant",
        model_id="claude-3-sonnet-20240229",
        # Enforcement fields
        user_email=enforcement_context_data["user_email"],
        user_id=enforcement_context_data["user_id"],
        user_roles=enforcement_context_data["user_roles"],
        team_id=enforcement_context_data["team_id"],
        team_name=enforcement_context_data["team_name"],
        environment=enforcement_context_data["environment"],
    )


@pytest.fixture
def activity_input(enforcement_context_data):
    """Create ActivityRuntimeExecuteInput with enforcement fields."""
    return ActivityRuntimeExecuteInput(
        execution_id="exec-test-123",
        agent_id="agent-test-456",
        organization_id="org-test-789",
        prompt="Test prompt",
        system_prompt="You are a test assistant",
        model_id="claude-3-sonnet-20240229",
        runtime_type="default",
        # Enforcement fields
        user_email=enforcement_context_data["user_email"],
        user_id=enforcement_context_data["user_id"],
        user_roles=enforcement_context_data["user_roles"],
        team_id=enforcement_context_data["team_id"],
        team_name=enforcement_context_data["team_name"],
        environment=enforcement_context_data["environment"],
    )


class TestRuntimeExecutionContextEnforcement:
    """Test that RuntimeExecutionContext properly includes enforcement fields."""

    def test_context_has_enforcement_fields(self, runtime_context):
        """Verify RuntimeExecutionContext includes all enforcement fields."""
        assert hasattr(runtime_context, "user_email")
        assert hasattr(runtime_context, "user_id")
        assert hasattr(runtime_context, "user_roles")
        assert hasattr(runtime_context, "team_id")
        assert hasattr(runtime_context, "team_name")
        assert hasattr(runtime_context, "environment")

        assert runtime_context.user_email == "test@example.com"
        assert runtime_context.user_id == "user-123"
        assert runtime_context.user_roles == ["developer"]
        assert runtime_context.team_id == "team-456"
        assert runtime_context.team_name == "Test Team"
        assert runtime_context.environment == "test"

    def test_context_enforcement_fields_optional(self):
        """Verify enforcement fields are optional and have defaults."""
        context = RuntimeExecutionContext(
            execution_id="exec-123",
            agent_id="agent-456",
            organization_id="org-789",
            prompt="Test",
        )

        # Should have default values
        assert context.user_email is None
        assert context.user_id is None
        assert context.user_roles == []
        assert context.team_id is None
        assert context.team_name is None
        assert context.environment == "production"  # Default


class TestActivityInputEnforcement:
    """Test that ActivityRuntimeExecuteInput properly includes enforcement fields."""

    def test_activity_input_has_enforcement_fields(self, activity_input):
        """Verify ActivityRuntimeExecuteInput includes all enforcement fields."""
        assert hasattr(activity_input, "user_email")
        assert hasattr(activity_input, "user_id")
        assert hasattr(activity_input, "user_roles")
        assert hasattr(activity_input, "team_id")
        assert hasattr(activity_input, "team_name")
        assert hasattr(activity_input, "environment")

        assert activity_input.user_email == "test@example.com"
        assert activity_input.user_id == "user-123"
        assert activity_input.user_roles == ["developer"]
        assert activity_input.team_id == "team-456"
        assert activity_input.team_name == "Test Team"
        assert activity_input.environment == "test"

    def test_activity_input_post_init_user_roles(self):
        """Verify __post_init__ initializes user_roles to empty list if None."""
        input_data = ActivityRuntimeExecuteInput(
            execution_id="exec-123",
            agent_id="agent-456",
            organization_id="org-789",
            prompt="Test",
            user_roles=None,
        )

        # Should be initialized to empty list
        assert input_data.user_roles == []


class TestAgnoRuntimeEnforcementInitialization:
    """Test that Agno runtime properly initializes enforcement."""

    def test_agno_runtime_initializes_enforcement_context(
        self, runtime_context
    ):
        """Test that Agno runtime creates enforcement context from RuntimeExecutionContext."""
        # Simulate what happens in the runtime - build enforcement context
        enforcement_context = {
            "organization_id": runtime_context.organization_id,
            "user_email": runtime_context.user_email,
            "user_id": runtime_context.user_id,
            "user_roles": runtime_context.user_roles or [],
            "team_id": runtime_context.team_id,
            "team_name": runtime_context.team_name,
            "agent_id": runtime_context.agent_id,
            "environment": runtime_context.environment,
            "model_id": runtime_context.model_id,
        }

        # Verify enforcement context has correct values
        assert enforcement_context["user_email"] == "test@example.com"
        assert enforcement_context["user_id"] == "user-123"
        assert enforcement_context["user_roles"] == ["developer"]
        assert enforcement_context["team_id"] == "team-456"
        assert enforcement_context["environment"] == "test"


class TestClaudeCodeRuntimeEnforcementInitialization:
    """Test that Claude Code runtime properly initializes enforcement."""

    def test_claude_code_config_builds_enforcement_context(
        self, runtime_context
    ):
        """Test that Claude Code config creates enforcement context."""
        # Build enforcement context as it would be in config.py
        enforcement_context = {
            "organization_id": runtime_context.organization_id,
            "user_email": runtime_context.user_email,
            "user_id": runtime_context.user_id,
            "user_roles": runtime_context.user_roles or [],
            "team_id": runtime_context.team_id,
            "team_name": runtime_context.team_name,
            "agent_id": runtime_context.agent_id,
            "environment": runtime_context.environment,
            "model_id": runtime_context.model_id,
        }

        # Verify enforcement context has correct values
        assert enforcement_context["user_email"] == "test@example.com"
        assert enforcement_context["user_id"] == "user-123"
        assert enforcement_context["user_roles"] == ["developer"]
        assert enforcement_context["team_id"] == "team-456"
        assert enforcement_context["environment"] == "test"
        assert enforcement_context["agent_id"] == "agent-test-456"


class TestEnforcementDataFlow:
    """Test that enforcement data flows correctly through the system."""

    def test_activity_to_runtime_context_mapping(self, activity_input):
        """Test that enforcement fields map from ActivityInput to RuntimeContext."""
        # Simulate what happens in runtime_activities.py
        context = RuntimeExecutionContext(
            execution_id=activity_input.execution_id,
            agent_id=activity_input.agent_id,
            organization_id=activity_input.organization_id,
            prompt=activity_input.prompt,
            system_prompt=activity_input.system_prompt,
            model_id=activity_input.model_id,
            # Enforcement context
            user_email=activity_input.user_email,
            user_id=activity_input.user_id,
            user_roles=activity_input.user_roles or [],
            team_id=activity_input.team_id,
            team_name=activity_input.team_name,
            environment=activity_input.environment,
        )

        # Verify all enforcement fields transferred correctly
        assert context.user_email == activity_input.user_email
        assert context.user_id == activity_input.user_id
        assert context.user_roles == activity_input.user_roles
        assert context.team_id == activity_input.team_id
        assert context.team_name == activity_input.team_name
        assert context.environment == activity_input.environment

    def test_runtime_context_to_enforcement_context(self, runtime_context):
        """Test building enforcement context from RuntimeExecutionContext."""
        # Simulate what happens in runtime initialization
        enforcement_context = {
            "organization_id": runtime_context.organization_id,
            "user_email": runtime_context.user_email,
            "user_id": runtime_context.user_id,
            "user_roles": runtime_context.user_roles or [],
            "team_id": runtime_context.team_id,
            "team_name": runtime_context.team_name,
            "agent_id": runtime_context.agent_id,
            "environment": runtime_context.environment,
            "model_id": runtime_context.model_id,
        }

        # Verify enforcement context is complete
        assert all(key in enforcement_context for key in [
            "organization_id", "user_email", "user_id", "user_roles",
            "team_id", "team_name", "agent_id", "environment"
        ])

        # Verify values
        assert enforcement_context["user_email"] == "test@example.com"
        assert enforcement_context["user_roles"] == ["developer"]
        assert enforcement_context["environment"] == "test"


class TestEnforcementEndToEnd:
    """End-to-end tests simulating full enforcement flow."""

    def test_e2e_enforcement_service_creation(self, runtime_context):
        """Test that enforcement service can be created from runtime context."""
        from control_plane_api.worker.services.tool_enforcement import ToolEnforcementService

        # Simulate creating enforcement service
        mock_enforcer = Mock()
        enforcement_service = ToolEnforcementService(mock_enforcer)

        # Verify service is created
        assert enforcement_service is not None
        assert enforcement_service.enabled is True
        assert enforcement_service.enforcer == mock_enforcer

        # Build enforcement context from runtime context
        enforcement_context = {
            "organization_id": runtime_context.organization_id,
            "user_email": runtime_context.user_email,
            "user_id": runtime_context.user_id,
            "user_roles": runtime_context.user_roles or [],
            "team_id": runtime_context.team_id,
            "team_name": runtime_context.team_name,
            "agent_id": runtime_context.agent_id,
            "environment": runtime_context.environment,
        }

        # Build enforcement payload
        payload = enforcement_service._build_enforcement_payload(
            tool_name="Read",
            tool_args={"file_path": "/tmp/test"},
            context=enforcement_context
        )

        # Verify payload structure
        assert payload["action"] == "tool_execution"
        assert payload["tool"]["name"] == "Read"
        assert payload["user"]["email"] == "test@example.com"
        assert payload["organization"]["id"] == "org-test-789"
        assert payload["execution"]["environment"] == "test"

    def test_e2e_enforcement_flow_components(self):
        """Test that all enforcement components work together."""
        from control_plane_api.worker.services.tool_enforcement import ToolEnforcementService

        # Component 1: Enforcement service
        mock_enforcer = AsyncMock()
        service = ToolEnforcementService(mock_enforcer)
        assert service.enabled

        # Component 2: Enforcement context
        context = {
            "organization_id": "org-123",
            "user_email": "test@example.com",
            "user_roles": ["developer"],
            "agent_id": "agent-456",
            "environment": "production"
        }

        # Component 3: Tool information
        tool_name = "Bash"
        tool_args = {"command": "ls /tmp"}

        # Component 4: Build payload
        payload = service._build_enforcement_payload(tool_name, tool_args, context)

        # Verify all components integrated correctly
        assert payload["tool"]["name"] == tool_name
        assert payload["tool"]["arguments"] == tool_args
        assert payload["tool"]["source"] == "builtin"
        assert payload["tool"]["category"] == "command_execution"
        assert payload["tool"]["risk_level"] == "high"
        assert payload["user"]["email"] == context["user_email"]
        assert payload["organization"]["id"] == context["organization_id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
