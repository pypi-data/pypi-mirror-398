"""
Slack Skill

Provides Slack integration capabilities with OAuth support and configurable permissions.
"""
from typing import Dict, Any, List
from control_plane_api.app.skills.base import (
    SkillDefinition,
    SkillType,
    SkillCategory,
    SkillVariant,
    SkillRequirements,
)
from control_plane_api.app.skills.registry import register_skill


class SlackSkill(SkillDefinition):
    """Slack integration skill with OAuth and configurable capabilities"""

    @property
    def type(self) -> SkillType:
        return SkillType.SLACK

    @property
    def name(self) -> str:
        return "Slack"

    @property
    def description(self) -> str:
        return "Slack integration with OAuth support and configurable capabilities for messaging, reactions, and channel management"

    @property
    def icon(self) -> str:
        return "Slack"

    def get_variants(self) -> List[SkillVariant]:
        return [
            SkillVariant(
                id="slack_read_only",
                name="Slack - Read Only",
                description="Read-only access to Slack: list channels, read messages, search, view threads and users",
                category=SkillCategory.COMMON,
                badge="Safe",
                icon="Eye",
                configuration={
                    "use_env_fallback": True,
                    "enable_read_messages": True,
                    "enable_write_messages": False,
                    "enable_reactions": False,
                    "enable_channel_management": False,
                    "read_channels": True,
                    "read_messages": True,
                    "search_messages": True,
                    "read_threads": True,
                    "read_users": True,
                    "timeout": 30,
                    "usage_guidelines": (
                        "Read-only Slack access for monitoring and information gathering:\n"
                        "- List and browse channels\n"
                        "- Read message history\n"
                        "- Search for messages\n"
                        "- View thread replies\n"
                        "- Get user information\n"
                        "Note: Cannot send messages, add reactions, or manage channels."
                    ),
                },
                is_default=True,
            ),
            SkillVariant(
                id="slack_communication",
                name="Slack - Communication",
                description="Full communication capabilities: read and write messages, manage threads, add reactions",
                category=SkillCategory.COMMON,
                badge="Recommended",
                icon="MessageSquare",
                configuration={
                    "use_env_fallback": True,
                    "enable_read_messages": True,
                    "enable_write_messages": True,
                    "enable_reactions": True,
                    "enable_channel_management": False,
                    "read_channels": True,
                    "read_messages": True,
                    "search_messages": True,
                    "read_threads": True,
                    "read_users": True,
                    "send_messages": True,
                    "post_messages": True,
                    "reply_to_threads": True,
                    "update_messages": True,
                    "add_reactions": True,
                    "remove_reactions": True,
                    "timeout": 30,
                    "usage_guidelines": (
                        "Full Slack communication capabilities:\n"
                        "- Send and post messages to channels\n"
                        "- Reply to and manage threads\n"
                        "- Update and delete messages\n"
                        "- Add and remove reactions\n"
                        "- Search and read message history\n"
                        "Note: Cannot create or manage channels."
                    ),
                },
                is_default=False,
            ),
            SkillVariant(
                id="slack_bot_assistant",
                name="Slack - Bot Assistant",
                description="Optimized for conversational bots: read/write messages, reactions, optimized for rapid responses",
                category=SkillCategory.COMMON,
                badge="Bot",
                icon="Bot",
                configuration={
                    "use_env_fallback": True,
                    "enable_read_messages": True,
                    "enable_write_messages": True,
                    "enable_reactions": True,
                    "enable_channel_management": False,
                    "read_channels": True,
                    "read_messages": True,
                    "search_messages": False,  # Disabled for performance
                    "read_threads": True,
                    "read_users": True,
                    "send_messages": True,
                    "post_messages": True,
                    "reply_to_threads": True,
                    "update_messages": False,  # Bots typically don't edit
                    "add_reactions": True,
                    "remove_reactions": False,  # Bots typically don't remove
                    "timeout": 20,  # Faster timeout for bot responses
                    "usage_guidelines": (
                        "Bot-optimized Slack configuration:\n"
                        "- Rapid message sending and thread replies\n"
                        "- React to messages for acknowledgment\n"
                        "- Read channels and threads for context\n"
                        "- Lightweight operations for fast responses\n"
                        "Optimized for: Chatbots, notifications, automated responses."
                    ),
                },
                is_default=False,
            ),
            SkillVariant(
                id="slack_full_access",
                name="Slack - Full Access",
                description="Complete Slack management: all messaging, reactions, and channel administration capabilities",
                category=SkillCategory.ADVANCED,
                badge="Advanced",
                icon="Slack",
                configuration={
                    "use_env_fallback": True,
                    "enable_read_messages": True,
                    "enable_write_messages": True,
                    "enable_reactions": True,
                    "enable_channel_management": True,
                    "read_channels": True,
                    "read_messages": True,
                    "search_messages": True,
                    "read_threads": True,
                    "read_users": True,
                    "send_messages": True,
                    "post_messages": True,
                    "reply_to_threads": True,
                    "update_messages": True,
                    "add_reactions": True,
                    "remove_reactions": True,
                    "create_channels": True,
                    "invite_to_channels": True,
                    "archive_channels": True,
                    "set_channel_topic": True,
                    "timeout": 30,
                    "usage_guidelines": (
                        "Full Slack workspace management capabilities:\n"
                        "- Complete messaging and communication\n"
                        "- Channel creation and management\n"
                        "- User invitations and permissions\n"
                        "- Channel archiving and topics\n"
                        "- All reaction and thread operations\n"
                        "Warning: Use responsibly - includes administrative permissions."
                    ),
                },
                is_default=False,
            ),
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Slack configuration"""
        validated = {}

        # Authentication settings
        if "integration_id" in config:
            validated["integration_id"] = str(config["integration_id"])

        # Handle both secret_name (single) and secrets (list) for backwards compatibility
        if "secret_name" in config and config["secret_name"]:
            # Single secret - convert to list
            validated["secrets"] = [str(config["secret_name"])]
        elif "secrets" in config:
            secrets = config["secrets"]
            if isinstance(secrets, str):
                # Comma-separated string to list
                validated["secrets"] = [s.strip() for s in secrets.split(",") if s.strip()]
            elif isinstance(secrets, list):
                validated["secrets"] = [str(s).strip() for s in secrets if s]

        validated["use_env_fallback"] = config.get("use_env_fallback", True)

        # Channel scoping
        if "allowed_channels" in config:
            channels = config["allowed_channels"]
            if isinstance(channels, str):
                # Convert comma-separated string to list
                validated["allowed_channels"] = [ch.strip() for ch in channels.split(",") if ch.strip()]
            elif isinstance(channels, list):
                validated["allowed_channels"] = [str(ch).strip() for ch in channels if ch]

        if "blocked_channels" in config:
            channels = config["blocked_channels"]
            if isinstance(channels, str):
                validated["blocked_channels"] = [ch.strip() for ch in channels.split(",") if ch.strip()]
            elif isinstance(channels, list):
                validated["blocked_channels"] = [str(ch).strip() for ch in channels if ch]

        # Capability groups
        validated["enable_read_messages"] = config.get("enable_read_messages", True)
        validated["enable_write_messages"] = config.get("enable_write_messages", False)
        validated["enable_reactions"] = config.get("enable_reactions", False)
        validated["enable_channel_management"] = config.get("enable_channel_management", False)

        # Fine-grained read permissions
        if validated["enable_read_messages"]:
            validated["read_channels"] = config.get("read_channels", True)
            validated["read_messages"] = config.get("read_messages", True)
            validated["search_messages"] = config.get("search_messages", True)
            validated["read_threads"] = config.get("read_threads", True)
            validated["read_users"] = config.get("read_users", True)

        # Fine-grained write permissions
        if validated["enable_write_messages"]:
            validated["send_messages"] = config.get("send_messages", True)
            validated["post_messages"] = config.get("post_messages", True)
            validated["reply_to_threads"] = config.get("reply_to_threads", True)
            validated["update_messages"] = config.get("update_messages", True)

        # Fine-grained reaction permissions
        if validated["enable_reactions"]:
            validated["add_reactions"] = config.get("add_reactions", True)
            validated["remove_reactions"] = config.get("remove_reactions", True)

        # Fine-grained channel management permissions
        if validated["enable_channel_management"]:
            validated["create_channels"] = config.get("create_channels", True)
            validated["invite_to_channels"] = config.get("invite_to_channels", True)
            validated["archive_channels"] = config.get("archive_channels", True)
            validated["set_channel_topic"] = config.get("set_channel_topic", True)

        # General settings
        validated["timeout"] = max(5, min(config.get("timeout", 30), 300))  # 5s to 5min

        if "default_channel" in config:
            validated["default_channel"] = str(config["default_channel"])

        # Context fields for system prompt injection
        if "usage_guidelines" in config:
            validated["usage_guidelines"] = str(config["usage_guidelines"])

        return validated

    def get_default_configuration(self) -> Dict[str, Any]:
        """Get default configuration (read-only)"""
        return {
            "use_env_fallback": True,
            "enable_read_messages": True,
            "enable_write_messages": False,
            "enable_reactions": False,
            "enable_channel_management": False,
            "read_channels": True,
            "read_messages": True,
            "search_messages": True,
            "read_threads": True,
            "read_users": True,
            "timeout": 30,
        }

    def get_requirements(self) -> SkillRequirements:
        """Get skill runtime requirements"""
        return SkillRequirements(
            python_packages=["slack-sdk>=3.27.0", "httpx>=0.27.0"],
            supported_os=["linux", "darwin", "win32"],
            min_python_version="3.10",
            required_env_vars=[],  # All optional: SLACK_BOT_TOKEN, KUBIYA_API_KEY, INTEGRATION_API_BASE
            external_dependencies=["Slack API"],
            notes=(
                "Requires either:\n"
                "1. Integration API with OAuth authentication (via integration_id), OR\n"
                "2. SLACK_BOT_TOKEN environment variable (Bot User OAuth Token)\n\n"
                "For Integration API: Set KUBIYA_API_KEY and optionally INTEGRATION_API_BASE"
            ),
        )


# Register the skill
register_skill(SlackSkill())
