"""Integration tests for ContextGraphSearchTools with both runtimes."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import asyncio

# Add worker to sys.path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.builtin.context_graph_search.agno_impl import ContextGraphSearchTools
from services.skill_factory import SkillFactory


class TestContextGraphSearchAgnoIntegration:
    """Integration tests for ContextGraphSearchTools with Agno runtime"""

    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Set up environment variables for testing"""
        monkeypatch.setenv("KUBIYA_API_KEY", "test_api_key_123")
        monkeypatch.setenv("CONTEXT_GRAPH_API_BASE", "https://test-graph.kubiya.ai")
        monkeypatch.setenv("KUBIYA_ORG_ID", "test_org_123")

    @pytest.fixture
    def skill_factory(self):
        """Create SkillFactory instance"""
        factory = SkillFactory(runtime_type="agno")
        factory.initialize()
        return factory

    def test_skill_factory_creates_context_graph_tools(self, skill_factory, mock_env_vars):
        """Test that SkillFactory can create ContextGraphSearchTools"""
        skill_configs = [
            {
                "name": "context_graph_search",
                "type": "context_graph_search",
                "enabled": True,
                "configuration": {}
            }
        ]

        skills = skill_factory.create_skills_from_list(skill_configs)

        assert len(skills) == 1
        assert type(skills[0]).__name__ == 'ContextGraphSearchTools'

    def test_skill_factory_with_custom_config(self, skill_factory, mock_env_vars):
        """Test SkillFactory creates tools with custom configuration"""
        skill_configs = [
            {
                "name": "context_graph_search",
                "type": "context_graph_search",
                "enabled": True,
                "configuration": {
                    "timeout": 60,
                    "default_limit": 50
                }
            }
        ]

        skills = skill_factory.create_skills_from_list(skill_configs)

        assert len(skills) == 1
        tool = skills[0]
        assert tool.timeout == 60
        assert tool.default_limit == 50

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_agno_runtime_tool_execution(self, mock_client_class, mock_env_vars):
        """Test executing a tool in Agno runtime context"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "labels": ["User", "Repository", "Service"]
        }

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Create tool instance
        tools = ContextGraphSearchTools()

        # Execute tool method
        result = tools.get_labels()

        # Verify result
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "labels" in parsed
        assert len(parsed["labels"]) == 3

        # Verify HTTP call was made correctly
        mock_client.__enter__.return_value.get.assert_called_once()
        call_args = mock_client.__enter__.return_value.get.call_args
        assert "https://test-graph.kubiya.ai/api/v1/graph/labels" in call_args[0][0]

    def test_toolkit_integration_with_agno_functions(self, mock_env_vars):
        """Test that toolkit properly registers functions for Agno"""
        tools = ContextGraphSearchTools()

        # Verify toolkit has functions attribute (required by Agno)
        assert hasattr(tools, "functions")
        assert isinstance(tools.functions, dict)
        assert len(tools.functions) >= 9

        # Verify each function has proper structure
        for func_name, func_obj in tools.functions.items():
            # Verify function object has required attributes
            assert hasattr(func_obj, "entrypoint"), f"{func_name} missing entrypoint"
            assert callable(func_obj.entrypoint), f"{func_name} entrypoint not callable"

            # Verify function has description
            description = getattr(func_obj, "description", None) or func_obj.entrypoint.__doc__
            assert description, f"{func_name} missing description"


class TestContextGraphSearchClaudeCodeIntegration:
    """Integration tests for ContextGraphSearchTools with Claude Code runtime"""

    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Set up environment variables for testing"""
        monkeypatch.setenv("KUBIYA_API_KEY", "test_api_key_123")
        monkeypatch.setenv("CONTEXT_GRAPH_API_BASE", "https://test-graph.kubiya.ai")

    @pytest.fixture
    def skill_factory(self):
        """Create SkillFactory instance for Claude Code"""
        factory = SkillFactory(runtime_type="claude_code")
        factory.initialize()
        return factory

    def test_skill_factory_creates_tools_for_claude_code(self, skill_factory, mock_env_vars):
        """Test that SkillFactory can create tools for Claude Code runtime"""
        skill_configs = [
            {
                "name": "context_graph_search",
                "type": "context_graph_search",
                "enabled": True,
                "configuration": {}
            }
        ]

        skills = skill_factory.create_skills_from_list(skill_configs)

        assert len(skills) == 1
        assert type(skills[0]).__name__ == 'ContextGraphSearchTools'

    @pytest.mark.asyncio
    async def test_mcp_conversion(self, mock_env_vars):
        """Test that tools can be converted to MCP server format"""
        from runtimes.claude_code.mcp_builder import build_mcp_servers

        # Create skill instance
        tools = ContextGraphSearchTools()

        # Convert to MCP servers
        mcp_servers, _ = build_mcp_servers(skills=[tools])

        # Verify MCP server was created
        assert "context-graph-search" in mcp_servers
        mcp_server = mcp_servers["context-graph-search"]

        # Verify it's a valid MCP server object
        assert mcp_server is not None

    def test_toolkit_functions_for_mcp_conversion(self, mock_env_vars):
        """Test that toolkit functions can be converted to MCP tools"""
        tools = ContextGraphSearchTools()

        # Verify functions registry exists (required for MCP conversion)
        assert hasattr(tools, "functions")
        assert len(tools.functions) >= 9

        # Each function should have the structure needed for MCP conversion
        expected_tools = [
            "search_nodes",
            "get_node",
            "get_relationships",
            "get_subgraph",
            "search_by_text",
            "execute_query",
            "get_labels",
            "get_relationship_types",
            "get_stats"
        ]

        for tool_name in expected_tools:
            assert tool_name in tools.functions
            func_obj = tools.functions[tool_name]

            # Verify function has entrypoint (required for MCP wrapping)
            assert hasattr(func_obj, "entrypoint")
            assert callable(func_obj.entrypoint)

            # Verify function has metadata (description, parameters)
            assert hasattr(func_obj, "description") or func_obj.entrypoint.__doc__

    @pytest.mark.asyncio
    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    async def test_mcp_tool_execution(self, mock_client_class, mock_env_vars):
        """Test executing a tool through MCP wrapper"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "nodes": [{"id": "node1", "label": "User"}]
        }

        mock_client = MagicMock()
        mock_client.__enter__.return_value.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Create tool instance
        tools = ContextGraphSearchTools()

        # Get the function from registry
        search_func = tools.functions["search_nodes"]
        entrypoint = search_func.entrypoint

        # Execute through entrypoint (simulating MCP call)
        result = entrypoint(label="User")

        # Verify result is JSON string
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "nodes" in parsed


class TestContextGraphSearchSkillDiscovery:
    """Test skill discovery and loading mechanisms"""

    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Set up environment variables"""
        monkeypatch.setenv("KUBIYA_API_KEY", "test_key")

    def test_skill_yaml_exists(self):
        """Test that skill.yaml file exists and is valid"""
        from pathlib import Path
        skill_dir = Path(__file__).parent.parent.parent / "skills" / "builtin" / "context_graph_search"
        skill_yaml = skill_dir / "skill.yaml"

        assert skill_yaml.exists(), "skill.yaml not found"

        # Try to parse it
        import yaml
        with open(skill_yaml) as f:
            skill_def = yaml.safe_load(f)

        # Verify required fields
        assert skill_def["apiVersion"] == "kubiya.ai/v1"
        assert skill_def["kind"] == "Skill"
        assert skill_def["metadata"]["name"] == "context-graph-search"
        assert skill_def["spec"]["type"] == "context_graph_search"

        # Verify implementations
        assert "agno" in skill_def["spec"]["implementations"]
        assert "claude_code" in skill_def["spec"]["implementations"]

    def test_agno_impl_exists(self):
        """Test that agno_impl.py exists and exports ContextGraphSearchTools"""
        from pathlib import Path
        skill_dir = Path(__file__).parent.parent.parent / "skills" / "builtin" / "context_graph_search"
        agno_impl = skill_dir / "agno_impl.py"

        assert agno_impl.exists(), "agno_impl.py not found"

        # Verify it can be imported
        from skills.builtin.context_graph_search.agno_impl import ContextGraphSearchTools
        assert ContextGraphSearchTools is not None

    def test_skill_factory_can_discover_skill(self, mock_env_vars):
        """Test that SkillFactory can discover the context_graph_search skill"""
        factory = SkillFactory(runtime_type="agno")
        factory.initialize()

        # Try to create the skill
        skill_configs = [
            {
                "name": "context_graph_search",
                "type": "context_graph_search",
                "enabled": True,
                "configuration": {}
            }
        ]

        skills = factory.create_skills_from_list(skill_configs)

        # Verify skill was created
        assert len(skills) == 1
        assert type(skills[0]).__name__ == 'ContextGraphSearchTools'

    def test_skill_can_be_imported(self):
        """Test that skill can be imported from __init__.py"""
        from skills.builtin.context_graph_search import ContextGraphSearchTools
        assert ContextGraphSearchTools is not None


