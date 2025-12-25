"""End-to-end tests for context graph node templates in system prompts."""
import pytest
import os
from unittest.mock import patch, MagicMock
import httpx
from control_plane_api.app.lib.templating.types import TemplateContext
from control_plane_api.app.lib.templating.resolver import resolve_templates
from control_plane_api.app.lib.templating.compiler import TemplateCompiler
from control_plane_api.app.lib.templating.engine import get_default_engine


class TestGraphTemplateE2EFlow:
    """End-to-end tests for full template resolution flow with graph nodes."""

    @patch('httpx.Client')
    def test_e2e_system_prompt_with_graph_node_api_fetch(self, mock_client_cls):
        """Test complete flow: system prompt → template parsing → API fetch → compilation."""
        # Mock API response for a service node
        service_node = {
            "id": "service-prod-api",
            "labels": ["Service", "Production"],
            "properties": {
                "name": "Production API",
                "version": "2.1.0",
                "environment": "production",
                "owner_team": "platform-team"
            },
            "relationships": {
                "incoming": [
                    {"type": "DEPENDS_ON", "from": "service-frontend", "properties": {}}
                ],
                "outgoing": [
                    {"type": "USES", "to": "database-prod", "properties": {"connection": "primary"}}
                ]
            }
        }

        mock_response = MagicMock()
        mock_response.json.return_value = service_node

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        # System prompt with graph node reference
        system_prompt = """
You are managing the following service:

{{.graph.service-prod-api}}

Please ensure all operations follow production best practices.
"""

        # Build template context (simulating agent executor)
        context = TemplateContext(
            variables={},
            secrets={},
            env_vars={},
            graph_api_base="https://graph.kubiya.ai",
            graph_api_key="test-api-key",
            graph_org_id="test-org-123"
        )

        # Resolve templates
        compiled_prompt = resolve_templates(
            system_prompt,
            context,
            strict=False,
            skip_on_error=False
        )

        # Verify compilation succeeded
        assert compiled_prompt != system_prompt
        assert "service-prod-api" in compiled_prompt
        assert "Production API" in compiled_prompt
        assert "version" in compiled_prompt
        assert "2.1.0" in compiled_prompt
        assert "relationships" in compiled_prompt

        # Verify API was called correctly
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "/api/v1/graph/nodes/service-prod-api" in call_args[0][0]

        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "UserKey test-api-key"
        assert headers["X-Organization-ID"] == "test-org-123"

    @patch('httpx.Client')
    def test_e2e_mixed_template_variables(self, mock_client_cls):
        """Test system prompt with mixed variable types: simple, secret, env, graph."""
        # Mock graph node
        user_node = {
            "id": "user-john",
            "properties": {"name": "John Doe", "email": "john@example.com"}
        }

        mock_response = MagicMock()
        mock_response.json.return_value = user_node

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        system_prompt = """
Agent: {{agent_name}}
API Key: {{.secret.api_key}}
Environment: {{.env.ENVIRONMENT}}
User Context: {{.graph.user-john}}
"""

        context = TemplateContext(
            variables={"agent_name": "TestAgent"},
            secrets={"api_key": "secret-key-123"},
            env_vars={"ENVIRONMENT": "staging"},
            graph_api_base="https://graph.kubiya.ai",
            graph_api_key="test-key"
        )

        compiled = resolve_templates(system_prompt, context, strict=False)

        # All variables should be resolved
        assert "TestAgent" in compiled
        assert "secret-key-123" in compiled
        assert "staging" in compiled
        assert "john@example.com" in compiled

    @patch('httpx.Client')
    def test_e2e_multiple_graph_nodes_caching(self, mock_client_cls):
        """Test that multiple references to same node only fetch once (caching)."""
        node_data = {"id": "repo-1", "name": "Backend Repo"}

        mock_response = MagicMock()
        mock_response.json.return_value = node_data

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        system_prompt = """
Primary repo: {{.graph.repo-1}}
Also check: {{.graph.repo-1}}
And again: {{.graph.repo-1}}
"""

        context = TemplateContext(
            graph_api_base="https://graph.kubiya.ai",
            graph_api_key="test-key"
        )

        compiled = resolve_templates(system_prompt, context)

        # Should appear 3 times in output
        assert compiled.count("Backend Repo") == 3

        # But API should only be called ONCE due to caching
        assert mock_client.get.call_count == 1

    @patch('httpx.Client')
    def test_e2e_node_not_found_404(self, mock_client_cls):
        """Test handling of non-existent nodes (404)."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=mock_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        system_prompt = "Service: {{.graph.nonexistent-service}}"

        context = TemplateContext(
            graph_api_base="https://graph.kubiya.ai",
            graph_api_key="test-key"
        )

        # Should fail with descriptive error
        compiler = TemplateCompiler()
        result = compiler.compile(system_prompt, context)

        assert not result.success
        assert "nonexistent-service" in result.error
        assert "not found" in result.error.lower()

    @patch('httpx.Client')
    def test_e2e_pre_populated_graph_nodes(self, mock_client_cls):
        """Test using pre-populated graph nodes (no API call needed)."""
        system_prompt = "User: {{.graph.user-alice}}"

        # Pre-populate node in context (e.g., from a previous fetch)
        context = TemplateContext(
            graph_nodes={
                "user-alice": {
                    "id": "user-alice",
                    "name": "Alice Smith",
                    "role": "admin"
                }
            }
        )

        compiled = resolve_templates(system_prompt, context)

        # Should compile successfully
        assert "Alice Smith" in compiled
        assert "admin" in compiled

        # No API call should be made
        mock_client_cls.assert_not_called()

    def test_e2e_graph_node_without_api_config_fails(self):
        """Test that graph nodes fail gracefully without API configuration."""
        system_prompt = "Service: {{.graph.service-1}}"

        # No API configuration
        context = TemplateContext(
            variables={},
            secrets={},
            env_vars={}
        )

        compiler = TemplateCompiler()
        result = compiler.compile(system_prompt, context)

        assert not result.success
        assert "service-1" in result.error
        assert "not configured" in result.error.lower()

    @patch('httpx.Client')
    def test_e2e_complex_node_with_relationships(self, mock_client_cls):
        """Test complex node with full metadata and relationships."""
        complex_node = {
            "id": "kubernetes-cluster-prod",
            "labels": ["Cluster", "Kubernetes", "Production"],
            "properties": {
                "name": "Production K8s Cluster",
                "version": "1.28.3",
                "region": "us-east-1",
                "node_count": 15,
                "created_at": "2023-01-15T10:30:00Z"
            },
            "relationships": {
                "incoming": [
                    {
                        "type": "DEPLOYED_TO",
                        "from": "service-api",
                        "properties": {"namespace": "production"}
                    },
                    {
                        "type": "DEPLOYED_TO",
                        "from": "service-worker",
                        "properties": {"namespace": "production"}
                    }
                ],
                "outgoing": [
                    {
                        "type": "MONITORS",
                        "to": "prometheus-prod",
                        "properties": {"scrape_interval": "30s"}
                    },
                    {
                        "type": "LOGS_TO",
                        "to": "elasticsearch-prod",
                        "properties": {}
                    }
                ]
            },
            "metadata": {
                "last_updated": "2024-12-01T15:45:00Z",
                "integration": "aws",
                "sync_status": "active"
            }
        }

        mock_response = MagicMock()
        mock_response.json.return_value = complex_node

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        system_prompt = """
You are managing:
{{.graph.kubernetes-cluster-prod}}

