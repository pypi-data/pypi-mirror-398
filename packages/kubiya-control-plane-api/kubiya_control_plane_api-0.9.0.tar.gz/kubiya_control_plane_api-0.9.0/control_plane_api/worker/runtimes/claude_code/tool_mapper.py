"""
Tool mapping module for Claude Code runtime.

This module handles the translation of generic skill types to specific
Claude Code SDK tool names, with validation and error handling.

BUG FIX #6: Added tool name validation before adding to allowed_tools.
Issue #4 Fix: Externalized tool mappings to configuration file.
"""

from typing import List, Tuple, Set, Dict, Optional
import structlog
import yaml
import os
from pathlib import Path

logger = structlog.get_logger(__name__)


# Known builtin Claude Code tools from SDK documentation
# This registry is the source of truth for validating builtin tool existence
CLAUDE_CODE_BUILTIN_TOOLS: Set[str] = {
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "Bash",
    "BashOutput",
    "KillShell",
    "WebFetch",
    "WebSearch",
    "Task",
    "NotebookEdit",
    "TodoWrite",
    "ExitPlanMode",
    "AskUserQuestion",
    "Skill",
    "SlashCommand",
    # MCP resource tools (both naming conventions)
    "ListMcpResources",
    "ReadMcpResource",
    "mcp__list_resources",
    "mcp__read_resource",
}

# Backward compatibility alias
KNOWN_BUILTIN_TOOLS: Set[str] = CLAUDE_CODE_BUILTIN_TOOLS

# DEPRECATED: Hardcoded mapping (kept for backward compatibility)
# Use ToolMappingRegistry instead
SKILL_TO_TOOL_MAPPING = {
    "shell": ["Bash", "BashOutput", "KillShell"],
    "file_system": ["Read", "Write", "Edit", "Glob", "Grep"],
    "web": ["WebFetch", "WebSearch"],
    "docker": ["Bash"],  # Docker commands via Bash
    "kubernetes": ["Bash"],  # kubectl via Bash
    "git": ["Bash"],  # git commands via Bash
    "task": ["Task"],  # Subagent tasks
    "notebook": ["NotebookEdit"],
    "planning": ["TodoWrite", "ExitPlanMode"],
}


