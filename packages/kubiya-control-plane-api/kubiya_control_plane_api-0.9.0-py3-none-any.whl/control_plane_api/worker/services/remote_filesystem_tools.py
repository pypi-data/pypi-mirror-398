"""
Remote Filesystem Tools for Agent Worker

Provides file operation tools that call the Control Plane storage API.
These tools are used by agents to interact with cloud storage.
"""

import os
import httpx
import json
from typing import Optional, List
from agno.tools import Toolkit
import structlog

logger = structlog.get_logger()


class RemoteFilesystemTools(Toolkit):
    """
    Remote filesystem toolkit for agents.

    Agents can use these tools to:
    - Upload files to cloud storage
    - Download files
    - List and search files
    - Manage folders
    - Batch operations
    """

    def __init__(
        self,
        name: Optional[str] = None,
        enable_upload: bool = True,
        enable_download: bool = True,
        enable_list: bool = True,
        enable_delete: bool = False,
        enable_search: bool = True,
        enable_metadata: bool = True,
        enable_move: bool = False,
        enable_copy: bool = False,
        enable_folders: bool = False,
        enable_batch_download: bool = False,
        allowed_paths: Optional[List[str]] = None,
        max_file_size_mb: Optional[int] = None,
        control_plane_base_url: Optional[str] = None,
        kubiya_api_key: Optional[str] = None,
        organization_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(name=name or "remote_filesystem")

        self.enable_upload = enable_upload
        self.enable_download = enable_download
        self.enable_list = enable_list
        self.enable_delete = enable_delete
        self.enable_search = enable_search
        self.enable_metadata = enable_metadata
        self.enable_move = enable_move
        self.enable_copy = enable_copy
        self.enable_folders = enable_folders
        self.enable_batch_download = enable_batch_download
        self.allowed_paths = allowed_paths
        self.max_file_size_mb = max_file_size_mb or 100

        # API configuration
        self.control_plane_base_url = (
            control_plane_base_url
            or os.environ.get("CONTROL_PLANE_BASE_URL", "http://localhost:8000")
        ).rstrip("/")

        self.kubiya_api_key = kubiya_api_key or os.environ.get("KUBIYA_API_KEY")
        self.organization_id = organization_id or os.environ.get("ORGANIZATION_ID")

        if not self.kubiya_api_key:
            raise ValueError("KUBIYA_API_KEY required for Remote Filesystem tools")

        self.client = httpx.AsyncClient(timeout=300.0)

        logger.info(
            "remote_filesystem_tools_initialized",
            base_url=self.control_plane_base_url,
            enabled_operations={
                "upload": self.enable_upload,
                "download": self.enable_download,
                "list": self.enable_list,
                "delete": self.enable_delete,
                "search": self.enable_search,
            }
        )

        # Register tools based on configuration
        self._register_tools()

    def _get_headers(self):
        """Get API request headers."""
        return {
            "Authorization": f"UserKey {self.kubiya_api_key}",
            "Content-Type": "application/json"
        }

    def _check_path_allowed(self, file_path: str) -> bool:
        """Check if file path is allowed."""
        if not self.allowed_paths:
            return True
        return any(file_path.startswith(prefix) for prefix in self.allowed_paths)

    def _register_tools(self):
        """Dynamically register tools based on configuration."""
        if self.enable_upload:
            self.register(self.upload_file)

        if self.enable_download:
            self.register(self.download_file)

        if self.enable_list:
            self.register(self.list_files)

        if self.enable_delete:
            self.register(self.delete_file)

        if self.enable_search:
            self.register(self.search_files)

        if self.enable_metadata:
            self.register(self.get_file_metadata)

        if self.enable_batch_download:
            self.register(self.batch_download_files)

    async def upload_file(
        self,
        local_file_path: str,
        remote_file_path: str,
        tags: Optional[str] = None
    ) -> str:
        """
        Upload a file to cloud storage.

        Args:
            local_file_path: Path to local file to upload
            remote_file_path: Destination path in cloud storage (e.g., /folder/file.txt)
            tags: Optional comma-separated tags for file organization

        Returns:
            Success message with file ID and metadata as JSON string

        Example:
            upload_file("/tmp/report.pdf", "/reports/2024/report.pdf", "report,monthly")
        """
        try:
            # Check path restrictions
            if not self._check_path_allowed(remote_file_path):
                return f"Error: Path '{remote_file_path}' is not allowed by configuration"

            # Check file exists
            if not os.path.exists(local_file_path):
                return f"Error: Local file not found: {local_file_path}"

            # Check file size
            file_size = os.path.getsize(local_file_path)
            max_size = self.max_file_size_mb * 1024 * 1024
            if file_size > max_size:
                return f"Error: File size {file_size} bytes exceeds limit {max_size} bytes ({self.max_file_size_mb}MB)"

            # Upload
            url = f"{self.control_plane_base_url}/api/v1/storage/files/upload"

            with open(local_file_path, 'rb') as f:
                files = {'file': (os.path.basename(local_file_path), f)}
                params = {
                    'file_path': remote_file_path,
                }
                if tags:
                    params['tags'] = tags

                response = await self.client.post(
                    url,
                    files=files,
                    params=params,
                    headers={"Authorization": f"UserKey {self.kubiya_api_key}"}
                )

            if response.status_code == 201:
                result = response.json()
                return f"✅ File uploaded successfully!\n\nFile ID: {result['id']}\nPath: {result['file_path']}\nSize: {result['file_size_bytes']} bytes\nChecksum: {result['checksum']}"
            elif response.status_code == 413:
                return f"❌ Error: Storage quota exceeded. Please contact your administrator to increase your storage limit."
            else:
                return f"❌ Error uploading file: {response.text}"

        except Exception as e:
            logger.error("upload_file_error", error=str(e), local_file_path=local_file_path)
            return f"❌ Error: {str(e)}"

    async def download_file(
        self,
        file_id: str,
        local_destination: str
    ) -> str:
        """
        Download a file from cloud storage.

        Args:
            file_id: File ID from storage (UUID)
            local_destination: Local path to save file

        Returns:
            Success message or error

        Example:
            download_file("550e8400-e29b-41d4-a716-446655440000", "/tmp/downloaded_file.pdf")
        """
        try:
            url = f"{self.control_plane_base_url}/api/v1/storage/files/{file_id}/download"

            response = await self.client.get(url, headers=self._get_headers())

            if response.status_code == 200:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(local_destination), exist_ok=True)

                with open(local_destination, 'wb') as f:
                    f.write(response.content)

                file_size = len(response.content)
                return f"✅ File downloaded successfully to {local_destination} ({file_size} bytes)"
            elif response.status_code == 404:
                return f"❌ Error: File not found with ID: {file_id}"
            else:
                return f"❌ Error downloading file: {response.text}"

        except Exception as e:
            logger.error("download_file_error", error=str(e), file_id=file_id)
            return f"❌ Error: {str(e)}"

    async def list_files(
        self,
        path_prefix: Optional[str] = None,
        limit: int = 100
    ) -> str:
        """
        List files in cloud storage.

        Args:
            path_prefix: Optional path prefix filter (e.g., "/reports/")
            limit: Maximum number of files to return (default 100, max 1000)

        Returns:
            JSON array of file metadata or error message

        Example:
            list_files("/reports/", 50)
        """
        try:
            url = f"{self.control_plane_base_url}/api/v1/storage/files"
            params = {"limit": min(limit, 1000)}
            if path_prefix:
                params["path_prefix"] = path_prefix

            response = await self.client.get(
                url,
                params=params,
                headers=self._get_headers()
            )

            if response.status_code == 200:
                files = response.json()
                if not files:
                    return "No files found."

                # Format output
                result = f"Found {len(files)} files:\n\n"
                for file in files:
                    result += f"• {file['file_path']}\n"
                    result += f"  ID: {file['id']}\n"
                    result += f"  Size: {file['file_size_bytes']} bytes\n"
                    result += f"  Type: {file['content_type']}\n"
                    result += f"  Created: {file['created_at']}\n"
                    if file.get('tags'):
                        result += f"  Tags: {', '.join(file['tags'])}\n"
                    result += "\n"

                return result
            else:
                return f"❌ Error listing files: {response.text}"

        except Exception as e:
            logger.error("list_files_error", error=str(e))
            return f"❌ Error: {str(e)}"

    async def search_files(
        self,
        query: Optional[str] = None,
        tags: Optional[str] = None,
        path_prefix: Optional[str] = None
    ) -> str:
        """
        Search for files with filters.

        Args:
            query: Text search in file name
            tags: Comma-separated tags to filter by
            path_prefix: Filter by path prefix

        Returns:
            JSON array of matching files or error message

        Example:
            search_files(query="report", tags="monthly,finance", path_prefix="/reports/")
        """
        try:
            url = f"{self.control_plane_base_url}/api/v1/storage/files/search"
            payload = {}

            if query:
                payload["query"] = query
            if tags:
                payload["tags"] = [t.strip() for t in tags.split(",")]
            if path_prefix:
                payload["path_prefix"] = path_prefix

            response = await self.client.post(
                url,
                json=payload,
                headers=self._get_headers()
            )

            if response.status_code == 200:
                results = response.json()
                if not results:
                    return "No matching files found."

                result = f"Found {len(results)} matching files:\n\n"
                for file in results:
                    result += f"• {file['file_path']}\n"
                    result += f"  ID: {file['id']}\n"
                    result += f"  Size: {file['file_size_bytes']} bytes\n"
                    if file.get('tags'):
                        result += f"  Tags: {', '.join(file['tags'])}\n"
                    result += "\n"

                return result
            else:
                return f"❌ Error searching files: {response.text}"

        except Exception as e:
            logger.error("search_files_error", error=str(e))
            return f"❌ Error: {str(e)}"

    async def delete_file(
        self,
        file_id: str,
        permanent: bool = False
    ) -> str:
        """
        Delete a file from cloud storage.

        Args:
            file_id: File ID to delete (UUID)
            permanent: If True, permanently delete; otherwise soft delete (default False)

        Returns:
            Success message or error

        Example:
            delete_file("550e8400-e29b-41d4-a716-446655440000", permanent=True)
        """
        try:
            url = f"{self.control_plane_base_url}/api/v1/storage/files/{file_id}"
            params = {"permanent": permanent}

            response = await self.client.delete(
                url,
                params=params,
                headers=self._get_headers()
            )

            if response.status_code == 200:
                delete_type = "permanently deleted" if permanent else "soft deleted"
                return f"✅ File {delete_type} successfully (ID: {file_id})"
            elif response.status_code == 404:
                return f"❌ Error: File not found with ID: {file_id}"
            else:
                return f"❌ Error deleting file: {response.text}"

        except Exception as e:
            logger.error("delete_file_error", error=str(e), file_id=file_id)
            return f"❌ Error: {str(e)}"

    async def get_file_metadata(
        self,
        file_id: str
    ) -> str:
        """
        Get detailed file metadata.

        Args:
            file_id: File ID (UUID)

        Returns:
            File metadata as formatted string

        Example:
            get_file_metadata("550e8400-e29b-41d4-a716-446655440000")
        """
        try:
            url = f"{self.control_plane_base_url}/api/v1/storage/files/{file_id}/metadata"

            response = await self.client.get(url, headers=self._get_headers())

            if response.status_code == 200:
                metadata = response.json()
                result = "File Metadata:\n\n"
                result += f"ID: {metadata['id']}\n"
                result += f"Name: {metadata['file_name']}\n"
                result += f"Path: {metadata['file_path']}\n"
                result += f"Type: {metadata['content_type']}\n"
                result += f"Size: {metadata['file_size_bytes']} bytes\n"
                result += f"Checksum: {metadata.get('checksum', 'N/A')}\n"
                result += f"Provider: {metadata['provider']}\n"
                result += f"Uploaded by: {metadata['uploaded_by']}\n"
                result += f"Created: {metadata['created_at']}\n"
                result += f"Last accessed: {metadata.get('last_accessed_at', 'Never')}\n"
                result += f"Access count: {metadata['access_count']}\n"
                if metadata.get('tags'):
                    result += f"Tags: {', '.join(metadata['tags'])}\n"
                if metadata.get('custom_metadata'):
                    result += f"Custom metadata: {json.dumps(metadata['custom_metadata'], indent=2)}\n"

                return result
            elif response.status_code == 404:
                return f"❌ Error: File not found with ID: {file_id}"
            else:
                return f"❌ Error getting metadata: {response.text}"

        except Exception as e:
            logger.error("get_metadata_error", error=str(e), file_id=file_id)
            return f"❌ Error: {str(e)}"

    async def batch_download_files(
        self,
        file_ids: str,
        local_destination: str,
        archive_name: str = "files.zip"
    ) -> str:
        """
        Download multiple files as a ZIP archive.

        Args:
            file_ids: Comma-separated list of file IDs (max 100)
            local_destination: Local directory to save ZIP file
            archive_name: Name of the ZIP file (default "files.zip")

        Returns:
            Success message or error

        Example:
            batch_download_files("id1,id2,id3", "/tmp/", "my_files.zip")
        """
        try:
            # Parse file IDs
            file_id_list = [fid.strip() for fid in file_ids.split(",")]

            if len(file_id_list) > 100:
                return f"❌ Error: Maximum 100 files per batch download. You requested {len(file_id_list)} files."

            url = f"{self.control_plane_base_url}/api/v1/storage/files/batch-download"
            payload = {
                "file_ids": file_id_list,
                "archive_name": archive_name
            }

            response = await self.client.post(
                url,
                json=payload,
                headers=self._get_headers()
            )

            if response.status_code == 200:
                # Save ZIP file
                os.makedirs(local_destination, exist_ok=True)
                zip_path = os.path.join(local_destination, archive_name)

                with open(zip_path, 'wb') as f:
                    f.write(response.content)

                file_size = len(response.content)
                return f"✅ Downloaded {len(file_id_list)} files as ZIP archive to {zip_path} ({file_size} bytes)"
            else:
                return f"❌ Error batch downloading files: {response.text}"

        except Exception as e:
            logger.error("batch_download_error", error=str(e))
            return f"❌ Error: {str(e)}"

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
