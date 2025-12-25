"""Unit tests for tool enforcement service."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone

from control_plane_api.worker.services.tool_enforcement import ToolEnforcementService


@pytest.fixture
def mock_enforcer_client():
    """Mock policy enforcer client."""
    client = AsyncMock()
    client.evaluation = AsyncMock()
    return client


@pytest.fixture
def enforcement_service(mock_enforcer_client):
    """Create enforcement service with mock client."""
    return ToolEnforcementService(mock_enforcer_client)


@pytest.fixture
def enforcement_context():
    """Sample enforcement context."""
    return {
        "user_email": "test@example.com",
        "user_id": "user-123",
        "user_roles": ["developer"],
        "organization_id": "org-456",
        "team_id": "team-789",
        "agent_id": "agent-xyz",
        "execution_id": "exec-abc",
        "environment": "production"
    }


class TestToolEnforcementService:
    """Test suite for ToolEnforcementService."""

    @pytest.mark.asyncio
    async def test_enforce_tool_allowed(self, enforcement_service, enforcement_context, mock_enforcer_client):
        """Test enforcement check when tool is allowed."""
        # Mock enforcer response
        mock_enforcer_client.evaluation.enforce.return_value = {
            "allow": True,
            "id": "enforcement-123",
            "policies": ["role_based_access"]
        }

        allow, violation, metadata = await enforcement_service.enforce_tool_execution(
            tool_name="Read",
            tool_args={"file_path": "/tmp/test.txt"},
            enforcement_context=enforcement_context
        )

        assert allow is True
        assert violation is None
        assert metadata["enforcer"] == "allowed"
        assert "role_based_access" in metadata["policies"]
        assert "enforcement_id" in metadata

    @pytest.mark.asyncio
    async def test_enforce_tool_blocked(self, enforcement_service, enforcement_context, mock_enforcer_client):
        """Test enforcement check when tool is blocked."""
        mock_enforcer_client.evaluation.enforce.return_value = {
            "allow": False,
            "id": "enforcement-456",
            "policies": ["production_safeguards"]
        }

        allow, violation, metadata = await enforcement_service.enforce_tool_execution(
            tool_name="Bash",
            tool_args={"command": "rm -rf /tmp/*"},
            enforcement_context=enforcement_context
        )

        assert allow is False
        assert violation is not None
        assert "blocked by policy enforcement" in violation.lower()
        assert "Bash" in violation
        assert metadata["enforcer"] == "blocked"
        assert "production_safeguards" in metadata["policies"]

    @pytest.mark.asyncio
    async def test_enforce_timeout_fails_open(self, enforcement_service, enforcement_context, mock_enforcer_client):
        """Test that enforcement timeout fails open (allows execution)."""
        # Mock timeout
        async def slow_enforce(*args, **kwargs):
            await asyncio.sleep(5)  # Longer than timeout
            return {"allow": False}

        mock_enforcer_client.evaluation.enforce = slow_enforce

        allow, violation, metadata = await enforcement_service.enforce_tool_execution(
            tool_name="Bash",
            tool_args={"command": "ls"},
            enforcement_context=enforcement_context,
            timeout=0.1  # Very short timeout
        )

        assert allow is True  # Fails open
        assert violation is None
        assert metadata["enforcer"] == "timeout"

    @pytest.mark.asyncio
    async def test_enforce_error_fails_open(self, enforcement_service, enforcement_context, mock_enforcer_client):
        """Test that enforcement errors fail open (allows execution)."""
        # Mock error
        mock_enforcer_client.evaluation.enforce.side_effect = Exception("Enforcer unavailable")

        allow, violation, metadata = await enforcement_service.enforce_tool_execution(
            tool_name="Bash",
            tool_args={"command": "ls"},
            enforcement_context=enforcement_context
        )

        assert allow is True  # Fails open
        assert violation is None
        assert metadata["enforcer"] == "error"
        assert "error" in metadata

    @pytest.mark.asyncio
    async def test_disabled_enforcer(self):
        """Test that disabled enforcer allows all tools."""
        service = ToolEnforcementService(None)

        allow, violation, metadata = await service.enforce_tool_execution(
            tool_name="Bash",
            tool_args={"command": "rm -rf /"},
            enforcement_context={}
        )

        assert allow is True
        assert violation is None
        assert metadata["enforcer"] == "disabled"

    def test_build_enforcement_payload(self, enforcement_service, enforcement_context):
        """Test enforcement payload construction."""
        payload = enforcement_service._build_enforcement_payload(
            tool_name="Bash",
            tool_args={"command": "kubectl get pods"},
            context=enforcement_context
        )

        assert payload["action"] == "tool_execution"
        assert payload["tool"]["name"] == "Bash"
        assert payload["tool"]["source"] == "builtin"
        assert payload["tool"]["category"] == "command_execution"
        assert payload["tool"]["risk_level"] == "high"
        assert payload["user"]["email"] == "test@example.com"
        assert payload["organization"]["id"] == "org-456"
        assert payload["execution"]["environment"] == "production"
        assert "timestamp" in payload["execution"]

    def test_determine_tool_source(self, enforcement_service):
        """Test tool source detection."""
        assert enforcement_service._determine_tool_source("mcp__github__list_repos") == "mcp"
        assert enforcement_service._determine_tool_source("Bash") == "builtin"
        assert enforcement_service._determine_tool_source("Read") == "builtin"
        assert enforcement_service._determine_tool_source("custom_tool") == "skill"

    def test_determine_tool_category(self, enforcement_service):
        """Test tool category detection."""
        assert enforcement_service._determine_tool_category("Bash") == "command_execution"
        assert enforcement_service._determine_tool_category("Read") == "file_operation"
        assert enforcement_service._determine_tool_category("Write") == "file_operation"
        assert enforcement_service._determine_tool_category("Grep") == "file_search"
        assert enforcement_service._determine_tool_category("WebFetch") == "network"
        assert enforcement_service._determine_tool_category("custom_tool") == "general"

    def test_determine_risk_level_critical(self, enforcement_service):
        """Test risk level assessment for critical commands."""
        # Critical risk - destructive commands
        assert enforcement_service._determine_risk_level(
            "Bash",
            {"command": "rm -rf /"}
        ) == "critical"

        assert enforcement_service._determine_risk_level(
            "Bash",
            {"command": "dd if=/dev/zero of=/dev/sda"}
        ) == "critical"

    def test_determine_risk_level_high(self, enforcement_service):
        """Test risk level assessment for high-risk operations."""
        # High risk - command execution
        assert enforcement_service._determine_risk_level(
            "Bash",
            {"command": "kubectl delete deployment"}
        ) == "high"

        # High risk - sensitive file access
        assert enforcement_service._determine_risk_level(
            "Read",
            {"file_path": "/etc/passwd"}
        ) == "high"

        assert enforcement_service._determine_risk_level(
            "Read",
            {"file_path": "~/.ssh/id_rsa"}
        ) == "high"

    def test_determine_risk_level_medium(self, enforcement_service):
        """Test risk level assessment for medium-risk operations."""
        assert enforcement_service._determine_risk_level(
            "Write",
            {"file_path": "/tmp/test.txt", "content": "test"}
        ) == "medium"

        assert enforcement_service._determine_risk_level(
            "Edit",
            {"file_path": "/tmp/config.yaml"}
        ) == "medium"

    def test_determine_risk_level_low(self, enforcement_service):
        """Test risk level assessment for low-risk operations."""
        assert enforcement_service._determine_risk_level(
            "Read",
            {"file_path": "/tmp/test.txt"}
        ) == "low"

        assert enforcement_service._determine_risk_level(
            "Grep",
            {"pattern": "error", "path": "/var/log"}
        ) == "low"

    def test_format_violation_message(self, enforcement_service):
        """Test violation message formatting."""
        enforcement_result = {
            "id": "enf-123",
            "allow": False,
            "policies": ["policy1", "policy2"]
        }

        message = enforcement_service._format_violation_message(
            tool_name="Bash",
            policies=["policy1", "policy2"],
            enforcement_result=enforcement_result
        )

        assert "Tool execution blocked" in message
        assert "Bash" in message
        assert "policy1, policy2" in message
        assert "enf-123" in message
        assert "administrator" in message.lower()


class TestToolEnforcementPayloadValidation:
    """Test payload structure validation."""

    def test_payload_has_all_required_fields(self, enforcement_service, enforcement_context):
        """Verify payload contains all required fields."""
        payload = enforcement_service._build_enforcement_payload(
            tool_name="Bash",
            tool_args={"command": "ls"},
            context=enforcement_context
        )

        # Top-level fields
        assert "action" in payload
        assert "tool" in payload
        assert "user" in payload
        assert "organization" in payload
        assert "team" in payload
        assert "execution" in payload

        # Tool fields
        assert "name" in payload["tool"]
        assert "arguments" in payload["tool"]
        assert "source" in payload["tool"]
        assert "category" in payload["tool"]
        assert "risk_level" in payload["tool"]

        # User fields
        assert "email" in payload["user"]
        assert "id" in payload["user"]
        assert "roles" in payload["user"]

        # Organization fields
        assert "id" in payload["organization"]

        # Execution fields
        assert "execution_id" in payload["execution"]
        assert "agent_id" in payload["execution"]
        assert "environment" in payload["execution"]
        assert "timestamp" in payload["execution"]

    def test_payload_timestamp_format(self, enforcement_service, enforcement_context):
        """Verify timestamp is in ISO format."""
        payload = enforcement_service._build_enforcement_payload(
            tool_name="Test",
            tool_args={},
            context=enforcement_context
        )

        timestamp = payload["execution"]["timestamp"]
        # Should be able to parse back
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert isinstance(parsed, datetime)

    def test_payload_handles_missing_context_fields(self, enforcement_service):
        """Test payload construction with minimal context."""
        minimal_context = {
            "organization_id": "org-123",
            "agent_id": "agent-456"
        }

        payload = enforcement_service._build_enforcement_payload(
            tool_name="Test",
            tool_args={},
            context=minimal_context
        )

        # Should not crash, just have None values
        assert payload["user"]["email"] is None
        assert payload["user"]["roles"] == []
        assert payload["organization"]["id"] == "org-123"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
