"""Abstract base class for social media platform integrations.

This module defines the SocialMediaPlatform ABC that serves as a blueprint
for implementing platform-specific clients (Instagram, Twitter, LinkedIn, etc.).
All concrete implementations must implement the abstract methods defined here.
"""

import inspect
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from datetime import datetime
from types import TracebackType
from typing import Any

from marqetive.core.client import APIClient
from marqetive.core.exceptions import (
    PlatformAuthError,
    RateLimitError,
)
from marqetive.core.models import (
    AuthCredentials,
    Comment,
    MediaAttachment,
    PlatformResponse,
    Post,
    PostCreateRequest,
    PostUpdateRequest,
    ProgressEvent,
    ProgressStatus,
)

# Type aliases for progress callbacks
# Supports both sync and async callbacks using ProgressEvent
type SyncProgressCallback = Callable[[ProgressEvent], None]
type AsyncProgressCallback = Callable[[ProgressEvent], Awaitable[None]]
type ProgressCallback = SyncProgressCallback | AsyncProgressCallback


class SocialMediaPlatform(ABC):
    """Abstract base class for social media platform integrations.

    This class defines the common interface that all platform-specific clients
    must implement. It uses composition to include an APIClient instance and
    provides both abstract methods (must be implemented) and concrete utility
    methods (can be used as-is or overridden).

    Attributes:
        platform_name: Name of the platform (e.g., "instagram", "twitter")
        credentials: Authentication credentials for the platform
        api_client: HTTPx-based API client for making requests
        base_url: Base URL for the platform's API

    Example:
        >>> class TwitterClient(SocialMediaPlatform):
        ...     def __init__(self, credentials: AuthCredentials):
        ...         super().__init__(
        ...             platform_name="twitter",
        ...             credentials=credentials,
        ...             base_url="https://api.x.com/2"
        ...         )
        ...     # Implement abstract methods...
    """

    def __init__(
        self,
        platform_name: str,
        credentials: AuthCredentials,
        base_url: str,
        timeout: float = 30.0,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Initialize the platform client.

        Args:
            platform_name: Name of the platform
            credentials: Authentication credentials
            base_url: Base URL for the platform API
            timeout: Request timeout in seconds
            progress_callback: Optional callback for progress updates during
                long-running operations (e.g., media uploads). The callback
                receives (operation, progress, total, message).

        Raises:
            PlatformAuthError: If credentials are invalid or expired
        """
        self.platform_name = platform_name
        self.credentials = credentials
        self.base_url = base_url
        self.timeout = timeout
        self._progress_callback = progress_callback
        self.api_client: APIClient | None = None
        self._rate_limit_remaining: int | None = None
        self._rate_limit_reset: datetime | None = None

        # Validate credentials on initialization
        if self.credentials.is_expired():
            raise PlatformAuthError(
                "Access token has expired",
                platform=platform_name,
            )

    async def __aenter__(self) -> "SocialMediaPlatform":
        """Async context manager entry.

        Returns:
            Self for use in context manager.

        Example:
            >>> async with TwitterClient(creds) as client:
            ...     post = await client.get_post("12345")
        """
        headers = self._build_auth_headers()
        self.api_client = APIClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=headers,
        )
        await self.api_client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[Exception] | None,
        exc_val: Exception | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        if self.api_client:
            await self.api_client.__aexit__(exc_type, exc_val, exc_tb)

    def _build_auth_headers(self) -> dict[str, str]:
        """Build authentication headers for API requests.

        Returns:
            Dictionary of headers including authorization.
        """
        return {
            "Authorization": f"{self.credentials.token_type} {self.credentials.access_token}",
            "Content-Type": "application/json",
        }

    def _check_rate_limit(self) -> None:
        """Check if rate limit has been exceeded.

        Raises:
            RateLimitError: If rate limit is exceeded.
        """
        if self._rate_limit_remaining is not None and self._rate_limit_remaining <= 0:
            retry_after = None
            if self._rate_limit_reset:
                retry_after = int(
                    (self._rate_limit_reset - datetime.now()).total_seconds()
                )
            raise RateLimitError(
                "Rate limit exceeded",
                platform=self.platform_name,
                status_code=429,
                retry_after=retry_after,
            )

    def _update_rate_limit_info(
        self, remaining: int | None, reset_time: datetime | None
    ) -> None:
        """Update rate limit information from API response.

        Args:
            remaining: Number of remaining requests in current window
            reset_time: Timestamp when rate limit resets
        """
        self._rate_limit_remaining = remaining
        self._rate_limit_reset = reset_time

    async def _emit_progress(
        self,
        operation: str,
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

        This method supports both synchronous and asynchronous callbacks.
        It is safe to call even if no callback is registered.

        Args:
            operation: Name of the operation (e.g., "upload_media", "create_post", "create_thread")
            status: Current status of the operation
            progress: Current progress value (0-100 for percentage, or bytes)
            total: Total value for completion (100 for percentage, or total bytes)
            message: Optional human-readable status message
            entity_id: Optional platform-specific ID (media_id, post_id, etc.)
            file_path: Optional file path for upload operations
            bytes_uploaded: Optional bytes uploaded so far
            total_bytes: Optional total bytes to upload

        Example:
            >>> await self._emit_progress(
            ...     operation="upload_media",
            ...     status=ProgressStatus.UPLOADING,
            ...     progress=50,
            ...     total=100,
            ...     message="Uploading image 1 of 3",
            ...     entity_id="media_123",
            ... )
        """
        if self._progress_callback is None:
            return

        event = ProgressEvent(
            operation=operation,
            platform=self.platform_name,
            status=status,
            progress=progress,
            total=total,
            message=message,
            entity_id=entity_id,
            file_path=file_path,
            bytes_uploaded=bytes_uploaded,
            total_bytes=total_bytes,
        )

        result = self._progress_callback(event)

        # If callback returned a coroutine, await it
        if inspect.iscoroutine(result):
            await result

    # ==================== Validation Helpers ====================

    @abstractmethod
    def _validate_create_post_request(self, request: PostCreateRequest) -> None:
        """Validate a post creation request.

        This base implementation performs no validation. Subclasses should
        override this method to implement platform-specific validation rules.

        The validation method should raise ValidationError with descriptive
        messages including platform name and field name for consistency.

        Args:
            request: The post creation request to validate.

        Raises:
            ValidationError: If validation fails.

        Example:
            >>> def _validate_create_post_request(self, request):
            ...     if not request.content:
            ...         raise ValidationError(
            ...             "Content is required",
            ...             platform=self.platform_name,
            ...             field="content",
            ...         )
        """
        pass

    # ==================== Abstract Authentication Methods ====================

    @abstractmethod
    async def authenticate(self) -> AuthCredentials:
        """Perform platform-specific authentication flow.

        Each platform implements its own authentication mechanism (OAuth2,
        API keys, etc.). This method should handle the complete auth flow
        and return valid credentials.

        Returns:
            AuthCredentials object with access tokens.

        Raises:
            PlatformAuthError: If authentication fails.

        Example:
            >>> async with TwitterClient(creds) as client:
            ...     new_creds = await client.authenticate()
        """
        pass

    @abstractmethod
    async def refresh_token(self) -> AuthCredentials:
        """Refresh the access token using refresh token.

        Returns:
            Updated AuthCredentials with new access token.

        Raises:
            PlatformAuthError: If token refresh fails.
        """
        pass

    @abstractmethod
    async def is_authenticated(self) -> bool:
        """Check if current credentials are valid.

        Returns:
            True if authenticated and token is valid, False otherwise.
        """
        pass

    # ==================== Abstract Post CRUD Methods ====================

    @abstractmethod
    async def create_post(self, request: PostCreateRequest) -> Post:
        """Create and publish a new post.

        Args:
            request: Post creation request with content and media.

        Returns:
            Created Post object with platform-assigned ID.

        Raises:
            PlatformAuthError: If not authenticated.
            ValidationError: If request data is invalid.
            MediaUploadError: If media upload fails.

        Example:
            >>> request = PostCreateRequest(
            ...     content="Hello world!",
            ...     media_urls=["https://example.com/image.jpg"]
            ... )
            >>> post = await client.create_post(request)
        """
        pass

    @abstractmethod
    async def get_post(self, post_id: str) -> Post:
        """Retrieve a post by its ID.

        Args:
            post_id: Platform-specific post identifier.

        Returns:
            Post object with current data.

        Raises:
            PostNotFoundError: If post doesn't exist.
            PlatformAuthError: If not authenticated.
        """
        pass

    @abstractmethod
    async def update_post(self, post_id: str, request: PostUpdateRequest) -> Post:
        """Update an existing post.

        Note: Not all platforms support editing posts. Implementation should
        raise an appropriate error if editing is not supported.

        Args:
            post_id: Platform-specific post identifier.
            request: Post update request with new content.

        Returns:
            Updated Post object.

        Raises:
            PostNotFoundError: If post doesn't exist.
            ValidationError: If update data is invalid.
            PlatformError: If platform doesn't support editing.
        """
        pass

    @abstractmethod
    async def delete_post(self, post_id: str) -> bool:
        """Delete a post.

        Args:
            post_id: Platform-specific post identifier.

        Returns:
            True if deletion was successful.

        Raises:
            PostNotFoundError: If post doesn't exist.
            PlatformAuthError: If not authenticated or authorized.
        """
        pass

    async def create_thread(
        self,
        posts: list[PostCreateRequest],
    ) -> list[Post]:
        """Create a thread of connected posts.

        Not all platforms support threads. The default implementation raises
        NotImplementedError. Platforms that support threads (like Twitter)
        should override this method.

        Args:
            posts: List of post requests to create as a thread.
                   Each post can have its own content, media, etc.
                   First post is the head of the thread.

        Returns:
            List of Post objects for each post in the thread.

        Raises:
            NotImplementedError: If platform doesn't support threads.
            ValidationError: If posts list is empty.
            PlatformAuthError: If not authenticated.

        Example:
            >>> # Twitter thread example
            >>> posts = [
            ...     TwitterPostRequest(content="Thread start! 1/3"),
            ...     TwitterPostRequest(content="Middle 2/3", media_urls=[...]),
            ...     TwitterPostRequest(content="End 3/3"),
            ... ]
            >>> thread = await client.create_thread(posts)
        """
        raise NotImplementedError(
            f"{self.platform_name} does not support thread creation"
        )

    # ==================== Abstract Comment Methods ====================

    @abstractmethod
    async def get_comments(
        self,
        post_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Comment]:
        """Retrieve comments for a post.

        Args:
            post_id: Platform-specific post identifier.
            limit: Maximum number of comments to retrieve.
            offset: Number of comments to skip (for pagination).

        Returns:
            List of Comment objects.

        Raises:
            PostNotFoundError: If post doesn't exist.
        """
        pass

    @abstractmethod
    async def create_comment(self, post_id: str, content: str) -> Comment:
        """Add a comment to a post.

        Args:
            post_id: Platform-specific post identifier.
            content: Text content of the comment.

        Returns:
            Created Comment object.

        Raises:
            PostNotFoundError: If post doesn't exist.
            ValidationError: If comment content is invalid.
        """
        pass

    @abstractmethod
    async def delete_comment(self, comment_id: str) -> bool:
        """Delete a comment.

        Args:
            comment_id: Platform-specific comment identifier.

        Returns:
            True if deletion was successful.

        Raises:
            PlatformError: If comment doesn't exist or can't be deleted.
        """
        pass

    # ==================== Abstract Media Methods ====================

    @abstractmethod
    async def upload_media(
        self,
        media_url: str,
        media_type: str,
        alt_text: str | None = None,
    ) -> MediaAttachment:
        """Upload media to the platform.

        Args:
            media_url: URL of the media file to upload.
            media_type: Type of media (image, video, etc.).
            alt_text: Alternative text for accessibility.

        Returns:
            MediaAttachment object with platform-assigned media ID.

        Raises:
            MediaUploadError: If upload fails.
            ValidationError: If media type or format is not supported.
        """
        pass

    # ==================== Concrete Utility Methods ====================

    def get_rate_limit_info(self) -> dict[str, Any]:
        """Get current rate limit information.

        Returns:
            Dictionary with rate limit details.
        """
        return {
            "remaining": self._rate_limit_remaining,
            "reset_time": self._rate_limit_reset,
            "platform": self.platform_name,
        }

    async def validate_credentials(self) -> PlatformResponse:
        """Validate current credentials by checking authentication status.

        Returns:
            PlatformResponse indicating if credentials are valid.
        """
        try:
            is_valid = await self.is_authenticated()
            return PlatformResponse(
                success=is_valid,
                platform=self.platform_name,
                data={"valid": is_valid},
            )
        except Exception as e:
            return PlatformResponse(
                success=False,
                platform=self.platform_name,
                error_message=str(e),
            )
