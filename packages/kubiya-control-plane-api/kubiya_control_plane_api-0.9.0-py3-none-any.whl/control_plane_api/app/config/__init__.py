"""
Configuration module for Control Plane API.

This module provides separate configuration classes for API and shared settings.
"""

from .api_config import APIConfig

# Create singleton instance
_api_config = None


def get_api_config() -> APIConfig:
    """
    Get or create the API configuration singleton.
    
    Returns:
        APIConfig instance
    """
    global _api_config
    
    if _api_config is None:
        _api_config = APIConfig()
    
    return _api_config


# For backward compatibility with existing code
settings = get_api_config()

__all__ = [
    "APIConfig",
    "get_api_config",
    "settings",
]
