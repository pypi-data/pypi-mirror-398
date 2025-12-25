"""
Storage configuration settings.

Manages storage provider configuration and quota settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, AliasChoices
from typing import Optional


class StorageConfig(BaseSettings):
    """Storage provider and quota configuration."""

    # ============================================================================
    # Provider Selection
    # ============================================================================

    storage_provider: Optional[str] = Field(
        default=None,
        description="Storage provider type: vercel_blob, s3, azure_blob, gcs. REQUIRED - no default",
        validation_alias=AliasChoices("STORAGE_PROVIDER", "storage_provider")
    )

    # ============================================================================
    # Vercel Blob Configuration
    # ============================================================================

    vercel_blob_token: Optional[str] = Field(
        default=None,
        description="Vercel Blob storage authentication token",
        validation_alias=AliasChoices("VERCEL_BLOB_TOKEN", "vercel_blob_token")
    )

    vercel_blob_store_name: Optional[str] = Field(
        default=None,
        description="Vercel Blob store name (optional, uses default store if not specified)",
        validation_alias=AliasChoices("VERCEL_BLOB_STORE_NAME", "vercel_blob_store_name")
    )

    # ============================================================================
    # S3 Configuration (Future)
    # ============================================================================

    s3_bucket_name: Optional[str] = Field(
        default=None,
        description="AWS S3 bucket name",
        validation_alias=AliasChoices("S3_BUCKET_NAME", "s3_bucket_name")
    )

    s3_region: Optional[str] = Field(
        default=None,
        description="AWS S3 region",
        validation_alias=AliasChoices("S3_REGION", "s3_region")
    )

    s3_access_key: Optional[str] = Field(
        default=None,
        description="AWS S3 access key ID",
        validation_alias=AliasChoices("S3_ACCESS_KEY", "AWS_ACCESS_KEY_ID", "s3_access_key")
    )

    s3_secret_key: Optional[str] = Field(
        default=None,
        description="AWS S3 secret access key",
        validation_alias=AliasChoices("S3_SECRET_KEY", "AWS_SECRET_ACCESS_KEY", "s3_secret_key")
    )

    # ============================================================================
    # Azure Blob Configuration (Future)
    # ============================================================================

    azure_blob_connection_string: Optional[str] = Field(
        default=None,
        description="Azure Blob Storage connection string",
        validation_alias=AliasChoices(
            "AZURE_BLOB_CONNECTION_STRING",
            "AZURE_STORAGE_CONNECTION_STRING",
            "azure_blob_connection_string"
        )
    )

    azure_blob_container_name: Optional[str] = Field(
        default=None,
        description="Azure Blob container name",
        validation_alias=AliasChoices("AZURE_BLOB_CONTAINER_NAME", "azure_blob_container_name")
    )

    # ============================================================================
    # GCS Configuration (Future)
    # ============================================================================

    gcs_bucket_name: Optional[str] = Field(
        default=None,
        description="Google Cloud Storage bucket name",
        validation_alias=AliasChoices("GCS_BUCKET_NAME", "gcs_bucket_name")
    )

    gcs_credentials_path: Optional[str] = Field(
        default=None,
        description="Path to GCS service account credentials JSON file",
        validation_alias=AliasChoices("GCS_CREDENTIALS_PATH", "GOOGLE_APPLICATION_CREDENTIALS", "gcs_credentials_path")
    )

    # ============================================================================
    # Quota Settings
    # ============================================================================

    storage_default_limit_gb: int = Field(
        default=1,
        description="Default storage quota per organization in gigabytes",
        validation_alias=AliasChoices("STORAGE_DEFAULT_LIMIT_GB", "storage_default_limit_gb"),
        ge=0
    )

    storage_limits_config_path: str = Field(
        default="conf/storage/limits_override.yaml",
        description="Path to YAML file with per-organization quota overrides",
        validation_alias=AliasChoices("STORAGE_LIMITS_CONFIG_PATH", "storage_limits_config_path")
    )

    # ============================================================================
    # Feature Flags
    # ============================================================================

    storage_enable_versioning: bool = Field(
        default=False,
        description="Enable file versioning (future feature)",
        validation_alias=AliasChoices("STORAGE_ENABLE_VERSIONING", "storage_enable_versioning")
    )

    storage_enable_encryption: bool = Field(
        default=False,
        description="Enable client-side encryption (future feature)",
        validation_alias=AliasChoices("STORAGE_ENABLE_ENCRYPTION", "storage_enable_encryption")
    )

    class Config:
        """Pydantic configuration."""
        env_file = ".env.local"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
_storage_config: Optional[StorageConfig] = None


def get_storage_config() -> StorageConfig:
    """
    Get or create storage configuration singleton.

    Returns:
        StorageConfig instance
    """
    global _storage_config
    if _storage_config is None:
        _storage_config = StorageConfig()
    return _storage_config
