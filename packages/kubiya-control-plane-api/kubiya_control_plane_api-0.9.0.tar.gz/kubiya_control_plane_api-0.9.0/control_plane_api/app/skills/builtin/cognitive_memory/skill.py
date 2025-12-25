"""
Cognitive Memory Skill

Provides semantic memory and context graph operations including memorization,
recall, and intelligent search across organizational knowledge.
"""
from typing import Dict, Any, List
from control_plane_api.app.skills.base import SkillDefinition, SkillType, SkillCategory, SkillVariant
from control_plane_api.app.skills.registry import register_skill


class CognitiveMemorySkill(SkillDefinition):
    """Cognitive Memory skill for semantic memory and context graph operations"""

    @property
    def type(self) -> SkillType:
        return SkillType.COGNITIVE_MEMORY

    @property
    def name(self) -> str:
        return "Cognitive Memory"

    @property
    def description(self) -> str:
        return "Semantic memory operations including memorize, recall, and intelligent search across context graphs with knowledge extraction capabilities"

    @property
    def icon(self) -> str:
        return "Brain"

    def get_variants(self) -> List[SkillVariant]:
        return [
            SkillVariant(
                id="cognitive_memory_standard",
                name="Cognitive Memory - Standard",
                description="Standard memory operations with balanced performance and context retention",
                category=SkillCategory.COMMON,
                badge="Recommended",
                icon="Brain",
                configuration={
                    "search_type": "GRAPH_COMPLETION",
                    "auto_memorize": True,
                    "context_window": 10,
                    "enable_insights": True,
                    "timeout": 60,
                },
                is_default=True,
            ),
            SkillVariant(
                id="cognitive_memory_fast",
                name="Cognitive Memory - Fast",
                description="Quick memory operations with reduced context for faster responses",
                category=SkillCategory.COMMON,
                badge="Fast",
                icon="Zap",
                configuration={
                    "search_type": "CHUNKS",
                    "auto_memorize": False,
                    "context_window": 5,
                    "enable_insights": False,
                    "timeout": 30,
                },
                is_default=False,
            ),
            SkillVariant(
                id="cognitive_memory_deep",
                name="Cognitive Memory - Deep Analysis",
                description="Comprehensive memory operations with full knowledge extraction and insights",
                category=SkillCategory.ADVANCED,
                badge="Thorough",
                icon="Database",
                configuration={
                    "search_type": "GRAPH_COMPLETION",
                    "auto_memorize": True,
                    "context_window": 20,
                    "enable_insights": True,
                    "enable_knowledge_extraction": True,
                    "timeout": 120,
                },
                is_default=False,
            ),
            SkillVariant(
                id="cognitive_memory_recall_only",
                name="Cognitive Memory - Read-Only",
                description="Search and recall only - no memorization for safe read-only access",
                category=SkillCategory.SECURITY,
                badge="Safe",
                icon="Eye",
                configuration={
                    "search_type": "GRAPH_COMPLETION",
                    "auto_memorize": False,
                    "allow_memorize": False,
                    "context_window": 10,
                    "enable_insights": True,
                    "timeout": 60,
                },
                is_default=False,
            ),
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate cognitive memory configuration"""
        validated = {
            "search_type": config.get("search_type", "GRAPH_COMPLETION"),
            "auto_memorize": config.get("auto_memorize", True),
            "context_window": config.get("context_window", 10),
            "enable_insights": config.get("enable_insights", True),
            "timeout": config.get("timeout", 60),
        }

        # Validate search type
        valid_search_types = ["GRAPH_COMPLETION", "RAG_COMPLETION", "CHUNKS", "SUMMARIES"]
        if validated["search_type"] not in valid_search_types:
            raise ValueError(f"search_type must be one of {valid_search_types}")

        # Validate context window
        if not (1 <= validated["context_window"] <= 50):
            raise ValueError("context_window must be between 1 and 50")

        # Validate timeout
        if not (10 <= validated["timeout"] <= 300):
            raise ValueError("Timeout must be between 10 and 300 seconds")

        # Optional parameters
        if "allow_memorize" in config:
            validated["allow_memorize"] = bool(config["allow_memorize"])

        if "enable_knowledge_extraction" in config:
            validated["enable_knowledge_extraction"] = bool(config["enable_knowledge_extraction"])

        # Add context graph API URL if specified
        if "context_graph_api_url" in config:
            validated["context_graph_api_url"] = str(config["context_graph_api_url"])

        # Dataset scoping
        if "dataset_ids" in config:
            validated["dataset_ids"] = config["dataset_ids"]

        return validated

    def get_default_configuration(self) -> Dict[str, Any]:
        """Default: standard memory with graph completion"""
        return {
            "search_type": "GRAPH_COMPLETION",
            "auto_memorize": True,
            "context_window": 10,
            "enable_insights": True,
            "timeout": 60,
        }

    def get_framework_class_name(self) -> str:
        """
        Get the underlying framework tool class name.

        The implementation should be provided by the kubiya SDK package.
        """
        return "CognitiveMemoryTools"

    def get_requirements(self) -> "SkillRequirements":
        """Get runtime requirements for this skill."""
        from control_plane_api.app.skills.base import SkillRequirements

        return SkillRequirements(
            python_packages=["kubiya>=2.0.3", "httpx>=0.28.0"],
            external_dependencies=["Context Graph API"],
            required_env_vars=["CONTEXT_GRAPH_API_URL"],
            notes="Cognitive Memory skill provides access to semantic memory and context graph operations. "
                  "Requires Context Graph API to be available. "
                  "This skill must be explicitly associated with agents/teams - it is not built-in by default."
        )


# Auto-register this skill
register_skill(CognitiveMemorySkill())