Ensure all operations are production-safe.
"""

        context = TemplateContext(
            graph_api_base="https://graph.kubiya.ai",
            graph_api_key="test-key"
        )

        compiled = resolve_templates(system_prompt, context)

        # Verify all complex data is present
        assert "Production K8s Cluster" in compiled
        assert "1.28.3" in compiled
        assert "us-east-1" in compiled
        assert "DEPLOYED_TO" in compiled
        assert "service-api" in compiled
        assert "MONITORS" in compiled
        assert "prometheus-prod" in compiled
        assert "elasticsearch-prod" in compiled
        assert "metadata" in compiled

    @patch('httpx.Client')
    def test_e2e_multiple_different_nodes(self, mock_client_cls):
        """Test system prompt with multiple different graph nodes."""
        # Mock responses for different nodes
        def mock_get(url, **kwargs):
            response = MagicMock()
            if "service-api" in url:
                response.json.return_value = {
                    "id": "service-api",
                    "properties": {"name": "API Service", "port": 8080}
                }
            elif "database-prod" in url:
                response.json.return_value = {
                    "id": "database-prod",
                    "properties": {"name": "Prod Database", "type": "PostgreSQL"}
                }
            elif "user-admin" in url:
                response.json.return_value = {
                    "id": "user-admin",
                    "properties": {"name": "Admin User", "email": "admin@example.com"}
                }
            return response

        mock_client = MagicMock()
        mock_client.get.side_effect = mock_get
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        system_prompt = """
Service: {{.graph.service-api}}
Database: {{.graph.database-prod}}
Admin: {{.graph.user-admin}}
"""

        context = TemplateContext(
            graph_api_base="https://graph.kubiya.ai",
            graph_api_key="test-key"
        )

        compiled = resolve_templates(system_prompt, context)

        # All three nodes should be present
        assert "API Service" in compiled
        assert "8080" in compiled
        assert "Prod Database" in compiled
        assert "PostgreSQL" in compiled
        assert "Admin User" in compiled
        assert "admin@example.com" in compiled

        # Should make 3 API calls (one per unique node)
        assert mock_client.get.call_count == 3

    @patch('httpx.Client')
    def test_e2e_graceful_degradation_with_skip_on_error(self, mock_client_cls):
        """Test graceful degradation when skip_on_error=True."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=MagicMock(),
            response=mock_response
        )
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        system_prompt = "Service: {{.graph.service-1}} with {{user}} access"

        context = TemplateContext(
            variables={"user": "john"},
            graph_api_base="https://graph.kubiya.ai",
            graph_api_key="test-key"
        )

        # With skip_on_error=True, should return original template on error
        compiled = resolve_templates(
            system_prompt,
            context,
            strict=False,
            skip_on_error=True
        )

        # Should return original (graceful degradation)
        assert compiled == system_prompt

    @patch.dict(os.environ, {
        "CONTEXT_GRAPH_API_BASE": "https://test-graph.example.com",
        "KUBIYA_API_KEY": "env-api-key-456",
        "KUBIYA_ORG_ID": "env-org-789"
    })
    @patch('httpx.Client')
    def test_e2e_uses_environment_variables(self, mock_client_cls):
        """Test that executor uses environment variables for graph API config."""
        node_data = {"id": "test-node", "name": "Test"}

        mock_response = MagicMock()
        mock_response.json.return_value = node_data

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        system_prompt = "Node: {{.graph.test-node}}"

        # Simulate what agent executor does
        context = TemplateContext(
            graph_api_base=os.environ.get("CONTEXT_GRAPH_API_BASE", "https://graph.kubiya.ai"),
            graph_api_key=os.environ.get("KUBIYA_API_KEY"),
            graph_org_id=os.environ.get("KUBIYA_ORG_ID")
        )

        compiled = resolve_templates(system_prompt, context)

        # Verify it used environment variables
        call_args = mock_client.get.call_args
        assert "https://test-graph.example.com" in call_args[0][0]

        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "UserKey env-api-key-456"
        assert headers["X-Organization-ID"] == "env-org-789"


