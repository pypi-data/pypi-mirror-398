"""LinkedIn media upload manager with support for images, videos, and documents.

LinkedIn uses the REST API for media uploads (Community Management API):
- Images API: POST /rest/images?action=initializeUpload
- Videos API: POST /rest/videos?action=initializeUpload + finalizeUpload
- Documents API: POST /rest/documents?action=initializeUpload

Upload process:
1. Initialize upload (get upload URL and asset URN)
2. Upload file to the URL (PUT)
3. For videos: Finalize upload with ETags from each chunk
4. For videos: Wait for processing to complete

This module supports:
- Image uploads (single and multiple)
- Video uploads with chunked upload and processing monitoring
- Document/PDF uploads
"""

import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

import httpx

from marqetive.core.exceptions import (
    MediaUploadError,
    ValidationError,
)
from marqetive.core.models import ProgressEvent, ProgressStatus
from marqetive.utils.file_handlers import download_file, read_file_bytes
from marqetive.utils.media import detect_mime_type, format_file_size
from marqetive.utils.retry import STANDARD_BACKOFF, retry_async

# Type aliases for progress callbacks
type SyncProgressCallback = Callable[[ProgressEvent], None]
type AsyncProgressCallback = Callable[[ProgressEvent], Awaitable[None]]
type ProgressCallback = SyncProgressCallback | AsyncProgressCallback

logger = logging.getLogger(__name__)

# LinkedIn limits (per REST API documentation)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 5 * 1024 * 1024 * 1024  # 5GB (for multi-part uploads)
MAX_VIDEO_SIZE_SINGLE = 200 * 1024 * 1024  # 200MB (practical limit for single upload)
MAX_DOCUMENT_SIZE = 100 * 1024 * 1024  # 100MB (per LinkedIn docs)
MAX_VIDEO_DURATION = 1800  # 30 minutes (per docs: 3 seconds to 30 minutes)
MAX_DOCUMENT_PAGES = 300  # Maximum pages for documents

# Video chunk size for multi-part uploads (per LinkedIn docs: 4MB per part)
VIDEO_CHUNK_SIZE = 4 * 1024 * 1024  # 4MB (4,194,304 bytes)

# Supported document MIME types
SUPPORTED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/vnd.ms-powerpoint",  # PPT
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # PPTX
    "application/msword",  # DOC
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
}

# Processing timeouts
VIDEO_PROCESSING_TIMEOUT = 600  # 10 minutes


class VideoProcessingState(str, Enum):
    """LinkedIn video processing states (per REST Videos API).

    Status values:
        PROCESSING: Asset processing to generate missing artifacts
        PROCESSING_FAILED: Processing failed (file size, format, internal error)
        AVAILABLE: Ready for use; all required artifacts available
        WAITING_UPLOAD: Waiting for source file upload completion
    """

    PROCESSING = "PROCESSING"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    AVAILABLE = "AVAILABLE"
    WAITING_UPLOAD = "WAITING_UPLOAD"


@dataclass
class UploadProgress:
    """Progress information for media upload.

    .. deprecated:: 0.2.0
        Use :class:`marqetive.core.models.ProgressEvent` instead.
        This class will be removed in a future version.
    """

    asset_id: str
    bytes_uploaded: int
    total_bytes: int
    status: Literal["registering", "uploading", "processing", "completed", "failed"]

    @property
    def percentage(self) -> float:
        """Calculate upload percentage."""
        if self.total_bytes == 0:
            return 0.0
        return (self.bytes_uploaded / self.total_bytes) * 100


@dataclass
class MediaAsset:
    """LinkedIn media asset result.

    Attributes:
        asset_id: LinkedIn asset URN.
        download_url: URL to download the media (if available).
        status: Current status of the asset.
    """

    asset_id: str
    download_url: str | None = None
    status: str | None = None


