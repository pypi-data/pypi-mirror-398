"""Files Module for SWS Session API.

This module provides a typed wrapper around the Session API "files" endpoints.

Endpoints covered (session_api):
- GET    /files/:type/:id/list
- GET    /files/:type/:id/view
- GET    /files/:type/:id/download
- POST   /files/:type/:id/upload
- POST   /files/:type/:id/folder
- DELETE /files/:type/:id/folder
- GET    /files/:type/:id/versions
- POST   /files/:type/:id/versions/edit
- DELETE /files/:type/:id/versions
- DELETE /files/:type/:id/hard-delete

The upload endpoints return a presigned S3 URL; the actual file upload is a separate
HTTP PUT to that URL.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel

from sws_api_client.sws_api_client import SwsApiClient

logger = logging.getLogger(__name__)


FileObjectType = Literal["domain", "dataset", "datatable"]


class CreatorInfo(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    id: Optional[str] = None


class FileListItem(BaseModel):
    path: str
    size: Optional[int] = None
    eTag: Optional[str] = None
    lastModified: Optional[datetime] = None
    contentType: Optional[str] = None
    createdAt: Optional[datetime] = None
    createdBy: Optional[CreatorInfo] = None
    metadata: Optional[Dict[str, str]] = None


class FileListResponse(BaseModel):
    prefix: str
    path: str
    folders: List[str]
    files: List[FileListItem]


class SignedUrlResponse(BaseModel):
    key: str
    url: str
    expiresIn: int
    versionId: Optional[str] = None

    contentType: Optional[str] = None
    contentLength: Optional[int] = None
    lastModified: Optional[datetime] = None

    createdAt: Optional[datetime] = None
    createdBy: Optional[CreatorInfo] = None
    metadata: Optional[Dict[str, str]] = None


class SignedUploadUrlResponse(BaseModel):
    key: str
    url: str
    expiresIn: int
    requiredHeaders: Optional[Dict[str, str]] = None


class FileVersionItem(BaseModel):
    versionId: Optional[str] = None
    isLatest: Optional[bool] = None
    lastModified: Optional[datetime] = None
    size: Optional[int] = None
    eTag: Optional[str] = None


class DeleteMarkerItem(BaseModel):
    versionId: Optional[str] = None
    isLatest: Optional[bool] = None
    lastModified: Optional[datetime] = None


class FileVersionsResponse(BaseModel):
    key: str
    versions: List[FileVersionItem]
    deleteMarkers: List[DeleteMarkerItem]


class RestoreVersionResponse(BaseModel):
    key: str
    restoredFromVersionId: str
    newVersionId: Optional[str] = None


class DeleteVersionResponse(BaseModel):
    key: str
    deletedVersionId: str


class HardDeleteResponse(BaseModel):
    key: str
    deletedCount: int


class DeleteFolderResponse(BaseModel):
    prefix: str
    path: str
    deletedCount: int


class BucketDetailsResponse(BaseModel):
    bucket: str
    region: str


class Files:
    """Client for files endpoints on the SWS Session API."""

    def __init__(self, sws_client: SwsApiClient) -> None:
        self.sws_client = sws_client

    def get_bucket_details(self) -> BucketDetailsResponse:
        """Get details about the S3 bucket used for file storage."""
        url = "/files/bucket-details"
        response = self.sws_client.discoverable.get("session_api", url)
        return BucketDetailsResponse(**response)

    @staticmethod
    def _bool_param(value: bool) -> str:
        # Requests would otherwise serialize bools as "True"/"False".
        return "true" if value else "false"

    def list(
        self,
        object_type: FileObjectType,
        object_id: str,
        *,
        path: Optional[str] = None,
        recursive: bool = False,
        include_metadata: bool = False,
    ) -> FileListResponse:
        """List files and folders under a given prefix.

        Args:
            object_type: One of "domain", "dataset", "datatable".
            object_id: The domain/dataset/datatable id.
            path: Optional sub-path to list.
            recursive: If True, returns a recursive listing.
            include_metadata: If True, enriches file entries with S3 object metadata.

        Returns:
            FileListResponse
        """
        url = f"/files/{object_type}/{object_id}/list"
        params: Dict[str, object] = {
            "recursive": self._bool_param(recursive),
            "includeMetadata": self._bool_param(include_metadata),
        }
        if path:
            params["path"] = path

        response = self.sws_client.discoverable.get("session_api", url, params=params)
        return FileListResponse(**response)

    def view(
        self,
        object_type: FileObjectType,
        object_id: str,
        *,
        path: str,
        version_id: Optional[str] = None,
    ) -> SignedUrlResponse:
        """Get a presigned inline URL for a file (and metadata)."""
        url = f"/files/{object_type}/{object_id}/view"
        params: Dict[str, str] = {"path": path}
        if version_id:
            params["versionId"] = version_id

        response = self.sws_client.discoverable.get("session_api", url, params=params)
        return SignedUrlResponse(**response)

    def download(
        self,
        object_type: FileObjectType,
        object_id: str,
        *,
        path: str,
        version_id: Optional[str] = None,
    ) -> SignedUrlResponse:
        """Get a presigned download URL for a file (and metadata)."""
        url = f"/files/{object_type}/{object_id}/download"
        params: Dict[str, str] = {"path": path}
        if version_id:
            params["versionId"] = version_id

        response = self.sws_client.discoverable.get("session_api", url, params=params)
        return SignedUrlResponse(**response)

    def upload_url(
        self,
        object_type: FileObjectType,
        object_id: str,
        *,
        path: str,
        content_type: Optional[str] = None,
    ) -> SignedUploadUrlResponse:
        """Request a presigned URL for uploading a file (creates a new version if the key exists)."""
        url = f"/files/{object_type}/{object_id}/upload"
        body: Dict[str, object] = {"path": path}
        if content_type:
            body["contentType"] = content_type

        response = self.sws_client.discoverable.post("session_api", url, data=body)
        return SignedUploadUrlResponse(**response)

    def create_folder_url(
        self,
        object_type: FileObjectType,
        object_id: str,
        *,
        path: str,
    ) -> SignedUploadUrlResponse:
        """Request a presigned URL for creating a folder placeholder object."""
        url = f"/files/{object_type}/{object_id}/folder"
        body: Dict[str, object] = {"path": path}

        response = self.sws_client.discoverable.post("session_api", url, data=body)
        return SignedUploadUrlResponse(**response)

    def delete_folder(
        self,
        object_type: FileObjectType,
        object_id: str,
        *,
        path: str,
    ) -> DeleteFolderResponse:
        """Recursively delete a folder prefix (hard-deletes all versions/delete markers)."""
        url = f"/files/{object_type}/{object_id}/folder"
        params = {"path": path}

        response = self.sws_client.discoverable.delete("session_api", url, params=params)
        return DeleteFolderResponse(**response)

    def versions(
        self,
        object_type: FileObjectType,
        object_id: str,
        *,
        path: str,
    ) -> FileVersionsResponse:
        """List S3 versions for a file."""
        url = f"/files/{object_type}/{object_id}/versions"
        params = {"path": path}

        response = self.sws_client.discoverable.get("session_api", url, params=params)
        return FileVersionsResponse(**response)

    def restore_version(
        self,
        object_type: FileObjectType,
        object_id: str,
        *,
        path: str,
        version_id: str,
    ) -> RestoreVersionResponse:
        """Restore a given version as the latest version."""
        url = f"/files/{object_type}/{object_id}/versions/edit"
        body = {"path": path, "versionId": version_id}

        response = self.sws_client.discoverable.post("session_api", url, data=body)
        return RestoreVersionResponse(**response)

    def delete_version(
        self,
        object_type: FileObjectType,
        object_id: str,
        *,
        path: str,
        version_id: str,
    ) -> DeleteVersionResponse:
        """Delete a specific S3 object version."""
        url = f"/files/{object_type}/{object_id}/versions"
        body = {"path": path, "versionId": version_id}

        response = self.sws_client.discoverable.delete("session_api", url, data=body)
        return DeleteVersionResponse(**response)

    def hard_delete(
        self,
        object_type: FileObjectType,
        object_id: str,
        *,
        path: str,
    ) -> HardDeleteResponse:
        """Hard-delete a file: deletes all versions and delete markers for that key."""
        url = f"/files/{object_type}/{object_id}/hard-delete"
        params = {"path": path}

        response = self.sws_client.discoverable.delete("session_api", url, params=params)
        return HardDeleteResponse(**response)
