"""
Docker Skill

Provides Docker management capabilities (containers, images, volumes, networks).
"""
from typing import Dict, Any, List
from control_plane_api.app.skills.base import SkillDefinition, SkillType, SkillCategory, SkillVariant, SkillRequirements
from control_plane_api.app.skills.registry import register_skill


class DockerSkill(SkillDefinition):
    """Docker management skill"""

    @property
    def type(self) -> SkillType:
        return SkillType.DOCKER

    @property
    def name(self) -> str:
        return "Docker"

    @property
    def description(self) -> str:
        return "Manage Docker containers, images, volumes, and networks on the local system"

    @property
    def icon(self) -> str:
        return "FaDocker"

    @property
    def icon_type(self) -> str:
        return "react-icon"

    def get_variants(self) -> List[SkillVariant]:
        return [
            SkillVariant(
                id="docker_containers",
                name="Docker - Containers",
                description="Manage Docker containers on local system (start, stop, inspect)",
                category=SkillCategory.COMMON,
                badge="Safe",
                icon="FaDocker",
                configuration={
                    "enable_container_management": True,
                    "enable_image_management": False,
                    "enable_volume_management": False,
                    "enable_network_management": False,
                },
                is_default=True,
            ),
            SkillVariant(
                id="docker_full_control",
                name="Docker - Full Control",
                description="Complete Docker management: containers, images, volumes, and networks",
                category=SkillCategory.ADVANCED,
                badge="Advanced",
                icon="FaDocker",
                configuration={
                    "enable_container_management": True,
                    "enable_image_management": True,
                    "enable_volume_management": True,
                    "enable_network_management": True,
                },
                is_default=False,
            ),
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Docker configuration"""
        validated = {
            "enable_container_management": config.get("enable_container_management", True),
            "enable_image_management": config.get("enable_image_management", False),
            "enable_volume_management": config.get("enable_volume_management", False),
            "enable_network_management": config.get("enable_network_management", False),
        }

        # Add docker_host if specified (e.g., "unix:///var/run/docker.sock")
        if "docker_host" in config:
            validated["docker_host"] = str(config["docker_host"])

        return validated

    def get_default_configuration(self) -> Dict[str, Any]:
        """Default: container management only"""
        return {
            "enable_container_management": True,
            "enable_image_management": False,
            "enable_volume_management": False,
            "enable_network_management": False,
        }

    def get_requirements(self) -> SkillRequirements:
        """Docker skill requires docker package and Docker daemon"""
        return SkillRequirements(
            python_packages=["docker>=6.0.0"],
            system_packages=["docker"],
            supported_os=["linux", "darwin", "windows"],
            external_dependencies=["Docker daemon must be running"],
            notes="Requires Docker to be installed and the Docker daemon to be accessible"
        )


# Auto-register this skill
register_skill(DockerSkill())