class ToolMappingRegistry:
    """
    Issue #4 Fix: Dynamic tool mapping registry with configuration file support.

    This class loads tool mappings from a YAML configuration file instead of
    hardcoding them, making the system more maintainable and extensible.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the tool mapping registry.

        Args:
            config_path: Optional path to configuration file.
                        Defaults to tool_mapping_config.yaml in this directory.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.mappings: Dict[str, List[str]] = {}
        self.default_tools: List[str] = []
        self.overrides: Dict[str, Dict[str, List[str]]] = {}
        self._load_config()

    def _get_default_config_path(self) -> Path:
        """Get path to default configuration file."""
        return Path(__file__).parent / "tool_mapping_config.yaml"

    def _load_config(self):
        """Load mappings from configuration file."""
        try:
            # Check for environment variable override
            env_config_path = os.environ.get("CLAUDE_CODE_TOOL_MAPPING_CONFIG")
            if env_config_path:
                config_path = Path(env_config_path)
                logger.info(
                    "using_tool_mapping_config_from_env",
                    path=str(config_path),
                )
            else:
                config_path = self.config_path

            if not config_path.exists():
                logger.warning(
                    "tool_mapping_config_not_found",
                    path=str(config_path),
                    fallback="using hardcoded mappings",
                )
                self._load_fallback_mappings()
                return

            with open(config_path) as f:
                config = yaml.safe_load(f)

            self.mappings = config.get("skill_type_mappings", {})
            self.default_tools = config.get("default_tools", ["Read", "Write", "Bash"])
            self.overrides = config.get("overrides", {})

            logger.info(
                "tool_mapping_config_loaded",
                path=str(config_path),
                skill_types=list(self.mappings.keys()),
                default_tools=self.default_tools,
            )

        except Exception as e:
            logger.error(
                "failed_to_load_tool_mapping_config",
                path=str(self.config_path),
                error=str(e),
                fallback="using hardcoded mappings",
                exc_info=True,
            )
            self._load_fallback_mappings()

    def _load_fallback_mappings(self):
        """Load fallback hardcoded mappings."""
        self.mappings = SKILL_TO_TOOL_MAPPING.copy()
        self.default_tools = ["Read", "Write", "Bash"]
        logger.debug("using_fallback_hardcoded_mappings")

    def get_tools_for_skill_type(self, skill_type: str) -> List[str]:
        """
        Get Claude Code tools for a skill type.

        Args:
            skill_type: Generic skill type (e.g., "file_system", "shell")

        Returns:
            List of Claude Code tool names
        """
        # Check for environment variable override first
        env_key = f"CLAUDE_CODE_MAPPING_{skill_type.upper()}"
        env_override = os.environ.get(env_key)
        if env_override:
            tools = [t.strip() for t in env_override.split(",")]
            logger.debug(
                "using_env_override_for_skill_type",
                skill_type=skill_type,
                tools=tools,
                env_key=env_key,
            )
            return tools

        # Check configuration
        tools = self.mappings.get(skill_type, [])
        if not tools:
            logger.warning(
                "no_mapping_for_skill_type",
                skill_type=skill_type,
                available_types=list(self.mappings.keys()),
            )

        return tools

    def get_default_tools(self) -> List[str]:
        """Get default tools when no specific skill types are provided."""
        # Check for environment variable override
        env_default = os.environ.get("CLAUDE_CODE_DEFAULT_TOOLS")
        if env_default:
            tools = [t.strip() for t in env_default.split(",")]
            logger.debug("using_env_override_for_default_tools", tools=tools)
            return tools

        return self.default_tools

    def validate_mapping(self, skill_type: str, tools: List[str]) -> bool:
        """
        Validate that all tools in a mapping exist in CLAUDE_CODE_BUILTIN_TOOLS.

        Args:
            skill_type: Skill type being validated
            tools: List of tool names

        Returns:
            True if all tools are valid, False otherwise
        """
        invalid_tools = [t for t in tools if t not in CLAUDE_CODE_BUILTIN_TOOLS]
        if invalid_tools:
            logger.error(
                "invalid_tools_in_mapping",
                skill_type=skill_type,
                invalid_tools=invalid_tools,
                valid_tools=sorted(CLAUDE_CODE_BUILTIN_TOOLS),
            )
            return False
        return True

    def reload_config(self):
        """Reload configuration from file."""
        logger.info("reloading_tool_mapping_config")
        self._load_config()


# Global registry instance
_tool_mapping_registry: Optional[ToolMappingRegistry] = None


def get_tool_mapping_registry() -> ToolMappingRegistry:
    """
    Get the global tool mapping registry instance.

    Returns:
        ToolMappingRegistry instance
    """
    global _tool_mapping_registry
    if _tool_mapping_registry is None:
        _tool_mapping_registry = ToolMappingRegistry()
    return _tool_mapping_registry


def map_skills_to_tools(skills: list) -> List[str]:
    """
    Map skills to Claude Code tool names.

    This function translates generic skill types to the specific
    tool names that Claude Code SDK understands.

    Issue #4 Fix: Now uses ToolMappingRegistry instead of hardcoded mappings.

    Args:
        skills: List of skill objects

    Returns:
        List of Claude Code tool names (deduplicated)
    """
    registry = get_tool_mapping_registry()
    tools = []

    for skill in skills:
        # Get skill type
        skill_type = None
        if hasattr(skill, "type"):
            skill_type = skill.type
        elif isinstance(skill, dict):
            skill_type = skill.get("type")

        # Map to Claude Code tools using registry
        if skill_type:
            mapped_tools = registry.get_tools_for_skill_type(skill_type)
            if mapped_tools:
                tools.extend(mapped_tools)

    # Deduplicate and add default tools if none specified
    if tools:
        unique_tools = list(set(tools))
    else:
        unique_tools = registry.get_default_tools()

    logger.info(
        "mapped_skills_to_claude_code_tools",
        skill_count=len(skills),
        tool_count=len(unique_tools),
        tools=unique_tools,
    )

    return unique_tools


def validate_builtin_tools(tool_names: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validate that builtin tool names exist in Claude Code SDK.

    Issue #2 Fix: This function ensures Claude Code builtin tools are validated
    before being used, preventing runtime errors.

    Args:
        tool_names: List of builtin tool names to validate

    Returns:
        Tuple of (valid_tools, invalid_tools)

    Raises:
        ValueError: If any builtin tool doesn't exist in CLAUDE_CODE_BUILTIN_TOOLS
    """
    valid = []
    invalid = []

    for tool_name in tool_names:
        if tool_name in CLAUDE_CODE_BUILTIN_TOOLS:
            valid.append(tool_name)
        else:
            invalid.append(tool_name)

    if invalid:
        error_msg = (
            f"Invalid builtin tool names detected: {invalid}. "
            f"These tools don't exist in Claude Code SDK. "
            f"Valid builtin tools are: {sorted(CLAUDE_CODE_BUILTIN_TOOLS)}"
        )
        logger.error(
            "invalid_builtin_tools_detected",
            invalid_tools=invalid,
            valid_tools=valid,
            available_tools=sorted(CLAUDE_CODE_BUILTIN_TOOLS),
        )
        raise ValueError(error_msg)

    logger.debug(
        "builtin_tools_validated",
        tool_count=len(valid),
        tools=valid,
    )

    return valid, invalid


