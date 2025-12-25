"""
Knowledge API Skill

Provides semantic search capabilities across the organization's central knowledge base.
"""
from typing import Dict, Any, List
from control_plane_api.app.skills.base import SkillDefinition, SkillType, SkillCategory, SkillVariant
from control_plane_api.app.skills.registry import register_skill


class KnowledgeAPISkill(SkillDefinition):
    """Knowledge API semantic search skill"""

    @property
    def type(self) -> SkillType:
        return SkillType.KNOWLEDGE_API

    @property
    def name(self) -> str:
        return "Knowledge API"

    @property
    def description(self) -> str:
        return "Semantic search across your organization's central knowledge base including documentation, code, conversations, and integration data"

    @property
    def icon(self) -> str:
        return "Database"

    def get_variants(self) -> List[SkillVariant]:
        return [
            SkillVariant(
                id="knowledge_api_standard",
                name="Knowledge API - Standard",
                description="Semantic search with automatic user context injection for scoped queries",
                category=SkillCategory.COMMON,
                badge="Recommended",
                icon="Database",
                configuration={
                    "stream": True,
                    "auto_inject_user_context": True,
                    "timeout": 60,
                },
                is_default=True,
            ),
            SkillVariant(
                id="knowledge_api_fast",
                name="Knowledge API - Fast",
                description="Quick semantic search with reduced timeout for faster responses",
                category=SkillCategory.COMMON,
                badge="Fast",
                icon="Zap",
                configuration={
                    "stream": False,
                    "auto_inject_user_context": True,
                    "timeout": 30,
                },
                is_default=False,
            ),
            SkillVariant(
                id="knowledge_api_thorough",
                name="Knowledge API - Thorough",
                description="Extended search timeout for comprehensive knowledge base queries",
                category=SkillCategory.ADVANCED,
                badge="Thorough",
                icon="Search",
                configuration={
                    "stream": True,
                    "auto_inject_user_context": True,
                    "timeout": 120,
                },
                is_default=False,
            ),
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate knowledge API configuration"""
        validated = {
            "stream": config.get("stream", True),
            "auto_inject_user_context": config.get("auto_inject_user_context", True),
            "timeout": config.get("timeout", 60),
        }

        # Validate timeout range
        if not (10 <= validated["timeout"] <= 300):
            raise ValueError("Timeout must be between 10 and 300 seconds")

        # Add orchestrator_url if specified
        if "orchestrator_url" in config:
            validated["orchestrator_url"] = str(config["orchestrator_url"])

        return validated

    def get_default_configuration(self) -> Dict[str, Any]:
        """Default: streaming with auto-context"""
        return {
            "stream": True,
            "auto_inject_user_context": True,
            "timeout": 60,
        }

    def get_framework_class_name(self) -> str:
        """
        Get the underlying framework tool class name.

        The implementation should be provided by the kubiya SDK package.
        """
        return "KnowledgeAPITools"

    def get_requirements(self) -> "SkillRequirements":
        """Get runtime requirements for this skill."""
        from control_plane_api.app.skills.base import SkillRequirements

        return SkillRequirements(
            python_packages=["kubiya>=2.0.3"],
            external_dependencies=["Kubiya Knowledge API"],
            required_env_vars=["KUBIYA_API_KEY"],
            notes="Knowledge API skill implementation is provided by the kubiya SDK package. "
                  "This skill must be explicitly associated with agents/teams - it is not built-in by default."
        )


# Auto-register this skill
register_skill(KnowledgeAPISkill())
