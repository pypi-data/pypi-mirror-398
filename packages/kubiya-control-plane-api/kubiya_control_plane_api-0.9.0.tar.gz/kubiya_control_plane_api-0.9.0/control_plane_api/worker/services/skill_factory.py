"""
Skill Factory - Dynamic skill loading with zero hardcoding

This factory discovers and instantiates skills dynamically from multiple sources
without any hardcoded if/elif chains. Works across all runtimes (agno, claude_code, etc.).
"""
from typing import Optional, Any, List
from pathlib import Path
import structlog
import os

from control_plane_api.worker.skills import (
    SkillRegistry,
    skill_registry,
    FilesystemSkillLoader,
    LoadedSkill,
)
from control_plane_api.worker.utils.tool_validation import (
    validate_and_sanitize_tools,
    is_valid_tool_name,
)

logger = structlog.get_logger()


class SkillFactory:
    """
    Dynamic skill factory with zero hardcoding.

    Discovers and instantiates skills from multiple sources automatically.
    No hardcoded if/elif chains required.
    """

    def __init__(self, runtime_type: str = "agno"):
        """
        Initialize the skill factory.

        Args:
            runtime_type: Runtime type (e.g., "agno", "claude_code")
        """
        self.runtime_type = runtime_type
        self.registry: SkillRegistry = skill_registry
        self.loaders = []
        self._initialized = False

        logger.info(
            "skill_factory_initialized",
            runtime_type=runtime_type,
        )

    def _validate_skill_tools(self, skill_instance: Any, skill_name: str) -> Optional[Any]:
        """
        Validate and sanitize tool names from a skill instance.

        This ensures ALL tools from ANY source meet universal LLM provider requirements.

        Args:
            skill_instance: The skill toolkit instance
            skill_name: Name of the skill for logging

        Returns:
            The skill instance with validated tools, or None if validation fails critically
        """
        # Try to extract tools from the skill instance
        tools = []

        # Handle Agno Toolkit objects
        if hasattr(skill_instance, 'tools'):
            tools = skill_instance.tools
        # Handle dict format (builtin skills)
        elif isinstance(skill_instance, dict) and 'tools' in skill_instance:
            tools = skill_instance['tools']
        # Handle iterable of tools
        elif hasattr(skill_instance, '__iter__') and not isinstance(skill_instance, (str, dict)):
            try:
                tools = list(skill_instance)
            except:
                pass

        if not tools:
            # No tools to validate or can't extract them
            return skill_instance

        # Validate and sanitize tool names
        def get_tool_name(tool):
            """Extract tool name from various tool formats."""
            if hasattr(tool, 'name'):
                return tool.name
            elif isinstance(tool, dict):
                return tool.get('name', tool.get('function', {}).get('name', str(tool)))
            elif hasattr(tool, '__name__'):
                return tool.__name__
            return str(tool)

        validated_tools, validation_report = validate_and_sanitize_tools(
            tools,
            tool_name_getter=get_tool_name,
            auto_fix=True,
            provider_context=self.runtime_type
        )

        # Log validation results
        sanitized_count = sum(1 for r in validation_report if r['action'] == 'sanitized')
        filtered_count = sum(1 for r in validation_report if r['action'] == 'filtered')

        if sanitized_count > 0:
            logger.warning(
                "skill_tools_sanitized",
                skill=skill_name,
                runtime=self.runtime_type,
                sanitized_count=sanitized_count,
                total_tools=len(tools),
                details=[r for r in validation_report if r['action'] == 'sanitized']
            )

        if filtered_count > 0:
            logger.error(
                "skill_tools_filtered",
                skill=skill_name,
                runtime=self.runtime_type,
                filtered_count=filtered_count,
                total_tools=len(tools),
                details=[r for r in validation_report if r['action'] == 'filtered']
            )

        # Update the skill instance with validated tools
        if hasattr(skill_instance, 'tools'):
            skill_instance.tools = validated_tools
        elif isinstance(skill_instance, dict) and 'tools' in skill_instance:
            skill_instance['tools'] = validated_tools

        return skill_instance

    def initialize(self):
        """
        Initialize the factory by discovering skills from all sources.

        Call this once during worker startup.
        """
        if self._initialized:
            logger.debug("skill_factory_already_initialized")
            return

        logger.info("skill_factory_initializing")

        # Setup loaders
        self._setup_loaders()

        # Discover skills
        self._discover_skills()

        self._initialized = True

        # Log statistics
        stats = self.registry.get_stats()
        logger.info(
            "skill_factory_initialized",
            total_skills=stats["total_skills"],
            by_source=stats["skills_by_source"],
            by_type=stats["skills_by_type"],
        )

    def _setup_loaders(self):
        """Setup skill loaders from different sources."""
        # 1. Filesystem loader (user skills)
        search_paths = []

        # Project skills (.kubiya/skills in current working directory)
        project_skills = Path.cwd() / ".kubiya/skills"
        if project_skills.exists():
            search_paths.append(project_skills)

        # User global skills (~/.kubiya/skills)
        user_skills = Path.home() / ".kubiya/skills"
        if user_skills.exists():
            search_paths.append(user_skills)

        # Built-in skills (in package directory)
        builtin_skills = Path(__file__).parent.parent / "skills" / "builtin"
        if builtin_skills.exists():
            search_paths.append(builtin_skills)

        if search_paths:
            fs_loader = FilesystemSkillLoader(search_paths)
            self.loaders.append(fs_loader)
            logger.info("filesystem_loader_configured", paths=[str(p) for p in search_paths])

        # TODO: Add API loader for Control Plane skills
        # TODO: Add package loader for pip-installed skills
        # TODO: Add git loader for remote skills

    def _discover_skills(self):
        """Discover skills from all loaders."""
        for loader in self.loaders:
            try:
                skills = loader.discover()

                for skill in skills:
                    # Check dependencies
                    missing = self.registry.resolve_dependencies(skill)
                    if missing:
                        logger.warning(
                            "skill_missing_dependencies",
                            skill=skill.name,
                            missing=missing,
                        )
                        # Register anyway - could still be usable

                    # Register
                    self.registry.register(skill)

            except Exception as e:
                logger.error(
                    "skill_discovery_failed",
                    loader=loader.__class__.__name__,
                    error=str(e),
                    exc_info=True,
                )

    def create_skill(self, skill_data: dict) -> Optional[Any]:
        """
        Create a skill toolkit from configuration.

        No hardcoded mappings - uses registry for discovery.

        Args:
            skill_data: Skill config from Control Plane:
                - name: Skill name (e.g., "slack-notifier")
                - type: Skill type (e.g., "shell", "file_system", "custom")
                - configuration: Dict with skill-specific config
                - enabled: Whether skill is enabled
                - execution_id: Optional execution ID for streaming

        Returns:
            Instantiated skill toolkit or None
        """
        # Ensure factory is initialized
        if not self._initialized:
            self.initialize()

        if not skill_data.get("enabled", True):
            logger.info("skill_disabled", name=skill_data.get("name"))
            return None

        skill_name = skill_data.get("name")
        skill_type = skill_data.get("type", "custom")
        config = skill_data.get("configuration", {})
        execution_id = skill_data.get("execution_id")

        # Try to find skill by name first
        loaded_skill = self.registry.get(skill_name)

        # If not found by name, try by type (for built-in skills)
        if not loaded_skill:
            loaded_skill = self.registry.get_by_type(skill_type)

        if not loaded_skill:
            logger.warning(
                "skill_not_found_in_registry",
                name=skill_name,
                type=skill_type,
                available_skills=[s.name for s in self.registry.list_skills()],
            )
            return None

        # Get runtime-appropriate implementation
        impl = self.registry.get_implementation_for_runtime(
            loaded_skill, self.runtime_type
        )

        if not impl:
            logger.error(
                "no_implementation_for_runtime",
                skill=loaded_skill.name,
                runtime=self.runtime_type,
                available_runtimes=list(loaded_skill.implementations.keys()),
            )
            return None

        # Check if this is a builtin implementation (like Claude Code SDK tools)
        if isinstance(impl, dict) and impl.get("builtin"):
            builtin_tools = impl.get("tools", [])

            logger.info(
                "skill_builtin",
                skill=loaded_skill.name,
                runtime=self.runtime_type,
                tools=builtin_tools,
            )

            # For builtin skills, return metadata - runtime handles tool mapping
            builtin_skill_dict = {
                "skill_name": loaded_skill.name,
                "skill_type": loaded_skill.skill_type,
                "builtin": True,
                "tools": builtin_tools,
                "config": config,
            }

            # UNIVERSAL VALIDATION: Validate builtin tool names
            validated_builtin = self._validate_skill_tools(builtin_skill_dict, loaded_skill.name)
            return validated_builtin

        # Prepare configuration for Python class instantiation
        instantiation_config = config.copy()

        # Inject workspace directory for file/shell skills if not explicitly set
        if loaded_skill.skill_type in ["file_system", "shell", "bash", "file", "file_generation"]:
            from control_plane_api.worker.utils.workspace_manager import (
                ensure_workspace,
                should_use_custom_base_directory,
            )

            # Only inject workspace if user hasn't explicitly set base_directory
            if execution_id and not should_use_custom_base_directory(skill_data):
                try:
                    workspace_path = ensure_workspace(execution_id)
                    if workspace_path:
                        instantiation_config["base_directory"] = str(workspace_path)

                        logger.info(
                            "skill_using_execution_workspace",
                            skill=loaded_skill.name,
                            execution_id=execution_id[:8] if len(execution_id) >= 8 else execution_id,
                            workspace=str(workspace_path),
                        )
                except Exception as e:
                    logger.warning(
                        "workspace_creation_failed_for_skill",
                        skill=loaded_skill.name,
                        execution_id=execution_id[:8] if len(execution_id) >= 8 else execution_id,
                        error=str(e),
                        error_type=type(e).__name__,
                        fallback="using_default_or_current_directory",
                    )
                    # Continue without workspace injection - skill will use its default

        # Inject execution_id if provided
        if execution_id:
            instantiation_config['execution_id'] = execution_id

        # Inject other runtime-specific config
        # (e.g., API keys from environment variables)
        self._inject_env_vars(instantiation_config, loaded_skill)

        # Instantiate with configuration
        try:
            instance = impl(**instantiation_config)

            logger.info(
                "skill_instantiated",
                skill=loaded_skill.name,
                runtime=self.runtime_type,
                implementation=impl.__name__,
            )

            # UNIVERSAL VALIDATION: Validate all tool names before returning
            validated_instance = self._validate_skill_tools(instance, loaded_skill.name)

            return validated_instance

        except Exception as e:
            logger.error(
                "skill_instantiation_failed",
                skill=loaded_skill.name,
                error=str(e),
                exc_info=True,
            )

            # Note: Error event publishing removed to avoid asyncio event loop issues
            # The error is already logged above and the skill will be skipped
            # This prevents "bound to a different event loop" errors in synchronous contexts

            return None

    def create_skills_from_list(
        self, skill_configs: List[dict], execution_id: Optional[str] = None
    ) -> List[Any]:
        """
        Create multiple skills from configurations.

        Args:
            skill_configs: List of skill config dicts
            execution_id: Optional execution ID to inject into all skills

        Returns:
            List of instantiated skills (non-None)
        """
        skills = []

        for config in skill_configs:
            # Inject execution_id if provided
            if execution_id:
                config = config.copy()
                config['execution_id'] = execution_id

            skill = self.create_skill(config)
            if skill:
                skills.append(skill)

        logger.info(
            "skills_batch_created",
            requested=len(skill_configs),
            created=len(skills),
        )

        return skills

    def _inject_env_vars(self, config: dict, skill: LoadedSkill):
        """
        Inject environment variables into skill configuration.

        Looks for environment variables defined in skill manifest.
        """
        env_vars = skill.manifest.get("spec", {}).get("environmentVariables", [])

        for env_var_def in env_vars:
            var_name = env_var_def.get("name")
            required = env_var_def.get("required", False)

            # Check if already in config
            if var_name.lower() in config or var_name in config:
                continue

            # Try to get from environment
            env_value = os.environ.get(var_name)

            if env_value:
                # Convert env var name to config key (lowercase)
                config_key = var_name.lower()
                config[config_key] = env_value
                logger.debug(
                    "injected_env_var",
                    skill=skill.name,
                    var_name=var_name,
                )
            elif required:
                logger.warning(
                    "required_env_var_missing",
                    skill=skill.name,
                    var_name=var_name,
                )

    def get_available_skills(self) -> List[str]:
        """Get list of all available skill names."""
        if not self._initialized:
            self.initialize()

        return [skill.name for skill in self.registry.list_skills()]

    def get_skill_info(self, skill_name: str) -> Optional[dict]:
        """Get information about a specific skill."""
        if not self._initialized:
            self.initialize()

        skill = self.registry.get(skill_name)
        if not skill:
            return None

        return {
            "name": skill.name,
            "version": skill.version,
            "type": skill.skill_type,
            "source": skill.source.value,
            "runtimes": list(skill.implementations.keys()),
            "metadata": skill.manifest.get("metadata", {}),
        }

# Backward compatibility alias
# Old code using SkillFactoryV2 will still work
SkillFactoryV2 = SkillFactory
