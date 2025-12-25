"""
Base Skill Template Loader

Abstract interface for all skill template loaders.
"""

from abc import ABC, abstractmethod
from typing import List
import logging

from control_plane_api.app.skills.base import SkillDefinition

logger = logging.getLogger(__name__)


class BaseSkillTemplateLoader(ABC):
    """
    Abstract base class for skill template loaders.

    Loaders discover skill templates from various sources and return
    SkillDefinition instances that can be registered in the skill registry.
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize loader.

        Args:
            enabled: Whether this loader is enabled
        """
        self.enabled = enabled
        self.logger = logger

    @abstractmethod
    def discover(self) -> List[SkillDefinition]:
        """
        Discover skill templates from this source.

        Returns:
            List of SkillDefinition instances

        Raises:
            Exception: If discovery fails
        """
        pass

    def get_source_name(self) -> str:
        """
        Get the name of this loader source.

        Returns:
            Source name for logging
        """
        return self.__class__.__name__

    def is_enabled(self) -> bool:
        """
        Check if this loader is enabled.

        Returns:
            True if enabled
        """
        return self.enabled

    def enable(self) -> None:
        """Enable this loader."""
        self.enabled = True
        self.logger.info(f"{self.get_source_name()} enabled")

    def disable(self) -> None:
        """Disable this loader."""
        self.enabled = False
        self.logger.info(f"{self.get_source_name()} disabled")
