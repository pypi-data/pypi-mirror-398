"""DEPRECATED: Use control_plane_api.version instead

This file is kept for backward compatibility only.
All new code should import from control_plane_api.version
"""
from control_plane_api.version import get_sdk_version, __version__

__all__ = ["__version__", "get_sdk_version"]
