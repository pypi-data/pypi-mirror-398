"""TikTok media upload manager for handling video uploads.

This module provides functionality for uploading videos to TikTok's Content Posting API v2,
implementing the official upload flow:
1. POST /post/publish/video/init/ - Initialize upload, get publish_id and upload_url
2. PUT {upload_url} - Upload video chunks with Content-Range header
3. POST /post/publish/status/fetch/ - Poll until PUBLISH_COMPLETE

Reference: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
"""

import asyncio
import inspect
import json
import logging
import math
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
    PlatformError,
)
from marqetive.core.models import ProgressEvent, ProgressStatus
from marqetive.platforms.tiktok.exceptions import TikTokErrorCode, map_tiktok_error
from marqetive.platforms.tiktok.models import PrivacyLevel
from marqetive.utils.file_handlers import download_file
from marqetive.utils.media import detect_mime_type, format_file_size

# Type aliases for progress callbacks
type SyncProgressCallback = Callable[[ProgressEvent], None]
type AsyncProgressCallback = Callable[[ProgressEvent], Awaitable[None]]
type ProgressCallback = SyncProgressCallback | AsyncProgressCallback

logger = logging.getLogger(__name__)

# TikTok API Base URLs
TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"

# Chunk size limits per TikTok documentation
MIN_CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB minimum
MAX_CHUNK_SIZE = 64 * 1024 * 1024  # 64 MB maximum
FINAL_CHUNK_MAX = 128 * 1024 * 1024  # Final chunk can be up to 128 MB
DEFAULT_CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB default

# Video size and duration limits
MAX_VIDEO_SIZE = 4 * 1024 * 1024 * 1024  # 4 GB max for direct post
MIN_VIDEO_DURATION_SECS = 3
MAX_VIDEO_DURATION_SECS = 600  # 10 minutes for most videos

# Timeouts
DEFAULT_REQUEST_TIMEOUT = 300.0
STATUS_POLL_INTERVAL = 5.0  # Poll every 5 seconds
MAX_PROCESSING_TIME = 600.0  # 10 minutes max wait for processing

# Supported MIME types for TikTok
SUPPORTED_VIDEO_TYPES = {"video/mp4", "video/quicktime"}  # MP4 and MOV


class PublishStatus(str, Enum):
    """TikTok publish status values."""

    PROCESSING_UPLOAD = "PROCESSING_UPLOAD"
    PROCESSING_DOWNLOAD = "PROCESSING_DOWNLOAD"
    PUBLISH_COMPLETE = "PUBLISH_COMPLETE"
    FAILED = "FAILED"


@dataclass
class UploadProgress:
    """Progress information for a media upload.

    .. deprecated:: 0.2.0
        Use :class:`marqetive.core.models.ProgressEvent` instead.
        This class will be removed in a future version.

    Attributes:
        publish_id: TikTok publish ID (if available).
        file_path: Path to file being uploaded.
        bytes_uploaded: Number of bytes uploaded so far.
        total_bytes: Total file size in bytes.
        status: Current upload status.
    """

    publish_id: str | None
    file_path: str
    bytes_uploaded: int
    total_bytes: int
    status: Literal["init", "uploading", "processing", "completed", "failed"]

    @property
    def percentage(self) -> float:
        if self.total_bytes == 0:
            return 0.0
        return (self.bytes_uploaded / self.total_bytes) * 100

    def __str__(self) -> str:
        return (
            f"Upload Progress: {self.percentage:.1f}% "
            f"({format_file_size(self.bytes_uploaded)} / "
            f"{format_file_size(self.total_bytes)}) - {self.status}"
        )


@dataclass
class UploadInitResult:
    """Result from initializing a video upload."""

    publish_id: str
    upload_url: str


@dataclass
class MediaUploadResult:
    """Result of a successful media upload and publish."""

    publish_id: str
    video_id: str | None = None  # Available after PUBLISH_COMPLETE
    status: str = PublishStatus.PROCESSING_UPLOAD


@dataclass
class CreatorInfo:
    """Creator info returned from query_creator_info endpoint."""

    creator_avatar_url: str | None = None
    creator_username: str | None = None
    creator_nickname: str | None = None
    privacy_level_options: list[str] | None = None
    comment_disabled: bool = False
    duet_disabled: bool = False
    stitch_disabled: bool = False
    max_video_post_duration_sec: int = 600


