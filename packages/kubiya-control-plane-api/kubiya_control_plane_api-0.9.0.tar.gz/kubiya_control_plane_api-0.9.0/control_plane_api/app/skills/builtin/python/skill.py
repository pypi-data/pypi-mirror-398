"""
Python Skill

Provides Python code execution capabilities with configurable restrictions.
"""
from typing import Dict, Any, List
from control_plane_api.app.skills.base import SkillDefinition, SkillType, SkillCategory, SkillVariant
from control_plane_api.app.skills.registry import register_skill


class PythonSkill(SkillDefinition):
    """Python code execution skill"""

    @property
    def type(self) -> SkillType:
        return SkillType.PYTHON

    @property
    def name(self) -> str:
        return "Python"

    @property
    def description(self) -> str:
        return "Execute Python code locally with configurable import restrictions"

    @property
    def icon(self) -> str:
        return "FaPython"

    @property
    def icon_type(self) -> str:
        return "react-icon"

    def get_variants(self) -> List[SkillVariant]:
        return [
            SkillVariant(
                id="python_runtime",
                name="Python Runtime",
                description="Execute Python code locally with restricted imports for security",
                category=SkillCategory.COMMON,
                badge="Safe",
                icon="FaPython",
                configuration={
                    "enable_code_execution": True,
                    "blocked_imports": ["os", "subprocess", "sys", "socket", "shutil"],
                },
                is_default=True,
            ),
            SkillVariant(
                id="python_unrestricted",
                name="Python - Unrestricted",
                description="Execute Python code without import restrictions or sandboxing",
                category=SkillCategory.ADVANCED,
                badge="Advanced",
                icon="FaPython",
                configuration={
                    "enable_code_execution": True,
                },
                is_default=False,
            ),
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Python configuration"""
        validated = {
            "enable_code_execution": config.get("enable_code_execution", True),
        }

        # Add blocked_imports if specified
        if "blocked_imports" in config:
            validated["blocked_imports"] = list(config["blocked_imports"])

        # Add allowed_imports if specified (whitelist mode)
        if "allowed_imports" in config:
            validated["allowed_imports"] = list(config["allowed_imports"])

        # Add timeout if specified
        if "timeout" in config:
            validated["timeout"] = min(config.get("timeout", 30), 300)  # Max 5 minutes

        return validated

    def get_default_configuration(self) -> Dict[str, Any]:
        """Default: restricted imports"""
        return {
            "enable_code_execution": True,
            "blocked_imports": ["os", "subprocess", "sys", "socket", "shutil"],
        }


# Auto-register this skill
register_skill(PythonSkill())
