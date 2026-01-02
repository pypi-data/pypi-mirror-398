"""
Files Namespace - Archivist object storage operations.

Provides file upload, download, and management via B2 object storage.
"""
import base64
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..start import Dominus


class FilesNamespace:
    """
    Object storage namespace.

    All file operations go through /api/archivist/* endpoints.
    Supports compliance mode for files requiring audit trails and retention.

    Usage:
        # Upload a file
        result = await dominus.files.upload(
            data=file_bytes,
            filename="report.pdf",
            category="documents"
        )

        # Upload compliance file
        result = await dominus.files.upload(
            data=pdf_bytes,
            filename="consent.pdf",
            compliance=True,
            actor=current_user_id,
            retention_days=365 * 7
        )

        # Download file (get presigned URL)
        url_info = await dominus.files.download(file_id=result["id"])

        # Fetch file content directly
        content = await dominus.files.fetch(file_id=result["id"])
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    async def upload(
        self,
        data: bytes,
        filename: str,
        content_type: Optional[str] = None,
        category: str = "general",
        path: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        compliance: bool = False,
        actor: Optional[str] = None,
        retention_days: int = 90
    ) -> Dict[str, Any]:
        """
        Upload a file to object storage.

        Args:
            data: File content as bytes
            filename: Original filename
            content_type: MIME type (auto-detected if not provided)
            category: File category (default: "general")
            path: Logical path within category (default: auto-generated)
            tags: Optional metadata tags
            compliance: If True, enables audit trail and retention
            actor: User ID or "machine" (required if compliance=True)
            retention_days: Retention period for compliance files (default: 90)

        Returns:
            Dict with file ID, path, size, and metadata
        """
        # Base64 encode the file content
        file_b64 = base64.b64encode(data).decode('utf-8')

        body = {
            "file_content": file_b64,
            "filename": filename,
            "category": category,
            "logical_path": path or filename
        }

        if content_type:
            body["content_type"] = content_type
        if tags:
            body["tags"] = tags

        # Compliance mode
        if compliance:
            body["is_compliance"] = True
            body["retention_days"] = retention_days
            if actor:
                body["owner_user_id"] = actor

        return await self._client._request(
            endpoint="/api/archivist/upload",
            body=body
        )

    async def download(
        self,
        file_id: Optional[str] = None,
        category: Optional[str] = None,
        path: Optional[str] = None,
        actor: Optional[str] = None,
        expires_seconds: int = 3600
    ) -> Dict[str, Any]:
        """
        Get a presigned download URL for a file.

        Args:
            file_id: File UUID (preferred)
            category: File category (alternative lookup with path)
            path: Logical path (alternative lookup with category)
            actor: User ID for audit (required for compliance files)
            expires_seconds: URL expiration time (default: 1 hour)

        Returns:
            Dict with "download_url", "expires_at", and file metadata
        """
        body = {"expires_seconds": expires_seconds}

        if file_id:
            body["id"] = file_id
        if category:
            body["category"] = category
        if path:
            body["logical_path"] = path
        if actor:
            body["actor_user_id"] = actor

        return await self._client._request(
            endpoint="/api/archivist/download",
            body=body
        )

    async def fetch(
        self,
        file_id: Optional[str] = None,
        category: Optional[str] = None,
        path: Optional[str] = None,
        actor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch file content directly.

        Args:
            file_id: File UUID (preferred)
            category: File category (alternative lookup with path)
            path: Logical path (alternative lookup with category)
            actor: User ID for audit (required for compliance files)

        Returns:
            Dict with "data" (base64 encoded), "filename", "content_type"
        """
        body = {}

        if file_id:
            body["id"] = file_id
        if category:
            body["category"] = category
        if path:
            body["logical_path"] = path
        if actor:
            body["actor_user_id"] = actor

        return await self._client._request(
            endpoint="/api/archivist/fetch",
            body=body
        )

    async def list(
        self,
        category: Optional[str] = None,
        prefix: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List files with optional filtering.

        Args:
            category: Filter by category
            prefix: Filter by path prefix
            limit: Maximum files to return (default: 100)
            cursor: Pagination cursor

        Returns:
            Dict with "objects" list, "cursor", "count"
        """
        body = {"limit": limit}

        if category:
            body["category"] = category
        if prefix:
            body["prefix"] = prefix
        if cursor:
            body["cursor"] = cursor

        return await self._client._request(
            endpoint="/api/archivist/list",
            body=body
        )

    async def delete(
        self,
        file_id: Optional[str] = None,
        category: Optional[str] = None,
        path: Optional[str] = None,
        actor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a file.

        Args:
            file_id: File UUID (preferred)
            category: File category (alternative lookup with path)
            path: Logical path (alternative lookup with category)
            actor: User ID for audit

        Returns:
            Dict with "deleted" status
        """
        body = {}

        if file_id:
            body["id"] = file_id
        if category:
            body["category"] = category
        if path:
            body["logical_path"] = path
        if actor:
            body["actor_user_id"] = actor

        return await self._client._request(
            endpoint="/api/archivist/delete",
            body=body
        )

    async def move(
        self,
        file_id: str,
        new_category: Optional[str] = None,
        new_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Move or rename a file.

        Args:
            file_id: File UUID
            new_category: New category (optional)
            new_path: New logical path (optional)

        Returns:
            Updated file metadata
        """
        body = {"id": file_id}

        if new_category:
            body["new_category"] = new_category
        if new_path:
            body["new_logical_path"] = new_path

        return await self._client._request(
            endpoint="/api/archivist/move",
            body=body
        )

    async def update_meta(
        self,
        file_id: str,
        tags: Optional[Dict[str, str]] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update file metadata.

        Args:
            file_id: File UUID
            tags: New metadata tags (replaces existing)
            description: New description

        Returns:
            Updated file metadata
        """
        body = {"id": file_id}

        if tags is not None:
            body["tags"] = tags
        if description is not None:
            body["description"] = description

        return await self._client._request(
            endpoint="/api/archivist/update",
            body=body
        )
