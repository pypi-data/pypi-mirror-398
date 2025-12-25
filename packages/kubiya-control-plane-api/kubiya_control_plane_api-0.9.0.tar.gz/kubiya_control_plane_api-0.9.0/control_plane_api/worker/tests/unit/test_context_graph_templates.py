"""Unit tests for context graph node template support."""
import pytest
from unittest.mock import patch, MagicMock
import httpx
from control_plane_api.app.lib.templating.parsers.graph import GraphNodeParser
from control_plane_api.app.lib.templating.types import (
    TemplateVariableType,
    TemplateContext,
)
from control_plane_api.app.lib.templating.engine import get_default_engine
from control_plane_api.app.lib.templating.compiler import TemplateCompiler
from control_plane_api.app.lib.templating.validator import TemplateValidator


class TestGraphNodeParser:
    """Test GraphNodeParser for {{.graph.node-id}} syntax."""

    def test_parser_matches_valid_graph_syntax(self):
        """Test that parser matches valid graph node syntax."""
        parser = GraphNodeParser()
        template = "Check {{.graph.user-123}} for details"

        match = parser.pattern.search(template)
        assert match is not None
        assert match.group(1) == "user-123"

    def test_parser_extracts_node_id(self):
        """Test that parser correctly extracts node ID."""
        parser = GraphNodeParser()
        template = "Node: {{.graph.service.prod}}"

        result = list(parser.parse(template))
        assert len(result) == 1
        assert result[0].name == "graph.service.prod"
        assert result[0].display_name == "service.prod"
        assert result[0].type == TemplateVariableType.GRAPH

    def test_parser_validates_node_id_format(self):
        """Test node ID validation rules."""
        parser = GraphNodeParser()

        # Valid IDs
        assert parser.validate_node_id("a")
        assert parser.validate_node_id("abc123")
        assert parser.validate_node_id("user-123")
        assert parser.validate_node_id("service_prod")
        assert parser.validate_node_id("repo.main")
        assert parser.validate_node_id("a.b.c-d_e")

        # Invalid IDs
        assert not parser.validate_node_id("")
        assert not parser.validate_node_id("-start")
        assert not parser.validate_node_id("end-")
        assert not parser.validate_node_id(".start")
        assert not parser.validate_node_id("end.")
        assert not parser.validate_node_id("has space")
        assert not parser.validate_node_id("has@special")

    def test_parser_handles_multiple_graph_vars(self):
        """Test parsing template with multiple graph variables."""
        parser = GraphNodeParser()
        template = "User {{.graph.user-1}} owns {{.graph.repo-2}}"

        result = list(parser.parse(template))
        assert len(result) == 2
        assert result[0].display_name == "user-1"
        assert result[1].display_name == "repo-2"

    def test_parser_returns_correct_positions(self):
        """Test that parser returns correct start/end positions."""
        parser = GraphNodeParser()
        template = "Start {{.graph.node-1}} middle {{.graph.node-2}} end"

        result = list(parser.parse(template))
        assert len(result) == 2

        # First variable
        assert template[result[0].start:result[0].end] == "{{.graph.node-1}}"

        # Second variable
        assert template[result[1].start:result[1].end] == "{{.graph.node-2}}"


class TestGraphNodeIntegrationWithEngine:
    """Test graph node parser integration with template engine."""

    def test_engine_detects_graph_variables(self):
        """Test that default engine detects graph variables."""
        engine = get_default_engine()
        template = "Check {{.graph.user-123}} status"

        parse_result = engine.parse(template)
        assert parse_result.is_valid
        assert len(parse_result.graph_variables) == 1
        assert parse_result.graph_variables[0].display_name == "user-123"

    def test_engine_handles_mixed_variable_types(self):
        """Test engine with mixed variable types."""
        engine = get_default_engine()
        template = "{{user}} from {{.graph.org-1}} using {{.secret.token}} in {{.env.ENV}}"

        parse_result = engine.parse(template)
        assert parse_result.is_valid
        assert len(parse_result.simple_variables) == 1
        assert len(parse_result.graph_variables) == 1
        assert len(parse_result.secret_variables) == 1
        assert len(parse_result.env_variables) == 1

    def test_graph_parser_registered_in_default_parsers(self):
        """Test that GraphNodeParser is in DEFAULT_PARSERS."""
        from control_plane_api.app.lib.templating.parsers import DEFAULT_PARSERS

        parser_types = [type(p).__name__ for p in DEFAULT_PARSERS]
        assert "GraphNodeParser" in parser_types


class TestGraphNodeValidator:
    """Test validation of graph node templates."""

    def test_validator_accepts_graph_with_api_config(self):
        """Test validator accepts graph vars when API is configured."""
        validator = TemplateValidator()
        template = "Check {{.graph.user-123}}"

        context = TemplateContext(
            graph_api_base="https://graph.kubiya.ai",
            graph_api_key="test-key",
            graph_org_id="test-org"
        )

        result = validator.validate(template, context)
        assert result.valid
        assert len(result.errors) == 0

    def test_validator_accepts_graph_in_context(self):
        """Test validator accepts graph vars when node is in context."""
        validator = TemplateValidator()
        template = "Check {{.graph.user-123}}"

        context = TemplateContext(
            graph_nodes={
                "user-123": {"id": "user-123", "name": "Test User"}
            }
        )

        result = validator.validate(template, context)
        assert result.valid
        assert len(result.errors) == 0

    def test_validator_rejects_graph_without_config(self):
        """Test validator rejects graph vars without API config or context."""
        validator = TemplateValidator()
        template = "Check {{.graph.user-123}}"

        context = TemplateContext()  # No graph config

        result = validator.validate(template, context)
        assert not result.valid
        assert len(result.errors) == 1
        assert result.errors[0].code == "MISSING_GRAPH_NODE"
        assert "user-123" in result.errors[0].message

    def test_validator_error_includes_node_id(self):
        """Test that validation error includes node ID."""
        validator = TemplateValidator()
        template = "{{.graph.missing-node}}"

        context = TemplateContext()

        result = validator.validate(template, context)
        assert not result.valid
        assert "missing-node" in result.missing_graph_nodes


