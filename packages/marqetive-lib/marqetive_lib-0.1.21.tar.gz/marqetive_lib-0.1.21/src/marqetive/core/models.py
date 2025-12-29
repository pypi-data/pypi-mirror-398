"""Common Pydantic models for social media platform integrations.

This module defines universal data models that provide a consistent interface
across different social media platforms. All models use Pydantic for validation
and type safety.
"""

from datetime import UTC, datetime, timedelta
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class MediaType(str, Enum):
    """Supported media types for platform posts."""

    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    DOCUMENT = "document"
    REEL = "reel"
    STORY = "story"


class PostStatus(str, Enum):
    """Status of a post on a platform."""

    DRAFT = "draft"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    FAILED = "failed"
    DELETED = "deleted"


class CommentStatus(str, Enum):
    """Status of a comment."""

    VISIBLE = "visible"
    HIDDEN = "hidden"
    DELETED = "deleted"


class AccountStatus(str, Enum):
    """Status of a platform account's authentication.

    Attributes:
        VALID: Account credentials are valid and working.
        EXPIRED: Access token has expired but can be refreshed.
        RECONNECTION_REQUIRED: OAuth error, user needs to reconnect account.
        ERROR: Temporary error occurred during authentication check.
    """

    VALID = "valid"
    EXPIRED = "expired"
    RECONNECTION_REQUIRED = "reconnection_required"
    ERROR = "error"


class ProgressStatus(StrEnum):
    """Standard progress status for operations across all platforms.

    Used with ProgressEvent to provide consistent progress tracking
    for long-running operations like media uploads and post creation.

    Attributes:
        INITIALIZING: Operation is starting, preparing resources.
        UPLOADING: Actively transferring data (e.g., uploading media).
        PROCESSING: Server-side processing (e.g., video transcoding).
        FINALIZING: Completing the operation (e.g., publishing post).
        COMPLETED: Operation finished successfully.
        FAILED: Operation failed with an error.
    """

    INITIALIZING = "initializing"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


class MediaAttachment(BaseModel):
    """Represents a media attachment (image, video, etc.).

    Attributes:
        media_id: Platform-specific media identifier
        media_type: Type of media (image, video, etc.)
        url: URL where the media is hosted
        thumbnail_url: URL of the thumbnail (for videos)
        width: Width in pixels
        height: Height in pixels
        size_bytes: File size in bytes
        duration_seconds: Duration for video/audio media
        alt_text: Alternative text for accessibility

    Example:
        >>> media = MediaAttachment(
        ...     media_id="12345",
        ...     media_type=MediaType.IMAGE,
        ...     url="https://example.com/image.jpg",
        ...     width=1080,
        ...     height=1080
        ... )
    """

    media_id: str
    media_type: MediaType
    url: HttpUrl
    thumbnail_url: HttpUrl | None = None
    width: int | None = None
    height: int | None = None
    size_bytes: int | None = None
    duration_seconds: float | None = None
    alt_text: str | None = None


class Post(BaseModel):
    """Universal representation of a social media post.

    Attributes:
        post_id: Platform-specific post identifier
        platform: Name of the platform (instagram, twitter, linkedin)
        content: Text content of the post
        media: List of media attachments
        status: Current status of the post
        url: Public URL of the post
        created_at: Timestamp when post was created
        updated_at: Timestamp when post was last updated
        scheduled_at: Timestamp when post is scheduled to publish
        author_id: ID of the user who created the post
        likes_count: Number of likes/reactions
        comments_count: Number of comments
        shares_count: Number of shares/retweets
        views_count: Number of views/impressions
        raw_data: Original platform-specific response data

    Example:
        >>> post = Post(
        ...     post_id="abc123",
        ...     platform="instagram",
        ...     content="Hello world!",
        ...     status=PostStatus.PUBLISHED,
        ...     created_at=datetime.now()
        ... )
    """

    post_id: str
    platform: str
    content: str | None = None
    media: list[MediaAttachment] = Field(default_factory=list)
    status: PostStatus = PostStatus.PUBLISHED
    url: HttpUrl | None = None
    created_at: datetime
    updated_at: datetime | None = None
    scheduled_at: datetime | None = None
    author_id: str | None = None
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    views_count: int = 0
    raw_data: dict[str, Any] = Field(default_factory=dict)


