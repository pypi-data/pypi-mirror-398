"""Unified version management for Control Plane API.

This is the ONLY authoritative source for SDK version.
Version.txt is the single source of truth.
"""
from pathlib import Path


def get_sdk_version() -> str:
    """Get the SDK version from version.txt.

    Attempts multiple paths to handle:
    - Development (running from source)
    - Installed packages (pip install)
    - Docker containers

    Returns:
        str: Version string (e.g., "0.6.0")
    """
    paths_to_try = [
        Path(__file__).parent.parent / "version.txt",  # Dev: repo_root/version.txt
        Path(__file__).parent.parent.absolute() / "version.txt",  # Absolute path (sandbox-safe)
        Path("/app/version.txt"),  # Docker container
    ]

    for version_file in paths_to_try:
        try:
            if version_file.exists():
                return version_file.read_text().strip()
        except Exception:
            pass

    # Fallback (update this when version.txt changes)
    return "0.6.0"


__version__ = get_sdk_version()
__all__ = ["__version__", "get_sdk_version"]
