"""Workspace management for execution isolation.

Provides utilities for creating and managing execution-scoped workspaces
where skills can safely operate without affecting global filesystem.

Pattern: .kubiya/workspaces/<execution-id>/
"""

from pathlib import Path
import re
import structlog

logger = structlog.get_logger(__name__)

# Module-level constants
WORKSPACE_ROOT = ".kubiya/workspaces"
MAX_EXECUTION_ID_LENGTH = 200

# Unsafe filesystem characters to sanitize
UNSAFE_CHARS_PATTERN = re.compile(r'[/\\:*?"<>|]')


def ensure_workspace(execution_id: str) -> Path:
    """
    Create or return a workspace directory path for a given execution ID.

    Purpose:
    - Provides an isolated directory for each execution
    - Used by file_system and shell skills for bounded operations
    - Prevents global filesystem modifications

    Path Created:
    - .kubiya/workspaces/<execution-id>/

    Behavior:
    - Creates directory if it doesn't exist
    - Returns existing path if already created
    - Parent directories created automatically with proper permissions

    Args:
        execution_id: Unique execution identifier (from RuntimeExecutionContext)

    Returns:
        Path object pointing to the workspace directory
        (Caller converts to str with str(workspace_path))

    Raises:
        ValueError: If execution_id is None/empty or unsafe for filesystem
        OSError: If directory creation fails (permission denied, etc.)

    Usage:
        workspace_path = ensure_workspace(execution_id)
        skill_instance = FileSystemTools(base_directory=str(workspace_path))
    """
    # Validate execution_id
    if not execution_id:
        logger.error(
            "workspace_creation_failed",
            error="execution_id is None or empty",
            error_type="ValueError",
        )
        raise ValueError("execution_id must be a non-empty string")

    # Sanitize execution_id for filesystem safety
    sanitized_id = UNSAFE_CHARS_PATTERN.sub("_", execution_id)

    # Truncate if too long
    if len(sanitized_id) > MAX_EXECUTION_ID_LENGTH:
        original_length = len(sanitized_id)
        sanitized_id = sanitized_id[:MAX_EXECUTION_ID_LENGTH]
        logger.warning(
            "workspace_execution_id_truncated",
            original_length=original_length,
            max_length=MAX_EXECUTION_ID_LENGTH,
            execution_id=sanitized_id[:8] if len(sanitized_id) >= 8 else sanitized_id,
        )

    # Log warning if sanitization was applied
    if sanitized_id != execution_id:
        logger.warning(
            "workspace_execution_id_sanitized",
            original=execution_id[:50] if len(execution_id) >= 50 else execution_id,
            sanitized=sanitized_id[:50] if len(sanitized_id) >= 50 else sanitized_id,
        )

    # Build workspace path relative to current working directory
    workspace_path = Path.cwd() / WORKSPACE_ROOT / sanitized_id

    # Create directory (idempotent with exist_ok=True)
    try:
        workspace_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            "execution_workspace_ensured",
            execution_id=sanitized_id[:8] if len(sanitized_id) >= 8 else sanitized_id,
            path=str(workspace_path),
        )

        return workspace_path

    except OSError as e:
        logger.error(
            "workspace_directory_creation_failed",
            execution_id=sanitized_id[:8] if len(sanitized_id) >= 8 else sanitized_id,
            path=str(workspace_path),
            error=str(e),
            error_type=type(e).__name__,
        )
        # Let exception propagate - caller handles with try/except
        raise


def should_use_custom_base_directory(skill_data: dict) -> bool:
    """
    Check if skill has explicitly configured base_directory.

    Purpose:
    - Prevents overriding user-specified base directories
    - Allows skills to use custom paths when explicitly configured

    Configuration Structure:
        skill_data = {
            "name": "file_system",
            "type": "file_system",
            "configuration": {
                "base_directory": "/custom/path",  # If present, return True
                ...
            },
            "enabled": True,
            "execution_id": "..."
        }

    Args:
        skill_data: Skill configuration dict from Control Plane

    Returns:
        True if skill_data["configuration"]["base_directory"] is set to a non-empty value
        False if base_directory is missing, None, empty string, or invalid

    Usage:
        if not should_use_custom_base_directory(skill_data):
            config["base_directory"] = workspace_path
    """
    # Safe dictionary access with defaults
    if not skill_data:
        return False

    configuration = skill_data.get("configuration", {})
    if not configuration:
        return False

    base_directory = configuration.get("base_directory")

    # Check if base_directory is set to a non-empty value
    if base_directory is None:
        return False

    # Handle empty strings and whitespace
    if isinstance(base_directory, str) and not base_directory.strip():
        return False

    # base_directory is explicitly set
    return True
