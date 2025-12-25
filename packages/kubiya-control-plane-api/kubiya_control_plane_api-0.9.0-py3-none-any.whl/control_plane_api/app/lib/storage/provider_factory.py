"""
Storage provider factory for creating and managing storage provider instances.

Supports multiple providers with environment-based configuration.
"""

from typing import Optional
import os
import structlog

from .base_provider import StorageProvider
from .vercel_blob_provider import VercelBlobStorageProvider

logger = structlog.get_logger()


class StorageProviderFactory:
    """Factory for creating storage provider instances based on configuration."""

    @staticmethod
    def create_provider(
        provider_type: Optional[str] = None,
        config: Optional[dict] = None
    ) -> StorageProvider:
        """
        Create a storage provider instance.

        Args:
            provider_type: Provider name ('vercel_blob', 's3', 'azure_blob', 'gcs')
                          If None, uses STORAGE_PROVIDER environment variable
            config: Provider-specific configuration dict (optional)

        Returns:
            StorageProvider instance

        Raises:
            ValueError: If provider is not configured, invalid, or missing required config
        """
        # Get provider from parameter or environment
        provider_type = provider_type or os.environ.get("STORAGE_PROVIDER")

        if not provider_type:
            raise ValueError(
                "No storage provider configured. "
                "Set STORAGE_PROVIDER environment variable to one of: "
                "vercel_blob, s3, azure_blob, gcs"
            )

        provider_type = provider_type.lower().strip()

        logger.info("storage_provider_factory_creating", provider_type=provider_type)

        # Vercel Blob Storage
        if provider_type == "vercel_blob":
            token = os.environ.get("VERCEL_BLOB_TOKEN")
            if not token:
                raise ValueError(
                    "VERCEL_BLOB_TOKEN environment variable is required for Vercel Blob provider"
                )

            store_name = os.environ.get("VERCEL_BLOB_STORE_NAME")

            logger.info(
                "creating_vercel_blob_provider",
                store_name=store_name if store_name else "default"
            )

            return VercelBlobStorageProvider(token=token, store_name=store_name)

        # AWS S3 (future implementation)
        elif provider_type == "s3":
            raise NotImplementedError(
                "S3 provider not yet implemented. "
                "To add S3 support, implement S3StorageProvider class."
            )

        # Azure Blob Storage (future implementation)
        elif provider_type == "azure_blob":
            raise NotImplementedError(
                "Azure Blob provider not yet implemented. "
                "To add Azure Blob support, implement AzureBlobStorageProvider class."
            )

        # Google Cloud Storage (future implementation)
        elif provider_type == "gcs":
            raise NotImplementedError(
                "GCS provider not yet implemented. "
                "To add GCS support, implement GCSStorageProvider class."
            )

        # Unknown provider
        else:
            raise ValueError(
                f"Unknown storage provider: {provider_type}. "
                f"Supported providers: vercel_blob, s3, azure_blob, gcs"
            )


# Singleton instance
_provider_instance: Optional[StorageProvider] = None
_provider_lock = False  # Simple lock for singleton pattern


def get_storage_provider(force_recreate: bool = False) -> StorageProvider:
    """
    Get or create storage provider singleton.

    Args:
        force_recreate: If True, recreates the provider instance

    Returns:
        StorageProvider instance

    Raises:
        ValueError: If provider is not configured

    Note:
        This is a singleton pattern to reuse HTTP clients and connections.
        The provider is created once per application lifecycle.
    """
    global _provider_instance, _provider_lock

    if force_recreate:
        _provider_instance = None

    if _provider_instance is None:
        if _provider_lock:
            # Simple wait if another thread is creating
            import time
            timeout = 5  # 5 second timeout
            start = time.time()
            while _provider_lock and (time.time() - start) < timeout:
                time.sleep(0.1)

        if _provider_instance is None:
            _provider_lock = True
            try:
                _provider_instance = StorageProviderFactory.create_provider()
                logger.info(
                    "storage_provider_singleton_created",
                    provider=_provider_instance.get_provider_name()
                )
            finally:
                _provider_lock = False

    return _provider_instance


def reset_storage_provider():
    """
    Reset the singleton instance.

    Useful for testing or when configuration changes.
    """
    global _provider_instance
    _provider_instance = None
    logger.info("storage_provider_singleton_reset")
