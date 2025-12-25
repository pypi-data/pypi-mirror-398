"""Integration tests for builtin skills fixes (import errors, data_visualization, MCP)."""
import pytest
import asyncio
from control_plane_api.worker.services.skill_factory import SkillFactory
from control_plane_api.worker.runtimes.claude_code.mcp_discovery import discover_mcp_resources


class TestImportFixes:
    """Test that import errors are fixed."""

    def test_agent_executor_v2_imports(self):
        """Test that agent_executor_v2 imports correctly."""
        from control_plane_api.worker.services.agent_executor_v2 import AgentExecutorServiceV2
        assert AgentExecutorServiceV2 is not None

    def test_team_executor_v2_imports(self):
        """Test that team_executor_v2 imports correctly."""
        from control_plane_api.worker.services.team_executor_v2 import TeamExecutorServiceV2
        assert TeamExecutorServiceV2 is not None


class TestDataVisualizationSkillRestoration:
    """Test that data_visualization skill is properly restored."""

    def test_data_visualization_skill_yaml_exists(self):
        """Test that skill.yaml exists."""
        import os
        skill_yaml_path = "control_plane_api/worker/skills/builtin/data_visualization/skill.yaml"
        assert os.path.exists(skill_yaml_path), "skill.yaml should exist"

    def test_data_visualization_agno_impl_exists(self):
        """Test that agno_impl.py exists."""
        import os
        agno_impl_path = "control_plane_api/worker/skills/builtin/data_visualization/agno_impl.py"
        assert os.path.exists(agno_impl_path), "agno_impl.py should exist"

    def test_data_visualization_imports(self):
        """Test that data_visualization skill imports correctly."""
        from control_plane_api.worker.skills.builtin.data_visualization.agno_impl import DataVisualizationTools
        assert DataVisualizationTools is not None

    def test_data_visualization_toolkit_instantiation(self):
        """Test that data_visualization toolkit can be instantiated."""
        from control_plane_api.worker.skills.builtin.data_visualization.agno_impl import DataVisualizationTools

        toolkit = DataVisualizationTools(
            enable_flowchart=True,
            enable_sequence=True,
            max_diagram_size=50000
        )

        assert toolkit is not None
        assert hasattr(toolkit, 'functions'), "Toolkit should have functions attribute"

        # Should have 11 diagram tools
        tool_count = len(toolkit.functions)
        assert tool_count == 11, f"Expected 11 tools, got {tool_count}"

    def test_data_visualization_skill_loading_agno(self):
        """Test that data_visualization skill loads correctly in agno runtime."""
        factory = SkillFactory(runtime_type="agno")
        factory.initialize()

        skill_config = {
            "name": "data-visualization",
            "type": "data_visualization",
            "enabled": True,
            "configuration": {
                "enable_flowchart": True,
                "max_diagram_size": 50000
            }
        }

        skill = factory.create_skill(skill_config)
        assert skill is not None, "Skill should be created"
        assert hasattr(skill, 'functions'), "Skill should have functions"
        assert len(skill.functions) == 11, f"Should have 11 tools, got {len(skill.functions)}"

    def test_data_visualization_skill_loading_claude_code(self):
        """Test that data_visualization skill loads correctly in claude_code runtime."""
        factory = SkillFactory(runtime_type="claude_code")
        factory.initialize()

        skill_config = {
            "name": "data-visualization",
            "type": "data_visualization",
            "enabled": True,
            "configuration": {
                "enable_flowchart": True,
                "max_diagram_size": 50000
            }
        }

        skill = factory.create_skill(skill_config)
        assert skill is not None, "Skill should be created"
        # For claude_code, it should be a toolkit instance that will be converted to MCP
        assert hasattr(skill, 'functions'), "Skill should have functions for MCP conversion"

    def test_data_visualization_with_execution_id(self):
        """Test that data_visualization skill accepts execution_id parameter."""
        factory = SkillFactory(runtime_type="claude_code")
        factory.initialize()

        skill_config = {
            "name": "data-visualization",
            "type": "data_visualization",
            "enabled": True,
            "configuration": {
                "enable_flowchart": True,
                "max_diagram_size": 50000
            },
            "execution_id": "test-exec-123"  # This was causing the failure
        }

        skill = factory.create_skill(skill_config)
        assert skill is not None, "Skill should be created even with execution_id"
        assert hasattr(skill, 'functions'), "Skill should have functions"
        assert len(skill.functions) == 11, "Should have all 11 diagram tools"


