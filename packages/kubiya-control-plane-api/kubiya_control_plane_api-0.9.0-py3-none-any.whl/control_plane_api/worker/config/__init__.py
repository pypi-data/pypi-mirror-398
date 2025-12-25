"""
Configuration module for Temporal workers.

This module provides configuration management for workers.
"""

from .worker_config import WorkerConfig

# Create singleton instance
_worker_config = None


def get_worker_config() -> WorkerConfig:
    """
    Get or create the worker configuration singleton.
    
    Returns:
        WorkerConfig instance
    """
    global _worker_config
    
    if _worker_config is None:
        _worker_config = WorkerConfig()
    
    return _worker_config


__all__ = [
    "WorkerConfig",
    "get_worker_config",
]