class TestGraphNodeCompiler:
    """Test compilation of graph node templates."""

    def test_compiler_uses_node_from_context(self):
        """Test compiler uses pre-populated node from context."""
        compiler = TemplateCompiler()
        template = "User: {{.graph.user-123}}"

        node_data = {
            "id": "user-123",
            "name": "Test User",
            "email": "test@example.com"
        }

        context = TemplateContext(
            graph_nodes={"user-123": node_data}
        )

        result = compiler.compile(template, context)
        assert result.success
        assert "user-123" in result.compiled
        assert "Test User" in result.compiled
        assert "test@example.com" in result.compiled

    @patch('httpx.Client')
    def test_compiler_fetches_node_from_api(self, mock_client_cls):
        """Test compiler fetches node from API when not in context."""
        # Mock the httpx client
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "user-456",
            "name": "API User",
            "properties": {"role": "admin"}
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        compiler = TemplateCompiler()
        template = "User: {{.graph.user-456}}"

        context = TemplateContext(
            graph_api_base="https://graph.kubiya.ai",
            graph_api_key="test-key",
            graph_org_id="test-org"
        )

        result = compiler.compile(template, context)
        assert result.success
        assert "user-456" in result.compiled
        assert "API User" in result.compiled

        # Verify API was called correctly
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "/api/v1/graph/nodes/user-456" in call_args[0][0]

        # Verify headers
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "UserKey test-key"
        assert headers["X-Organization-ID"] == "test-org"

    @patch('httpx.Client')
    def test_compiler_caches_fetched_nodes(self, mock_client_cls):
        """Test that compiler caches fetched nodes in context."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "node-1", "name": "Test"}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        compiler = TemplateCompiler()
        template = "Node {{.graph.node-1}} again {{.graph.node-1}}"

        context = TemplateContext(
            graph_api_base="https://graph.kubiya.ai",
            graph_api_key="test-key"
        )

        result = compiler.compile(template, context)
        assert result.success

        # Should only call API once (second ref uses cache)
        assert mock_client.get.call_count == 1

        # Verify node is cached
        assert "node-1" in context.graph_nodes
        assert context.graph_nodes["node-1"]["name"] == "Test"

    @patch('httpx.Client')
    def test_compiler_handles_404_not_found(self, mock_client_cls):
        """Test compiler handles 404 for non-existent nodes."""
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

        compiler = TemplateCompiler()
        template = "{{.graph.missing-node}}"

        context = TemplateContext(
            graph_api_base="https://graph.kubiya.ai",
            graph_api_key="test-key"
        )

        result = compiler.compile(template, context)
        assert not result.success
        assert "missing-node" in result.error
        assert "not found" in result.error.lower()

    @patch('httpx.Client')
    def test_compiler_handles_api_errors(self, mock_client_cls):
        """Test compiler handles API errors gracefully."""
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

        compiler = TemplateCompiler()
        template = "{{.graph.node-1}}"

        context = TemplateContext(
            graph_api_base="https://graph.kubiya.ai",
            graph_api_key="test-key"
        )

        result = compiler.compile(template, context)
        assert not result.success
        assert "HTTP 500" in result.error

    def test_compiler_formats_node_as_json(self):
        """Test that compiler formats node data as JSON."""
        compiler = TemplateCompiler()
        template = "{{.graph.node-1}}"

        node_data = {
            "id": "node-1",
            "properties": {"key": "value"},
            "relationships": []
        }

        context = TemplateContext(
            graph_nodes={"node-1": node_data}
        )

        result = compiler.compile(template, context)
        assert result.success

        # Should be valid JSON
        import json
        parsed = json.loads(result.compiled)
        assert parsed["id"] == "node-1"
        assert parsed["properties"]["key"] == "value"


class TestGraphNodeEdgeCases:
    """Test edge cases for graph node templates."""

    def test_empty_graph_nodes_dict(self):
        """Test handling of empty graph_nodes dict."""
        validator = TemplateValidator()
        template = "{{.graph.node-1}}"

        context = TemplateContext(
            graph_nodes={},  # Empty dict
            graph_api_base="https://graph.kubiya.ai",
            graph_api_key="test-key"
        )

        # Should still be valid (will fetch from API)
        result = validator.validate(template, context)
        assert result.valid

    def test_graph_node_with_special_characters(self):
        """Test node IDs with allowed special characters."""
        parser = GraphNodeParser()
        template = "{{.graph.service.prod-2023_v1}}"

        result = list(parser.parse(template))
        assert len(result) == 1
        assert result[0].display_name == "service.prod-2023_v1"

    def test_multiple_dots_in_node_id(self):
        """Test node ID with multiple dots."""
        parser = GraphNodeParser()
        template = "{{.graph.a.b.c.d}}"

        result = list(parser.parse(template))
        assert len(result) == 1
        assert result[0].display_name == "a.b.c.d"

    def test_compilation_without_org_id(self):
        """Test compilation works without org_id (optional)."""
        compiler = TemplateCompiler()
        template = "{{.graph.node-1}}"

        context = TemplateContext(
            graph_nodes={"node-1": {"id": "node-1"}},
            # No org_id
        )

        result = compiler.compile(template, context)
        assert result.success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
