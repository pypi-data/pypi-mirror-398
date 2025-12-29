"""TikTok API client implementation.

This module provides a concrete implementation of the SocialMediaPlatform
ABC for TikTok, using the TikTok Content Posting API v2.

API Documentation: https://developers.tiktok.com/doc/content-posting-api-get-started
"""

from datetime import datetime
from typing import Any

from pydantic import HttpUrl

from marqetive.core.base import ProgressCallback, SocialMediaPlatform
from marqetive.core.exceptions import (
    PlatformAuthError,
    PlatformError,
    PostNotFoundError,
    ValidationError,
)
from marqetive.core.models import (
    AuthCredentials,
    Comment,
    CommentStatus,
    MediaAttachment,
    MediaType,
    Post,
    PostCreateRequest,
    PostStatus,
    PostUpdateRequest,
)
from marqetive.platforms.tiktok.exceptions import TikTokErrorCode, map_tiktok_error
from marqetive.platforms.tiktok.media import (
    CreatorInfo,
    MediaUploadResult,
    TikTokMediaManager,
)
from marqetive.platforms.tiktok.models import PrivacyLevel

# TikTok API base URL
TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"

# Video query fields
VIDEO_QUERY_FIELDS = [
    "id",
    "title",
    "video_description",
    "create_time",
    "cover_image_url",
    "share_url",
    "duration",
    "height",
    "width",
    "like_count",
    "comment_count",
    "share_count",
    "view_count",
]


