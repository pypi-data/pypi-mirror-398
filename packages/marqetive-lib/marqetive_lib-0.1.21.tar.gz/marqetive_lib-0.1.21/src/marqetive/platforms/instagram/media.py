"""Instagram media manager for container-based publishing.

Instagram uses a two-step publishing process:
1. Create media containers (upload and process media)
2. Publish containers to make content live

This module provides comprehensive media management for:
- Feed posts (single image or carousel)
- Reels (videos)
- Stories (images and videos)
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
from marqetive.utils.retry import STANDARD_BACKOFF, retry_async

# Type aliases for progress callbacks
type SyncProgressCallback = Callable[[ProgressEvent], None]
type AsyncProgressCallback = Callable[[ProgressEvent], Awaitable[None]]
type ProgressCallback = SyncProgressCallback | AsyncProgressCallback

logger = logging.getLogger(__name__)

# Instagram API limits
MAX_CAROUSEL_ITEMS = 10
MAX_CAPTION_LENGTH = 2200
MAX_VIDEO_DURATION_FEED = 60  # seconds
MAX_VIDEO_DURATION_REEL = 90  # seconds
MAX_VIDEO_DURATION_STORY = 60  # seconds

# Processing timeouts
DEFAULT_VIDEO_TIMEOUT = 300  # 5 minutes
REEL_VIDEO_TIMEOUT = 420  # 7 minutes
STORY_VIDEO_TIMEOUT = 180  # 3 minutes


class MediaType(str, Enum):
    """Instagram media types."""

    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    CAROUSEL = "CAROUSEL"


class PublishStatus(str, Enum):
    """Container publishing status."""

    EXPIRED = "EXPIRED"
    ERROR = "ERROR"
    FINISHED = "FINISHED"
    IN_PROGRESS = "IN_PROGRESS"
    PUBLISHED = "PUBLISHED"


@dataclass
class MediaItem:
    """Media item for Instagram posts.

    Attributes:
        url: URL of the media file (must be publicly accessible).
        type: Type of media ("image" or "video").
        alt_text: Alternative text for accessibility.
    """

    url: str
    type: Literal["image", "video"]
    alt_text: str | None = None

    def __post_init__(self) -> None:
        """Validate media item."""
        if not self.url:
            raise ValidationError("Media URL cannot be empty", platform="instagram")

        if self.type not in ("image", "video"):
            raise ValidationError(
                f"Invalid media type: {self.type}. Must be 'image' or 'video'",
                platform="instagram",
            )


@dataclass
class ContainerResult:
    """Result of creating a media container.

    Attributes:
        container_id: Instagram container ID.
        status: Current status of the container.
        media_type: Type of media in container.
    """

    container_id: str
    status: str
    media_type: str


@dataclass
class PublishResult:
    """Result of publishing a container.

    Attributes:
        media_id: Instagram media ID (post/reel/story ID).
        permalink: Direct link to the published content.
    """

    media_id: str
    permalink: str | None = None


class InstagramMediaManager:
    """Manager for Instagram container-based media publishing.

    Instagram requires a two-step process:
    1. Create container (uploads and processes media)
    2. Publish container (makes it live)

    Example:
        >>> manager = InstagramMediaManager(ig_user_id, access_token)
        >>> # Single image post
        >>> media = [MediaItem(url="https://...", type="image")]
        >>> container_ids = await manager.create_feed_containers(
        ...     media, caption="Hello Instagram!"
        ... )
        >>> result = await manager.publish_container(container_ids[0])
    """

    def __init__(
        self,
        ig_user_id: str,
        access_token: str,
        *,
        api_version: str = "v21.0",
        timeout: float = 30.0,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Initialize Instagram media manager.

        Args:
            ig_user_id: Instagram Business Account ID.
            access_token: Instagram/Facebook access token.
            api_version: Instagram Graph API version.
            timeout: Request timeout in seconds.
            progress_callback: Optional callback for progress updates.
                Receives ProgressEvent objects with upload status and metrics.
        """
        self.ig_user_id = ig_user_id
        self.access_token = access_token
        self.api_version = api_version
        self.timeout = timeout
        self.progress_callback = progress_callback

        self.base_url = f"https://graph.instagram.com/{api_version}"
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            params={"access_token": access_token},
        )

    async def __aenter__(self) -> "InstagramMediaManager":
        """Enter async context."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context and cleanup."""
        await self.client.aclose()

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
            platform="instagram",
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

    async def create_feed_containers(
        self,
        media_items: list[MediaItem],
        *,
        caption: str | None = None,
        location_id: str | None = None,
        share_to_feed: bool = True,
    ) -> list[str]:
        """Create containers for Instagram feed post (single or carousel).

        Note: Instagram deprecated video feed posts. Use create_reel_container instead.

        Args:
            media_items: List of media items (images only, 1-10 items).
            caption: Post caption (max 2200 characters).
            location_id: Optional location ID.
            share_to_feed: Whether to share to feed (default: True).

        Returns:
            List of container IDs.

        Raises:
            ValidationError: If validation fails.
            MediaUploadError: If container creation fails.

        Example:
            >>> media = [
            ...     MediaItem("https://example.com/img1.jpg", "image"),
            ...     MediaItem("https://example.com/img2.jpg", "image"),
            ... ]
            >>> containers = await manager.create_feed_containers(
            ...     media, caption="Carousel post!"
            ... )
        """
        # Validate inputs
        if not media_items:
            raise ValidationError(
                "At least one media item required",
                platform="instagram",
                field="media_items",
            )

        if len(media_items) > MAX_CAROUSEL_ITEMS:
            raise ValidationError(
                f"Maximum {MAX_CAROUSEL_ITEMS} media items allowed",
                platform="instagram",
                field="media_items",
            )

        # Check for videos (not allowed in feed posts)
        video_items = [m for m in media_items if m.type == "video"]
        if video_items:
            raise ValidationError(
                "Instagram feed posts no longer support videos. Use create_reel_container instead.",
                platform="instagram",
                field="media_items",
            )

        if caption and len(caption) > MAX_CAPTION_LENGTH:
            raise ValidationError(
                f"Caption exceeds {MAX_CAPTION_LENGTH} characters",
                platform="instagram",
                field="caption",
            )

        is_carousel = len(media_items) > 1
        container_ids: list[str] = []

        logger.info(
            f"Creating {'carousel' if is_carousel else 'single'} "
            f"feed containers for {len(media_items)} items"
        )

        # Create individual containers
        for idx, media_item in enumerate(media_items):
            if is_carousel:
                # Carousel item containers
                container_id = await self._create_carousel_item_container(
                    media_item.url,
                    media_item.alt_text,
                )
            else:
                # Single post container
                container_id = await self._create_single_image_container(
                    media_item.url,
                    caption=caption,
                    location_id=location_id,
                    share_to_feed=share_to_feed,
                )

            container_ids.append(container_id)

            # Notify progress
            progress = int(((idx + 1) / len(media_items)) * 100)
            await self._emit_progress(
                status=ProgressStatus.COMPLETED,
                progress=progress,
                total=100,
                message=f"Created container {idx + 1}/{len(media_items)}",
                entity_id=container_id,
            )

        # If carousel, create parent container
        if is_carousel:
            parent_container = await self._create_carousel_parent_container(
                container_ids,
                caption=caption,
                location_id=location_id,
                share_to_feed=share_to_feed,
            )
            # Return only parent container for publishing
            return [parent_container]

        return container_ids

    async def create_reel_container(
        self,
        video_url: str,
        *,
        caption: str | None = None,
        cover_url: str | None = None,
        share_to_feed: bool = True,
        audio_name: str | None = None,
        wait_for_processing: bool = True,
    ) -> str:
        """Create container for Instagram Reel (video).

        Args:
            video_url: URL of video file (publicly accessible).
            caption: Reel caption (max 2200 characters).
            cover_url: Optional thumbnail image URL.
            share_to_feed: Share reel to main feed.
            audio_name: Optional audio/music name attribution.
            wait_for_processing: Wait for video processing to complete.

        Returns:
            Container ID ready for publishing.

        Raises:
            ValidationError: If validation fails.
            MediaUploadError: If container creation or processing fails.

        Example:
            >>> container_id = await manager.create_reel_container(
            ...     "https://example.com/video.mp4",
            ...     caption="Check out this reel!",
            ...     share_to_feed=True
            ... )
            >>> result = await manager.publish_container(container_id)
        """
        if caption and len(caption) > MAX_CAPTION_LENGTH:
            raise ValidationError(
                f"Caption exceeds {MAX_CAPTION_LENGTH} characters",
                platform="instagram",
                field="caption",
            )

        @retry_async(config=STANDARD_BACKOFF)
        async def _create() -> str:
            params: dict[str, Any] = {
                "media_type": "REELS",
                "video_url": video_url,
            }

            if caption:
                params["caption"] = caption
            if cover_url:
                params["cover_url"] = cover_url
            if not share_to_feed:
                params["share_to_feed"] = "false"
            if audio_name:
                params["audio_name"] = audio_name

            response = await self.client.post(
                f"{self.base_url}/{self.ig_user_id}/media",
                params=params,
            )
            response.raise_for_status()
            result = response.json()
            return result["id"]

        try:
            container_id = await _create()
            logger.info(f"Created reel container: {container_id}")

            # Wait for video processing if requested
            if wait_for_processing:
                await self._wait_for_container_ready(
                    container_id,
                    timeout=REEL_VIDEO_TIMEOUT,
                    media_type="reel",
                )

            await self._emit_progress(
                status=ProgressStatus.COMPLETED,
                progress=100,
                total=100,
                message="Reel container ready for publishing",
                entity_id=container_id,
            )

            return container_id

        except httpx.HTTPError as e:
            raise MediaUploadError(
                f"Failed to create reel container: {e}",
                platform="instagram",
                media_type="video",
            ) from e

    async def create_story_container(
        self,
        media_url: str,
        media_type: Literal["image", "video"],
        *,
        wait_for_processing: bool = True,
    ) -> str:
        """Create container for Instagram Story.

        Args:
            media_url: URL of media file.
            media_type: Type of media ("image" or "video").
            wait_for_processing: Wait for video processing (if video).

        Returns:
            Container ID ready for publishing.

        Raises:
            MediaUploadError: If container creation fails.

        Example:
            >>> container_id = await manager.create_story_container(
            ...     "https://example.com/story.jpg",
            ...     "image"
            ... )
            >>> result = await manager.publish_container(container_id)
        """

        @retry_async(config=STANDARD_BACKOFF)
        async def _create() -> str:
            params: dict[str, Any] = {
                "media_type": "STORIES",
            }

            if media_type == "image":
                params["image_url"] = media_url
            else:
                params["video_url"] = media_url

            response = await self.client.post(
                f"{self.base_url}/{self.ig_user_id}/media",
                params=params,
            )
            response.raise_for_status()
            result = response.json()
            return result["id"]

        try:
            container_id = await _create()
            logger.info(f"Created story container: {container_id}")

            # Wait for video processing if needed
            if media_type == "video" and wait_for_processing:
                await self._wait_for_container_ready(
                    container_id,
                    timeout=STORY_VIDEO_TIMEOUT,
                    media_type="story",
                )

            await self._emit_progress(
                status=ProgressStatus.COMPLETED,
                progress=100,
                total=100,
                message="Story container ready for publishing",
                entity_id=container_id,
            )

            return container_id

        except httpx.HTTPError as e:
            raise MediaUploadError(
                f"Failed to create story container: {e}",
                platform="instagram",
                media_type=media_type,
            ) from e

    async def publish_container(
        self,
        container_id: str,
    ) -> PublishResult:
        """Publish a media container to make it live.

        Args:
            container_id: Container ID to publish.

        Returns:
            PublishResult with media ID and permalink.

        Raises:
            MediaUploadError: If publishing fails.

        Example:
            >>> result = await manager.publish_container(container_id)
            >>> print(f"Published: {result.media_id}")
            >>> print(f"Link: {result.permalink}")
        """

        @retry_async(config=STANDARD_BACKOFF)
        async def _publish() -> PublishResult:
            response = await self.client.post(
                f"{self.base_url}/{self.ig_user_id}/media_publish",
                params={"creation_id": container_id},
            )
            response.raise_for_status()
            result = response.json()

            media_id = result["id"]

            # Fetch permalink
            permalink = await self._get_media_permalink(media_id)

            return PublishResult(media_id=media_id, permalink=permalink)

        try:
            result = await _publish()
            logger.info(f"Published container {container_id} -> {result.media_id}")
            return result

        except httpx.HTTPError as e:
            raise MediaUploadError(
                f"Failed to publish container: {e}",
                platform="instagram",
            ) from e

    async def get_container_status(self, container_id: str) -> dict[str, Any]:
        """Get status of a media container.

        Args:
            container_id: Container ID to check.

        Returns:
            Dictionary with container status information.

        Example:
            >>> status = await manager.get_container_status(container_id)
            >>> print(f"Status: {status['status_code']}")
        """

        @retry_async(config=STANDARD_BACKOFF)
        async def _get_status() -> dict[str, Any]:
            response = await self.client.get(
                f"{self.base_url}/{container_id}",
                params={"fields": "status_code,status"},
            )
            response.raise_for_status()
            return response.json()

        return await _get_status()

    async def _wait_for_container_ready(
        self,
        container_id: str,
        *,
        timeout: int = DEFAULT_VIDEO_TIMEOUT,
        check_interval: int = 5,
        media_type: str = "media",
    ) -> None:
        """Wait for container to finish processing.

        Args:
            container_id: Container ID to monitor.
            timeout: Maximum wait time in seconds.
            check_interval: Seconds between status checks.
            media_type: Type of media for logging.

        Raises:
            MediaUploadError: If processing fails or times out.
        """
        elapsed = 0
        logger.info(f"Waiting for {media_type} container {container_id} to process...")

        while elapsed < timeout:
            status_data = await self.get_container_status(container_id)
            status = status_data.get("status_code")

            if status == PublishStatus.FINISHED.value:
                logger.info(f"Container {container_id} processing complete")
                return

            if status in (PublishStatus.ERROR.value, PublishStatus.EXPIRED.value):
                error_msg = status_data.get("status", "Unknown error")
                raise MediaUploadError(
                    f"Container processing failed: {error_msg}",
                    platform="instagram",
                )

            # Notify progress
            progress = min(int((elapsed / timeout) * 90), 90)  # Cap at 90%
            await self._emit_progress(
                status=ProgressStatus.PROCESSING,
                progress=progress,
                total=100,
                message=f"Processing {media_type} container",
                entity_id=container_id,
            )

            await asyncio.sleep(check_interval)
            elapsed += check_interval

        raise MediaUploadError(
            f"Container processing timeout after {timeout}s",
            platform="instagram",
        )

    async def _create_single_image_container(
        self,
        image_url: str,
        *,
        caption: str | None = None,
        location_id: str | None = None,
        share_to_feed: bool = True,
    ) -> str:
        """Create container for single image post."""

        @retry_async(config=STANDARD_BACKOFF)
        async def _create() -> str:
            params: dict[str, Any] = {
                "image_url": image_url,
            }

            if caption:
                params["caption"] = caption
            if location_id:
                params["location_id"] = location_id
            if not share_to_feed:
                params["share_to_feed"] = "false"

            response = await self.client.post(
                f"{self.base_url}/{self.ig_user_id}/media",
                params=params,
            )
            response.raise_for_status()
            result = response.json()
            return result["id"]

        return await _create()

    async def _create_carousel_item_container(
        self,
        image_url: str,
        alt_text: str | None = None,
    ) -> str:
        """Create container for carousel item."""

        @retry_async(config=STANDARD_BACKOFF)
        async def _create() -> str:
            params: dict[str, Any] = {
                "image_url": image_url,
                "is_carousel_item": "true",
            }

            if alt_text:
                params["caption"] = alt_text  # Alt text goes in caption for items

            response = await self.client.post(
                f"{self.base_url}/{self.ig_user_id}/media",
                params=params,
            )
            response.raise_for_status()
            result = response.json()
            return result["id"]

        return await _create()

    async def _create_carousel_parent_container(
        self,
        children_ids: list[str],
        *,
        caption: str | None = None,
        location_id: str | None = None,
        share_to_feed: bool = True,
    ) -> str:
        """Create parent container for carousel post."""

        @retry_async(config=STANDARD_BACKOFF)
        async def _create() -> str:
            params: dict[str, Any] = {
                "media_type": "CAROUSEL",
                "children": ",".join(children_ids),
            }

            if caption:
                params["caption"] = caption
            if location_id:
                params["location_id"] = location_id
            if not share_to_feed:
                params["share_to_feed"] = "false"

            response = await self.client.post(
                f"{self.base_url}/{self.ig_user_id}/media",
                params=params,
            )
            response.raise_for_status()
            result = response.json()
            return result["id"]

        return await _create()

    async def _get_media_permalink(self, media_id: str) -> str | None:
        """Get permalink for published media."""
        try:
            response = await self.client.get(
                f"{self.base_url}/{media_id}",
                params={"fields": "permalink"},
            )
            response.raise_for_status()
            result = response.json()
            return result.get("permalink")
        except httpx.HTTPError:
            return None