class TikTokMediaManager:
    """Manages video uploads to the TikTok Content Posting API v2.

    This class implements the official TikTok upload flow:
    1. Initialize upload via POST /post/publish/video/init/
    2. Upload video chunks via PUT to upload_url
    3. Poll status via POST /post/publish/status/fetch/

    Reference: https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide
    """

    def __init__(
        self,
        access_token: str,
        open_id: str,
        *,
        progress_callback: ProgressCallback | None = None,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
    ) -> None:
        """Initialize the TikTok media manager.

        Args:
            access_token: OAuth access token with video.publish scope.
            open_id: User's open_id from OAuth flow.
            progress_callback: Optional callback for progress updates.
                Accepts ProgressEvent and can be sync or async.
            timeout: Request timeout in seconds.
        """
        self.access_token = access_token
        self.open_id = open_id
        self.progress_callback = progress_callback
        self.timeout = timeout

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8",
            },
        )
        # Separate client for uploads (no JSON content type)
        self._upload_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
        )

    async def __aenter__(self) -> "TikTokMediaManager":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._client.aclose()
        await self._upload_client.aclose()

    def _parse_json_response(self, response: httpx.Response) -> dict[str, Any]:
        """Parse JSON from HTTP response with proper error handling.

        Args:
            response: HTTP response object.

        Returns:
            Parsed JSON data as dictionary.

        Raises:
            PlatformError: If response is not valid JSON.
        """
        try:
            return response.json()
        except json.JSONDecodeError as e:
            raise PlatformError(
                f"Invalid JSON response from TikTok API: {e}",
                platform="tiktok",
                status_code=response.status_code,
            ) from e

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
            platform="tiktok",
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

    async def query_creator_info(self) -> CreatorInfo:
        """Query creator info before posting.

        This endpoint MUST be called before creating a post to get
        available privacy levels and posting limits.

        Returns:
            CreatorInfo with available options for this creator.

        Raises:
            PlatformError: If the request fails.
        """
        url = f"{TIKTOK_API_BASE}/post/publish/creator_info/query/"

        response = await self._client.post(url)
        data = self._parse_json_response(response)

        self._check_response_error(response.status_code, data)

        creator_data = data.get("data", {})
        return CreatorInfo(
            creator_avatar_url=creator_data.get("creator_avatar_url"),
            creator_username=creator_data.get("creator_username"),
            creator_nickname=creator_data.get("creator_nickname"),
            privacy_level_options=creator_data.get("privacy_level_options", []),
            comment_disabled=creator_data.get("comment_disabled", False),
            duet_disabled=creator_data.get("duet_disabled", False),
            stitch_disabled=creator_data.get("stitch_disabled", False),
            max_video_post_duration_sec=creator_data.get(
                "max_video_post_duration_sec", 600
            ),
        )

    async def init_video_upload(
        self,
        file_path: str,
        *,
        title: str = "",
        privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE,
        disable_duet: bool = False,
        disable_comment: bool = False,
        disable_stitch: bool = False,
        video_cover_timestamp_ms: int = 1000,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> UploadInitResult:
        """Initialize a video upload via FILE_UPLOAD source.

        Args:
            file_path: Path to the video file.
            title: Video title/description (with hashtags, mentions).
            privacy_level: Privacy setting for the video.
            disable_duet: Disable duet for this video.
            disable_comment: Disable comments for this video.
            disable_stitch: Disable stitch for this video.
            video_cover_timestamp_ms: Timestamp for cover image (ms).
            chunk_size: Size of each upload chunk.

        Returns:
            UploadInitResult with publish_id and upload_url.

        Raises:
            MediaUploadError: If initialization fails.
        """
        file_size = os.path.getsize(file_path)
        chunk_size = self._normalize_chunk_size(chunk_size, file_size)
        total_chunks = math.ceil(file_size / chunk_size)

        url = f"{TIKTOK_API_BASE}/post/publish/video/init/"

        payload = {
            "post_info": {
                "title": title,
                "privacy_level": privacy_level.value,
                "disable_duet": disable_duet,
                "disable_comment": disable_comment,
                "disable_stitch": disable_stitch,
                "video_cover_timestamp_ms": video_cover_timestamp_ms,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": chunk_size,
                "total_chunk_count": total_chunks,
            },
        }

        response = await self._client.post(url, json=payload)
        data = self._parse_json_response(response)

        self._check_response_error(response.status_code, data)

        result_data = data.get("data", {})
        publish_id = result_data.get("publish_id")
        upload_url = result_data.get("upload_url")

        if not publish_id or not upload_url:
            raise MediaUploadError(
                "Upload initialization succeeded but missing publish_id or upload_url",
                platform="tiktok",
            )

        logger.info(f"TikTok upload initialized: publish_id={publish_id}")
        return UploadInitResult(publish_id=publish_id, upload_url=upload_url)

    async def init_url_upload(
        self,
        video_url: str,
        *,
        title: str = "",
        privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE,
        disable_duet: bool = False,
        disable_comment: bool = False,
        disable_stitch: bool = False,
        video_cover_timestamp_ms: int = 1000,
    ) -> UploadInitResult:
        """Initialize a video upload via PULL_FROM_URL source.

        TikTok will download the video from the provided URL.

        Args:
            video_url: Public URL of the video to upload.
            title: Video title/description.
            privacy_level: Privacy setting for the video.
            disable_duet: Disable duet for this video.
            disable_comment: Disable comments for this video.
            disable_stitch: Disable stitch for this video.
            video_cover_timestamp_ms: Timestamp for cover image (ms).

        Returns:
            UploadInitResult with publish_id (no upload_url for URL source).

        Raises:
            MediaUploadError: If initialization fails.
        """
        url = f"{TIKTOK_API_BASE}/post/publish/video/init/"

        payload = {
            "post_info": {
                "title": title,
                "privacy_level": privacy_level.value,
                "disable_duet": disable_duet,
                "disable_comment": disable_comment,
                "disable_stitch": disable_stitch,
                "video_cover_timestamp_ms": video_cover_timestamp_ms,
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "video_url": video_url,
            },
        }

        response = await self._client.post(url, json=payload)
        data = self._parse_json_response(response)

        self._check_response_error(response.status_code, data)

        result_data = data.get("data", {})
        publish_id = result_data.get("publish_id")

        if not publish_id:
            raise MediaUploadError(
                "URL upload initialization succeeded but missing publish_id",
                platform="tiktok",
            )

        logger.info(f"TikTok URL upload initialized: publish_id={publish_id}")
        return UploadInitResult(publish_id=publish_id, upload_url="")

    async def upload_video_chunks(
        self,
        upload_url: str,
        file_path: str,
        publish_id: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> None:
        """Upload video file in chunks to the upload_url.

        Uses PUT requests with Content-Range header as per TikTok spec.

        Args:
            upload_url: The upload URL from init_video_upload.
            file_path: Path to the video file.
            publish_id: The publish_id for progress tracking.
            chunk_size: Size of each chunk (5MB - 64MB).

        Raises:
            MediaUploadError: If any chunk upload fails.
        """
        file_size = os.path.getsize(file_path)
        chunk_size = self._normalize_chunk_size(chunk_size, file_size)
        mime_type = detect_mime_type(file_path)

        await self._emit_progress(
            status=ProgressStatus.UPLOADING,
            progress=0,
            total=100,
            message="Starting video upload",
            entity_id=publish_id,
            file_path=file_path,
            bytes_uploaded=0,
            total_bytes=file_size,
        )

        bytes_uploaded = 0

        async with aiofiles.open(file_path, "rb") as f:
            chunk_index = 0
            while True:
                chunk_data = await f.read(chunk_size)
                if not chunk_data:
                    break

                chunk_start = bytes_uploaded
                chunk_end = bytes_uploaded + len(chunk_data) - 1

                headers = {
                    "Content-Type": mime_type,
                    "Content-Range": f"bytes {chunk_start}-{chunk_end}/{file_size}",
                    "Content-Length": str(len(chunk_data)),
                }

                logger.debug(
                    f"Uploading chunk {chunk_index + 1}: "
                    f"bytes {chunk_start}-{chunk_end}/{file_size}"
                )

                response = await self._upload_client.put(
                    upload_url,
                    content=chunk_data,
                    headers=headers,
                )

                if response.status_code not in (200, 201, 206):
                    raise MediaUploadError(
                        f"Chunk upload failed with status {response.status_code}: "
                        f"{response.text}",
                        platform="tiktok",
                        status_code=response.status_code,
                    )

                bytes_uploaded += len(chunk_data)
                chunk_index += 1

                await self._emit_progress(
                    status=ProgressStatus.UPLOADING,
                    progress=int((bytes_uploaded / file_size) * 100),
                    total=100,
                    message=f"Uploading chunk {chunk_index}",
                    entity_id=publish_id,
                    file_path=file_path,
                    bytes_uploaded=bytes_uploaded,
                    total_bytes=file_size,
                )

        logger.info(
            f"TikTok video upload complete: {bytes_uploaded} bytes in {chunk_index} chunks"
        )

    async def check_publish_status(self, publish_id: str) -> MediaUploadResult:
        """Check the publish status of an upload.

        Args:
            publish_id: The publish_id from upload initialization.

        Returns:
            MediaUploadResult with current status and video_id if complete.

        Raises:
            PlatformError: If the status check fails.
        """
        url = f"{TIKTOK_API_BASE}/post/publish/status/fetch/"

        response = await self._client.post(url, json={"publish_id": publish_id})
        data = self._parse_json_response(response)

        self._check_response_error(response.status_code, data)

        result_data = data.get("data", {})
        status = result_data.get("status", PublishStatus.FAILED)

        logger.debug(f"TikTok publish status response: {data}")

        video_id = None
        if status == PublishStatus.PUBLISH_COMPLETE:
            # Video IDs are in publicaly_available_post_id array (note TikTok's typo)
            # For private/SELF_ONLY posts, this may be empty
            video_ids = result_data.get("publicaly_available_post_id", [])
            if video_ids:
                video_id = str(video_ids[0])
            else:
                # Try alternative field names that TikTok might use
                video_id = result_data.get("video_id") or result_data.get("item_id")
                logger.warning(
                    f"No video ID in publicaly_available_post_id, "
                    f"tried alternatives: video_id={video_id}"
                )

        return MediaUploadResult(
            publish_id=publish_id,
            video_id=video_id,
            status=status,
        )

    async def wait_for_publish(
        self,
        publish_id: str,
        file_path: str = "",
        max_wait: float = MAX_PROCESSING_TIME,
    ) -> MediaUploadResult:
        """Wait for a video to finish publishing.

        Polls the status endpoint until PUBLISH_COMPLETE or FAILED.

        Args:
            publish_id: The publish_id from upload initialization.
            file_path: Original file path for progress callbacks.
            max_wait: Maximum time to wait in seconds.

        Returns:
            MediaUploadResult with final status and video_id.

        Raises:
            MediaUploadError: If publishing fails or times out.
        """
        if file_path:
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            await self._emit_progress(
                status=ProgressStatus.PROCESSING,
                progress=0,
                total=100,
                message="Processing video on TikTok servers",
                entity_id=publish_id,
                file_path=file_path,
                bytes_uploaded=file_size,
                total_bytes=file_size,
            )

        elapsed = 0.0
        while elapsed < max_wait:
            result = await self.check_publish_status(publish_id)

            if result.status == PublishStatus.PUBLISH_COMPLETE:
                logger.info(f"TikTok video published: video_id={result.video_id}")
                if file_path:
                    file_size = (
                        os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    )
                    await self._emit_progress(
                        status=ProgressStatus.COMPLETED,
                        progress=100,
                        total=100,
                        message="Video published successfully",
                        entity_id=publish_id,
                        file_path=file_path,
                        bytes_uploaded=file_size,
                        total_bytes=file_size,
                    )
                return result

            if result.status == PublishStatus.FAILED:
                if file_path:
                    await self._emit_progress(
                        status=ProgressStatus.FAILED,
                        progress=0,
                        total=100,
                        message="Video publishing failed",
                        entity_id=publish_id,
                        file_path=file_path,
                        bytes_uploaded=0,
                        total_bytes=0,
                    )
                raise MediaUploadError(
                    f"TikTok video publishing failed: publish_id={publish_id}",
                    platform="tiktok",
                )

            logger.debug(f"Publish status: {result.status}, waiting...")
            await asyncio.sleep(STATUS_POLL_INTERVAL)
            elapsed += STATUS_POLL_INTERVAL

        raise MediaUploadError(
            f"Timed out waiting for video to publish after {max_wait}s",
            platform="tiktok",
        )

    async def upload_media(
        self,
        file_path: str,
        *,
        title: str = "",
        privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        wait_for_publish: bool = True,
    ) -> MediaUploadResult:
        """Upload a video file to TikTok (full flow).

        This is the main entry point that handles the complete upload flow:
        1. Download if URL
        2. Validate file
        3. Initialize upload
        4. Upload chunks
        5. Wait for publish (optional)

        Args:
            file_path: Local path or URL of the video to upload.
            title: Video title/description with hashtags.
            privacy_level: Privacy setting for the video.
            chunk_size: Size of each upload chunk.
            wait_for_publish: If True, wait until video is published.

        Returns:
            MediaUploadResult with publish_id and video_id (if published).

        Raises:
            FileNotFoundError: If the local file does not exist.
            InvalidFileTypeError: If the file is not a supported video format.
            MediaUploadError: If upload or processing fails.
        """
        # Track if we downloaded a temp file that needs cleanup
        temp_file_path: str | None = None

        try:
            # Handle URL downloads
            if file_path.startswith(("http://", "https://")):
                logger.info(f"Downloading media from URL: {file_path}")
                file_path = await download_file(file_path)
                temp_file_path = file_path  # Mark for cleanup

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Media file not found: {file_path}")

            # Validate file
            mime_type = detect_mime_type(file_path)
            file_size = os.path.getsize(file_path)
            self._validate_media(mime_type, file_size)

            # Initialize upload
            init_result = await self.init_video_upload(
                file_path,
                title=title,
                privacy_level=privacy_level,
                chunk_size=chunk_size,
            )

            # Upload chunks
            await self.upload_video_chunks(
                init_result.upload_url,
                file_path,
                init_result.publish_id,
                chunk_size=chunk_size,
            )

            # Wait for publish
            if wait_for_publish:
                return await self.wait_for_publish(init_result.publish_id, file_path)

            return MediaUploadResult(
                publish_id=init_result.publish_id,
                status=PublishStatus.PROCESSING_UPLOAD,
            )
        finally:
            # Clean up downloaded temp file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.debug(f"Cleaned up temp file: {temp_file_path}")
                except OSError as e:
                    logger.warning(
                        f"Failed to clean up temp file {temp_file_path}: {e}"
                    )

    def _normalize_chunk_size(self, chunk_size: int, file_size: int) -> int:
        """Normalize chunk size to TikTok's requirements.

        TikTok chunk requirements:
        - Minimum chunk size: 5MB (except for files smaller than 5MB)
        - Maximum chunk size: 64MB (final chunk can be up to 128MB)
        - All non-final chunks must be at least MIN_CHUNK_SIZE

        Args:
            chunk_size: Requested chunk size.
            file_size: Total file size.

        Returns:
            Normalized chunk size within TikTok limits.
        """
        # Files smaller than MAX_CHUNK_SIZE (64MB) should be uploaded as single chunk
        # This avoids issues with the final chunk being smaller than MIN_CHUNK_SIZE
        if file_size <= MAX_CHUNK_SIZE:
            return file_size

        # For larger files, ensure chunk size is within limits
        chunk_size = max(MIN_CHUNK_SIZE, min(chunk_size, MAX_CHUNK_SIZE))

        # Ensure the last chunk won't be smaller than MIN_CHUNK_SIZE
        # If it would be, increase chunk size to make fewer, larger chunks
        total_chunks = math.ceil(file_size / chunk_size)
        last_chunk_size = file_size - (chunk_size * (total_chunks - 1))

        if last_chunk_size < MIN_CHUNK_SIZE and total_chunks > 1:
            # Recalculate to have fewer chunks with larger size
            # Use ceiling division to ensure last chunk is large enough
            total_chunks = math.ceil(file_size / MAX_CHUNK_SIZE)
            chunk_size = math.ceil(file_size / total_chunks)
            # Ensure still within limits
            chunk_size = max(MIN_CHUNK_SIZE, min(chunk_size, MAX_CHUNK_SIZE))

        return chunk_size

    def _validate_media(self, mime_type: str, file_size: int) -> None:
        """Validate media type and size against TikTok's requirements.

        Args:
            mime_type: MIME type of the file.
            file_size: Size of the file in bytes.

        Raises:
            InvalidFileTypeError: If MIME type is not supported.
            MediaUploadError: If file size exceeds limits.
        """
        if mime_type not in SUPPORTED_VIDEO_TYPES:
            raise InvalidFileTypeError(
                f"Unsupported video type for TikTok: {mime_type}. "
                f"Supported types: {', '.join(SUPPORTED_VIDEO_TYPES)}",
                platform="tiktok",
            )

        if file_size > MAX_VIDEO_SIZE:
            raise MediaUploadError(
                f"Video file size ({format_file_size(file_size)}) exceeds the "
                f"TikTok limit of {format_file_size(MAX_VIDEO_SIZE)}",
                platform="tiktok",
                media_type=mime_type,
            )

    def _check_response_error(self, status_code: int, data: dict[str, Any]) -> None:
        """Check API response for errors and raise appropriate exception.

        Args:
            status_code: HTTP status code.
            data: Response JSON data.

        Raises:
            PlatformError: If the response indicates an error.
        """
        error_data = data.get("error", {})
        error_code = error_data.get("code", "")

        # "ok" means success
        if error_code == TikTokErrorCode.OK:
            return

        # Map to appropriate exception
        error_message = error_data.get("message", "")
        raise map_tiktok_error(
            status_code=status_code,
            error_code=error_code,
            error_message=error_message,
            response_data=data,
        )
