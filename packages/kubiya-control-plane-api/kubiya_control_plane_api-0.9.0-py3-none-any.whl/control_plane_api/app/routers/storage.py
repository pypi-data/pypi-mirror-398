"""
Storage Router - Remote Filesystem API

Provides RESTful endpoints for cloud file storage operations:
- File CRUD (upload, download, delete, list)
- Advanced operations (move, copy, search)
- Folder management
- Batch operations
- Usage analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel, Field
import structlog
from datetime import datetime
import zipfile
from io import BytesIO

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.services.storage_service import StorageService, StorageQuotaExceeded

logger = structlog.get_logger()
router = APIRouter()


# ============================================================================
# Pydantic Schemas
# ============================================================================

class FileMetadata(BaseModel):
    """File metadata response"""
    id: str
    file_name: str
    file_path: str
    content_type: str
    file_size_bytes: int
    checksum: Optional[str]
    tags: List[str] = Field(default_factory=list)
    custom_metadata: dict = Field(default_factory=dict)
    uploaded_by: str
    created_at: str
    updated_at: str
    last_accessed_at: Optional[str]
    access_count: int
    provider: str


class BatchDownloadRequest(BaseModel):
    """Batch download request"""
    file_ids: List[str] = Field(..., min_length=1, max_length=100)
    archive_name: str = Field(default="files.zip")


class SearchFilesRequest(BaseModel):
    """File search request"""
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    path_prefix: Optional[str] = None
    content_type: Optional[str] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    uploaded_by: Optional[str] = None


class UsageStatsResponse(BaseModel):
    """Storage usage statistics"""
    organization_id: str
    total_bytes_used: int
    total_files_count: int
    quota_bytes: int
    remaining_bytes: int
    usage_percentage: float
    total_bytes_uploaded: int
    total_bytes_downloaded: int


class MoveFileRequest(BaseModel):
    """Move file request"""
    new_path: str


class CopyFileRequest(BaseModel):
    """Copy file request"""
    destination_path: str


class UpdateMetadataRequest(BaseModel):
    """Update file metadata request"""
    tags: Optional[List[str]] = None
    custom_metadata: Optional[dict] = None


# ============================================================================
# File Operations Endpoints
# ============================================================================

@router.post("/files/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    file_path: str = Query(..., description="Destination path (e.g., /folder/file.txt)"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    organization: dict = Depends(get_current_organization),
):
    """
    Upload a file to cloud storage.

    - Enforces organization quota
    - Supports custom metadata and tags
    - Returns file metadata with provider URL
    """
    try:
        storage_service = StorageService(organization["id"])

        # Parse tags
        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        # Upload file
        file_metadata = await storage_service.upload_file(
            file_content=file.file,
            file_name=file.filename or "unnamed",
            file_path=file_path,
            content_type=file.content_type or "application/octet-stream",
            uploaded_by=organization.get("user_id", "unknown"),
            tags=tag_list,
            custom_metadata={}
        )

        logger.info(
            "file_uploaded",
            organization_id=organization["id"],
            file_name=file.filename,
            file_size=file_metadata["file_size_bytes"],
            file_id=file_metadata["id"]
        )

        return file_metadata

    except StorageQuotaExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e)
        )
    except Exception as e:
        logger.error("file_upload_failed", error=str(e), organization_id=organization["id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: str,
    organization: dict = Depends(get_current_organization),
):
    """
    Download a file from cloud storage.

    - Streams file content
    - Updates access tracking
    - Returns proper content-type headers
    """
    try:
        storage_service = StorageService(organization["id"])

        # Get file metadata and stream
        file_stream, file_metadata = await storage_service.download_file(file_id)

        return StreamingResponse(
            file_stream,
            media_type=file_metadata["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{file_metadata["file_name"]}"',
                "Content-Length": str(file_metadata["file_size_bytes"]),
            }
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error("file_download_failed", error=str(e), file_id=file_id)
        raise HTTPException(status_code=500, detail="Download failed")


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    permanent: bool = Query(False, description="Permanently delete (vs soft delete)"),
    organization: dict = Depends(get_current_organization),
):
    """
    Delete a file.

    - Supports soft delete (default) or permanent deletion
    - Updates usage statistics
    """
    try:
        storage_service = StorageService(organization["id"])

        success = await storage_service.delete_file(file_id, permanent=permanent)

        if success:
            logger.info(
                "file_deleted",
                organization_id=organization["id"],
                file_id=file_id,
                permanent=permanent
            )
            return {"success": True, "file_id": file_id, "permanent": permanent}
        else:
            raise HTTPException(status_code=404, detail="File not found")

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error("file_delete_failed", error=str(e), file_id=file_id)
        raise HTTPException(status_code=500, detail="Delete failed")


@router.get("/files", response_model=List[FileMetadata])
async def list_files(
    path_prefix: Optional[str] = Query(None, description="Filter by path prefix"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum files to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sort_by: str = Query("created_at", regex="^(created_at|file_name|file_size_bytes)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    organization: dict = Depends(get_current_organization),
):
    """
    List files in organization's storage.

    - Supports path filtering
    - Pagination with limit/offset
    - Sorting options
    """
    try:
        storage_service = StorageService(organization["id"])
        files = await storage_service.list_files(
            path_prefix=path_prefix,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )

        logger.info(
            "files_listed",
            organization_id=organization["id"],
            count=len(files),
            path_prefix=path_prefix
        )

        return files

    except Exception as e:
        logger.error("list_files_failed", error=str(e))
        raise HTTPException(status_code=500, detail="List failed")


@router.post("/files/search", response_model=List[FileMetadata])
async def search_files(
    search_request: SearchFilesRequest,
    organization: dict = Depends(get_current_organization),
):
    """
    Advanced file search with multiple filters.

    - Search by name, tags, metadata
    - Filter by size, type, uploader
    - Path prefix filtering
    """
    try:
        storage_service = StorageService(organization["id"])
        results = await storage_service.search_files(
            query=search_request.query,
            tags=search_request.tags,
            path_prefix=search_request.path_prefix,
            content_type=search_request.content_type,
            min_size=search_request.min_size,
            max_size=search_request.max_size,
            uploaded_by=search_request.uploaded_by
        )

        logger.info(
            "files_searched",
            organization_id=organization["id"],
            results_count=len(results),
            query=search_request.query
        )

        return results

    except Exception as e:
        logger.error("search_files_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Search failed")


@router.post("/files/batch-download")
async def batch_download_files(
    request: BatchDownloadRequest,
    organization: dict = Depends(get_current_organization),
):
    """
    Download multiple files as a ZIP archive.

    - Maximum 100 files per request
    - Streams ZIP archive
    """
    try:
        storage_service = StorageService(organization["id"])

        # Create ZIP archive in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_id in request.file_ids:
                try:
                    file_stream, file_metadata = await storage_service.download_file(file_id)

                    zip_file.writestr(
                        file_metadata["file_path"],
                        file_stream.read()
                    )
                except Exception as e:
                    logger.warning("batch_download_file_skipped", file_id=file_id, error=str(e))
                    continue

        zip_buffer.seek(0)

        logger.info(
            "batch_download_completed",
            organization_id=organization["id"],
            file_count=len(request.file_ids)
        )

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{request.archive_name}"'
            }
        )

    except Exception as e:
        logger.error("batch_download_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Batch download failed")


# ============================================================================
# Advanced Operations
# ============================================================================

@router.post("/files/{file_id}/move")
async def move_file(
    file_id: str,
    move_request: MoveFileRequest,
    organization: dict = Depends(get_current_organization),
):
    """Move/rename a file."""
    # TODO: Implement move operation
    raise HTTPException(status_code=501, detail="Move operation not yet implemented")


@router.post("/files/{file_id}/copy")
async def copy_file(
    file_id: str,
    copy_request: CopyFileRequest,
    organization: dict = Depends(get_current_organization),
):
    """Copy a file to a new location."""
    # TODO: Implement copy operation
    raise HTTPException(status_code=501, detail="Copy operation not yet implemented")


@router.get("/files/{file_id}/metadata", response_model=FileMetadata)
async def get_file_metadata(
    file_id: str,
    organization: dict = Depends(get_current_organization),
):
    """Get detailed file metadata."""
    try:
        storage_service = StorageService(organization["id"])
        metadata = await storage_service.get_file_metadata(file_id)
        return metadata

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error("get_metadata_failed", error=str(e), file_id=file_id)
        raise HTTPException(status_code=500, detail="Failed to get metadata")


@router.put("/files/{file_id}/metadata")
async def update_file_metadata(
    file_id: str,
    update_request: UpdateMetadataRequest,
    organization: dict = Depends(get_current_organization),
):
    """Update file tags and custom metadata."""
    # TODO: Implement metadata update
    raise HTTPException(status_code=501, detail="Metadata update not yet implemented")


@router.post("/folders")
async def create_folder(
    folder_path: str = Query(..., description="Folder path to create"),
    organization: dict = Depends(get_current_organization),
):
    """Create a folder (explicit folder management)."""
    # TODO: Implement folder creation
    raise HTTPException(status_code=501, detail="Folder creation not yet implemented")


# ============================================================================
# Usage & Analytics
# ============================================================================

@router.get("/usage", response_model=UsageStatsResponse)
async def get_storage_usage(
    organization: dict = Depends(get_current_organization),
):
    """Get current storage usage and quota information."""
    try:
        storage_service = StorageService(organization["id"])
        usage = await storage_service.get_usage_stats()

        logger.info(
            "usage_stats_retrieved",
            organization_id=organization["id"],
            usage_percentage=usage["usage_percentage"]
        )

        return usage

    except Exception as e:
        logger.error("get_usage_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get usage statistics")


@router.get("/analytics")
async def get_storage_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    organization: dict = Depends(get_current_organization),
):
    """
    Get storage analytics over time.

    Returns:
    - Daily storage growth
    - File type breakdown
    - Most accessed files
    - Upload/download trends
    """
    # TODO: Implement analytics aggregation
    raise HTTPException(status_code=501, detail="Analytics not yet implemented")
