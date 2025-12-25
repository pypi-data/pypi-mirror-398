"""
Skill Template Loaders

Loaders for discovering and loading skill templates from various sources.
Control Plane uses these to dynamically discover available skills.
"""

from .base import BaseSkillTemplateLoader
from .filesystem_loader import FilesystemSkillTemplateLoader

__all__ = [
    "BaseSkillTemplateLoader",
    "FilesystemSkillTemplateLoader",
]
