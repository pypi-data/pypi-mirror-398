"""
Vercel Blob Storage provider implementation.

Documentation: https://vercel.com/docs/storage/vercel-blob
"""

import httpx
import hashlib
from typing import BinaryIO, Dict, List, Optional, Tuple
from datetime import datetime
from io import BytesIO
import structlog

from .base_provider import StorageProvider, StorageFile, UploadResult

logger = structlog.get_logger()


class VercelBlobStorageProvider(StorageProvider):
    """
    Vercel Blob Storage implementation.

    Uses Vercel's Blob Storage API for file storage with organization-level isolation.
    Files are stored with organization prefix for multi-tenancy.
    """

    def __init__(self, token: str, store_name: Optional[str] = None):
        """
        Initialize Vercel Blob provider.

        Args:
            token: VERCEL_BLOB_TOKEN from environment
            store_name: Optional store name (defaults to main store)
        """
        self.token = token
        self.store_name = store_name
        self.base_url = "https://blob.vercel-storage.com"
        self.client = httpx.AsyncClient(timeout=300.0)

        logger.info(
            "vercel_blob_provider_initialized",
            store_name=store_name,
            base_url=self.base_url
        )

    def _get_blob_path(self, organization_id: str, file_path: str) -> str:
        """
        Construct organization-scoped blob path.

        Args:
            organization_id: Organization ID
            file_path: Virtual file path

        Returns:
            Full blob path with organization prefix
        """
        # Ensure file_path starts with /
        if not file_path.startswith("/"):
            file_path = f"/{file_path}"

        # Construct: {org_id}{file_path}
        return f"{organization_id}{file_path}"

    async def upload(
        self,
        file_content: BinaryIO,
        file_name: str,
        file_path: str,
        content_type: str,
        organization_id: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> UploadResult:
        """Upload file to Vercel Blob."""

        # Construct org-scoped blob path
        blob_path = self._get_blob_path(organization_id, file_path)

        # Read content and calculate checksum
        content = file_content.read()
        if hasattr(file_content, 'seek'):
            file_content.seek(0)
        checksum = hashlib.sha256(content).hexdigest()

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Content-Type": content_type,
        }

        # Add metadata as headers
        if metadata:
            for key, value in metadata.items():
                safe_key = key.replace(" ", "_").replace("-", "_")
                headers[f"X-Meta-{safe_key}"] = str(value)

        try:
            # Upload to Vercel Blob
            logger.info(
                "vercel_blob_upload_started",
                blob_path=blob_path,
                file_name=file_name,
                size_bytes=len(content),
                organization_id=organization_id
            )

            response = await self.client.put(
                f"{self.base_url}/{blob_path}",
                content=content,
                headers=headers
            )
            response.raise_for_status()

            result = response.json()

            logger.info(
                "vercel_blob_upload_completed",
                blob_path=blob_path,
                url=result.get("url"),
                organization_id=organization_id
            )

            return UploadResult(
                file_id=result["url"],  # Vercel uses URL as ID
                url=result["url"],
                file_size_bytes=len(content),
                checksum=checksum,
                provider_metadata={
                    "downloadUrl": result.get("downloadUrl"),
                    "pathname": result.get("pathname"),
                    "blob_path": blob_path,
                }
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                "vercel_blob_upload_failed",
                error=str(e),
                status_code=e.response.status_code,
                blob_path=blob_path
            )
            raise Exception(f"Vercel Blob upload failed: {e.response.text}")
        except Exception as e:
            logger.error(
                "vercel_blob_upload_error",
                error=str(e),
                blob_path=blob_path
            )
            raise

    async def download(
        self,
        file_id: str,
        organization_id: str
    ) -> Tuple[BinaryIO, str, int]:
        """Download file from Vercel Blob."""

        try:
            logger.info(
                "vercel_blob_download_started",
                file_id=file_id,
                organization_id=organization_id
            )

            # file_id is the blob URL for Vercel
            response = await self.client.get(file_id, follow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "application/octet-stream")
            file_size = int(response.headers.get("content-length", 0))

            logger.info(
                "vercel_blob_download_completed",
                file_id=file_id,
                size_bytes=file_size,
                organization_id=organization_id
            )

            # Return as BytesIO
            return BytesIO(response.content), content_type, file_size

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise FileNotFoundError(f"File not found: {file_id}")
            logger.error(
                "vercel_blob_download_failed",
                error=str(e),
                status_code=e.response.status_code,
                file_id=file_id
            )
            raise Exception(f"Vercel Blob download failed: {e.response.text}")
        except Exception as e:
            logger.error(
                "vercel_blob_download_error",
                error=str(e),
                file_id=file_id
            )
            raise

    async def delete(self, file_id: str, organization_id: str) -> bool:
        """Delete file from Vercel Blob."""

        try:
            logger.info(
                "vercel_blob_delete_started",
                file_id=file_id,
                organization_id=organization_id
            )

            # Vercel Blob delete API
            response = await self.client.post(
                f"{self.base_url}/delete",
                json={"urls": [file_id]},
                headers={"Authorization": f"Bearer {self.token}"}
            )

            success = response.status_code == 200

            if success:
                logger.info(
                    "vercel_blob_delete_completed",
                    file_id=file_id,
                    organization_id=organization_id
                )
            else:
                logger.warning(
                    "vercel_blob_delete_failed",
                    status_code=response.status_code,
                    file_id=file_id
                )

            return success

        except Exception as e:
            logger.error(
                "vercel_blob_delete_error",
                error=str(e),
                file_id=file_id
            )
            return False

    async def list_files(
        self,
        organization_id: str,
        prefix: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Tuple[List[StorageFile], Optional[str]]:
        """
        List files from Vercel Blob.

        Note: Vercel Blob list API has limitations. For production use,
        it's recommended to use database queries with provider_file_id instead.
        """

        try:
            # Construct org-scoped prefix
            org_prefix = organization_id
            if prefix:
                org_prefix = self._get_blob_path(organization_id, prefix)

            params = {
                "prefix": org_prefix,
                "limit": limit
            }
            if cursor:
                params["cursor"] = cursor

            logger.info(
                "vercel_blob_list_started",
                organization_id=organization_id,
                prefix=org_prefix,
                limit=limit
            )

            response = await self.client.get(
                f"{self.base_url}/list",
                params=params,
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()

            data = response.json()
            blobs = data.get("blobs", [])
            next_cursor = data.get("cursor")

            # Convert to StorageFile objects
            files = []
            for blob in blobs:
                # Extract file path by removing org prefix
                pathname = blob.get("pathname", "")
                if pathname.startswith(organization_id):
                    file_path = pathname[len(organization_id):]
                else:
                    file_path = pathname

                files.append(StorageFile(
                    file_id=blob["url"],
                    file_name=file_path.split("/")[-1],
                    file_path=file_path,
                    content_type=blob.get("contentType", "application/octet-stream"),
                    file_size_bytes=blob.get("size", 0),
                    checksum=None,  # Vercel doesn't provide checksum in list
                    created_at=datetime.fromisoformat(blob["uploadedAt"].replace("Z", "+00:00"))
                    if "uploadedAt" in blob else None,
                    provider_metadata=blob
                ))

            logger.info(
                "vercel_blob_list_completed",
                organization_id=organization_id,
                files_count=len(files),
                has_more=next_cursor is not None
            )

            return files, next_cursor

        except Exception as e:
            logger.error(
                "vercel_blob_list_error",
                error=str(e),
                organization_id=organization_id
            )
            raise

    async def get_metadata(
        self,
        file_id: str,
        organization_id: str
    ) -> StorageFile:
        """
        Get file metadata.

        Vercel Blob doesn't have a dedicated metadata endpoint,
        so we use HEAD request to get headers.
        """

        try:
            response = await self.client.head(file_id, follow_redirects=True)
            response.raise_for_status()

            # Extract metadata from headers
            content_type = response.headers.get("content-type", "application/octet-stream")
            file_size = int(response.headers.get("content-length", 0))

            # Extract pathname from URL
            pathname = file_id.split("/")[-1]

            return StorageFile(
                file_id=file_id,
                file_name=pathname.split("/")[-1],
                file_path=pathname,
                content_type=content_type,
                file_size_bytes=file_size,
                checksum=None,
                created_at=None,
                provider_metadata={"url": file_id}
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise FileNotFoundError(f"File not found: {file_id}")
            raise Exception(f"Failed to get metadata: {e.response.text}")

    async def copy(
        self,
        source_file_id: str,
        destination_path: str,
        organization_id: str
    ) -> UploadResult:
        """
        Copy file to new location.

        Vercel Blob doesn't have native copy, so we download and re-upload.
        """

        try:
            logger.info(
                "vercel_blob_copy_started",
                source_file_id=source_file_id,
                destination_path=destination_path,
                organization_id=organization_id
            )

            # Download source file
            file_stream, content_type, _ = await self.download(source_file_id, organization_id)

            # Get filename from destination path
            file_name = destination_path.split("/")[-1]

            # Upload to new location
            result = await self.upload(
                file_content=file_stream,
                file_name=file_name,
                file_path=destination_path,
                content_type=content_type,
                organization_id=organization_id
            )

            logger.info(
                "vercel_blob_copy_completed",
                source_file_id=source_file_id,
                destination_file_id=result.file_id,
                organization_id=organization_id
            )

            return result

        except Exception as e:
            logger.error(
                "vercel_blob_copy_error",
                error=str(e),
                source_file_id=source_file_id
            )
            raise

    async def move(
        self,
        file_id: str,
        new_path: str,
        organization_id: str
    ) -> StorageFile:
        """
        Move/rename file.

        Vercel Blob doesn't have native move, so we copy and delete.
        """

        try:
            logger.info(
                "vercel_blob_move_started",
                file_id=file_id,
                new_path=new_path,
                organization_id=organization_id
            )

            # Copy to new location
            upload_result = await self.copy(file_id, new_path, organization_id)

            # Delete original
            await self.delete(file_id, organization_id)

            # Get metadata of new file
            new_file = await self.get_metadata(upload_result.file_id, organization_id)

            logger.info(
                "vercel_blob_move_completed",
                old_file_id=file_id,
                new_file_id=upload_result.file_id,
                organization_id=organization_id
            )

            return new_file

        except Exception as e:
            logger.error(
                "vercel_blob_move_error",
                error=str(e),
                file_id=file_id
            )
            raise

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "vercel_blob"

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