class LinkedInMediaManager:
    """Manager for LinkedIn media uploads using the Community Management API.

    Supports images, videos, and documents with progress tracking.

    Example:
        >>> manager = LinkedInMediaManager(person_urn, access_token)
        >>> asset = await manager.upload_image("/path/to/image.jpg")
        >>> print(f"Uploaded: {asset.asset_id}")
    """

    # Default API version in YYYYMM format
    DEFAULT_LINKEDIN_VERSION = "202511"

    def __init__(
        self,
        person_urn: str,
        access_token: str,
        *,
        linkedin_version: str | None = None,
        timeout: float = 60.0,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Initialize LinkedIn media manager.

        Args:
            person_urn: LinkedIn person or organization URN
                (e.g., "urn:li:person:ABC123" or "urn:li:organization:12345").
            access_token: LinkedIn OAuth access token.
            linkedin_version: LinkedIn API version in YYYYMM format (e.g., "202511").
                Defaults to the latest supported version.
            timeout: Request timeout in seconds.
            progress_callback: Optional callback for progress updates.
                Accepts ProgressEvent and can be sync or async.
        """
        self.person_urn = person_urn
        self.access_token = access_token
        self.linkedin_version = linkedin_version or self.DEFAULT_LINKEDIN_VERSION
        self.timeout = timeout
        self.progress_callback = progress_callback

        # Use REST API for media uploads (Community Management API)
        self.base_url = "https://api.linkedin.com/rest"
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
                "Linkedin-Version": self.linkedin_version,
                "Content-Type": "application/json",
            },
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
            platform="linkedin",
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

    async def __aenter__(self) -> "LinkedInMediaManager":
        """Enter async context."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context and cleanup."""
        await self.client.aclose()

    async def upload_image(
        self,
        file_path: str,
        *,
        alt_text: str | None = None,  # noqa: ARG002
    ) -> MediaAsset:
        """Upload an image to LinkedIn using the REST Images API.

        Uses the REST API endpoint: POST /rest/images?action=initializeUpload
        https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/images-api

        Args:
            file_path: Path to image file or URL.
            alt_text: Alternative text for accessibility (stored for reference).

        Returns:
            MediaAsset with image URN (urn:li:image:xxx).

        Raises:
            MediaUploadError: If upload fails.
            ValidationError: If file is invalid.

        Supported formats:
            JPG, GIF, PNG (GIF up to 250 frames)

        Example:
            >>> asset = await manager.upload_image("photo.jpg")
            >>> print(f"Image URN: {asset.asset_id}")
        """
        # Download if URL
        if file_path.startswith(("http://", "https://")):
            file_path = await download_file(file_path)

        # Validate
        mime_type = detect_mime_type(file_path)
        if not mime_type.startswith("image/"):
            raise ValidationError(
                f"File is not an image: {mime_type}",
                platform="linkedin",
            )

        # Read file
        file_bytes = await read_file_bytes(file_path)
        file_size = len(file_bytes)

        if file_size > MAX_IMAGE_SIZE:
            raise ValidationError(
                f"Image exceeds {format_file_size(MAX_IMAGE_SIZE)} limit",
                platform="linkedin",
            )

        # Step 1: Initialize upload using REST Images API
        init_payload = {"initializeUploadRequest": {"owner": self.person_urn}}

        try:
            response = await self.client.post(
                f"{self.base_url}/images?action=initializeUpload",
                json=init_payload,
            )
            response.raise_for_status()
            init_result = response.json()
        except httpx.HTTPError as e:
            raise MediaUploadError(
                f"Failed to initialize image upload: {e}",
                platform="linkedin",
                media_type="image",
            ) from e

        # Extract upload URL and image URN from response
        upload_url = init_result["value"]["uploadUrl"]
        image_urn = init_result["value"]["image"]

        # Notify start
        await self._emit_progress(
            status=ProgressStatus.INITIALIZING,
            progress=0,
            total=100,
            message="Registering image upload",
            entity_id=image_urn,
            bytes_uploaded=0,
            total_bytes=file_size,
        )

        # Step 2: Upload image binary via PUT
        await self._emit_progress(
            status=ProgressStatus.UPLOADING,
            progress=0,
            total=100,
            message="Uploading image",
            entity_id=image_urn,
            bytes_uploaded=0,
            total_bytes=file_size,
        )

        try:
            upload_response = await self.client.put(
                upload_url,
                content=file_bytes,
                headers={"Content-Type": "application/octet-stream"},
            )
            upload_response.raise_for_status()
        except httpx.HTTPError as e:
            raise MediaUploadError(
                f"Failed to upload image binary: {e}",
                platform="linkedin",
                media_type="image",
            ) from e

        # Notify completion
        await self._emit_progress(
            status=ProgressStatus.COMPLETED,
            progress=100,
            total=100,
            message="Image upload completed",
            entity_id=image_urn,
            bytes_uploaded=file_size,
            total_bytes=file_size,
        )

        logger.info(f"Image uploaded successfully: {image_urn}")
        return MediaAsset(asset_id=image_urn, status="AVAILABLE")

    async def upload_video(
        self,
        file_path: str,
        *,
        title: str | None = None,  # noqa: ARG002
        wait_for_processing: bool = True,
    ) -> MediaAsset:
        """Upload a video to LinkedIn using the REST Videos API.

        Uses the REST API endpoints:
        - POST /rest/videos?action=initializeUpload
        - PUT {uploadUrl} (for each chunk)
        - POST /rest/videos?action=finalizeUpload

        https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/videos-api

        Args:
            file_path: Path to video file or URL.
            title: Video title (reserved for future use).
            wait_for_processing: Wait for video processing to complete.

        Returns:
            MediaAsset with video URN (urn:li:video:xxx).

        Raises:
            MediaUploadError: If upload or processing fails.
            ValidationError: If file is invalid.

        Specifications:
            - Length: 3 seconds to 30 minutes
            - File size: 75 KB to 5 GB
            - Format: MP4
            - Chunk size: 4 MB per part (for multi-part uploads)

        Example:
            >>> asset = await manager.upload_video(
            ...     "video.mp4",
            ...     wait_for_processing=True
            ... )
            >>> print(f"Video URN: {asset.asset_id}")
        """
        # Download if URL
        if file_path.startswith(("http://", "https://")):
            file_path = await download_file(file_path)

        # Validate
        mime_type = detect_mime_type(file_path)
        if not mime_type.startswith("video/"):
            raise ValidationError(
                f"File is not a video: {mime_type}",
                platform="linkedin",
            )

        # Read file
        file_bytes = await read_file_bytes(file_path)
        file_size = len(file_bytes)

        if file_size > MAX_VIDEO_SIZE:
            raise ValidationError(
                f"Video exceeds {format_file_size(MAX_VIDEO_SIZE)} limit",
                platform="linkedin",
            )

        # Step 1: Initialize upload using REST Videos API
        init_payload = {
            "initializeUploadRequest": {
                "owner": self.person_urn,
                "fileSizeBytes": file_size,
                "uploadCaptions": False,
                "uploadThumbnail": False,
            }
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/videos?action=initializeUpload",
                json=init_payload,
            )
            response.raise_for_status()
            init_result = response.json()
        except httpx.HTTPError as e:
            raise MediaUploadError(
                f"Failed to initialize video upload: {e}",
                platform="linkedin",
                media_type="video",
            ) from e

        # Extract video URN and upload instructions
        video_urn = init_result["value"]["video"]
        upload_instructions = init_result["value"]["uploadInstructions"]
        upload_token = init_result["value"].get("uploadToken", "")

        # Notify start
        await self._emit_progress(
            status=ProgressStatus.INITIALIZING,
            progress=0,
            total=100,
            message="Registering video upload",
            entity_id=video_urn,
            bytes_uploaded=0,
            total_bytes=file_size,
        )

        # Step 2: Upload video in chunks and collect ETags
        uploaded_part_ids: list[str] = []
        total_chunks = len(upload_instructions)
        bytes_uploaded = 0

        for i, instruction in enumerate(upload_instructions):
            upload_url = instruction["uploadUrl"]
            first_byte = instruction["firstByte"]
            last_byte = instruction["lastByte"]

            # Extract chunk from file bytes
            chunk = file_bytes[first_byte : last_byte + 1]
            chunk_size = len(chunk)

            # Notify progress
            progress_pct = int((i / total_chunks) * 80)  # 80% for upload
            await self._emit_progress(
                status=ProgressStatus.UPLOADING,
                progress=progress_pct,
                total=100,
                message=f"Uploading chunk {i + 1}/{total_chunks}",
                entity_id=video_urn,
                bytes_uploaded=bytes_uploaded,
                total_bytes=file_size,
            )

            try:
                upload_response = await self.client.put(
                    upload_url,
                    content=chunk,
                    headers={"Content-Type": "application/octet-stream"},
                )
                upload_response.raise_for_status()

                # Get ETag from response headers (required for finalization)
                etag = upload_response.headers.get("etag")
                if etag:
                    uploaded_part_ids.append(etag)

                bytes_uploaded += chunk_size

            except httpx.HTTPError as e:
                raise MediaUploadError(
                    f"Failed to upload video chunk {i + 1}: {e}",
                    platform="linkedin",
                    media_type="video",
                ) from e

        # Step 3: Finalize upload
        await self._emit_progress(
            status=ProgressStatus.UPLOADING,
            progress=85,
            total=100,
            message="Finalizing video upload",
            entity_id=video_urn,
            bytes_uploaded=file_size,
            total_bytes=file_size,
        )

        finalize_payload = {
            "finalizeUploadRequest": {
                "video": video_urn,
                "uploadToken": upload_token,
                "uploadedPartIds": uploaded_part_ids,
            }
        }

        try:
            finalize_response = await self.client.post(
                f"{self.base_url}/videos?action=finalizeUpload",
                json=finalize_payload,
            )
            finalize_response.raise_for_status()
        except httpx.HTTPError as e:
            raise MediaUploadError(
                f"Failed to finalize video upload: {e}",
                platform="linkedin",
                media_type="video",
            ) from e

        # Step 4: Wait for processing if requested
        if wait_for_processing:
            await self._wait_for_video_processing(video_urn)

        # Notify completion
        final_status = (
            ProgressStatus.COMPLETED
            if wait_for_processing
            else ProgressStatus.PROCESSING
        )
        await self._emit_progress(
            status=final_status,
            progress=100,
            total=100,
            message=(
                "Video upload completed" if wait_for_processing else "Video processing"
            ),
            entity_id=video_urn,
            bytes_uploaded=file_size,
            total_bytes=file_size,
        )

        logger.info(f"Video uploaded successfully: {video_urn}")
        return MediaAsset(
            asset_id=video_urn,
            status="AVAILABLE" if wait_for_processing else "PROCESSING",
        )

    async def upload_document(
        self,
        file_path: str,
        *,
        title: str | None = None,  # noqa: ARG002
    ) -> MediaAsset:
        """Upload a document to LinkedIn using the Documents API.

        Uses the REST API endpoint /rest/documents as per LinkedIn documentation:
        https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/documents-api

        Args:
            file_path: Path to document file or URL.
            title: Document title (currently unused, reserved for future use).

        Returns:
            MediaAsset with document URN (urn:li:document:xxx).

        Raises:
            MediaUploadError: If upload fails.
            ValidationError: If file is invalid.

        Supported formats:
            PDF, PPT, PPTX, DOC, DOCX (max 100MB, 300 pages)

        Example:
            >>> asset = await manager.upload_document(
            ...     "presentation.pdf",
            ...     title="Q4 Report"
            ... )
        """
        # Download if URL
        if file_path.startswith(("http://", "https://")):
            file_path = await download_file(file_path)

        # Validate MIME type
        mime_type = detect_mime_type(file_path)
        if mime_type not in SUPPORTED_DOCUMENT_TYPES:
            raise ValidationError(
                f"Unsupported document type: {mime_type}. "
                f"Supported: PDF, PPT, PPTX, DOC, DOCX",
                platform="linkedin",
            )

        # Read file
        file_bytes = await read_file_bytes(file_path)
        file_size = len(file_bytes)

        if file_size > MAX_DOCUMENT_SIZE:
            raise ValidationError(
                f"Document exceeds {format_file_size(MAX_DOCUMENT_SIZE)} limit",
                platform="linkedin",
            )

        # Step 1: Initialize upload using REST documents API
        # Per docs: POST /rest/documents?action=initializeUpload
        init_payload = {"initializeUploadRequest": {"owner": self.person_urn}}

        try:
            response = await self.client.post(
                f"{self.base_url}/documents?action=initializeUpload",
                json=init_payload,
            )
            response.raise_for_status()
            init_result = response.json()
        except httpx.HTTPError as e:
            raise MediaUploadError(
                f"Failed to initialize document upload: {e}",
                platform="linkedin",
                media_type="document",
            ) from e

        # Extract upload URL and document URN from response
        upload_url = init_result["value"]["uploadUrl"]
        document_urn = init_result["value"]["document"]

        # Notify start
        await self._emit_progress(
            status=ProgressStatus.INITIALIZING,
            progress=0,
            total=100,
            message="Registering document upload",
            entity_id=document_urn,
            bytes_uploaded=0,
            total_bytes=file_size,
        )

        # Step 2: Upload document binary via PUT
        await self._emit_progress(
            status=ProgressStatus.UPLOADING,
            progress=0,
            total=100,
            message="Uploading document",
            entity_id=document_urn,
            bytes_uploaded=0,
            total_bytes=file_size,
        )

        try:
            upload_response = await self.client.put(
                upload_url,
                content=file_bytes,
                headers={"Content-Type": "application/octet-stream"},
            )
            upload_response.raise_for_status()
        except httpx.HTTPError as e:
            raise MediaUploadError(
                f"Failed to upload document binary: {e}",
                platform="linkedin",
                media_type="document",
            ) from e

        # Notify completion
        await self._emit_progress(
            status=ProgressStatus.COMPLETED,
            progress=100,
            total=100,
            message="Document upload completed",
            entity_id=document_urn,
            bytes_uploaded=file_size,
            total_bytes=file_size,
        )

        logger.info(f"Document uploaded successfully: {document_urn}")
        return MediaAsset(asset_id=document_urn, status="AVAILABLE")

    async def get_video_status(self, video_urn: str) -> dict[str, Any]:
        """Get processing status of a video using the REST Videos API.

        Uses the REST API endpoint: GET /rest/videos/{videoUrn}

        Args:
            video_urn: LinkedIn video URN (urn:li:video:xxx).

        Returns:
            Dictionary with video status information including:
            - status: PROCESSING, PROCESSING_FAILED, AVAILABLE, WAITING_UPLOAD
            - downloadUrl: URL to download/view the video (when AVAILABLE)
            - duration: Video length in milliseconds
            - aspectRatioWidth/Height: Video dimensions

        Example:
            >>> status = await manager.get_video_status("urn:li:video:C5505AQH...")
            >>> print(f"Status: {status['status']}")
        """
        from urllib.parse import quote

        encoded_urn = quote(video_urn, safe="")

        @retry_async(config=STANDARD_BACKOFF)
        async def _get_status() -> dict[str, Any]:
            response = await self.client.get(
                f"{self.base_url}/videos/{encoded_urn}",
            )
            response.raise_for_status()
            return response.json()

        return await _get_status()

    async def _wait_for_video_processing(
        self,
        video_urn: str,
        *,
        timeout: int = VIDEO_PROCESSING_TIMEOUT,
        check_interval: int = 5,
    ) -> None:
        """Wait for video processing to complete using the REST Videos API.

        Args:
            video_urn: LinkedIn video URN (urn:li:video:xxx).
            timeout: Maximum time to wait in seconds.
            check_interval: Time between status checks in seconds.

        Raises:
            MediaUploadError: If processing fails or times out.
        """
        elapsed = 0
        logger.info(f"Waiting for video {video_urn} to process...")

        while elapsed < timeout:
            status_data = await self.get_video_status(video_urn)
            status = status_data.get("status")

            if status == VideoProcessingState.AVAILABLE.value:
                logger.info(f"Video {video_urn} processing complete")
                return

            if status == VideoProcessingState.PROCESSING_FAILED.value:
                failure_reason = status_data.get("processingFailureReason", "Unknown")
                raise MediaUploadError(
                    f"Video processing failed for {video_urn}: {failure_reason}",
                    platform="linkedin",
                    media_type="video",
                )

            # Notify progress
            progress_pct = min(int((elapsed / timeout) * 90) + 85, 99)
            await self._emit_progress(
                status=ProgressStatus.PROCESSING,
                progress=progress_pct,
                total=100,
                message=f"Processing video ({status})",
                entity_id=video_urn,
            )

            await asyncio.sleep(check_interval)
            elapsed += check_interval

        raise MediaUploadError(
            f"Video processing timeout after {timeout}s",
            platform="linkedin",
            media_type="video",
        )