class Comment(BaseModel):
    """Represents a comment on a post.

    Attributes:
        comment_id: Platform-specific comment identifier
        post_id: ID of the post this comment belongs to
        platform: Name of the platform
        content: Text content of the comment
        author_id: ID of the user who created the comment
        author_username: Username of the comment author
        created_at: Timestamp when comment was created
        updated_at: Timestamp when comment was last updated
        likes_count: Number of likes on the comment
        replies_count: Number of replies to this comment
        parent_comment_id: ID of parent comment if this is a reply
        status: Current status of the comment
        raw_data: Original platform-specific response data

    Example:
        >>> comment = Comment(
        ...     comment_id="comment123",
        ...     post_id="post456",
        ...     platform="twitter",
        ...     content="Great post!",
        ...     author_id="user789",
        ...     created_at=datetime.now()
        ... )
    """

    comment_id: str
    post_id: str
    platform: str
    content: str
    author_id: str
    author_username: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    likes_count: int = 0
    replies_count: int = 0
    parent_comment_id: str | None = None
    status: CommentStatus = CommentStatus.VISIBLE
    raw_data: dict[str, Any] = Field(default_factory=dict)


class AuthCredentials(BaseModel):
    """Container for platform authentication credentials.

    Attributes:
        platform: Name of the platform
        access_token: OAuth access token or API key
        refresh_token: OAuth refresh token
        token_type: Type of token (Bearer, OAuth, etc.)
        expires_at: Timestamp when access token expires
        scope: List of permission scopes granted
        user_id: ID of the authenticated user
        username: Username/handle of the authenticated user
        status: Current status of the account credentials
        additional_data: Platform-specific auth data

    Example:
        >>> creds = AuthCredentials(
        ...     platform="instagram",
        ...     access_token="abc123",
        ...     token_type="Bearer",
        ...     expires_at=datetime(2025, 12, 31),
        ...     status=AccountStatus.VALID
        ... )
    """

    platform: str
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_at: datetime | None = None
    scope: list[str] = Field(default_factory=list)
    user_id: str | None = None
    username: str | None = None
    status: AccountStatus = AccountStatus.VALID
    additional_data: dict[str, Any] = Field(default_factory=dict)

    def is_expired(self, threshold_minutes: int = 5) -> bool:
        """Check if the access token has expired or will expire soon.

        Args:
            threshold_minutes: Consider token expired if it expires within
                             this many minutes (default: 5).

        Returns:
            True if token is expired or will expire soon, False otherwise.
        """
        if self.expires_at is None:
            return False

        threshold = datetime.now(UTC) + timedelta(minutes=threshold_minutes)
        return self.expires_at.astimezone(UTC) <= threshold

    def is_valid(self) -> bool:
        """Check if credentials are valid and not expired.

        Returns:
            True if status is VALID and token is not expired, False otherwise.
        """
        return self.status == AccountStatus.VALID and not self.is_expired()

    def needs_refresh(self) -> bool:
        """Check if credentials need to be refreshed.

        Returns:
            True if token is expired or status is EXPIRED, False otherwise.
        """
        return self.status == AccountStatus.EXPIRED or self.is_expired()

    def mark_expired(self) -> None:
        """Mark credentials as expired."""
        self.status = AccountStatus.EXPIRED

    def mark_valid(self) -> None:
        """Mark credentials as valid."""
        self.status = AccountStatus.VALID

    def mark_reconnection_required(self) -> None:
        """Mark credentials as requiring reconnection (OAuth error)."""
        self.status = AccountStatus.RECONNECTION_REQUIRED

    def mark_error(self) -> None:
        """Mark credentials as having a temporary error."""
        self.status = AccountStatus.ERROR


class PlatformResponse(BaseModel):
    """Wrapper for platform API responses.

    Attributes:
        success: Whether the API call was successful
        platform: Name of the platform
        data: Response data (can be any type)
        error_message: Error message if success is False
        status_code: HTTP status code
        rate_limit_remaining: Remaining API calls in current window
        rate_limit_reset: Timestamp when rate limit resets

    Example:
        >>> response = PlatformResponse(
        ...     success=True,
        ...     platform="twitter",
        ...     data={"tweet_id": "123"},
        ...     status_code=200
        ... )
    """

    success: bool
    platform: str
    data: Any = None
    error_message: str | None = None
    status_code: int | None = None
    rate_limit_remaining: int | None = None
    rate_limit_reset: datetime | None = None


