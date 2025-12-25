"""
Filesystem Skill Template Loader

Loads skill templates from filesystem directories containing Python skill definitions.
"""

import sys
import importlib.util
from pathlib import Path
from typing import List
import logging

from .base import BaseSkillTemplateLoader
from control_plane_api.app.skills.base import SkillDefinition

logger = logging.getLogger(__name__)


class FilesystemSkillTemplateLoader(BaseSkillTemplateLoader):
    """
    Loader for filesystem-based skill templates.

    Discovers skill templates by searching for skill_template.py files
    in configured directories (e.g., ~/.kubiya/skills/).

    Directory structure:
        ~/.kubiya/skills/
        ├── my_custom_skill/
        │   └── skill_template.py  # Contains SkillDefinition subclass
        └── another_skill/
            └── skill_template.py
    """

    def __init__(
        self,
        base_paths: List[str] = None,
        enabled: bool = True,
    ):
        """
        Initialize filesystem loader.

        Args:
            base_paths: List of base directories to search
            enabled: Whether this loader is enabled
        """
        super().__init__(enabled=enabled)

        # Default paths
        if base_paths is None:
            base_paths = []
            # Add .kubiya/skills/ from home directory
            home_skills = Path.home() / ".kubiya" / "skills"
            if home_skills.exists():
                base_paths.append(str(home_skills))

        self.base_paths = [Path(p) for p in base_paths]
        logger.info(
            f"FilesystemSkillTemplateLoader initialized with paths: {[str(p) for p in self.base_paths]}"
        )

    def discover(self) -> List[SkillDefinition]:
        """
        Discover skill templates by scanning for skill_template.py files.

        Returns:
            List of discovered SkillDefinition instances
        """
        discovered = []

        for base_path in self.base_paths:
            if not base_path.exists():
                logger.warning(f"Base path not found: {base_path}")
                continue

            # Search for skill template files
            skill_dirs = self._find_skill_directories(base_path)

            for skill_dir in skill_dirs:
                try:
                    skill_def = self._load_skill_template(skill_dir)
                    if skill_def:
                        discovered.append(skill_def)
                        logger.info(
                            f"Loaded skill template: {skill_def.name} from {skill_dir}"
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to load skill template from {skill_dir}: {e}",
                        exc_info=True
                    )

        logger.info(f"Discovered {len(discovered)} skill templates from filesystem")
        return discovered

    def _find_skill_directories(self, base_path: Path) -> List[Path]:
        """
        Find all directories containing skill_template.py files.

        Args:
            base_path: Base directory to search

        Returns:
            List of directories containing skill templates
        """
        skill_dirs = []

        for item in base_path.iterdir():
            if item.is_dir():
                skill_template = item / "skill_template.py"
                if skill_template.exists():
                    skill_dirs.append(item)

        return skill_dirs

    def _load_skill_template(self, skill_dir: Path) -> SkillDefinition:
        """
        Load skill template from a directory.

        Args:
            skill_dir: Directory containing skill_template.py

        Returns:
            SkillDefinition instance

        Raises:
            Exception: If loading fails
        """
        skill_template_path = skill_dir / "skill_template.py"

        # Add skill directory to path temporarily
        skill_dir_str = str(skill_dir)
        if skill_dir_str not in sys.path:
            sys.path.insert(0, skill_dir_str)

        try:
            # Load the module dynamically
            module_name = f"skill_template_{skill_dir.name}"
            spec = importlib.util.spec_from_file_location(
                module_name,
                skill_template_path
            )

            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load module spec from {skill_template_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find SkillDefinition subclass in module
            skill_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type) and
                    issubclass(attr, SkillDefinition) and
                    attr is not SkillDefinition
                ):
                    skill_class = attr
                    break

            if skill_class is None:
                raise ValueError(
                    f"No SkillDefinition subclass found in {skill_template_path}"
                )

            # Instantiate the skill definition
            skill_instance = skill_class()

            return skill_instance

        finally:
            # Clean up sys.path
            if skill_dir_str in sys.path:
                sys.path.remove(skill_dir_str)

    def add_base_path(self, path: str) -> None:
        """
        Add an additional base path to search.

        Args:
            path: Path to add
        """
        path_obj = Path(path)
        if path_obj not in self.base_paths:
            self.base_paths.append(path_obj)
            logger.info(f"Added base path: {path_obj}")

    def remove_base_path(self, path: str) -> None:
        """
        Remove a base path from search.

        Args:
            path: Path to remove
        """
        path_obj = Path(path)
        if path_obj in self.base_paths:
            self.base_paths.remove(path_obj)
            logger.info(f"Removed base path: {path_obj}")