class TestContextGraphSearchErrorHandling:
    """Test error handling and edge cases"""

    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Set up environment variables"""
        monkeypatch.setenv("KUBIYA_API_KEY", "test_key")
        monkeypatch.setenv("CONTEXT_GRAPH_API_BASE", "https://test-graph.api")

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_network_error_handling(self, mock_client_class, mock_env_vars):
        """Test handling of network errors"""
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = Exception("Network error")
        mock_client_class.return_value = mock_client

        tools = ContextGraphSearchTools()

        with pytest.raises(Exception, match="Request failed"):
            tools.get_labels()

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_invalid_json_response(self, mock_client_class, mock_env_vars):
        """Test handling of invalid JSON responses"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        tools = ContextGraphSearchTools()

        with pytest.raises(Exception):
            tools.get_labels()

    def test_missing_api_key(self, monkeypatch):
        """Test behavior when API key is missing"""
        monkeypatch.delenv("KUBIYA_API_KEY", raising=False)

        # Should still create tools but with warning
        tools = ContextGraphSearchTools()
        assert tools.api_key is None

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_empty_response_handling(self, mock_client_class, mock_env_vars):
        """Test handling of empty responses"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        tools = ContextGraphSearchTools()
        result = tools.get_labels()

        # Should still return valid JSON string
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == {}
