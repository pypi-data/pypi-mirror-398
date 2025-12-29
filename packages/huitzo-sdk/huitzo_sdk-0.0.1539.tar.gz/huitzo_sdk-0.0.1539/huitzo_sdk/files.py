"""
File Upload Service client for Huitzo SDK.

This module provides the FilesClient class for uploading and managing files:
- upload(): Upload a file to the backend for use in command workflows
- upload_bytes(): Upload file content directly from bytes/buffer
- get(): Get metadata for a specific uploaded file

All methods are async and handle error responses appropriately.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, Literal
from uuid import UUID

import aiohttp

from .exceptions import (
    AuthenticationError,
    HuitzoAPIError,
    RateLimitError,
    ValidationError,
)

if TYPE_CHECKING:
    from .client import HuitzoTools


class FileUploadResult:
    """
    Result of a file upload operation.

    Attributes:
        file_id: UUID of the uploaded file
        filename: Sanitized filename on server
        path: Absolute filesystem path for CLI use
        size_bytes: Size of uploaded file in bytes
        content_type: MIME content type (if detected)
        uploaded_at: When the file was uploaded
        expires_at: When the file will be deleted (None for persistent)
    """

    def __init__(
        self,
        file_id: UUID,
        filename: str,
        path: str,
        size_bytes: int,
        content_type: str | None,
        uploaded_at: datetime,
        expires_at: datetime | None,
    ):
        self.file_id = file_id
        self.filename = filename
        self.path = path
        self.size_bytes = size_bytes
        self.content_type = content_type
        self.uploaded_at = uploaded_at
        self.expires_at = expires_at

    def __repr__(self) -> str:
        return (
            f"FileUploadResult(file_id={self.file_id!r}, "
            f"filename={self.filename!r}, path={self.path!r})"
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileUploadResult":
        """Create FileUploadResult from API response dictionary."""
        return cls(
            file_id=UUID(data["file_id"]) if isinstance(data["file_id"], str) else data["file_id"],
            filename=data["filename"],
            path=data["path"],
            size_bytes=data["size_bytes"],
            content_type=data.get("content_type"),
            uploaded_at=(
                datetime.fromisoformat(data["uploaded_at"].replace("Z", "+00:00"))
                if isinstance(data["uploaded_at"], str)
                else data["uploaded_at"]
            ),
            expires_at=(
                datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
                if data.get("expires_at") and isinstance(data["expires_at"], str)
                else data.get("expires_at")
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "file_id": str(self.file_id),
            "filename": self.filename,
            "path": self.path,
            "size_bytes": self.size_bytes,
            "content_type": self.content_type,
            "uploaded_at": self.uploaded_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class FilesClient:
    """
    Client for File Upload Service.

    This client provides methods for uploading files to the backend
    for use in command workflows. Uploaded files are stored with
    automatic TTL-based cleanup.

    Example:
        ```python
        async with HuitzoTools(api_token="your_token") as sdk:
            # Upload a file
            result = await sdk.files.upload(
                file_path="./data.csv",
                purpose="temp"
            )
            print(f"File uploaded: {result.path}")
            print(f"Expires at: {result.expires_at}")

            # Use the path in a command
            await sdk.cron.schedule(
                name="process_file",
                command="data.process",
                schedule="0 * * * *",
                arguments={"input_file": result.path}
            )
        ```
    """

    # Default size limit (100MB) - backend may have different limit
    DEFAULT_MAX_SIZE = 100 * 1024 * 1024

    def __init__(self, sdk: "HuitzoTools"):
        """
        Initialize FilesClient.

        Args:
            sdk: Parent HuitzoTools instance
        """
        self._sdk = sdk

    async def upload(
        self,
        file_path: str | Path,
        purpose: Literal["temp", "persistent"] | None = None,
        content_type: str | None = None,
    ) -> FileUploadResult:
        """
        Upload a file from disk.

        Reads a file from the local filesystem and uploads it to the backend
        for use in command workflows.

        Args:
            file_path: Path to the file to upload
            purpose: Storage purpose ("temp" for TTL-based cleanup, "persistent" for long-term)
                Default: "temp" (24-hour TTL)
            content_type: MIME content type override. If not provided, will be
                inferred from filename extension.

        Returns:
            FileUploadResult containing file metadata and server-side path

        Raises:
            ValidationError: If file doesn't exist, is too large (>100MB),
                or is not a regular file
            RateLimitError: If API rate limit exceeded
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            # Upload a CSV file for processing
            result = await sdk.files.upload(
                file_path="./reports/data.csv",
                purpose="temp"
            )
            print(f"Server path: {result.path}")

            # Upload with explicit content type
            result = await sdk.files.upload(
                file_path="./data.bin",
                content_type="application/octet-stream"
            )
            ```
        """
        # Convert to Path and validate
        path = Path(file_path)
        if not path.exists():
            raise ValidationError(f"File not found: {file_path}")

        if not path.is_file():
            raise ValidationError(f"Path is not a file: {file_path}")

        # Check file size
        file_size = path.stat().st_size
        if file_size > self.DEFAULT_MAX_SIZE:
            raise ValidationError(
                f"File exceeds {self.DEFAULT_MAX_SIZE // (1024 * 1024)}MB limit: "
                f"{file_size / (1024 * 1024):.2f}MB"
            )

        # Read file content
        try:
            with open(path, "rb") as f:
                file_data = f.read()
        except Exception as e:
            raise ValidationError(f"Failed to read file: {e}")

        # Infer content type if not provided
        if content_type is None:
            content_type = self._infer_content_type(path.name)

        return await self.upload_bytes(
            file_data=file_data,
            filename=path.name,
            purpose=purpose,
            content_type=content_type,
        )

    async def upload_bytes(
        self,
        file_data: bytes | BinaryIO,
        filename: str,
        purpose: Literal["temp", "persistent"] | None = None,
        content_type: str | None = None,
    ) -> FileUploadResult:
        """
        Upload file content from bytes or buffer.

        Uploads raw file content without reading from disk. Useful for
        in-memory file generation or streaming uploads.

        Args:
            file_data: File content as bytes or file-like object
            filename: Name for the file on server
            purpose: Storage purpose ("temp" or "persistent")
            content_type: MIME content type (default: application/octet-stream)

        Returns:
            FileUploadResult containing file metadata and server-side path

        Raises:
            ValidationError: If file is too large or filename is invalid
            RateLimitError: If API rate limit exceeded
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            # Upload generated content
            csv_content = "name,value\\nfoo,1\\nbar,2"
            result = await sdk.files.upload_bytes(
                file_data=csv_content.encode("utf-8"),
                filename="generated.csv",
                content_type="text/csv"
            )

            # Upload from file-like object
            import io
            buffer = io.BytesIO(b"binary content")
            result = await sdk.files.upload_bytes(
                file_data=buffer.read(),
                filename="data.bin"
            )
            ```
        """
        # Convert file-like object to bytes
        if hasattr(file_data, "read"):
            file_data = file_data.read()

        # Validate size
        if len(file_data) > self.DEFAULT_MAX_SIZE:
            raise ValidationError(
                f"File exceeds {self.DEFAULT_MAX_SIZE // (1024 * 1024)}MB limit: "
                f"{len(file_data) / (1024 * 1024):.2f}MB"
            )

        # Validate filename
        if not filename or filename in ("", ".", ".."):
            raise ValidationError("Invalid filename")

        # Default content type
        if content_type is None:
            content_type = self._infer_content_type(filename) or "application/octet-stream"

        # Build multipart form data
        form_data = aiohttp.FormData()
        form_data.add_field(
            "file",
            file_data,
            filename=filename,
            content_type=content_type,
        )
        if purpose:
            form_data.add_field("purpose", purpose)

        # Make API request (multipart upload requires custom headers)
        headers = {
            "Authorization": f"Bearer {self._sdk.api_token}",
            "User-Agent": "huitzo-sdk/2.1.0",
        }
        if self._sdk._user_id:
            headers["X-User-ID"] = self._sdk._user_id

        async with self._sdk._session.post(
            f"{self._sdk.base_url}/api/v1/files/upload",
            data=form_data,
            headers=headers,
        ) as response:
            return await self._handle_upload_response(response)

    async def _handle_upload_response(self, response: aiohttp.ClientResponse) -> FileUploadResult:
        """
        Handle file upload response with specific error handling.

        Args:
            response: aiohttp ClientResponse object

        Returns:
            FileUploadResult from parsed JSON response

        Raises:
            ValidationError: 400/413 - Invalid input or file too large
            RateLimitError: 429 - Rate limit exceeded
            AuthenticationError: 401 - Authentication failed
            HuitzoAPIError: Other errors
        """
        status = response.status

        # Success case (201 Created)
        if status == 201:
            try:
                data = await response.json()
                return FileUploadResult.from_dict(data)
            except Exception as e:
                raise HuitzoAPIError(
                    f"Invalid JSON response from API: {e}",
                    status_code=status,
                )

        # Handle error responses
        try:
            error_data = await response.json()
            error_message = error_data.get("detail", f"HTTP {status}")
        except Exception:
            try:
                error_message = await response.text()
            except Exception:
                error_message = f"HTTP {status}"
            error_data = {}

        # Map status codes to exceptions
        if status == 413:
            raise ValidationError(
                message="File exceeds server size limit",
                response_data=error_data,
            )
        elif status == 400:
            raise ValidationError(
                message=error_message,
                response_data=error_data,
            )
        elif status == 401:
            raise AuthenticationError(
                message=error_message,
                status_code=status,
                response_data=error_data,
            )
        elif status == 429:
            raise RateLimitError(
                message=error_message,
                response_data=error_data,
            )
        else:
            raise HuitzoAPIError(
                message=error_message,
                status_code=status,
                response_data=error_data,
            )

    def _infer_content_type(self, filename: str) -> str | None:
        """
        Infer MIME content type from filename extension.

        Args:
            filename: Name of the file

        Returns:
            MIME content type or None if unknown
        """
        extension = Path(filename).suffix.lower()
        content_types = {
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".json": "application/json",
            ".xml": "application/xml",
            ".html": "text/html",
            ".htm": "text/html",
            ".pdf": "application/pdf",
            ".zip": "application/zip",
            ".tar": "application/x-tar",
            ".gz": "application/gzip",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".mp3": "audio/mpeg",
            ".mp4": "video/mp4",
            ".wav": "audio/wav",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ppt": "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".py": "text/x-python",
            ".js": "text/javascript",
            ".ts": "text/typescript",
            ".css": "text/css",
            ".md": "text/markdown",
            ".yaml": "text/yaml",
            ".yml": "text/yaml",
        }
        return content_types.get(extension)
