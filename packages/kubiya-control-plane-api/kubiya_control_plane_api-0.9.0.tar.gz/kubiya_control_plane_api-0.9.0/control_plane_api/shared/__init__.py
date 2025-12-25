"""
Shared utilities and constants accessible to both API and worker packages.
"""

# Re-export from unified version module for backward compatibility
from control_plane_api.version import __version__, get_sdk_version

__all__ = ["__version__", "get_sdk_version"]
