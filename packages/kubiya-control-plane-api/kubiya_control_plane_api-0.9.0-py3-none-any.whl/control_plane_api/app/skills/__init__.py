"""
Skills Module

This module manages all available skills (OS-level capabilities) that can be
assigned to agents and teams. Each skill corresponds to a capability that agents
can use during execution (file system, shell, Docker, Python, etc.).

Skills are defined as Python classes that provide:
- Metadata (name, description, icon)
- Default configuration
- Validation logic
- Instantiation logic for the underlying framework

Skills can be:
1. Built-in (imported below)
2. Dynamic (loaded from .kubiya/skills/ via loaders)
"""

from .base import SkillDefinition, SkillType, SkillCategory, SkillRequirements, SkillVariant
from .registry import skill_registry, get_skill, get_all_skills, register_skill
from .config import get_skill_template_paths, is_dynamic_skills_enabled
from .loaders import FilesystemSkillTemplateLoader
import logging

# Import all built-in skill definitions to auto-register them
from .builtin import (
    FileSystemSkill,
    ShellSkill,
    DockerSkill,
    PythonSkill,
    FileGenerationSkill,
    DataVisualizationSkill,
    WorkflowExecutorSkill,
    KnowledgeAPISkill,
    AgentCommunicationSkill,
)

logger = logging.getLogger(__name__)

__all__ = [
    "SkillDefinition",
    "SkillType",
    "SkillCategory",
    "SkillRequirements",
    "SkillVariant",
    "skill_registry",
    "get_skill",
    "get_all_skills",
    "register_skill",
    "FileSystemSkill",
    "ShellSkill",
    "DockerSkill",
    "PythonSkill",
    "FileGenerationSkill",
    "DataVisualizationSkill",
    "WorkflowExecutorSkill",
    "KnowledgeAPISkill",
    "AgentCommunicationSkill",
    "initialize_dynamic_skills",
]


def initialize_dynamic_skills() -> int:
    """
    Initialize and load dynamic skills from configured sources.

    This should be called during Control Plane startup, after built-in
    skills have been registered.

    Returns:
        Number of dynamic skills loaded

    Environment Variables:
        KUBIYA_ENABLE_DYNAMIC_SKILLS: Enable/disable dynamic loading (default: true)
        KUBIYA_SKILLS_TEMPLATES_PATH: Primary skills directory
        KUBIYA_SKILLS_EXTRA_PATHS: Additional paths (colon-separated)
    """
    if not is_dynamic_skills_enabled():
        logger.info("Dynamic skills loading is disabled")
        return 0

    logger.info("Initializing dynamic skills...")

    # Get configured paths
    paths = get_skill_template_paths()

    if not paths:
        logger.info("No skill template paths configured, skipping dynamic loading")
        return 0

    # Create filesystem loader
    loaders = [
        FilesystemSkillTemplateLoader(base_paths=paths, enabled=True)
    ]

    # Load from all loaders
    loaded_count = skill_registry.load_from_loaders(loaders)

    logger.info(f"Dynamic skills initialization complete: {loaded_count} skills loaded")
    return loaded_count