class ProgressEvent(BaseModel):
    """Unified progress event for tracking long-running operations.

    Provides a consistent interface for progress callbacks across all platforms.
    Supports both synchronous and asynchronous callbacks.

    Attributes:
        operation: Name of the operation (e.g., "upload_media", "create_post", "create_thread").
        platform: Platform name (e.g., "twitter", "linkedin", "instagram", "tiktok").
        status: Current status of the operation.
        progress: Current progress value (0-100 for percentage, or bytes uploaded).
        total: Total value for completion (100 for percentage, or total bytes).
        message: Optional human-readable status message.
        entity_id: Optional platform-specific ID (media_id, post_id, container_id).
        file_path: Optional file path for upload operations.
        bytes_uploaded: Optional bytes uploaded so far.
        total_bytes: Optional total bytes to upload.

    Example:
        >>> # Progress callback for media upload
        >>> def on_progress(event: ProgressEvent) -> None:
        ...     print(f"{event.operation}: {event.percentage:.1f}% - {event.message}")
        ...
        >>> # Async progress callback
        >>> async def on_progress_async(event: ProgressEvent) -> None:
        ...     await log_to_database(event)

        >>> event = ProgressEvent(
        ...     operation="upload_media",
        ...     platform="twitter",
        ...     status=ProgressStatus.UPLOADING,
        ...     progress=50,
        ...     total=100,
        ...     message="Uploading image 1 of 2",
        ...     bytes_uploaded=524288,
        ...     total_bytes=1048576,
        ... )
        >>> print(event.percentage)  # 50.0
    """

    operation: str
    platform: str
    status: ProgressStatus
    progress: int
    total: int
    message: str | None = None

    # Optional detailed info
    entity_id: str | None = None
    file_path: str | None = None
    bytes_uploaded: int | None = None
    total_bytes: int | None = None

    @property
    def percentage(self) -> float:
        """Calculate progress as a percentage.

        Returns:
            Progress percentage (0.0 to 100.0).
        """
        if self.total == 0:
            return 0.0
        return (self.progress / self.total) * 100

    model_config = ConfigDict(frozen=True)


class PostCreateRequest(BaseModel):
    """Base request model for creating a new post.

    This is a minimal base model with universal fields that work across all platforms.
    For platform-specific features, use the dedicated request models:
    - TwitterPostRequest
    - LinkedInPostRequest
    - InstagramPostRequest
    - TikTokPostRequest

    Attributes:
        content: Text content of the post
        media_urls: List of URLs to media files to attach
        media_ids: List of pre-uploaded media IDs
        schedule_at: Optional timestamp to schedule the post
        link: URL to include in the post
        tags: List of hashtags or user tags
        location: Location/place tag for the post
        additional_data: Platform-specific data for backward compatibility

    Example:
        >>> request = PostCreateRequest(
        ...     content="Check out our new product!",
        ...     media_urls=["https://example.com/image.jpg"],
        ...     tags=["#newproduct", "#launch"]
        ... )
    """

    content: str | None = None
    media_urls: list[str] = Field(default_factory=list)
    media_ids: list[str] = Field(default_factory=list)
    schedule_at: datetime | None = None
    link: str | None = None
    tags: list[str] = Field(default_factory=list)
    location: str | None = None
    additional_data: dict[str, Any] = Field(default_factory=dict)


class PostUpdateRequest(BaseModel):
    """Base request model for updating an existing post.

    Note: Not all platforms support editing posts:
    - Twitter: No editing support (for most users)
    - Instagram: No editing support
    - TikTok: No editing support
    - LinkedIn: Supports updating content, CTA, and landing page

    For LinkedIn-specific update features, use LinkedInPostUpdateRequest.

    Attributes:
        content: Updated text content
        tags: Updated list of tags
        location: Updated location

    Example:
        >>> request = PostUpdateRequest(
        ...     content="Updated content here"
        ... )
    """

    content: str | None = None
    tags: list[str] | None = None
    location: str | None = None
