"""
Skill Context Enhancement for System Prompts.

This enhancement extracts context information from skill configurations
and injects it into the system prompt to provide agents with usage guidelines
and environment awareness.
"""

from typing import Optional, List, Dict, Any
import structlog

from control_plane_api.worker.services.system_prompt_enhancement import (
    SystemPromptEnhancement,
    RuntimeType,
)

logger = structlog.get_logger(__name__)


class SkillContextEnhancement(SystemPromptEnhancement):
    """
    Inject skill context (usage guidelines, environment info) into system prompt.

    This enhancement reads skill configurations passed via RuntimeExecutionContext
    and generates formatted context sections that help the agent understand:
    - How to use specific skills effectively
    - Environment-specific information
    - Custom shell configurations

    The enhancement is designed to work with skill configurations that include:
    - usage_guidelines: Optional[str] - Instructions for using the skill
    - environment_context: Optional[str] - Environment-specific information
    - shell_binary: Optional[str] - Custom shell binary path
    - shell_args: Optional[List[str]] - Shell arguments
    """

    def __init__(self, skill_configs: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize skill context enhancement.

        Args:
            skill_configs: List of skill configuration dictionaries.
                          If None, no context will be injected.
        """
        # Apply to all runtimes
        super().__init__(runtime_types=[RuntimeType.ALL])
        self.skill_configs = skill_configs or []

    @property
    def name(self) -> str:
        return "skill_context"

    def enhance(self, base_prompt: Optional[str]) -> str:
        """
        Enhance system prompt with skill context information.

        Args:
            base_prompt: The base system prompt

        Returns:
            Enhanced prompt with skill context sections
        """
        if not self.skill_configs:
            # No skills configured - return base prompt unchanged
            return base_prompt or ""

        # Extract skills with context information
        skills_with_context = [
            skill for skill in self.skill_configs
            if self._has_context_fields(skill)
        ]

        if not skills_with_context:
            # No skills have context fields - return base prompt unchanged
            logger.debug(
                "skill_context_enhancement_skipped",
                reason="no_skills_with_context_fields",
                total_skills=len(self.skill_configs),
            )
            return base_prompt or ""

        # Build context sections
        context_parts = []
        context_parts.append("")  # Blank line before section
        context_parts.append("---")
        context_parts.append("")
        context_parts.append("# Skill Context & Usage Guidelines")
        context_parts.append("")
        context_parts.append(
            "The following skills have been configured with specific usage "
            "guidelines and environment information to help you use them effectively:"
        )
        context_parts.append("")

        for skill in skills_with_context:
            try:
                skill_name = skill.get("name", "Unknown Skill")
                skill_type = skill.get("type", "unknown")
                config = skill.get("configuration", {})

                # Add skill header
                context_parts.append(f"## {skill_name}")
                context_parts.append("")

                # Add usage guidelines if present
                usage_guidelines = config.get("usage_guidelines", "").strip()
                if usage_guidelines:
                    context_parts.append("**Usage Guidelines:**")
                    context_parts.append("")
                    # Handle multi-line guidelines
                    for line in usage_guidelines.split("\n"):
                        context_parts.append(line)
                    context_parts.append("")

                # Add environment context if present
                environment_context = config.get("environment_context", "").strip()
                if environment_context:
                    context_parts.append("**Environment Context:**")
                    context_parts.append("")
                    for line in environment_context.split("\n"):
                        context_parts.append(line)
                    context_parts.append("")

                # Add shell configuration if present (for shell skills)
                if skill_type in ["shell", "SHELL"]:
                    shell_binary = config.get("shell_binary")
                    shell_args = config.get("shell_args")

                    if shell_binary or shell_args:
                        context_parts.append("**Shell Configuration:**")
                        context_parts.append("")
                        if shell_binary:
                            context_parts.append(f"- Binary: `{shell_binary}`")
                        if shell_args:
                            args_str = " ".join(shell_args)
                            context_parts.append(f"- Arguments: `{args_str}`")
                        context_parts.append("")
            except Exception as e:
                logger.warning(
                    "skill_context_enhancement_skipped_malformed_skill",
                    error=str(e),
                    skill=skill,
                )
                continue

        context_parts.append("---")
        context_parts.append("")

        enhancement_text = "\n".join(context_parts)

        # Log the enhancement
        logger.info(
            "skill_context_enhancement_applied",
            skills_with_context=len(skills_with_context),
            total_skills=len(self.skill_configs),
            enhancement_size=len(enhancement_text),
        )

        # Append to base prompt
        if base_prompt:
            return base_prompt + "\n\n" + enhancement_text
        else:
            return enhancement_text.lstrip()

    def _has_context_fields(self, skill: Dict[str, Any]) -> bool:
        """
        Check if a skill configuration has any context fields.

        Args:
            skill: Skill configuration dictionary

        Returns:
            True if skill has usage_guidelines, environment_context, or shell config
        """
        config = skill.get("configuration", {})
        return bool(
            config.get("usage_guidelines", "").strip()
            or config.get("environment_context", "").strip()
            or config.get("shell_binary")
            or config.get("shell_args")
        )
