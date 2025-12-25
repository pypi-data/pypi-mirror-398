"""
Storage service for managing remote file storage with quota enforcement.

Provides high-level file operations with:
- Quota enforcement
- Usage tracking
- Multi-tenant isolation
- YAML configuration for per-org overrides
"""

from typing import BinaryIO, Dict, List, Optional, Tuple, Any
import structlog
from datetime import datetime
import yaml
import os
from io import BytesIO

from control_plane_api.app.lib.supabase import get_supabase
from control_plane_api.app.lib.storage.provider_factory import get_storage_provider
from control_plane_api.app.lib.storage.base_provider import StorageProvider

logger = structlog.get_logger()


class StorageQuotaExceeded(Exception):
    """Raised when organization exceeds storage quota."""
    pass


class StorageService:
    """
    Service for managing remote file storage with quota enforcement.

    Handles file operations, quota management, and usage tracking
    for a specific organization.
    """

    def __init__(self, organization_id: str):
        """
        Initialize storage service for an organization.

        Args:
            organization_id: Organization ID for scoping
        """
        self.organization_id = organization_id
        self.provider: StorageProvider = get_storage_provider()
        self.client = get_supabase()

        # Load quota overrides
        self.quota_overrides = self._load_quota_overrides()

        logger.info(
            "storage_service_initialized",
            organization_id=organization_id,
            provider=self.provider.get_provider_name()
        )

    def _load_quota_overrides(self) -> Dict[str, Dict[str, int]]:
        """
        Load per-organization quota overrides from YAML config.

        Returns:
            Dict mapping organization_id to quota configuration
        """
        config_path = os.environ.get(
            "STORAGE_LIMITS_CONFIG_PATH",
            "conf/storage/limits_override.yaml"
        )

        if not os.path.exists(config_path):
            logger.debug(
                "quota_overrides_file_not_found",
                path=config_path,
                using_defaults=True
            )
            return {}

        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                overrides = config.get("organizations", {})

                logger.info(
                    "quota_overrides_loaded",
                    path=config_path,
                    org_count=len(overrides)
                )

                return overrides

        except Exception as e:
            logger.warning(
                "failed_to_load_quota_overrides",
                error=str(e),
                path=config_path
            )
            return {}

    def _get_quota_limit(self) -> int:
        """
        Get quota limit for organization (in bytes).

        Returns:
            Quota limit in bytes
        """
        # Check for org-specific override
        if self.organization_id in self.quota_overrides:
            quota_gb = self.quota_overrides[self.organization_id].get("quota_gb", 1)
            return int(quota_gb * 1024 ** 3)

        # Default from environment or 1GB
        default_gb = int(os.environ.get("STORAGE_DEFAULT_LIMIT_GB", "1"))
        return default_gb * 1024 ** 3

    async def _ensure_usage_record(self):
        """Ensure usage record exists for organization."""
        try:
            result = self.client.table("storage_usage").select("*").eq(
                "organization_id", self.organization_id
            ).execute()

            if not result.data:
                quota_bytes = self._get_quota_limit()
                self.client.table("storage_usage").insert({
                    "organization_id": self.organization_id,
                    "quota_bytes": quota_bytes
                }).execute()

                logger.info(
                    "storage_usage_record_created",
                    organization_id=self.organization_id,
                    quota_bytes=quota_bytes
                )

        except Exception as e:
            logger.error(
                "failed_to_ensure_usage_record",
                error=str(e),
                organization_id=self.organization_id
            )
            raise

    async def check_quota(self, additional_bytes: int) -> Tuple[bool, Dict]:
        """
        Check if upload would exceed quota.

        Args:
            additional_bytes: Size of file to upload

        Returns:
            Tuple of (within_quota, usage_info_dict)
        """
        await self._ensure_usage_record()

        result = self.client.table("storage_usage").select("*").eq(
            "organization_id", self.organization_id
        ).single().execute()

        usage = result.data
        new_total = usage["total_bytes_used"] + additional_bytes
        within_quota = new_total <= usage["quota_bytes"]

        usage_info = {
            "current_bytes": usage["total_bytes_used"],
            "quota_bytes": usage["quota_bytes"],
            "requested_bytes": additional_bytes,
            "new_total_bytes": new_total,
            "remaining_bytes": usage["quota_bytes"] - new_total,
            "usage_percentage": (new_total / usage["quota_bytes"]) * 100 if usage["quota_bytes"] > 0 else 100
        }

        logger.info(
            "quota_check",
            organization_id=self.organization_id,
            within_quota=within_quota,
            usage_percentage=usage_info["usage_percentage"]
        )

        return within_quota, usage_info

    async def upload_file(
        self,
        file_content: BinaryIO,
        file_name: str,
        file_path: str,
        content_type: str,
        uploaded_by: str,
        tags: Optional[List[str]] = None,
        custom_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Upload file with quota enforcement.

        Args:
            file_content: Binary file content
            file_name: Original filename
            file_path: Virtual path for file
            content_type: MIME type
            uploaded_by: User ID uploading file
            tags: Optional tags for categorization
            custom_metadata: Optional custom metadata

        Returns:
            File record dict from database

        Raises:
            StorageQuotaExceeded: If upload would exceed quota
        """
        # Get file size
        file_content.seek(0, 2)  # Seek to end
        file_size = file_content.tell()
        file_content.seek(0)  # Reset to beginning

        # Check quota
        within_quota, usage_info = await self.check_quota(file_size)
        if not within_quota:
            raise StorageQuotaExceeded(
                f"Upload would exceed storage quota. "
                f"Current usage: {usage_info['usage_percentage']:.1f}% "
                f"({usage_info['current_bytes']} / {usage_info['quota_bytes']} bytes)"
            )

        try:
            # Upload to provider
            logger.info(
                "file_upload_started",
                organization_id=self.organization_id,
                file_name=file_name,
                file_path=file_path,
                file_size=file_size
            )

            upload_result = await self.provider.upload(
                file_content=file_content,
                file_name=file_name,
                file_path=file_path,
                content_type=content_type,
                organization_id=self.organization_id,
                metadata=custom_metadata
            )

            # Store metadata in database
            file_record = {
                "organization_id": self.organization_id,
                "file_name": file_name,
                "file_path": file_path,
                "content_type": content_type,
                "file_size_bytes": file_size,
                "provider": self.provider.get_provider_name(),
                "provider_file_id": upload_result.file_id,
                "provider_metadata": upload_result.provider_metadata,
                "checksum": upload_result.checksum,
                "tags": tags or [],
                "custom_metadata": custom_metadata or {},
                "uploaded_by": uploaded_by,
            }

            result = self.client.table("storage_files").insert(file_record).execute()

            logger.info(
                "file_upload_completed",
                organization_id=self.organization_id,
                file_id=result.data[0]["id"],
                file_path=file_path
            )

            return result.data[0]

        except Exception as e:
            logger.error(
                "file_upload_failed",
                error=str(e),
                organization_id=self.organization_id,
                file_path=file_path
            )
            raise

    async def download_file(self, file_id: str) -> Tuple[BinaryIO, Dict]:
        """
        Download file and update access tracking.

        Args:
            file_id: File ID (UUID from database)

        Returns:
            Tuple of (file_stream, file_metadata)

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        try:
            # Get file record from database
            result = self.client.table("storage_files").select("*").eq(
                "id", file_id
            ).eq(
                "organization_id", self.organization_id
            ).is_("deleted_at", "null").single().execute()

            if not result.data:
                raise FileNotFoundError(f"File not found: {file_id}")

            file_record = result.data

            # Download from provider
            logger.info(
                "file_download_started",
                organization_id=self.organization_id,
                file_id=file_id,
                file_path=file_record["file_path"]
            )

            file_stream, _, _ = await self.provider.download(
                file_id=file_record["provider_file_id"],
                organization_id=self.organization_id
            )

            # Update access tracking
            self.client.table("storage_files").update({
                "last_accessed_at": datetime.utcnow().isoformat(),
                "access_count": file_record.get("access_count", 0) + 1
            }).eq("id", file_id).execute()

            # Track download bandwidth
            self.client.rpc("increment_download_bandwidth", {
                "p_organization_id": self.organization_id,
                "p_bytes": file_record["file_size_bytes"]
            }).execute()

            logger.info(
                "file_download_completed",
                organization_id=self.organization_id,
                file_id=file_id
            )

            return file_stream, file_record

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "file_download_failed",
                error=str(e),
                organization_id=self.organization_id,
                file_id=file_id
            )
            raise

    async def delete_file(self, file_id: str, permanent: bool = False) -> bool:
        """
        Delete a file (soft delete by default).

        Args:
            file_id: File ID to delete
            permanent: If True, permanently delete; otherwise soft delete

        Returns:
            True if successful

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        try:
            # Get file record
            result = self.client.table("storage_files").select("*").eq(
                "id", file_id
            ).eq(
                "organization_id", self.organization_id
            ).is_("deleted_at", "null").single().execute()

            if not result.data:
                raise FileNotFoundError(f"File not found: {file_id}")

            file_record = result.data

            if permanent:
                # Delete from provider
                await self.provider.delete(
                    file_id=file_record["provider_file_id"],
                    organization_id=self.organization_id
                )

                # Delete from database
                self.client.table("storage_files").delete().eq(
                    "id", file_id
                ).execute()

                logger.info(
                    "file_permanently_deleted",
                    organization_id=self.organization_id,
                    file_id=file_id
                )
            else:
                # Soft delete
                self.client.table("storage_files").update({
                    "deleted_at": datetime.utcnow().isoformat()
                }).eq("id", file_id).execute()

                logger.info(
                    "file_soft_deleted",
                    organization_id=self.organization_id,
                    file_id=file_id
                )

            return True

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "file_delete_failed",
                error=str(e),
                organization_id=self.organization_id,
                file_id=file_id
            )
            return False

    async def list_files(
        self,
        path_prefix: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[Dict]:
        """
        List files in organization's storage.

        Args:
            path_prefix: Optional path prefix filter
            limit: Maximum files to return
            offset: Pagination offset
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            List of file metadata dicts
        """
        try:
            query = self.client.table("storage_files").select("*").eq(
                "organization_id", self.organization_id
            ).is_("deleted_at", "null")

            if path_prefix:
                query = query.like("file_path", f"{path_prefix}%")

            query = query.order(sort_by, desc=(sort_order == "desc")).range(
                offset, offset + limit - 1
            )

            result = query.execute()

            logger.info(
                "files_listed",
                organization_id=self.organization_id,
                count=len(result.data),
                path_prefix=path_prefix
            )

            return result.data

        except Exception as e:
            logger.error(
                "list_files_failed",
                error=str(e),
                organization_id=self.organization_id
            )
            raise

    async def search_files(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        path_prefix: Optional[str] = None,
        content_type: Optional[str] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        uploaded_by: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Advanced file search with multiple filters.

        Args:
            query: Text search in file name
            tags: Filter by tags (any match)
            path_prefix: Filter by path prefix
            content_type: Filter by content type
            min_size: Minimum file size
            max_size: Maximum file size
            uploaded_by: Filter by uploader
            limit: Maximum results

        Returns:
            List of matching file metadata dicts
        """
        try:
            db_query = self.client.table("storage_files").select("*").eq(
                "organization_id", self.organization_id
            ).is_("deleted_at", "null")

            if query:
                db_query = db_query.ilike("file_name", f"%{query}%")

            if tags:
                # PostgreSQL array contains any of tags
                db_query = db_query.overlaps("tags", tags)

            if path_prefix:
                db_query = db_query.like("file_path", f"{path_prefix}%")

            if content_type:
                db_query = db_query.eq("content_type", content_type)

            if min_size is not None:
                db_query = db_query.gte("file_size_bytes", min_size)

            if max_size is not None:
                db_query = db_query.lte("file_size_bytes", max_size)

            if uploaded_by:
                db_query = db_query.eq("uploaded_by", uploaded_by)

            db_query = db_query.limit(limit)

            result = db_query.execute()

            logger.info(
                "files_searched",
                organization_id=self.organization_id,
                results_count=len(result.data),
                query=query
            )

            return result.data

        except Exception as e:
            logger.error(
                "search_files_failed",
                error=str(e),
                organization_id=self.organization_id
            )
            raise

    async def get_usage_stats(self) -> Dict:
        """
        Get current storage usage and quota information.

        Returns:
            Usage statistics dict
        """
        await self._ensure_usage_record()

        result = self.client.table("storage_usage").select("*").eq(
            "organization_id", self.organization_id
        ).single().execute()

        usage = result.data

        return {
            "organization_id": self.organization_id,
            "total_bytes_used": usage["total_bytes_used"],
            "total_files_count": usage["total_files_count"],
            "quota_bytes": usage["quota_bytes"],
            "remaining_bytes": usage["quota_bytes"] - usage["total_bytes_used"],
            "usage_percentage": (usage["total_bytes_used"] / usage["quota_bytes"]) * 100
            if usage["quota_bytes"] > 0 else 0,
            "total_bytes_uploaded": usage["total_bytes_uploaded"],
            "total_bytes_downloaded": usage["total_bytes_downloaded"],
        }

    async def get_file_metadata(self, file_id: str) -> Dict:
        """
        Get detailed file metadata.

        Args:
            file_id: File ID

        Returns:
            File metadata dict

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        result = self.client.table("storage_files").select("*").eq(
            "id", file_id
        ).eq(
            "organization_id", self.organization_id
        ).is_("deleted_at", "null").single().execute()

        if not result.data:
            raise FileNotFoundError(f"File not found: {file_id}")

        return result.data
