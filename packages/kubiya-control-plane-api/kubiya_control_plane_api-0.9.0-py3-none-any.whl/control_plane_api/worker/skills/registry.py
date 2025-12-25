"""
Worker-side Skill Registry

Central registry for all skills available to the worker.
Discovers and tracks skills from multiple sources (filesystem, API, packages).
"""
from typing import Dict, List, Optional, Type, Any, Union
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()


class SkillSource(str, Enum):
    """Source where skill was loaded from."""
    CONTROL_PLANE_API = "api"           # Centralized skills from DB
    USER_WORKSPACE = "workspace"        # .kubiya/skills/ in project
    USER_GLOBAL = "global"              # ~/.kubiya/skills/
    PYTHON_PACKAGE = "package"          # pip installed packages
    GIT_REPOSITORY = "git"              # Git repos
    BUILTIN = "builtin"                 # Built-in skills


@dataclass
class LoadedSkill:
    """A loaded and ready-to-use skill."""
    name: str
    version: str
    source: SkillSource
    skill_type: str  # e.g., "shell", "file_system", "custom"
    manifest: Dict[str, Any]  # Parsed skill.yaml or metadata
    implementations: Dict[str, Union[Type, Dict[str, Any]]]  # Runtime -> class or builtin config
    metadata: Dict[str, Any]  # Additional metadata (path, etc.)


class SkillRegistry:
    """
    Central registry for all skills on worker side.

    Responsibilities:
    - Track loaded skills
    - Resolve dependencies
    - Handle versioning
    - Match skills to runtimes
    """

    def __init__(self):
        self._skills: Dict[str, LoadedSkill] = {}
        self._skills_by_type: Dict[str, List[LoadedSkill]] = {}
        self.logger = structlog.get_logger()

    def register(self, skill: LoadedSkill) -> None:
        """Register a loaded skill."""
        skill_key = f"{skill.name}:{skill.version}"

        if skill_key in self._skills:
            self.logger.warning(
                "skill_already_registered",
                name=skill.name,
                version=skill.version,
                existing_source=self._skills[skill_key].source,
                new_source=skill.source,
            )
            # Source priority: builtin < global < workspace < git < package < api
            if self._should_replace(self._skills[skill_key].source, skill.source):
                self._skills[skill_key] = skill
                self.logger.info("skill_replaced", name=skill.name)
        else:
            self._skills[skill_key] = skill
            self.logger.info(
                "skill_registered",
                name=skill.name,
                version=skill.version,
                source=skill.source,
                skill_type=skill.skill_type,
            )

        # Index by type for faster lookup
        if skill.skill_type not in self._skills_by_type:
            self._skills_by_type[skill.skill_type] = []

        # Remove old version if exists
        self._skills_by_type[skill.skill_type] = [
            s for s in self._skills_by_type[skill.skill_type]
            if s.name != skill.name
        ]
        self._skills_by_type[skill.skill_type].append(skill)

    def get(self, name: str, version: Optional[str] = None) -> Optional[LoadedSkill]:
        """
        Get a skill by name and optional version.

        If version not specified, returns latest version.
        """
        if version:
            return self._skills.get(f"{name}:{version}")

        # Get latest version
        matching = [s for s in self._skills.values() if s.name == name]
        if not matching:
            return None

        # Sort by semantic version
        try:
            from packaging import version as pkg_version
            return max(matching, key=lambda s: pkg_version.parse(s.version))
        except:
            # Fallback to simple comparison if packaging not available
            return matching[0]

    def get_by_type(self, skill_type: str) -> Optional[LoadedSkill]:
        """
        Get a skill by type (e.g., "shell", "file_system").

        Returns the first registered skill of that type.
        Useful for built-in skills where type maps 1:1 to skill.
        """
        skills = self._skills_by_type.get(skill_type, [])
        return skills[0] if skills else None

    def list_skills(self, source: Optional[SkillSource] = None) -> List[LoadedSkill]:
        """List all registered skills, optionally filtered by source."""
        skills = list(self._skills.values())
        if source:
            skills = [s for s in skills if s.source == source]
        return skills

    def get_implementation_for_runtime(
        self, skill: LoadedSkill, runtime_type: str
    ) -> Optional[Union[Type, Dict[str, Any]]]:
        """
        Get the appropriate implementation class for a specific runtime.

        Falls back to 'default' implementation if runtime-specific not available.

        Returns:
            Either a Python class (Type) or a dict with builtin config
        """
        # Check runtime-specific implementation
        impl = skill.implementations.get(runtime_type)
        if impl:
            return impl

        # Fall back to default implementation
        return skill.implementations.get("default")

    def resolve_dependencies(self, skill: LoadedSkill) -> List[str]:
        """
        Resolve skill dependencies.

        Returns list of missing dependency names.
        """
        missing = []
        dependencies = skill.manifest.get("spec", {}).get("dependencies", [])

        for dep in dependencies:
            dep_name = dep["name"]
            dep_version = dep.get("version", ">=0.0.0")

            resolved = self.get(dep_name)
            if not resolved:
                if not dep.get("optional", False):
                    missing.append(f"{dep_name} {dep_version}")
            else:
                # Check version constraint
                try:
                    from packaging import version, specifiers
                    spec = specifiers.SpecifierSet(dep_version)
                    if not spec.contains(resolved.version):
                        missing.append(
                            f"{dep_name} {dep_version} (found {resolved.version})"
                        )
                except:
                    # Skip version check if packaging not available
                    pass

        return missing

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_skills": len(self._skills),
            "skills_by_source": {
                source.value: len([s for s in self._skills.values() if s.source == source])
                for source in SkillSource
            },
            "skills_by_type": {
                skill_type: len(skills)
                for skill_type, skills in self._skills_by_type.items()
            },
        }

    def _should_replace(self, existing: SkillSource, new: SkillSource) -> bool:
        """Determine if new source should replace existing based on priority."""
        priority = {
            SkillSource.BUILTIN: 1,
            SkillSource.USER_GLOBAL: 2,
            SkillSource.USER_WORKSPACE: 3,
            SkillSource.GIT_REPOSITORY: 4,
            SkillSource.PYTHON_PACKAGE: 5,
            SkillSource.CONTROL_PLANE_API: 6,
        }
        return priority.get(new, 0) > priority.get(existing, 0)


# Global registry instance
skill_registry = SkillRegistry()
