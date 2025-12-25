"""
File System Skill

Provides file system access capabilities (read, write, list, search files).
"""
from typing import Dict, Any, List
from control_plane_api.app.skills.base import SkillDefinition, SkillType, SkillCategory, SkillVariant
from control_plane_api.app.skills.registry import register_skill


class FileSystemSkill(SkillDefinition):
    """File system access skill"""

    @property
    def type(self) -> SkillType:
        return SkillType.FILE_SYSTEM

    @property
    def name(self) -> str:
        return "File System"

    @property
    def description(self) -> str:
        return "Access and manipulate files and directories on the local file system"

    @property
    def icon(self) -> str:
        return "FolderOpen"

    def get_variants(self) -> List[SkillVariant]:
        return [
            SkillVariant(
                id="file_system_read_only",
                name="File System - Read Only",
                description="Access local file system for reading, listing, and searching files safely",
                category=SkillCategory.COMMON,
                badge="Safe",
                icon="FolderOpen",
                configuration={
                    "enable_save_file": False,
                    "enable_read_file": True,
                    "enable_list_files": True,
                    "enable_search_files": True,
                },
                is_default=False,
            ),
            SkillVariant(
                id="file_system_full_access",
                name="File System - Full Access",
                description="Complete file system access: read, write, create, and modify local files",
                category=SkillCategory.COMMON,
                badge="Recommended",
                icon="HardDrive",
                configuration={
                    "enable_save_file": True,
                    "enable_read_file": True,
                    "enable_list_files": True,
                    "enable_search_files": True,
                },
                is_default=True,
            ),
            SkillVariant(
                id="file_system_sandboxed",
                name="File System - Sandboxed",
                description="Isolated file access limited to /sandbox directory only",
                category=SkillCategory.SECURITY,
                badge="Secure",
                icon="Shield",
                configuration={
                    "base_dir": "/sandbox",
                    "enable_save_file": True,
                    "enable_read_file": True,
                    "enable_list_files": True,
                    "enable_search_files": False,
                },
                is_default=False,
            ),
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate file system configuration"""
        validated = {
            "enable_save_file": config.get("enable_save_file", False),
            "enable_read_file": config.get("enable_read_file", True),
            "enable_list_files": config.get("enable_list_files", True),
            "enable_search_files": config.get("enable_search_files", True),
        }

        # Add base_dir if specified
        if "base_dir" in config:
            validated["base_dir"] = str(config["base_dir"])

        # Add allowed_extensions if specified
        if "allowed_extensions" in config:
            validated["allowed_extensions"] = list(config["allowed_extensions"])

        return validated

    def get_default_configuration(self) -> Dict[str, Any]:
        """Default: full access"""
        return {
            "enable_save_file": True,
            "enable_read_file": True,
            "enable_list_files": True,
            "enable_search_files": True,
        }


# Auto-register this skill
register_skill(FileSystemSkill())
