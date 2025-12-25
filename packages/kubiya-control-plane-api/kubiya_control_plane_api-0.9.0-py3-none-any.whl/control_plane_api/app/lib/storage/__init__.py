"""
Storage provider module for remote filesystem support.

Provides abstract base classes and implementations for different storage providers:
- Vercel Blob Storage
- AWS S3 (future)
- Azure Blob Storage (future)
- Google Cloud Storage (future)
"""

from .base_provider import StorageProvider, StorageFile, UploadResult
from .provider_factory import StorageProviderFactory, get_storage_provider

__all__ = [
    "StorageProvider",
    "StorageFile",
    "UploadResult",
    "StorageProviderFactory",
    "get_storage_provider",
]
