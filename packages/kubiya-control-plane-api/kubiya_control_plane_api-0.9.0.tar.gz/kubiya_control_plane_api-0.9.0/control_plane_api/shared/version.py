"""DEPRECATED: Use control_plane_api.version instead

This file is kept for backward compatibility only.
All new code should import from control_plane_api.version

Kubiya Control Plane SDK Version

This version must match between worker and control plane for compatibility.
Workers will check this version during registration and exit if mismatched.

Version is read from version.txt in the repository root (single source of truth).
"""

# Re-export from unified version module
from control_plane_api.version import get_sdk_version, __version__

__all__ = ["__version__", "get_sdk_version"]
