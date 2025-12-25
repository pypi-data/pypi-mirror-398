"""
Shell Skill

Provides shell command execution capabilities with configurable restrictions.
"""
from typing import Dict, Any, List
from control_plane_api.app.skills.base import SkillDefinition, SkillType, SkillCategory, SkillVariant
from control_plane_api.app.skills.registry import register_skill


class ShellSkill(SkillDefinition):
    """Shell command execution skill"""

    @property
    def type(self) -> SkillType:
        return SkillType.SHELL

    @property
    def name(self) -> str:
        return "Shell"

    @property
    def description(self) -> str:
        return "Execute shell commands on the local system with configurable restrictions"

    @property
    def icon(self) -> str:
        return "Terminal"

    def get_variants(self) -> List[SkillVariant]:
        return [
            SkillVariant(
                id="shell_safe_commands",
                name="Shell - Safe Commands",
                description="Execute read-only shell commands on the local system (ls, cat, grep, ps)",
                category=SkillCategory.COMMON,
                badge="Safe",
                icon="Terminal",
                configuration={
                    "allowed_commands": ["ls", "cat", "grep", "find", "ps", "top", "pwd", "echo", "head", "tail"],
                    "timeout": 30,
                    "usage_guidelines": (
                        "Use this skill for safe, read-only operations:\n"
                        "- File exploration: ls, find, cat\n"
                        "- Text processing: grep, head, tail\n"
                        "- Process monitoring: ps, top\n"
                        "- Working directory: pwd\n"
                        "Note: Destructive operations are blocked for safety."
                    ),
                },
                is_default=True,
            ),
            SkillVariant(
                id="shell_full_access",
                name="Shell - Full Access",
                description="Unrestricted shell access to execute any command on local system",
                category=SkillCategory.ADVANCED,
                badge="Advanced",
                icon="Terminal",
                configuration={
                    "timeout": 300,
                    "usage_guidelines": (
                        "Full shell access with no restrictions. Use responsibly:\n"
                        "- Package management: apt, yum, brew\n"
                        "- System administration: systemctl, service\n"
                        "- File operations: cp, mv, rm\n"
                        "- Network tools: curl, wget, ssh\n"
                        "Warning: All commands are permitted - exercise caution with destructive operations."
                    ),
                },
                is_default=False,
            ),
            SkillVariant(
                id="shell_read_only",
                name="Shell - Read Only",
                description="Maximum security: only non-destructive read commands allowed",
                category=SkillCategory.SECURITY,
                badge="Secure",
                icon="ShieldCheck",
                configuration={
                    "allowed_commands": ["ls", "cat", "head", "tail", "grep", "find", "pwd"],
                    "blocked_commands": ["rm", "mv", "cp", "chmod", "chown", "kill"],
                    "timeout": 15,
                    "usage_guidelines": (
                        "Highly restricted read-only shell access:\n"
                        "- View files: cat, head, tail\n"
                        "- Search: grep, find\n"
                        "- Navigate: ls, pwd\n"
                        "Security: Destructive commands explicitly blocked."
                    ),
                },
                is_default=False,
            ),
            SkillVariant(
                id="shell_debug_mode",
                name="Shell - Debug Mode",
                description="Shell with debug tracing enabled for troubleshooting",
                category=SkillCategory.ADVANCED,
                badge="Debug",
                icon="Bug",
                configuration={
                    "timeout": 60,
                    "shell_binary": "/bin/bash",
                    "shell_args": ["-x", "-e"],
                    "usage_guidelines": (
                        "Debug shell with command tracing:\n"
                        "- All executed commands are logged\n"
                        "- Script execution stops on first error\n"
                        "- Useful for troubleshooting complex workflows\n"
                        "- Review output carefully as it includes trace information"
                    ),
                    "environment_context": "Running in debug mode with command tracing enabled.",
                },
                is_default=False,
            ),
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate shell configuration"""
        validated = {
            "timeout": min(config.get("timeout", 30), 600),  # Max 10 minutes
        }

        # Add allowed_commands if specified
        if "allowed_commands" in config:
            validated["allowed_commands"] = list(config["allowed_commands"])

        # Add blocked_commands if specified
        if "blocked_commands" in config:
            validated["blocked_commands"] = list(config["blocked_commands"])

        # Add working_directory if specified
        if "working_directory" in config:
            validated["working_directory"] = str(config["working_directory"])

        # Context fields for system prompt injection
        if "usage_guidelines" in config:
            validated["usage_guidelines"] = str(config["usage_guidelines"])

        if "environment_context" in config:
            validated["environment_context"] = str(config["environment_context"])

        # Custom shell binary configuration
        if "shell_binary" in config:
            validated["shell_binary"] = str(config["shell_binary"])

        if "shell_args" in config:
            validated["shell_args"] = list(config["shell_args"])

        return validated

    def get_default_configuration(self) -> Dict[str, Any]:
        """Default: safe commands only"""
        return {
            "allowed_commands": ["ls", "cat", "grep", "find", "ps", "top", "pwd", "echo", "head", "tail"],
            "timeout": 30,
        }


# Auto-register this skill
register_skill(ShellSkill())
