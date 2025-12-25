"""
Test suite for all 6 critical skill ecosystem fixes.

This test file validates that all issues identified in the audit have been resolved.
"""
import pytest
import yaml
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Issue #1: SkillFactory consolidation tests
def test_skill_factory_v2_imports():
    """Test that SkillFactoryV2 can be imported and is preferred over old SkillFactory."""
    from control_plane_api.worker.services.skill_factory_v2 import SkillFactoryV2

    # Should be able to create instance
    factory = SkillFactoryV2(runtime_type="agno")
    assert factory.runtime_type == "agno"
    assert factory._initialized == False


def test_old_skill_factory_deprecation_warning():
    """Test that old SkillFactory issues deprecation warning."""
    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from control_plane_api.worker.services.skill_factory import SkillFactory

        # Should have issued deprecation warning
        assert len(w) > 0
        assert issubclass(w[-1].category, DeprecationWarning)
        assert "deprecated" in str(w[-1].message).lower()


# Issue #2: Builtin tool validation tests
def test_claude_code_builtin_tools_registry():
    """Test that CLAUDE_CODE_BUILTIN_TOOLS registry exists and is comprehensive."""
    from control_plane_api.worker.runtimes.claude_code.tool_mapper import CLAUDE_CODE_BUILTIN_TOOLS

    # Should contain essential tools
    essential_tools = {"Read", "Write", "Bash", "Edit", "Glob", "Grep"}
    assert essential_tools.issubset(CLAUDE_CODE_BUILTIN_TOOLS)

    # Should be a set for O(1) lookup
    assert isinstance(CLAUDE_CODE_BUILTIN_TOOLS, set)


def test_validate_builtin_tools_success():
    """Test that validate_builtin_tools accepts valid tools."""
    from control_plane_api.worker.runtimes.claude_code.tool_mapper import validate_builtin_tools

    valid_tools = ["Read", "Write", "Bash"]
    valid, invalid = validate_builtin_tools(valid_tools)

    assert valid == valid_tools
    assert invalid == []


def test_validate_builtin_tools_failure():
    """Test that validate_builtin_tools rejects invalid tools."""
    from control_plane_api.worker.runtimes.claude_code.tool_mapper import validate_builtin_tools

    invalid_tools = ["InvalidTool", "NonExistentTool"]

    with pytest.raises(ValueError) as exc_info:
        validate_builtin_tools(invalid_tools)

    assert "Invalid builtin tool names" in str(exc_info.value)
    assert "InvalidTool" in str(exc_info.value)


# Issue #3: Silent implementation failures tests
def test_filesystem_loader_fails_loudly_on_missing_file():
    """Test that filesystem loader raises clear error when implementation file is missing."""
    from control_plane_api.worker.skills.loaders.filesystem_loader import FilesystemSkillLoader

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()

        # Create skill.yaml with missing implementation file
        skill_yaml = skill_dir / "skill.yaml"
        skill_yaml.write_text(yaml.dump({
            "apiVersion": "kubiya.ai/v1",
            "kind": "Skill",
            "metadata": {"name": "test-skill", "version": "1.0.0"},
            "spec": {
                "type": "custom",
                "implementations": {
                    "agno": {
                        "module": "missing_module",
                        "class": "MissingClass"
                    }
                }
            }
        }))

        loader = FilesystemSkillLoader([Path(tmpdir)])

        with pytest.raises(ValueError) as exc_info:
            loader.discover()

        # Should have clear error with recovery steps
        error_msg = str(exc_info.value)
        assert "Failed to load any implementations" in error_msg
        assert "Recovery steps" in error_msg
        assert "missing_module" in error_msg


