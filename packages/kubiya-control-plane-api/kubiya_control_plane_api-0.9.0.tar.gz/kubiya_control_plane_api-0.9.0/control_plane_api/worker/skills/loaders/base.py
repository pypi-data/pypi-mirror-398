"""Base loader interface for skill discovery."""
from abc import ABC, abstractmethod
from typing import List
from control_plane_api.worker.skills.registry import LoadedSkill, SkillSource


class BaseSkillLoader(ABC):
    """Base class for skill loaders."""

    @abstractmethod
    def discover(self) -> List[LoadedSkill]:
        """Discover available skills from this source."""
        pass

    @abstractmethod
    def get_source_type(self) -> SkillSource:
        """Get the source type for this loader."""
        pass

    @abstractmethod
    def load_skill(self, skill_id: str) -> LoadedSkill:
        """Load a specific skill by ID."""
        pass