class TikTokClient(SocialMediaPlatform):
    """TikTok API client.

    This client implements the SocialMediaPlatform interface for TikTok,
    focusing on video uploads and management using the Content Posting API v2.

    Note: Some operations (delete, update, comments) are not supported by TikTok API.
    """

    def __init__(
        self,
        credentials: AuthCredentials,
        timeout: float = 300.0,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Initialize TikTok client.

        Args:
            credentials: OAuth credentials with access_token and open_id in additional_data.
            timeout: Request timeout in seconds (default 300s for video processing).
            progress_callback: Optional callback for progress updates during
                long-running operations like video uploads.
        """
        super().__init__(
            platform_name="tiktok",
            credentials=credentials,
            base_url=TIKTOK_API_BASE,
            timeout=timeout,
            progress_callback=progress_callback,
        )
        self._media_manager: TikTokMediaManager | None = None
        self._creator_info: CreatorInfo | None = None

    async def _setup_managers(self) -> None:
        """Setup media manager."""
        if not self.credentials.access_token:
            raise PlatformAuthError("Access token is required", "tiktok")

        if (
            not self.credentials.additional_data
            or "open_id" not in self.credentials.additional_data
        ):
            raise PlatformAuthError("open_id is required in additional_data", "tiktok")

        self._media_manager = TikTokMediaManager(
            access_token=self.credentials.access_token,
            open_id=self.credentials.additional_data["open_id"],
            timeout=self.timeout,
        )
        await self._media_manager.__aenter__()

    async def _cleanup_managers(self) -> None:
        """Cleanup media manager."""
        if self._media_manager:
            await self._media_manager.__aexit__(None, None, None)
            self._media_manager = None

    async def __aenter__(self) -> "TikTokClient":
        await super().__aenter__()
        await self._setup_managers()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self._cleanup_managers()
        await super().__aexit__(exc_type, exc_val, exc_tb)

    async def authenticate(self) -> AuthCredentials:
        """Perform TikTok authentication."""
        if await self.is_authenticated():
            return self.credentials
        raise PlatformAuthError(
            "Invalid or expired credentials. Please re-authenticate via TikTok OAuth.",
            platform=self.platform_name,
        )

    async def refresh_token(self) -> AuthCredentials:
        """Refresh TikTok access token.

        Note: Token refresh should be handled by the AccountFactory.
        This method just returns the current credentials.
        """
        return self.credentials

    async def is_authenticated(self) -> bool:
        """Check if TikTok credentials are valid.

        Validates credentials by fetching user info from the API.
        """
        if not self.api_client:
            return False
        try:
            # Verify credentials by fetching authenticated user info
            # TikTok requires 'fields' as query parameter
            response = await self.api_client.get(
                "user/info/",
                params={"fields": "open_id,union_id,avatar_url,display_name"},
            )
            data = response.data

            # Check for error in response
            error_code = data.get("error", {}).get("code", "")
            if error_code and error_code != TikTokErrorCode.OK:
                return False

            return data.get("data", {}).get("user") is not None
        except PlatformError:
            return False

    # ==================== Validation ====================

    def _validate_create_post_request(self, request: PostCreateRequest) -> None:
        """Validate TikTok post creation request.

        TikTok Requirements:
            - Video URL is ALWAYS required (TikTok is a video-only platform)
            - Video duration: 3 seconds to 10 minutes
            - open_id must be in credentials.additional_data

        Args:
            request: Post creation request to validate.

        Raises:
            ValidationError: If validation fails.
        """
        if not request.media_urls:
            raise ValidationError(
                "A video URL is required to create a TikTok post. "
                "TikTok is a video platform - image-only or text-only posts are not supported.",
                platform=self.platform_name,
                field="media_urls",
            )

    # ==================== TikTok-specific Methods ====================

    async def query_creator_info(self) -> CreatorInfo:
        """Query creator info before posting.

        This must be called before creating a post to get available
        privacy levels and posting limits.

        Returns:
            CreatorInfo with available options for this creator.
        """
        if not self._media_manager:
            raise RuntimeError("Client must be used as async context manager")

        self._creator_info = await self._media_manager.query_creator_info()
        return self._creator_info

    async def create_post(self, request: PostCreateRequest) -> Post:
        """Create and publish a TikTok video.

        TikTok requires a video to be uploaded. The upload flow is:
        1. Query creator info (required)
        2. Initialize upload (get publish_id and upload_url)
        3. Upload video chunks
        4. Poll status until PUBLISH_COMPLETE

        Args:
            request: The post creation request, must contain a video URL.

        Returns:
            The created Post object.

        Raises:
            ValidationError: If the request is invalid (e.g., no media).
            MediaUploadError: If the video upload fails.
        """
        if not self._media_manager or not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        # Validate request
        self._validate_create_post_request(request)

        # 1. Query creator info (required before posting)
        if not self._creator_info:
            await self.query_creator_info()

        # 2. Determine privacy level
        privacy_level = PrivacyLevel.PRIVATE  # Default for unaudited apps
        requested_privacy = request.additional_data.get("privacy_level")
        if requested_privacy and self._creator_info:
            # Check if requested privacy is available
            available_privacies = self._creator_info.privacy_level_options or []
            if requested_privacy in available_privacies:
                privacy_level = PrivacyLevel(requested_privacy)

        # 3. Upload video and wait for publish
        video_url = request.media_urls[0]
        upload_result = await self._media_manager.upload_media(
            video_url,
            title=request.content or "",
            privacy_level=privacy_level,
            wait_for_publish=True,
        )

        # 4. Return minimal Post object without fetching details
        video_id = upload_result.video_id or upload_result.publish_id
        url = (
            HttpUrl(f"https://www.tiktok.com/@{self.credentials.username}/video/{video_id}")
            if self.credentials.username and video_id
            else None
        )

        return Post(
            post_id=video_id,
            platform=self.platform_name,
            content=request.content,
            status=PostStatus.PUBLISHED,
            created_at=datetime.now(),
            author_id=self.credentials.additional_data.get("open_id"),
            url=url,
            raw_data={
                "publish_id": upload_result.publish_id,
                "video_id": upload_result.video_id,
                "upload_status": upload_result.status,
                "privacy_level": privacy_level.value,
            },
        )

    async def get_post(self, post_id: str) -> Post:
        """Retrieve a TikTok video by its ID.

        Uses POST /video/query/ endpoint with filters.video_ids.

        Args:
            post_id: The video ID to retrieve.

        Returns:
            Post object with video details.

        Raises:
            PostNotFoundError: If the video doesn't exist.
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        try:
            # TikTok uses POST for video query with body
            response = await self.api_client.post(
                "video/query/",
                data={
                    "filters": {"video_ids": [post_id]},
                    "fields": VIDEO_QUERY_FIELDS,
                },
            )
            data = response.data

            # Check for API errors
            error_code = data.get("error", {}).get("code", "")
            if error_code and error_code != TikTokErrorCode.OK:
                raise map_tiktok_error(
                    status_code=response.status_code,
                    error_code=error_code,
                    error_message=data.get("error", {}).get("message"),
                    response_data=data,
                )

            videos = data.get("data", {}).get("videos", [])
            if not videos:
                raise PostNotFoundError(post_id, self.platform_name)

            return self._parse_video_post(videos[0])

        except PostNotFoundError:
            raise
        except PlatformError as e:
            raise PostNotFoundError(
                post_id, self.platform_name, status_code=e.status_code
            ) from e

    async def update_post(
        self,
        post_id: str,  # noqa: ARG002
        request: PostUpdateRequest,  # noqa: ARG002
    ) -> Post:
        """Update a TikTok video.

        TikTok API does not support updating videos after publishing.
        """
        raise PlatformError(
            "TikTok API does not support updating videos after publishing.",
            self.platform_name,
        )

    async def delete_post(self, post_id: str) -> bool:  # noqa: ARG002
        """Delete a TikTok video.

        TikTok API does not support deleting videos via API.
        Users must delete videos through the TikTok app.
        """
        raise PlatformError(
            "TikTok API does not support deleting videos. "
            "Please delete the video through the TikTok app.",
            self.platform_name,
        )

    async def get_comments(
        self,
        post_id: str,  # noqa: ARG002
        limit: int = 20,  # noqa: ARG002
        offset: int = 0,  # noqa: ARG002
    ) -> list[Comment]:
        """Retrieve comments for a TikTok video.

        Note: The standard TikTok API v2 does NOT provide access to video comments.
        Only comment_count is available in video metadata.
        The Comments API is only available via the Research API for academic use.

        Raises:
            PlatformError: Always, as this feature is not available.
        """
        raise PlatformError(
            "TikTok's standard API does not provide access to video comments. "
            "Comments are only available via the Research API for academic researchers.",
            self.platform_name,
        )

    async def create_comment(
        self,
        post_id: str,  # noqa: ARG002
        content: str,  # noqa: ARG002
    ) -> Comment:
        """Create a comment on a TikTok video.

        TikTok API does not support creating comments programmatically.
        """
        raise PlatformError(
            "TikTok API does not support creating comments.",
            self.platform_name,
        )

    async def delete_comment(self, comment_id: str) -> bool:  # noqa: ARG002
        """Delete a comment on a TikTok video.

        TikTok API does not support deleting comments programmatically.
        """
        raise PlatformError(
            "TikTok API does not support deleting comments.",
            self.platform_name,
        )

    async def upload_media(
        self,
        media_url: str,
        media_type: str,
        alt_text: str | None = None,  # noqa: ARG002
    ) -> MediaAttachment:
        """Upload a video to TikTok.

        This initiates the upload flow but doesn't publish.
        Use create_post() for full upload + publish flow.

        Args:
            media_url: URL or path to the video file.
            media_type: Must be "video" for TikTok.
            alt_text: Not used (TikTok doesn't support alt text).

        Returns:
            MediaAttachment with publish_id as media_id.

        Raises:
            ValidationError: If media_type is not "video".
        """
        if not self._media_manager:
            raise RuntimeError("Client not initialized. Use as async context manager.")

        if media_type != "video":
            raise ValidationError(
                "Only video media type is supported for TikTok.",
                platform=self.platform_name,
            )

        # Upload without waiting for publish
        result = await self._media_manager.upload_media(
            media_url,
            wait_for_publish=False,
        )

        # Use original URL if it's a valid HTTP URL, otherwise use a placeholder
        url = (
            HttpUrl(media_url)
            if media_url.startswith("http")
            else HttpUrl("https://www.tiktok.com/")
        )

        return MediaAttachment(
            media_id=result.publish_id,
            media_type=MediaType.VIDEO,
            url=url,
        )

    async def check_publish_status(self, publish_id: str) -> MediaUploadResult:
        """Check the publish status of an upload.

        Args:
            publish_id: The publish_id from upload_media.

        Returns:
            MediaUploadResult with current status and video_id if complete.
        """
        if not self._media_manager:
            raise RuntimeError("Client not initialized. Use as async context manager.")

        return await self._media_manager.check_publish_status(publish_id)

    async def wait_for_publish(self, publish_id: str) -> MediaUploadResult:
        """Wait for a video to finish publishing.

        Args:
            publish_id: The publish_id from upload_media.

        Returns:
            MediaUploadResult with video_id once published.
        """
        if not self._media_manager:
            raise RuntimeError("Client not initialized. Use as async context manager.")

        return await self._media_manager.wait_for_publish(publish_id)

    def _parse_video_post(self, video_data: dict[str, Any]) -> Post:
        """Parse a TikTok API video object into a Post model.

        Args:
            video_data: Raw video data from TikTok API.

        Returns:
            Post model with video details.
        """
        # TikTok uses 'id' field for video ID
        video_id = video_data.get("id", video_data.get("video_id", ""))

        # Handle share_url - construct URL from username if share_url not available
        share_url = video_data.get("share_url", "")
        if share_url:
            post_url: HttpUrl | None = HttpUrl(share_url)
        elif self.credentials.username and video_id:
            post_url = HttpUrl(
                f"https://www.tiktok.com/@{self.credentials.username}/video/{video_id}"
            )
        else:
            post_url = None

        # MediaAttachment.url requires a non-null HttpUrl, use placeholder if needed
        media_url = post_url if post_url else HttpUrl("https://www.tiktok.com/")

        return Post(
            post_id=video_id,
            platform=self.platform_name,
            content=video_data.get("title", video_data.get("video_description", "")),
            url=post_url,
            media=[
                MediaAttachment(
                    media_id=video_id,
                    media_type=MediaType.VIDEO,
                    url=media_url,
                    width=video_data.get("width"),
                    height=video_data.get("height"),
                )
            ],
            status=PostStatus.PUBLISHED,
            created_at=datetime.fromtimestamp(video_data.get("create_time", 0)),
            author_id=video_data.get("open_id", ""),
            likes_count=video_data.get("like_count", 0),
            comments_count=video_data.get("comment_count", 0),
            shares_count=video_data.get("share_count", 0),
            views_count=video_data.get("view_count", 0),
            raw_data=video_data,
        )

    def _parse_comment(self, comment_data: dict[str, Any], post_id: str) -> Comment:
        """Parse a TikTok API comment object into a Comment model.

        Note: This method exists for interface completeness but comments
        are not accessible via standard TikTok API.
        """
        return Comment(
            comment_id=comment_data.get("id", ""),
            post_id=post_id,
            platform=self.platform_name,
            content=comment_data.get("text", ""),
            author_id=comment_data.get("open_id", ""),
            created_at=datetime.fromtimestamp(comment_data.get("create_time", 0)),
            likes_count=comment_data.get("like_count", 0),
            replies_count=comment_data.get("reply_count", 0),
            status=CommentStatus.VISIBLE,
            raw_data=comment_data,
        )
