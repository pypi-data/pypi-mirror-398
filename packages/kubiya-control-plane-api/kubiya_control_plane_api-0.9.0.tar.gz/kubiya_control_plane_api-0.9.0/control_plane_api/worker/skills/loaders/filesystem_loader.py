"""
Filesystem Skill Loader

Discovers skills from filesystem directories by scanning for skill.yaml files.
"""
import yaml
import importlib.util
import sys
import json
from pathlib import Path
from typing import List, Type, Dict, Any
import structlog

from .base import BaseSkillLoader
from control_plane_api.worker.skills.registry import LoadedSkill, SkillSource

logger = structlog.get_logger()

# Try to import jsonschema for validation (optional dependency)
try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    logger.warning(
        "jsonschema_not_available",
        message="Install jsonschema package for skill.yaml validation: pip install jsonschema"
    )


def validate_skill_yaml(manifest: Dict[str, Any], yaml_path: Path) -> None:
    """
    Issue #6 Fix: Validate skill.yaml structure against JSON schema.

    Args:
        manifest: Parsed YAML manifest
        yaml_path: Path to the YAML file for error reporting

    Raises:
        ValueError: If validation fails
    """
    if not JSONSCHEMA_AVAILABLE:
        logger.debug(
            "skipping_skill_yaml_validation",
            yaml_path=str(yaml_path),
            reason="jsonschema not installed",
        )
        return

    # Load schema
    schema_path = Path(__file__).parent.parent / "skill_yaml_schema.json"
    if not schema_path.exists():
        logger.warning(
            "skill_yaml_schema_not_found",
            schema_path=str(schema_path),
            yaml_path=str(yaml_path),
        )
        return

    try:
        with open(schema_path) as f:
            schema = json.load(f)

        # Validate
        jsonschema.validate(instance=manifest, schema=schema)

        logger.debug(
            "skill_yaml_validation_passed",
            yaml_path=str(yaml_path),
            skill_name=manifest.get("metadata", {}).get("name", "unknown"),
        )

    except jsonschema.ValidationError as e:
        # Build helpful error message
        error_path = " -> ".join(str(p) for p in e.path) if e.path else "root"
        error_msg = (
            f"Invalid skill.yaml at {yaml_path}\n"
            f"Location: {error_path}\n"
            f"Error: {e.message}\n\n"
            f"Schema requirement: {e.schema.get('description', 'No description')}\n"
        )

        # Add suggestions based on common errors
        if "required" in e.message.lower():
            error_msg += f"\nMissing required fields. Check the skill.yaml schema.\n"
        elif "enum" in str(e.schema):
            allowed = e.schema.get("enum", [])
            error_msg += f"\nAllowed values: {allowed}\n"

        logger.error(
            "skill_yaml_validation_failed",
            yaml_path=str(yaml_path),
            error_path=error_path,
            error_message=e.message,
            schema_path=str(schema_path),
        )

        raise ValueError(error_msg)

    except Exception as e:
        logger.error(
            "skill_yaml_validation_error",
            yaml_path=str(yaml_path),
            error=str(e),
            exc_info=True,
        )
        raise ValueError(f"Failed to validate skill.yaml at {yaml_path}: {str(e)}")