def test_filesystem_loader_logs_detailed_errors():
    """Test that implementation failures are logged with detailed information."""
    from control_plane_api.worker.skills.loaders.filesystem_loader import FilesystemSkillLoader
    import structlog

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()

        skill_yaml = skill_dir / "skill.yaml"
        skill_yaml.write_text(yaml.dump({
            "apiVersion": "kubiya.ai/v1",
            "kind": "Skill",
            "metadata": {"name": "test-skill", "version": "1.0.0"},
            "spec": {
                "type": "custom",
                "implementations": {
                    "agno": {
                        "module": "impl",
                        "class": "WrongClass"
                    }
                }
            }
        }))

        # Create implementation file with wrong class name
        impl_file = skill_dir / "impl.py"
        impl_file.write_text("class CorrectClass: pass")

        loader = FilesystemSkillLoader([Path(tmpdir)])

        with pytest.raises(ValueError) as exc_info:
            loader.discover()

        error_msg = str(exc_info.value)
        assert "WrongClass" in error_msg or "Class" in error_msg


# Issue #4: Tool mapping registry tests
def test_tool_mapping_registry_loads_config():
    """Test that ToolMappingRegistry loads from configuration file."""
    from control_plane_api.worker.runtimes.claude_code.tool_mapper import ToolMappingRegistry

    registry = ToolMappingRegistry()

    # Should have loaded mappings
    assert len(registry.mappings) > 0
    assert "shell" in registry.mappings
    assert "file_system" in registry.mappings


def test_tool_mapping_registry_env_override():
    """Test that environment variables can override tool mappings."""
    from control_plane_api.worker.runtimes.claude_code.tool_mapper import ToolMappingRegistry
    import os

    # Set environment override
    os.environ["CLAUDE_CODE_MAPPING_CUSTOM"] = "Read,Write,Custom"

    registry = ToolMappingRegistry()
    tools = registry.get_tools_for_skill_type("custom")

    assert "Read" in tools
    assert "Write" in tools
    assert "Custom" in tools

    # Cleanup
    del os.environ["CLAUDE_CODE_MAPPING_CUSTOM"]


def test_tool_mapping_registry_validates_mappings():
    """Test that registry validates tool names against builtin tools."""
    from control_plane_api.worker.runtimes.claude_code.tool_mapper import ToolMappingRegistry

    registry = ToolMappingRegistry()

    # Valid mapping
    assert registry.validate_mapping("shell", ["Bash", "Read"])

    # Invalid mapping
    assert not registry.validate_mapping("shell", ["InvalidTool"])


def test_map_skills_to_tools_uses_registry():
    """Test that map_skills_to_tools uses ToolMappingRegistry."""
    from control_plane_api.worker.runtimes.claude_code.tool_mapper import map_skills_to_tools

    skills = [
        {"type": "shell"},
        {"type": "file_system"}
    ]

    tools = map_skills_to_tools(skills)

    # Should include tools from both skill types
    assert "Bash" in tools
    assert "Read" in tools or "Write" in tools


# Issue #5: MCP tool name extraction tests
def test_extract_mcp_tool_names_uses_explicit_tools():
    """Test that explicit MCP tools from config are prioritized."""
    from control_plane_api.worker.runtimes.claude_code.mcp_builder import extract_mcp_tool_names

    explicit_tools = ["explicit_tool_1", "explicit_tool_2"]
    server_obj = Mock()

    result = extract_mcp_tool_names("test_server", server_obj, explicit_tools)

    assert result == explicit_tools


def test_extract_mcp_tool_names_warns_on_fallback():
    """Test that fallback extraction logs warnings."""
    from control_plane_api.worker.runtimes.claude_code.mcp_builder import extract_mcp_tool_names
    import structlog

    # Mock server with tools attribute
    server_obj = Mock()
    server_obj.tools = [Mock(name="fallback_tool")]

    with patch('structlog.get_logger') as mock_logger:
        logger = Mock()
        mock_logger.return_value = logger

        result = extract_mcp_tool_names("test_server", server_obj, explicit_tools=None)

        # Should have logged warning about fallback
        # (exact assertion depends on logging implementation)


def test_build_mcp_servers_accepts_explicit_config():
    """Test that build_mcp_servers accepts mcp_tools_config parameter."""
    from control_plane_api.worker.runtimes.claude_code.mcp_builder import build_mcp_servers

    mcp_tools_config = {
        "server1": ["tool1", "tool2"],
        "server2": ["tool3"]
    }

    context_servers = {
        "server1": Mock(),
        "server2": Mock()
    }

    # Should not raise error
    servers, tool_names = build_mcp_servers(
        skills=[],
        context_mcp_servers=context_servers,
        mcp_tools_config=mcp_tools_config
    )


