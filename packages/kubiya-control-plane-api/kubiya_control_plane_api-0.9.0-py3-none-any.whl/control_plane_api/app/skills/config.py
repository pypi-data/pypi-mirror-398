"""
Skills Configuration

Environment variable based configuration for dynamic skill loading.
"""

import os
from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)


def get_skill_template_paths() -> List[str]:
    """
    Get skill template paths from environment variables.

    Environment Variables:
        KUBIYA_SKILLS_TEMPLATES_PATH: Primary skills template directory
        KUBIYA_SKILLS_EXTRA_PATHS: Additional paths (colon-separated on Unix, semicolon on Windows)

    Returns:
        List of paths to search for skill templates
    """
    paths = []

    # Primary path from environment
    primary_path = os.getenv("KUBIYA_SKILLS_TEMPLATES_PATH")
    if primary_path:
        paths.append(primary_path)

    # Extra paths (colon-separated on Unix, semicolon on Windows)
    extra_paths_str = os.getenv("KUBIYA_SKILLS_EXTRA_PATHS", "")
    separator = ";" if os.name == "nt" else ":"
    extra_paths = [p.strip() for p in extra_paths_str.split(separator) if p.strip()]
    paths.extend(extra_paths)

    # Default: ~/.kubiya/skills if nothing configured
    if not paths:
        default_path = Path.home() / ".kubiya" / "skills"
        if default_path.exists():
            paths.append(str(default_path))

    logger.info(f"Skill template paths configured: {paths}")
    return paths


def is_dynamic_skills_enabled() -> bool:
    """
    Check if dynamic skill loading is enabled.

    Environment Variable:
        KUBIYA_ENABLE_DYNAMIC_SKILLS: Set to 'true', '1', or 'yes' to enable

    Returns:
        True if dynamic skills are enabled
    """
    enabled_str = os.getenv("KUBIYA_ENABLE_DYNAMIC_SKILLS", "true").lower()
    enabled = enabled_str in ("true", "1", "yes")

    logger.info(f"Dynamic skills loading enabled: {enabled}")
    return enabled