def validate_tool_names(tool_names: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validate tool names before adding to allowed_tools.

    BUG FIX #6: This function ensures only valid tool names are used.

    Args:
        tool_names: List of tool names to validate

    Returns:
        Tuple of (valid_tools, invalid_tools)
    """
    valid = []
    invalid = []

    for tool_name in tool_names:
        # Builtin tools or MCP tools (mcp__ prefix) are valid
        if tool_name in KNOWN_BUILTIN_TOOLS or tool_name.startswith("mcp__"):
            valid.append(tool_name)
        else:
            invalid.append(tool_name)

    if invalid:
        logger.warning(
            "invalid_tool_names_filtered",
            invalid_tools=invalid,
            valid_count=len(valid),
            invalid_count=len(invalid),
            message="These tools will be filtered out as they're not recognized",
        )

    return valid, invalid


def sanitize_tool_name(name: str) -> str:
    """
    Sanitize a tool name to meet universal LLM provider requirements.

    Uses the universal validator to ensure compatibility across all providers.

    Args:
        name: Tool name to sanitize

    Returns:
        Sanitized tool name that works for all LLM providers
    """
    from control_plane_api.worker.utils.tool_validation import sanitize_tool_name as universal_sanitize
    return universal_sanitize(name)


def construct_mcp_tool_name(server_name: str, tool_name: str = None) -> str:
    """
    Construct a full MCP tool name following the naming convention.

    Convention: mcp__<server_name>__<tool_name>

    Args:
        server_name: Name of the MCP server
        tool_name: Optional tool name. If omitted, only server name is used.

    Returns:
        Full MCP tool name (sanitized)
    """
    sanitized_server = sanitize_tool_name(server_name)

    if tool_name:
        sanitized_tool = sanitize_tool_name(tool_name)
        # Avoid duplication: mcp__run_ado_test not mcp__run_ado_test__run_ado_test
        if sanitized_tool == sanitized_server:
            return f"mcp__{sanitized_server}"
        else:
            return f"mcp__{sanitized_server}__{sanitized_tool}"
    else:
        return f"mcp__{sanitized_server}"