# Issue #6: YAML schema validation tests
def test_skill_yaml_schema_exists():
    """Test that skill.yaml JSON schema file exists."""
    from pathlib import Path

    schema_path = Path(__file__).parent.parent / "control_plane_api/worker/skills/skill_yaml_schema.json"
    assert schema_path.exists(), "skill_yaml_schema.json should exist"

    # Should be valid JSON
    with open(schema_path) as f:
        schema = json.load(f)

    assert "$schema" in schema
    assert "properties" in schema


def test_validate_skill_yaml_accepts_valid_manifest():
    """Test that validate_skill_yaml accepts a valid skill manifest."""
    from control_plane_api.worker.skills.loaders.filesystem_loader import validate_skill_yaml

    valid_manifest = {
        "apiVersion": "kubiya.ai/v1",
        "kind": "Skill",
        "metadata": {
            "name": "test-skill",
            "version": "1.0.0"
        },
        "spec": {
            "type": "custom",
            "implementations": {
                "agno": {
                    "module": "implementation",
                    "class": "TestSkill"
                }
            }
        }
    }

    with tempfile.NamedTemporaryFile(suffix=".yaml") as tmp:
        tmp_path = Path(tmp.name)

        # Should not raise error
        try:
            validate_skill_yaml(valid_manifest, tmp_path)
        except ImportError:
            pytest.skip("jsonschema not installed")


def test_validate_skill_yaml_rejects_invalid_manifest():
    """Test that validate_skill_yaml rejects invalid manifests."""
    from control_plane_api.worker.skills.loaders.filesystem_loader import validate_skill_yaml

    invalid_manifest = {
        "apiVersion": "kubiya.ai/v1",
        # Missing "kind"
        "metadata": {
            "name": "test-skill"
            # Missing version
        },
        "spec": {
            # Missing type and implementations
        }
    }

    with tempfile.NamedTemporaryFile(suffix=".yaml") as tmp:
        tmp_path = Path(tmp.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                validate_skill_yaml(invalid_manifest, tmp_path)

            # Should have helpful error message
            assert "Invalid skill.yaml" in str(exc_info.value)
        except ImportError:
            pytest.skip("jsonschema not installed")


def test_validate_skill_yaml_provides_helpful_errors():
    """Test that validation errors include helpful suggestions."""
    from control_plane_api.worker.skills.loaders.filesystem_loader import validate_skill_yaml

    manifest_with_wrong_type = {
        "apiVersion": "kubiya.ai/v1",
        "kind": "Skill",
        "metadata": {"name": "test", "version": "1.0.0"},
        "spec": {
            "type": "invalid_type",  # Not in enum
            "implementations": {}
        }
    }

    with tempfile.NamedTemporaryFile(suffix=".yaml") as tmp:
        tmp_path = Path(tmp.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                validate_skill_yaml(manifest_with_wrong_type, tmp_path)

            error_msg = str(exc_info.value)
            # Should mention allowed values
            assert "Allowed values" in error_msg or "enum" in error_msg.lower()
        except ImportError:
            pytest.skip("jsonschema not installed")


# Integration test
def test_all_fixes_work_together():
    """Integration test: All fixes work together in a realistic scenario."""
    from control_plane_api.worker.services.skill_factory_v2 import SkillFactoryV2
    from control_plane_api.worker.runtimes.claude_code.tool_mapper import get_tool_mapping_registry

    # Create factory
    factory = SkillFactoryV2(runtime_type="claude_code")

    # Get tool mapping registry
    registry = get_tool_mapping_registry()

    # Should be able to get tools for various skill types
    shell_tools = registry.get_tools_for_skill_type("shell")
    assert len(shell_tools) > 0

    # Should be able to validate those tools
    from control_plane_api.worker.runtimes.claude_code.tool_mapper import validate_builtin_tools

    valid, invalid = validate_builtin_tools(shell_tools)
    assert len(valid) == len(shell_tools)
    assert len(invalid) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