class TestGraphTemplateValidation:
    """E2E tests for template validation with graph nodes."""

    def test_e2e_validation_syntax_check(self):
        """Test validation catches invalid graph node syntax."""
        from control_plane_api.app.lib.templating.validator import TemplateValidator

        validator = TemplateValidator()

        # Valid syntax
        valid_templates = [
            "{{.graph.node-1}}",
            "{{.graph.service.prod}}",
            "{{.graph.user_123}}",
            "{{.graph.a.b.c-d_e}}"
        ]

        for template in valid_templates:
            context = TemplateContext(
                graph_api_base="https://graph.kubiya.ai",
                graph_api_key="test-key"
            )
            result = validator.validate(template, context)
            assert result.valid, f"Template should be valid: {template}"

    def test_e2e_validation_missing_api_config(self):
        """Test validation detects missing API configuration."""
        from control_plane_api.app.lib.templating.validator import TemplateValidator

        validator = TemplateValidator()
        template = "{{.graph.node-1}}"

        # Missing API config
        context = TemplateContext()

        result = validator.validate(template, context)
        assert not result.valid
        assert len(result.errors) == 1
        assert result.errors[0].code == "MISSING_GRAPH_NODE"
        assert "node-1" in result.missing_graph_nodes


class TestGraphTemplateWithRealResolver:
    """E2E tests using the actual resolve_templates function."""

    @patch('httpx.Client')
    def test_resolve_templates_integration(self, mock_client_cls):
        """Test resolve_templates function with graph nodes."""
        node_data = {
            "id": "integration-test",
            "properties": {"status": "active"}
        }

        mock_response = MagicMock()
        mock_response.json.return_value = node_data

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        template = "Status: {{.graph.integration-test}}"

        context = TemplateContext(
            graph_api_base="https://graph.kubiya.ai",
            graph_api_key="test-key"
        )

        # Use the actual resolver
        result = resolve_templates(template, context)

        assert "active" in result
        assert node_data["id"] in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
