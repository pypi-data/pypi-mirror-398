"""
Abstract base class for storage providers.

All storage provider implementations must inherit from StorageProvider
and implement all abstract methods to ensure consistent behavior.
"""

from abc import ABC, abstractmethod
from typing import BinaryIO, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class StorageFile:
    """
    File metadata returned from storage operations.

    Attributes:
        file_id: Provider-specific unique identifier
        file_name: Original filename
        file_path: Organization-scoped virtual path
        content_type: MIME type of the file
        file_size_bytes: File size in bytes
        checksum: File checksum (MD5 or SHA256)
        created_at: Creation timestamp
        provider_metadata: Provider-specific additional metadata
    """
    file_id: str
    file_name: str
    file_path: str
    content_type: str
    file_size_bytes: int
    checksum: Optional[str] = None
    created_at: Optional[datetime] = None
    provider_metadata: Optional[Dict[str, any]] = None


@dataclass
class UploadResult:
    """
    Result of file upload operation.

    Attributes:
        file_id: Provider-specific unique identifier for the uploaded file
        url: Access URL for the file (may be provider-specific)
        file_size_bytes: Actual size of uploaded file
        checksum: File checksum for integrity verification
        provider_metadata: Provider-specific metadata from upload
    """
    file_id: str
    url: str
    file_size_bytes: int
    checksum: str
    provider_metadata: Dict[str, any]


class StorageProvider(ABC):
    """
    Abstract base class for storage providers.

    All providers must implement this interface to ensure
    consistent behavior across different storage backends.

    Each provider should handle:
    - Organization-level isolation (typically via path prefixes or separate buckets)
    - Authentication with the underlying storage service
    - Error handling and retry logic
    - Streaming support for large files
    """

    @abstractmethod
    async def upload(
        self,
        file_content: BinaryIO,
        file_name: str,
        file_path: str,
        content_type: str,
        organization_id: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> UploadResult:
        """
        Upload a file to storage.

        Args:
            file_content: Binary file content (file-like object)
            file_name: Original filename
            file_path: Organization-scoped virtual path (e.g., /folder/file.txt)
            content_type: MIME type of the file
            organization_id: Organization ID for namespacing
            metadata: Optional additional metadata to store with the file

        Returns:
            UploadResult with file ID, URL, and metadata

        Raises:
            Exception: If upload fails (provider-specific exceptions)
        """
        pass

    @abstractmethod
    async def download(
        self,
        file_id: str,
        organization_id: str
    ) -> Tuple[BinaryIO, str, int]:
        """
        Download file content.

        Args:
            file_id: Provider-specific file identifier
            organization_id: Organization ID for validation

        Returns:
            Tuple of (file_stream, content_type, file_size_bytes)

        Raises:
            FileNotFoundError: If file doesn't exist
            Exception: If download fails
        """
        pass

    @abstractmethod
    async def delete(
        self,
        file_id: str,
        organization_id: str
    ) -> bool:
        """
        Delete a file from storage.

        Args:
            file_id: Provider-specific file identifier
            organization_id: Organization ID for validation

        Returns:
            True if deletion was successful, False otherwise

        Raises:
            Exception: If deletion fails
        """
        pass

    @abstractmethod
    async def list_files(
        self,
        organization_id: str,
        prefix: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Tuple[List[StorageFile], Optional[str]]:
        """
        List files with pagination support.

        Args:
            organization_id: Organization ID for filtering
            prefix: Optional path prefix filter (e.g., /folder/)
            limit: Maximum number of files to return
            cursor: Pagination cursor from previous request

        Returns:
            Tuple of (files_list, next_cursor)
            next_cursor is None if no more files

        Raises:
            Exception: If listing fails
        """
        pass

    @abstractmethod
    async def get_metadata(
        self,
        file_id: str,
        organization_id: str
    ) -> StorageFile:
        """
        Get file metadata without downloading content.

        Args:
            file_id: Provider-specific file identifier
            organization_id: Organization ID for validation

        Returns:
            StorageFile with metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            Exception: If metadata retrieval fails
        """
        pass

    @abstractmethod
    async def copy(
        self,
        source_file_id: str,
        destination_path: str,
        organization_id: str
    ) -> UploadResult:
        """
        Copy file to new location within same organization.

        Args:
            source_file_id: Source file identifier
            destination_path: Destination virtual path
            organization_id: Organization ID

        Returns:
            UploadResult for the new file

        Raises:
            FileNotFoundError: If source file doesn't exist
            Exception: If copy fails
        """
        pass

    @abstractmethod
    async def move(
        self,
        file_id: str,
        new_path: str,
        organization_id: str
    ) -> StorageFile:
        """
        Move/rename file to new location.

        Args:
            file_id: File identifier to move
            new_path: New virtual path
            organization_id: Organization ID

        Returns:
            StorageFile with updated metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            Exception: If move fails
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Return provider name identifier.

        Returns:
            Provider name (e.g., 'vercel_blob', 's3', 'azure_blob')
        """
        pass

    async def exists(
        self,
        file_id: str,
        organization_id: str
    ) -> bool:
        """
        Check if a file exists.

        Default implementation uses get_metadata, but providers
        can override with more efficient implementation.

        Args:
            file_id: File identifier
            organization_id: Organization ID

        Returns:
            True if file exists, False otherwise
        """
        try:
            await self.get_metadata(file_id, organization_id)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False
