"""
Skill Registry

Central registry for all available skills. Skills self-register
when their modules are imported, or can be loaded dynamically from external sources.
"""
from typing import Dict, List, Optional
from .base import SkillDefinition, SkillType
import logging

logger = logging.getLogger(__name__)


class SkillRegistry:
    """Registry for all available skill definitions"""

    def __init__(self):
        self._skills: Dict[SkillType, SkillDefinition] = {}
        self._dynamic_loaded = False

    def register(self, skill: SkillDefinition):
        """Register a skill definition"""
        if skill.type in self._skills:
            logger.warning(f"Skill {skill.type} is already registered, overwriting")

        self._skills[skill.type] = skill
        logger.info(f"Registered skill: {skill.type} - {skill.name}")

    def load_from_loaders(self, loaders: List) -> int:
        """
        Load skills from multiple loaders.

        Args:
            loaders: List of BaseSkillTemplateLoader instances

        Returns:
            Number of skills loaded
        """
        loaded_count = 0

        for loader in loaders:
            if not loader.is_enabled():
                logger.info(f"Skipping disabled loader: {loader.get_source_name()}")
                continue

            try:
                logger.info(f"Loading skills from: {loader.get_source_name()}")
                skills = loader.discover()

                for skill in skills:
                    try:
                        self.register(skill)
                        loaded_count += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to register skill {skill.name}: {e}",
                            exc_info=True
                        )

            except Exception as e:
                logger.error(
                    f"Loader {loader.get_source_name()} failed: {e}",
                    exc_info=True
                )

        self._dynamic_loaded = True
        logger.info(f"Loaded {loaded_count} skills from {len(loaders)} loaders")
        return loaded_count

    def get(self, skill_type: SkillType) -> Optional[SkillDefinition]:
        """Get a skill definition by type"""
        return self._skills.get(skill_type)

    def get_all(self) -> List[SkillDefinition]:
        """Get all registered skills"""
        return list(self._skills.values())

    def get_by_name(self, name: str) -> Optional[SkillDefinition]:
        """Get a skill by name"""
        for skill in self._skills.values():
            if skill.name.lower() == name.lower():
                return skill
        return None

    def list_types(self) -> List[SkillType]:
        """List all registered skill types"""
        return list(self._skills.keys())

    def is_dynamic_loaded(self) -> bool:
        """Check if dynamic skills have been loaded"""
        return self._dynamic_loaded

    def get_stats(self) -> Dict[str, any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry stats
        """
        return {
            "total_skills": len(self._skills),
            "skill_types": [str(st) for st in self._skills.keys()],
            "skill_names": [skill.name for skill in self._skills.values()],
            "dynamic_loaded": self._dynamic_loaded,
        }


# Global registry instance
skill_registry = SkillRegistry()


def register_skill(skill: SkillDefinition):
    """Decorator or function to register a skill"""
    skill_registry.register(skill)
    return skill


def get_skill(skill_type: SkillType) -> Optional[SkillDefinition]:
    """Get a skill definition by type"""
    return skill_registry.get(skill_type)


def get_all_skills() -> List[SkillDefinition]:
    """Get all registered skills"""
    return skill_registry.get_all()