class FilesystemSkillLoader(BaseSkillLoader):
    """
    Load skills from filesystem directories.

    Scans for skill.yaml files in configured paths.
    """

    def __init__(self, search_paths: List[Path]):
        self.search_paths = [Path(p) for p in search_paths]
        self.logger = structlog.get_logger()

    def discover(self) -> List[LoadedSkill]:
        """
        Discover skills by scanning filesystem for skill.yaml files.
        """
        skills = []

        for search_path in self.search_paths:
            if not search_path.exists():
                self.logger.debug("search_path_not_found", path=str(search_path))
                continue

            # Find all skill.yaml files
            for skill_yaml in search_path.rglob("skill.yaml"):
                try:
                    skill = self._load_skill_from_yaml(skill_yaml)
                    skills.append(skill)
                    self.logger.info(
                        "skill_discovered",
                        name=skill.name,
                        path=str(skill_yaml.parent),
                    )
                except Exception as e:
                    self.logger.error(
                        "failed_to_load_skill",
                        path=str(skill_yaml),
                        error=str(e),
                        exc_info=True,
                    )

        return skills

    def _load_skill_from_yaml(self, yaml_path: Path) -> LoadedSkill:
        """Load a skill from a skill.yaml file."""
        with open(yaml_path) as f:
            manifest = yaml.safe_load(f)

        # Issue #6 Fix: Validate skill.yaml before parsing
        validate_skill_yaml(manifest, yaml_path)

        skill_dir = yaml_path.parent
        metadata = manifest.get("metadata", {})
        spec = manifest.get("spec", {})

        # Load implementations
        implementations = {}
        impl_configs = spec.get("implementations", {})

        if not impl_configs:
            raise ValueError(f"No implementations defined in {yaml_path}")

        # Track failed implementations for better error reporting
        failed_implementations = {}

        for runtime, impl_info in impl_configs.items():
            try:
                # Check if this is a builtin runtime implementation
                if impl_info.get("builtin", False):
                    # Builtin implementations (like Claude Code SDK tools)
                    # Store metadata about builtin tools instead of Python class
                    implementations[runtime] = {
                        "builtin": True,
                        "tools": impl_info.get("tools", []),
                    }
                    self.logger.debug(
                        "builtin_implementation_registered",
                        skill=metadata["name"],
                        runtime=runtime,
                        tools=impl_info.get("tools", []),
                    )
                    continue

                module_name = impl_info["module"]
                class_name = impl_info["class"]

                # Import the module
                impl_class = self._import_class_from_skill(
                    skill_dir, module_name, class_name
                )
                implementations[runtime] = impl_class

                self.logger.info(
                    "implementation_loaded_successfully",
                    skill=metadata["name"],
                    runtime=runtime,
                    class_name=class_name,
                    module_path=str(skill_dir / f"{module_name}.py"),
                )
            except FileNotFoundError as e:
                # Issue #3 Fix: Fail loudly with actionable error
                error_detail = str(e)
                failed_implementations[runtime] = error_detail
                self.logger.error(
                    "implementation_file_not_found",
                    skill=metadata["name"],
                    runtime=runtime,
                    error=error_detail,
                    module_name=module_name,
                    expected_path=str(skill_dir / f"{module_name}.py"),
                    recovery_suggestion=f"Create the file '{module_name}.py' in {skill_dir} or update the skill.yaml to reference an existing module.",
                )
            except AttributeError as e:
                # Issue #3 Fix: Class not found in module
                error_detail = str(e)
                failed_implementations[runtime] = error_detail
                self.logger.error(
                    "implementation_class_not_found",
                    skill=metadata["name"],
                    runtime=runtime,
                    error=error_detail,
                    class_name=class_name,
                    module_name=module_name,
                    recovery_suggestion=f"Ensure class '{class_name}' exists in '{module_name}.py' or update the skill.yaml with the correct class name.",
                )
            except ImportError as e:
                # Issue #3 Fix: Module import failed
                error_detail = str(e)
                failed_implementations[runtime] = error_detail
                self.logger.error(
                    "implementation_import_failed",
                    skill=metadata["name"],
                    runtime=runtime,
                    error=error_detail,
                    module_name=module_name,
                    recovery_suggestion=f"Check that '{module_name}.py' is valid Python and all dependencies are installed. Error: {error_detail}",
                )
            except Exception as e:
                # Issue #3 Fix: Generic implementation failure
                error_detail = str(e)
                failed_implementations[runtime] = error_detail
                self.logger.error(
                    "implementation_load_failed",
                    skill=metadata["name"],
                    runtime=runtime,
                    error=error_detail,
                    error_type=type(e).__name__,
                    recovery_suggestion="Check the implementation file for syntax errors or missing dependencies.",
                    exc_info=True,
                )

        # Issue #3 Fix: Fail loudly if no valid implementations
        if not implementations:
            error_summary = "\n".join([
                f"  - {runtime}: {error}"
                for runtime, error in failed_implementations.items()
            ])
            raise ValueError(
                f"Failed to load any implementations for skill '{metadata['name']}' from {yaml_path}.\n"
                f"All {len(impl_configs)} runtime(s) failed:\n{error_summary}\n\n"
                f"Recovery steps:\n"
                f"1. Check that implementation files exist in {skill_dir}\n"
                f"2. Verify module and class names in skill.yaml match actual files\n"
                f"3. Ensure all dependencies are installed\n"
                f"4. Check implementation files for syntax errors"
            )

        return LoadedSkill(
            name=metadata["name"],
            version=metadata.get("version", "0.0.0"),
            source=self._get_source_for_path(yaml_path),
            skill_type=spec.get("type", "custom"),
            manifest=manifest,
            implementations=implementations,
            metadata={
                "path": str(skill_dir),
                "yaml_path": str(yaml_path),
            },
        )

    def _import_class_from_skill(
        self, skill_dir: Path, module_name: str, class_name: str
    ) -> Type:
        """
        Dynamically import a class from a skill's module.

        Args:
            skill_dir: Directory containing the skill
            module_name: Module name (e.g., "implementation" or "agno_impl")
            class_name: Class name to import

        Returns:
            The imported class
        """
        # Convert module name to file path
        module_file = skill_dir / f"{module_name}.py"

        if not module_file.exists():
            raise FileNotFoundError(f"Module file not found: {module_file}")

        # Create unique module name to avoid collisions
        unique_module_name = f"skill_{skill_dir.name}_{module_name}"

        # Load the module
        spec = importlib.util.spec_from_file_location(unique_module_name, module_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module spec from {module_file}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[unique_module_name] = module
        spec.loader.exec_module(module)

        # Get the class
        if not hasattr(module, class_name):
            raise AttributeError(
                f"Class '{class_name}' not found in module {module_file}"
            )

        return getattr(module, class_name)

    def _get_source_for_path(self, yaml_path: Path) -> SkillSource:
        """Determine source type based on path."""
        path_str = str(yaml_path.resolve())

        # Check if it's in user workspace (.kubiya/skills in current dir)
        if ".kubiya/skills" in path_str and Path.cwd() in yaml_path.parents:
            return SkillSource.USER_WORKSPACE

        # Check if it's in global user directory (~/.kubiya/skills)
        global_skills = Path.home() / ".kubiya/skills"
        if global_skills in yaml_path.parents:
            return SkillSource.USER_GLOBAL

        # Default to builtin
        return SkillSource.BUILTIN

    def get_source_type(self) -> SkillSource:
        return SkillSource.USER_WORKSPACE

    def load_skill(self, skill_id: str) -> LoadedSkill:
        """Load a specific skill by searching for its directory."""
        for search_path in self.search_paths:
            skill_path = search_path / skill_id / "skill.yaml"
            if skill_path.exists():
                return self._load_skill_from_yaml(skill_path)

        raise FileNotFoundError(
            f"Skill '{skill_id}' not found in search paths: {self.search_paths}"
        )
