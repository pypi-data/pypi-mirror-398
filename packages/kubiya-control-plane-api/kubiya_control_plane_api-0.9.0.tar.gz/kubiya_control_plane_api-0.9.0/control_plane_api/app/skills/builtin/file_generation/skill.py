"""
File Generation Skill

Provides file generation capabilities for various formats (JSON, CSV, PDF, TXT).
"""
from typing import Dict, Any, List
from control_plane_api.app.skills.base import SkillDefinition, SkillType, SkillCategory, SkillVariant
from control_plane_api.app.skills.registry import register_skill


class FileGenerationSkill(SkillDefinition):
    """File generation skill"""

    @property
    def type(self) -> SkillType:
        return SkillType.FILE_GENERATION

    @property
    def name(self) -> str:
        return "File Generator"

    @property
    def description(self) -> str:
        return "Generate and save files in various formats (JSON, CSV, PDF, TXT)"

    @property
    def icon(self) -> str:
        return "FileOutput"

    def get_variants(self) -> List[SkillVariant]:
        return [
            SkillVariant(
                id="file_generator",
                name="File Generator",
                description="Generate and save files locally: JSON, CSV, PDF, and TXT formats",
                category=SkillCategory.COMMON,
                badge="Recommended",
                icon="FileOutput",
                configuration={
                    "enable_json_generation": True,
                    "enable_csv_generation": True,
                    "enable_pdf_generation": True,
                    "enable_txt_generation": True,
                },
                is_default=True,
            ),
            SkillVariant(
                id="file_generator_data_only",
                name="File Generator - Data Only",
                description="Generate data files only (JSON, CSV) without document formats",
                category=SkillCategory.COMMON,
                badge="Safe",
                icon="FileText",
                configuration={
                    "enable_json_generation": True,
                    "enable_csv_generation": True,
                    "enable_pdf_generation": False,
                    "enable_txt_generation": True,
                },
                is_default=False,
            ),
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate file generation configuration"""
        validated = {
            "enable_json_generation": config.get("enable_json_generation", True),
            "enable_csv_generation": config.get("enable_csv_generation", True),
            "enable_pdf_generation": config.get("enable_pdf_generation", True),
            "enable_txt_generation": config.get("enable_txt_generation", True),
        }

        # Add output_directory if specified
        if "output_directory" in config:
            validated["output_directory"] = str(config["output_directory"])

        # Add max_file_size if specified (in MB)
        if "max_file_size" in config:
            validated["max_file_size"] = min(config.get("max_file_size", 10), 100)  # Max 100MB

        return validated

    def get_default_configuration(self) -> Dict[str, Any]:
        """Default: all formats enabled"""
        return {
            "enable_json_generation": True,
            "enable_csv_generation": True,
            "enable_pdf_generation": True,
            "enable_txt_generation": True,
        }


# Auto-register this skill
register_skill(FileGenerationSkill())
