"""
Remote Filesystem Skill

Provides cloud storage capabilities for uploading, downloading, and managing files
with multi-provider support (Vercel Blob, S3, Azure Blob, GCS).
"""

from typing import Dict, Any, List
from control_plane_api.app.skills.base import (
    SkillDefinition,
    SkillType,
    SkillCategory,
    SkillVariant,
    SkillRequirements
)
from control_plane_api.app.skills.registry import register_skill


class RemoteFilesystemSkill(SkillDefinition):
    """Remote filesystem skill with cloud storage provider support."""

    @property
    def type(self) -> SkillType:
        return SkillType.REMOTE_FILESYSTEM

    @property
    def name(self) -> str:
        return "Remote Filesystem"

    @property
    def description(self) -> str:
        return "Cloud storage for uploading, downloading, and managing files with multi-provider support"

    @property
    def icon(self) -> str:
        return "Cloud"

    @property
    def icon_type(self) -> str:
        return "lucide"

    def get_variants(self) -> List[SkillVariant]:
        return [
            SkillVariant(
                id="remote_filesystem_read_only",
                name="Remote Filesystem - Read Only",
                description="Download and list files from cloud storage safely",
                category=SkillCategory.COMMON,
                badge="Safe",
                icon="CloudDownload",
                configuration={
                    "enable_upload": False,
                    "enable_download": True,
                    "enable_list": True,
                    "enable_delete": False,
                    "enable_search": True,
                    "enable_metadata": True,
                    "enable_move": False,
                    "enable_copy": False,
                    "enable_folders": False,
                    "enable_batch_download": False,
                },
                is_default=False,
            ),
            SkillVariant(
                id="remote_filesystem_write_enabled",
                name="Remote Filesystem - Write Enabled",
                description="Upload and download files with read/write access",
                category=SkillCategory.COMMON,
                badge="Recommended",
                icon="Cloud",
                configuration={
                    "enable_upload": True,
                    "enable_download": True,
                    "enable_list": True,
                    "enable_delete": False,
                    "enable_search": True,
                    "enable_metadata": True,
                    "enable_move": True,
                    "enable_copy": True,
                    "enable_folders": False,
                    "enable_batch_download": False,
                },
                is_default=True,
            ),
            SkillVariant(
                id="remote_filesystem_full_access",
                name="Remote Filesystem - Full Access",
                description="Complete cloud storage access including file deletion",
                category=SkillCategory.ADVANCED,
                badge="Advanced",
                icon="CloudCog",
                configuration={
                    "enable_upload": True,
                    "enable_download": True,
                    "enable_list": True,
                    "enable_delete": True,
                    "enable_search": True,
                    "enable_metadata": True,
                    "enable_move": True,
                    "enable_copy": True,
                    "enable_folders": True,
                    "enable_batch_download": True,
                },
                is_default=False,
            ),
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate remote filesystem configuration."""
        validated = {
            "enable_upload": config.get("enable_upload", False),
            "enable_download": config.get("enable_download", True),
            "enable_list": config.get("enable_list", True),
            "enable_delete": config.get("enable_delete", False),
            "enable_search": config.get("enable_search", True),
            "enable_metadata": config.get("enable_metadata", True),
            "enable_move": config.get("enable_move", False),
            "enable_copy": config.get("enable_copy", False),
            "enable_folders": config.get("enable_folders", False),
            "enable_batch_download": config.get("enable_batch_download", False),
        }

        # Optional: path restrictions
        if "allowed_paths" in config:
            validated["allowed_paths"] = list(config["allowed_paths"])

        # Optional: file size limit
        if "max_file_size_mb" in config:
            validated["max_file_size_mb"] = int(config["max_file_size_mb"])

        # Optional: allowed file extensions
        if "allowed_extensions" in config:
            validated["allowed_extensions"] = list(config["allowed_extensions"])

        return validated

    def get_default_configuration(self) -> Dict[str, Any]:
        """Default: write-enabled without delete."""
        return {
            "enable_upload": True,
            "enable_download": True,
            "enable_list": True,
            "enable_delete": False,
            "enable_search": True,
            "enable_metadata": True,
            "enable_move": True,
            "enable_copy": True,
            "enable_folders": False,
            "enable_batch_download": False,
        }

    def get_requirements(self) -> SkillRequirements:
        return SkillRequirements(
            python_packages=["httpx>=0.24.0", "PyYAML>=6.0"],
            required_env_vars=["STORAGE_PROVIDER"],
            external_dependencies=[
                "Storage provider configuration required:",
                "  - Vercel Blob: VERCEL_BLOB_TOKEN",
                "  - S3: AWS credentials (future)",
                "  - Azure Blob: Azure credentials (future)",
                "  - GCS: GCP credentials (future)"
            ],
            notes="Requires storage provider to be configured via STORAGE_PROVIDER environment variable. "
                  "No default provider - must be explicitly enabled."
        )


# Auto-register this skill
register_skill(RemoteFilesystemSkill())