class TestContextGraphSearchMCPFix:
    """Test that context_graph_search MCP verification is fixed."""

    @pytest.mark.asyncio
    async def test_sdk_mcp_server_object_handling(self):
        """Test that SDK MCP server objects are handled correctly (not treated as config dicts)."""
        from claude_agent_sdk import create_sdk_mcp_server, tool as mcp_tool

        # Create a simple SDK MCP server
        @mcp_tool("test_tool", "A test tool", {"arg": str})
        async def test_tool(args: dict) -> dict:
            return {"result": "test"}

        sdk_server = create_sdk_mcp_server(
            name="test-server",
            version="1.0.0",
            tools=[test_tool]
        )

        # This should NOT raise an error - it should skip pre-discovery
        result = await discover_mcp_resources("test-server", sdk_server)

        assert result["server_name"] == "test-server"
        # SDK servers are skipped, which means connected=True and skipped=True
        assert result.get("skipped") == True, "SDK MCP server should be skipped"
        # If skipped, connected should be True (means "will work")
        if result.get("skipped"):
            assert result["connected"] == True, "Skipped SDK servers should report as connected"
        assert "error" not in result or result["error"] is None

    @pytest.mark.asyncio
    async def test_context_graph_search_mcp_creation(self):
        """Test that context_graph_search skill creates MCP server successfully."""
        from control_plane_api.worker.runtimes.claude_code.mcp_builder import build_mcp_servers
        from control_plane_api.worker.services.skill_factory import SkillFactory

        # Create skill instance
        factory = SkillFactory(runtime_type="claude_code")
        factory.initialize()

        skill_config = {
            "name": "context-graph-search",
            "type": "context_graph_search",
            "enabled": True,
            "configuration": {}
        }

        skill = factory.create_skill(skill_config)
        assert skill is not None

        # Build MCP servers
        mcp_servers, _ = build_mcp_servers([skill], {})

        assert "context-graph-search" in mcp_servers, "Should create MCP server for context-graph-search"

        # Verify the server can be discovered without errors
        server = mcp_servers["context-graph-search"]
        result = await discover_mcp_resources("context-graph-search", server)

        # SDK servers should be skipped
        assert result.get("skipped") == True, "SDK MCP servers should be skipped"
        # If skipped, connected should be True
        if result.get("skipped"):
            assert result["connected"] == True, "Skipped SDK servers should report as connected"


class TestSkillFactoryAutoInclude:
    """Test that context_graph_search is auto-included correctly."""

    def test_context_graph_search_auto_include(self):
        """Test that context_graph_search is properly auto-included."""
        skill_configs = []

        # Auto-include logic from executor
        builtin_skill_types = {'context_graph_search'}
        existing_skill_types = {cfg.get('type') for cfg in skill_configs}

        for builtin_type in builtin_skill_types:
            if builtin_type not in existing_skill_types:
                builtin_config = {
                    'name': builtin_type,
                    'type': builtin_type,
                    'enabled': True,
                    'configuration': {}
                }
                skill_configs.append(builtin_config)

        assert len(skill_configs) == 1
        assert skill_configs[0]['type'] == 'context_graph_search'

        # Now try to load it
        factory = SkillFactory(runtime_type="claude_code")
        factory.initialize()

        skill = factory.create_skill(skill_configs[0])
        assert skill is not None


class TestSkillRegistryStats:
    """Test that skill registry has expected skills."""

    def test_builtin_skills_registered(self):
        """Test that all expected builtin skills are registered."""
        factory = SkillFactory(runtime_type="agno")
        factory.initialize()

        stats = factory.registry.get_stats()

        # Should have these builtin skills (using underscores - that's how they're registered)
        expected_skills = {
            'shell', 'file_system', 'python', 'docker',
            'data_visualization',  # Restored!
            'context_graph_search',  # Note: underscore, not hyphen
            'workflow_executor', 'file_generation'
        }

        registered_skills = set(stats['skills_by_type'].keys())

        for skill in expected_skills:
            assert skill in registered_skills, f"Expected skill '{skill}' not registered. Registered: {registered_skills}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
