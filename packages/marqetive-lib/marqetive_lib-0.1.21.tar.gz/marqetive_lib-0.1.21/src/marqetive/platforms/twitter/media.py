"""Twitter media upload manager with chunked upload support.

This module provides comprehensive media upload functionality for Twitter API v2:
- Chunked upload for large files (videos, GIFs)
- Simple upload for images
- Progress tracking with callbacks
- Automatic retry with exponential backoff
- Async processing status monitoring
"""

import asyncio
import inspect
import logging
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

import aiofiles
import httpx

from marqetive.core.exceptions import (
    InvalidFileTypeError,
    MediaUploadError,
)
from marqetive.core.models import ProgressEvent, ProgressStatus
from marqetive.utils.file_handlers import download_file
from marqetive.utils.media import (
    detect_mime_type,
    format_file_size,
    get_chunk_count,
)
from marqetive.utils.retry import STANDARD_BACKOFF, retry_async

# Type aliases for progress callbacks
type SyncProgressCallback = Callable[[ProgressEvent], None]
type AsyncProgressCallback = Callable[[ProgressEvent], Awaitable[None]]
type ProgressCallback = SyncProgressCallback | AsyncProgressCallback

# Legacy callback type for backward compatibility
type LegacyProgressCallback = Callable[["UploadProgress"], None]

logger = logging.getLogger(__name__)

# Constants
DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024  # 4MB chunks
MAX_CHUNK_SIZE = 5 * 1024 * 1024  # 5MB max (Twitter limit)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB for images
MAX_GIF_SIZE = 15 * 1024 * 1024  # 15MB for GIFs
MAX_VIDEO_SIZE = 512 * 1024 * 1024  # 512MB for videos
DEFAULT_REQUEST_TIMEOUT = 120.0  # 2 minutes

# Twitter API v2 media upload endpoints
MEDIA_UPLOAD_BASE_URL = "https://api.x.com/2/media/upload"


class MediaCategory(str, Enum):
    """Twitter media categories."""

    TWEET_IMAGE = "tweet_image"
    TWEET_VIDEO = "tweet_video"
    TWEET_GIF = "tweet_gif"
    AMPLIFY_VIDEO = "amplify_video"
    DM_IMAGE = "dm_image"
    DM_VIDEO = "dm_video"
    DM_GIF = "dm_gif"
    SUBTITLES = "subtitles"


