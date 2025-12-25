"""
Base classes for skill definitions
"""
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
import platform


class SkillType(str, Enum):
    """Supported skill types"""
    FILE_SYSTEM = "file_system"
    SHELL = "shell"
    DOCKER = "docker"
    PYTHON = "python"
    FILE_GENERATION = "file_generation"
    DATA_VISUALIZATION = "data_visualization"
    SLEEP = "sleep"
    WORKFLOW_EXECUTOR = "workflow_executor"
    CONTEXTUAL_AWARENESS = "contextual_awareness"
    KNOWLEDGE_API = "knowledge_api"
    COGNITIVE_MEMORY = "cognitive_memory"  # Context graph + semantic memory operations
    CODE_INGESTION = "code_ingestion"  # Code repository ingestion and analysis
    AGENT_COMMUNICATION = "agent_communication"
    REMOTE_FILESYSTEM = "remote_filesystem"
    SLACK = "slack"
    CUSTOM = "custom"


class SkillCategory(str, Enum):
    """Skill categories for organization"""
    COMMON = "common"          # Frequently used, safe defaults
    ADVANCED = "advanced"       # Advanced features, require more privileges
    SECURITY = "security"       # Security-focused, restricted access
    CUSTOM = "custom"           # User-defined custom skills


class SkillRequirements(BaseModel):
    """Runtime requirements for a skill"""
    # Python packages required (will be checked/installed by worker)
    python_packages: List[str] = Field(default_factory=list)

    # System packages required (informational, worker should validate)
    system_packages: List[str] = Field(default_factory=list)

    # Supported operating systems (e.g., ["linux", "darwin", "windows"])
    supported_os: Optional[List[str]] = None

    # Minimum Python version (e.g., "3.10")
    min_python_version: Optional[str] = None

    # Environment variables required
    required_env_vars: List[str] = Field(default_factory=list)

    # External services/APIs required (informational)
    external_dependencies: List[str] = Field(default_factory=list)

    # Additional notes about requirements
    notes: Optional[str] = None


class SkillVariant(BaseModel):
    """A specific variant/preset of a skill"""
    id: str
    name: str
    description: str
    category: SkillCategory
    configuration: Dict[str, Any]
    badge: Optional[str] = None  # e.g., "Safe", "Recommended", "Advanced"
    icon: Optional[str] = None
    is_default: bool = False


class SkillDefinition(ABC):
    """
    Base class for all skill definitions.

    Each skill type should subclass this and implement the required methods.
    This provides a clean interface for defining new skills.
    """

    @property
    @abstractmethod
    def type(self) -> SkillType:
        """The type identifier for this skill"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this skill does"""
        pass

    @property
    @abstractmethod
    def icon(self) -> str:
        """Icon name (Lucide or React Icons)"""
        pass

    @property
    def icon_type(self) -> str:
        """Icon type: 'lucide' or 'react-icon'"""
        return "lucide"

    @abstractmethod
    def get_variants(self) -> List[SkillVariant]:
        """
        Get all predefined variants/presets for this skill.

        Returns a list of variants with different configurations
        (e.g., "Read Only", "Full Access", "Sandboxed")
        """
        pass

    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize configuration.

        Args:
            config: Raw configuration dict

        Returns:
            Validated and normalized configuration

        Raises:
            ValueError: If configuration is invalid
        """
        pass

    @abstractmethod
    def get_default_configuration(self) -> Dict[str, Any]:
        """Get the default configuration for this skill"""
        pass

    def get_framework_class_name(self) -> str:
        """
        Get the underlying framework tool class name.
        This is used for instantiation during agent execution.

        Returns:
            Class name (e.g., "FileTools", "ShellTools")
        """
        # Default mapping based on type
        mapping = {
            SkillType.FILE_SYSTEM: "FileTools",
            SkillType.SHELL: "ShellTools",
            SkillType.DOCKER: "DockerTools",
            SkillType.PYTHON: "PythonTools",
            SkillType.FILE_GENERATION: "FileGenerationTools",
            SkillType.DATA_VISUALIZATION: "DataVisualizationTools",
            SkillType.SLEEP: "SleepTools",
            SkillType.CONTEXTUAL_AWARENESS: "ContextualAwarenessTools",
            SkillType.AGENT_COMMUNICATION: "AgentCommunicationTools",
            SkillType.REMOTE_FILESYSTEM: "RemoteFilesystemTools",
        }
        return mapping.get(self.type, "BaseTool")

    def get_requirements(self) -> SkillRequirements:
        """
        Get runtime requirements for this skill.

        Override this method to specify requirements like:
        - Python packages
        - System packages
        - OS requirements
        - Environment variables

        Returns:
            SkillRequirements instance
        """
        # Default: no special requirements
        return SkillRequirements()

    def check_requirements(self) -> tuple[bool, List[str]]:
        """
        Check if requirements are met in current environment.

        Returns:
            Tuple of (is_satisfied, missing_requirements)
        """
        requirements = self.get_requirements()
        missing = []

        # Check OS
        if requirements.supported_os:
            current_os = platform.system().lower()
            if current_os not in requirements.supported_os:
                missing.append(f"OS '{current_os}' not supported (requires: {', '.join(requirements.supported_os)})")

        # Check Python version
        if requirements.min_python_version:
            import sys
            from packaging import version
            current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
            if version.parse(current_version) < version.parse(requirements.min_python_version):
                missing.append(f"Python {requirements.min_python_version}+ required (current: {current_version})")

        # Check environment variables
        import os
        for env_var in requirements.required_env_vars:
            if not os.getenv(env_var):
                missing.append(f"Environment variable '{env_var}' not set")

        # Check Python packages (basic import check)
        for package in requirements.python_packages:
            package_name = package.split('[')[0].split('>=')[0].split('==')[0].strip()
            try:
                __import__(package_name)
            except ImportError:
                missing.append(f"Python package '{package}' not installed")

        return len(missing) == 0, missing

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        requirements = self.get_requirements()
        is_satisfied, missing = self.check_requirements()

        return {
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "icon_type": self.icon_type,
            "default_configuration": self.get_default_configuration(),
            "variants": [v.model_dump() for v in self.get_variants()],
            "framework_class": self.get_framework_class_name(),
            "requirements": requirements.model_dump(),
            "requirements_satisfied": is_satisfied,
            "missing_requirements": missing,
        }