class ProcessingState(str, Enum):
    """States for async media processing."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


# Supported MIME types for Twitter
SUPPORTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
SUPPORTED_VIDEO_TYPES = ["video/mp4", "video/quicktime"]
SUPPORTED_GIF_TYPE = "image/gif"


@dataclass
class UploadProgress:
    """Progress information for media upload.

    .. deprecated:: 0.2.0
        Use :class:`marqetive.core.models.ProgressEvent` instead.
        This class will be removed in a future version.

    Attributes:
        media_id: Twitter media ID (if available).
        file_path: Path to file being uploaded.
        bytes_uploaded: Number of bytes uploaded so far.
        total_bytes: Total file size in bytes.
        percentage: Upload progress as percentage (0-100).
        status: Current upload status.
    """

    media_id: str | None
    file_path: str
    bytes_uploaded: int
    total_bytes: int
    status: Literal["init", "uploading", "processing", "completed", "failed"]

    @property
    def percentage(self) -> float:
        """Calculate upload percentage."""
        if self.total_bytes == 0:
            return 0.0
        return (self.bytes_uploaded / self.total_bytes) * 100

    def __str__(self) -> str:
        """String representation of progress."""
        return (
            f"Upload Progress: {self.percentage:.1f}% "
            f"({format_file_size(self.bytes_uploaded)} / "
            f"{format_file_size(self.total_bytes)}) - {self.status}"
        )


@dataclass
class MediaUploadResult:
    """Result of a media upload operation.

    Attributes:
        media_id: Twitter media ID.
        media_key: Twitter media key (if available).
        size: File size in bytes.
        expires_after_secs: Time until media expires.
        processing_info: Processing status info (for videos).
    """

    media_id: str
    media_key: str | None = None
    size: int | None = None
    expires_after_secs: int | None = None
    processing_info: dict[str, Any] | None = None


class TwitterMediaManager:
    """Manager for Twitter media uploads.

    Handles both simple and chunked uploads with progress tracking.
    Uses Twitter API v2 media upload endpoints.

    Example:
        >>> manager = TwitterMediaManager(bearer_token="your_token")
        >>> result = await manager.upload_media("/path/to/image.jpg")
        >>> print(f"Media ID: {result.media_id}")

        >>> # With progress callback
        >>> def on_progress(event: ProgressEvent) -> None:
        ...     print(f"{event.operation}: {event.percentage:.1f}%")
        >>> manager = TwitterMediaManager(
        ...     bearer_token="your_token",
        ...     progress_callback=on_progress,
        ... )
    """

    def __init__(
        self,
        bearer_token: str,
        *,
        progress_callback: ProgressCallback | None = None,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
    ) -> None:
        """Initialize Twitter media manager.

        Args:
            bearer_token: Twitter OAuth 2.0 bearer token.
            progress_callback: Optional callback for progress updates.
                Accepts ProgressEvent and can be sync or async.
            timeout: Request timeout in seconds.
        """
        self.bearer_token = bearer_token
        self.progress_callback = progress_callback
        self.timeout = timeout
        self.base_url = MEDIA_UPLOAD_BASE_URL

        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={"Authorization": f"Bearer {bearer_token}"},
        )

    async def _emit_progress(
        self,
        status: ProgressStatus,
        progress: int,
        total: int,
        message: str | None = None,
        *,
        entity_id: str | None = None,
        file_path: str | None = None,
        bytes_uploaded: int | None = None,
        total_bytes: int | None = None,
    ) -> None:
        """Emit a progress update if a callback is registered.

        Supports both sync and async callbacks.
        """
        if self.progress_callback is None:
            return

        event = ProgressEvent(
            operation="upload_media",
            platform="twitter",
            status=status,
            progress=progress,
            total=total,
            message=message,
            entity_id=entity_id,
            file_path=file_path,
            bytes_uploaded=bytes_uploaded,
            total_bytes=total_bytes,
        )

        result = self.progress_callback(event)

        # If callback returned a coroutine, await it
        if inspect.iscoroutine(result):
            await result

    async def __aenter__(self) -> "TwitterMediaManager":
        """Enter async context."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context and cleanup."""
        await self.client.aclose()

    async def upload_media(
        self,
        file_path: str,
        *,
        media_category: MediaCategory | None = None,
        alt_text: str | None = None,
        additional_owners: list[str] | None = None,
    ) -> MediaUploadResult:
        """Upload media file to Twitter.

        Automatically chooses between simple and chunked upload based on file type.

        Args:
            file_path: Path to media file or URL.
            media_category: Twitter media category (auto-detected if None).
            alt_text: Alternative text for accessibility.
            additional_owners: Additional user IDs who can use this media.

        Returns:
            MediaUploadResult with media ID and metadata.

        Raises:
            InvalidFileTypeError: If file type is not supported.
            MediaUploadError: If upload fails.
            FileNotFoundError: If file doesn't exist.

        Example:
            >>> result = await manager.upload_media("photo.jpg")
            >>> result = await manager.upload_media("video.mp4", alt_text="Demo video")
        """
        # Download file if it's a URL
        if file_path.startswith(("http://", "https://")):
            logger.info(f"Downloading media from URL: {file_path}")
            file_path = await download_file(file_path)

        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Media file not found: {file_path}")

        # Detect MIME type
        mime_type = detect_mime_type(file_path)
        file_size = os.path.getsize(file_path)

        # Auto-detect category if not provided
        if media_category is None:
            media_category = self._detect_media_category(mime_type)

        # Validate file type
        self._validate_media(mime_type, file_size)

        # Choose upload method
        if mime_type in SUPPORTED_VIDEO_TYPES or mime_type == SUPPORTED_GIF_TYPE:
            result = await self.chunked_upload(
                file_path,
                media_category=media_category,
                additional_owners=additional_owners,
            )
        else:
            result = await self.simple_upload(
                file_path,
                media_category=media_category,
                additional_owners=additional_owners,
            )

        # Set alt text if provided
        if alt_text:
            await self.add_alt_text(result.media_id, alt_text)

        return result

    async def simple_upload(
        self,
        file_path: str,
        *,
        media_category: MediaCategory | None = None,
        additional_owners: list[str] | None = None,
    ) -> MediaUploadResult:
        """Upload media using simple upload (for images).

        Args:
            file_path: Path to media file.
            media_category: Twitter media category.
            additional_owners: Additional user IDs.

        Returns:
            MediaUploadResult with media ID.

        Raises:
            MediaUploadError: If upload fails.
        """
        file_size = os.path.getsize(file_path)

        # Notify upload start
        await self._emit_progress(
            status=ProgressStatus.INITIALIZING,
            progress=0,
            total=100,
            message="Initializing upload",
            file_path=file_path,
            bytes_uploaded=0,
            total_bytes=file_size,
        )

        @retry_async(config=STANDARD_BACKOFF)
        async def _do_upload() -> MediaUploadResult:
            # Read file asynchronously
            async with aiofiles.open(file_path, "rb") as f:
                file_data = await f.read()

            # Prepare multipart form data
            files = {"media": (os.path.basename(file_path), file_data)}
            data: dict[str, str] = {}

            if media_category:
                data["media_category"] = media_category.value
            if additional_owners:
                data["additional_owners"] = ",".join(additional_owners)

            # Notify upload in progress
            await self._emit_progress(
                status=ProgressStatus.UPLOADING,
                progress=0,
                total=100,
                message="Uploading file",
                file_path=file_path,
                bytes_uploaded=0,
                total_bytes=file_size,
            )

            # Upload - v2 API uses base URL directly
            response = await self.client.post(
                self.base_url,
                files=files,
                data=data,
            )
            response.raise_for_status()
            result_data = response.json()
            logger.debug(f"Simple upload response: {result_data}")

            # Parse result - v2 API returns {"data": {"id": "..."}}
            media_data = result_data["data"]
            media_id = str(media_data["id"])
            result = MediaUploadResult(
                media_id=media_id,
                media_key=media_data.get("media_key"),
                size=media_data.get("size"),
                expires_after_secs=media_data.get("expires_after_secs"),
            )

            # Notify completion
            await self._emit_progress(
                status=ProgressStatus.COMPLETED,
                progress=100,
                total=100,
                message="Upload completed",
                entity_id=media_id,
                file_path=file_path,
                bytes_uploaded=file_size,
                total_bytes=file_size,
            )

            logger.info(f"Simple upload completed: {media_id}")
            return result

        try:
            return await _do_upload()
        except httpx.HTTPError as e:
            raise MediaUploadError(
                f"Simple upload failed: {e}",
                platform="twitter",
                media_type=detect_mime_type(file_path),
            ) from e

    async def chunked_upload(
        self,
        file_path: str,
        *,
        media_category: MediaCategory,
        additional_owners: list[str] | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        wait_for_processing: bool = True,
    ) -> MediaUploadResult:
        """Upload media using chunked upload (INIT → APPEND → FINALIZE).

        Used for large files like videos and GIFs.

        Args:
            file_path: Path to media file.
            media_category: Twitter media category.
            additional_owners: Additional user IDs.
            chunk_size: Size of chunks (default: 4MB).
            wait_for_processing: Wait for async processing to complete.

        Returns:
            MediaUploadResult with media ID.

        Raises:
            MediaUploadError: If upload or processing fails.
        """
        file_size = os.path.getsize(file_path)
        mime_type = detect_mime_type(file_path)

        # Calculate optimal chunk size
        chunk_size = self._calculate_chunk_size(file_size, chunk_size)

        # STEP 1: Initialize upload
        media_id = await self._chunked_upload_init(
            file_size,
            mime_type,
            media_category,
            additional_owners,
        )

        logger.info(
            f"Initialized chunked upload: media_id={media_id}, "
            f"file_size={format_file_size(file_size)}, "
            f"chunks={get_chunk_count(file_path, chunk_size)}"
        )

        # Notify upload start
        await self._emit_progress(
            status=ProgressStatus.UPLOADING,
            progress=0,
            total=100,
            message="Starting chunked upload",
            entity_id=media_id,
            file_path=file_path,
            bytes_uploaded=0,
            total_bytes=file_size,
        )

        # STEP 2: Upload chunks
        bytes_uploaded = 0
        segment_index = 0

        async with aiofiles.open(file_path, "rb") as f:
            while True:
                chunk_data = await f.read(chunk_size)
                if not chunk_data:
                    break

                await self._chunked_upload_append(
                    media_id,
                    chunk_data,
                    segment_index,
                    os.path.basename(file_path),
                )

                bytes_uploaded += len(chunk_data)
                segment_index += 1

                # Notify progress
                progress_pct = int((bytes_uploaded / file_size) * 100)
                await self._emit_progress(
                    status=ProgressStatus.UPLOADING,
                    progress=progress_pct,
                    total=100,
                    message=f"Uploading chunk {segment_index}",
                    entity_id=media_id,
                    file_path=file_path,
                    bytes_uploaded=bytes_uploaded,
                    total_bytes=file_size,
                )

                logger.debug(
                    f"Uploaded chunk {segment_index}: "
                    f"{format_file_size(bytes_uploaded)} / "
                    f"{format_file_size(file_size)}"
                )

        # STEP 3: Finalize upload
        result = await self._chunked_upload_finalize(media_id)

        # STEP 4: Wait for async processing if needed
        if wait_for_processing and result.processing_info:
            await self._wait_for_processing(result, file_path)

        # Notify completion
        await self._emit_progress(
            status=ProgressStatus.COMPLETED,
            progress=100,
            total=100,
            message="Chunked upload completed",
            entity_id=media_id,
            file_path=file_path,
            bytes_uploaded=file_size,
            total_bytes=file_size,
        )

        logger.info(f"Chunked upload completed: {media_id}")
        return result

    async def _chunked_upload_init(
        self,
        total_bytes: int,
        media_type: str,
        media_category: MediaCategory,
        additional_owners: list[str] | None,
    ) -> str:
        """Initialize chunked upload (INIT command).

        Args:
            total_bytes: Total file size.
            media_type: MIME type.
            media_category: Twitter media category.
            additional_owners: Additional user IDs.

        Returns:
            Media ID for subsequent operations.
        """

        @retry_async(config=STANDARD_BACKOFF)
        async def _do_init() -> str:
            # v2 API uses JSON body for INIT
            json_data: dict[str, Any] = {
                "total_bytes": total_bytes,
                "media_type": media_type,
                "media_category": media_category.value,
                "shared": False,
            }

            if additional_owners:
                json_data["additional_owners"] = ",".join(additional_owners)

            logger.debug(f"INIT request: {json_data}")
            response = await self.client.post(
                f"{self.base_url}/initialize",
                json=json_data,
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"INIT response: {result}")
            # v2 API returns {"data": {"id": "..."}}
            return str(result["data"]["id"])

        return await _do_init()

    async def _chunked_upload_append(
        self,
        media_id: str,
        chunk_data: bytes,
        segment_index: int,
        filename: str,
    ) -> None:
        """Append chunk to upload (APPEND command).

        Args:
            media_id: Media ID from INIT.
            chunk_data: Chunk bytes.
            segment_index: Sequential chunk index.
            filename: Original filename.
        """

        @retry_async(config=STANDARD_BACKOFF)
        async def _do_append() -> None:
            # v2 API uses /{media_id}/append endpoint with form data
            files = {"media": (filename, chunk_data)}
            data = {"segment_index": str(segment_index)}

            response = await self.client.post(
                f"{self.base_url}/{media_id}/append",
                files=files,
                data=data,
            )
            logger.debug(f"APPEND response status: {response.status_code}")
            response.raise_for_status()
            # APPEND returns empty body on success

        await _do_append()

    async def _chunked_upload_finalize(self, media_id: str) -> MediaUploadResult:
        """Finalize chunked upload (FINALIZE command).

        Args:
            media_id: Media ID from INIT.

        Returns:
            MediaUploadResult with processing info.
        """

        @retry_async(config=STANDARD_BACKOFF)
        async def _do_finalize() -> MediaUploadResult:
            # v2 API uses /{media_id}/finalize endpoint
            logger.debug(f"Finalizing chunked upload for media_id: {media_id}")
            response = await self.client.post(
                f"{self.base_url}/{media_id}/finalize",
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"FINALIZE response: {result}")

            # v2 API returns {"data": {...}}
            media_data = result["data"]
            return MediaUploadResult(
                media_id=str(media_data["id"]),
                media_key=media_data.get("media_key"),
                size=media_data.get("size"),
                expires_after_secs=media_data.get("expires_after_secs"),
                processing_info=media_data.get("processing_info"),
            )

        return await _do_finalize()

    async def get_upload_status(self, media_id: str) -> MediaUploadResult:
        """Check status of async media processing (STATUS command).

        Args:
            media_id: Media ID to check.

        Returns:
            MediaUploadResult with current processing status.
        """

        @retry_async(config=STANDARD_BACKOFF)
        async def _do_status() -> MediaUploadResult:
            # v2 API uses GET with media_id and command params
            params = {
                "media_id": media_id,
                "command": "STATUS",
            }

            response = await self.client.get(
                self.base_url,
                params=params,
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"STATUS response: {result}")

            # v2 API returns {"data": {...}}
            media_data = result["data"]
            return MediaUploadResult(
                media_id=str(media_data["id"]),
                media_key=media_data.get("media_key"),
                size=media_data.get("size"),
                expires_after_secs=media_data.get("expires_after_secs"),
                processing_info=media_data.get("processing_info"),
            )

        return await _do_status()

    async def add_alt_text(self, media_id: str, alt_text: str) -> None:
        """Add alternative text to media for accessibility.

        Args:
            media_id: Twitter media ID.
            alt_text: Alternative text description (max 1000 chars).

        Raises:
            MediaUploadError: If alt text addition fails.
        """
        if len(alt_text) > 1000:
            raise MediaUploadError(
                "Alt text must be 1000 characters or less",
                platform="twitter",
            )

        try:
            response = await self.client.post(
                f"{self.base_url}/metadata/create",
                json={
                    "media_id": media_id,
                    "alt_text": {"text": alt_text},
                },
            )
            response.raise_for_status()
            logger.info(f"Added alt text to media: {media_id}")

        except httpx.HTTPError as e:
            raise MediaUploadError(
                f"Failed to add alt text: {e}",
                platform="twitter",
            ) from e

    async def _wait_for_processing(
        self,
        result: MediaUploadResult,
        file_path: str,
    ) -> None:
        """Wait for async processing to complete.

        Args:
            result: Upload result with processing info.
            file_path: File path for progress tracking.

        Raises:
            MediaUploadError: If processing fails.
        """
        if not result.processing_info:
            return

        processing_info = result.processing_info
        state = processing_info.get("state")

        while state in (
            ProcessingState.PENDING.value,
            ProcessingState.IN_PROGRESS.value,
        ):
            check_after = processing_info.get("check_after_secs", 5)
            logger.info(
                f"Media processing {state}, checking again in {check_after}s..."
            )

            # Notify processing status
            file_size = os.path.getsize(file_path)
            await self._emit_progress(
                status=ProgressStatus.PROCESSING,
                progress=90,  # Show 90% during processing
                total=100,
                message=f"Processing media ({state})",
                entity_id=result.media_id,
                file_path=file_path,
                bytes_uploaded=file_size,
                total_bytes=file_size,
            )

            await asyncio.sleep(check_after)

            # Check status
            result = await self.get_upload_status(result.media_id)
            processing_info = result.processing_info or {}
            state = processing_info.get("state")

        # Check final state
        if state == ProcessingState.FAILED.value:
            error_msg = processing_info.get("error", {}).get("message", "Unknown error")
            raise MediaUploadError(
                f"Media processing failed: {error_msg}",
                platform="twitter",
            )

        if state != ProcessingState.SUCCEEDED.value:
            raise MediaUploadError(
                f"Media processing ended in unexpected state: {state}",
                platform="twitter",
            )

        logger.info(f"Media processing succeeded: {result.media_id}")

    def _detect_media_category(self, mime_type: str) -> MediaCategory:
        """Auto-detect Twitter media category from MIME type.

        Args:
            mime_type: MIME type string.

        Returns:
            Appropriate MediaCategory.
        """
        if mime_type in SUPPORTED_IMAGE_TYPES:
            return MediaCategory.TWEET_IMAGE
        elif mime_type == SUPPORTED_GIF_TYPE:
            return MediaCategory.TWEET_GIF
        elif mime_type in SUPPORTED_VIDEO_TYPES:
            return MediaCategory.TWEET_VIDEO
        else:
            return MediaCategory.TWEET_IMAGE  # Default

    def _validate_media(self, mime_type: str, file_size: int) -> None:
        """Validate media type and size.

        Args:
            mime_type: MIME type of file.
            file_size: Size in bytes.

        Raises:
            InvalidFileTypeError: If type not supported.
            MediaUploadError: If file exceeds size limit.
        """
        all_supported = (
            SUPPORTED_IMAGE_TYPES + SUPPORTED_VIDEO_TYPES + [SUPPORTED_GIF_TYPE]
        )

        if mime_type not in all_supported:
            raise InvalidFileTypeError(
                f"Unsupported media type: {mime_type}. "
                f"Supported: {', '.join(all_supported)}",
                platform="twitter",
            )

        # Check size limits
        if mime_type in SUPPORTED_IMAGE_TYPES and file_size > MAX_IMAGE_SIZE:
            raise MediaUploadError(
                f"Image exceeds {format_file_size(MAX_IMAGE_SIZE)} limit",
                platform="twitter",
                media_type=mime_type,
            )
        elif mime_type == SUPPORTED_GIF_TYPE and file_size > MAX_GIF_SIZE:
            raise MediaUploadError(
                f"GIF exceeds {format_file_size(MAX_GIF_SIZE)} limit",
                platform="twitter",
                media_type=mime_type,
            )
        elif mime_type in SUPPORTED_VIDEO_TYPES and file_size > MAX_VIDEO_SIZE:
            raise MediaUploadError(
                f"Video exceeds {format_file_size(MAX_VIDEO_SIZE)} limit",
                platform="twitter",
                media_type=mime_type,
            )

    def _calculate_chunk_size(self, file_size: int, requested_chunk_size: int) -> int:
        """Calculate optimal chunk size for upload.

        Twitter requires minimum 1000 chunks, maximum 999 chunks.

        Args:
            file_size: Total file size.
            requested_chunk_size: Requested chunk size.

        Returns:
            Optimal chunk size in bytes.
        """
        # Minimum chunk size (file_size / 999)
        min_chunk_size = (file_size + 998) // 999

        # Maximum chunk size (Twitter API limit)
        max_chunk_size = MAX_CHUNK_SIZE

        # Ensure requested size is within bounds
        chunk_size = max(min(requested_chunk_size, max_chunk_size), min_chunk_size)

        return chunk_size
