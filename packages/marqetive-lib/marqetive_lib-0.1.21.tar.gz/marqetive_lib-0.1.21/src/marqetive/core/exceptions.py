"""Custom exceptions for social media platform integrations.

This module defines platform-specific exceptions for handling errors
that may occur during API interactions with various social media platforms.
"""


class PlatformError(Exception):
    """Base exception for all platform-related errors.

    Args:
        message: Human-readable error message
        platform: Name of the platform where error occurred
        status_code: HTTP status code if applicable

    Example:
        >>> raise PlatformError("API request failed", platform="instagram")
    """

    def __init__(
        self,
        message: str,
        platform: str | None = None,
        status_code: int | None = None,
    ) -> None:
        self.message = message
        self.platform = platform
        self.status_code = status_code
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message with platform and status code."""
        parts = [self.message]
        if self.platform:
            parts.append(f"Platform: {self.platform}")
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        return " | ".join(parts)


class PlatformAuthError(PlatformError):
    """Raised when authentication or authorization fails.

    This exception is raised when:
    - Authentication credentials are invalid or expired
    - Access token refresh fails
    - OAuth flow encounters errors
    - Insufficient permissions for requested operation

    Args:
        message: Human-readable error message
        platform: Name of the platform where error occurred
        status_code: HTTP status code if applicable
        requires_reconnection: If True, user must re-authenticate (token permanently invalid)

    Example:
        >>> raise PlatformAuthError(
        ...     "Access token expired",
        ...     platform="twitter",
        ...     status_code=401
        ... )
        >>> # For invalid refresh token requiring user re-auth:
        >>> raise PlatformAuthError(
        ...     "Refresh token invalid",
        ...     platform="twitter",
        ...     status_code=400,
        ...     requires_reconnection=True
        ... )
    """

    def __init__(
        self,
        message: str,
        platform: str | None = None,
        status_code: int | None = None,
        *,
        requires_reconnection: bool = False,
    ) -> None:
        self.requires_reconnection = requires_reconnection
        super().__init__(message, platform, status_code)

    def _format_message(self) -> str:
        """Format the error message with reconnection info."""
        base_message = super()._format_message()
        if self.requires_reconnection:
            return f"{base_message} | Reconnection required"
        return base_message


class RateLimitError(PlatformError):
    """Raised when API rate limit is exceeded.

    Args:
        message: Human-readable error message
        platform: Name of the platform where error occurred
        status_code: HTTP status code (typically 429)
        retry_after: Seconds until rate limit resets

    Example:
        >>> raise RateLimitError(
        ...     "Rate limit exceeded",
        ...     platform="instagram",
        ...     status_code=429,
        ...     retry_after=3600
        ... )
    """

    def __init__(
        self,
        message: str,
        platform: str | None = None,
        status_code: int | None = None,
        retry_after: int | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, platform, status_code)

    def _format_message(self) -> str:
        """Format the error message with retry information."""
        base_message = super()._format_message()
        if self.retry_after:
            return f"{base_message} | Retry after: {self.retry_after}s"
        return base_message


class PostNotFoundError(PlatformError):
    """Raised when a requested post does not exist.

    Args:
        post_id: ID of the post that was not found
        platform: Name of the platform where error occurred
        status_code: HTTP status code (typically 404)

    Example:
        >>> raise PostNotFoundError(
        ...     post_id="12345",
        ...     platform="linkedin",
        ...     status_code=404
        ... )
    """

    def __init__(
        self,
        post_id: str,
        platform: str | None = None,
        status_code: int | None = None,
        message: str | None = None,
    ) -> None:
        self.post_id = post_id
        message = message or f"Post not found: {post_id}"
        super().__init__(message, platform, status_code)


class MediaUploadError(PlatformError):
    """Raised when media upload fails.

    This exception is raised when:
    - Media file format is not supported
    - Media file size exceeds platform limits
    - Network error during upload
    - Platform-specific upload validation fails

    Args:
        message: Human-readable error message
        platform: Name of the platform where error occurred
        status_code: HTTP status code if applicable
        media_type: Type of media that failed to upload (image, video, etc.)

    Example:
        >>> raise MediaUploadError(
        ...     "File size exceeds limit",
        ...     platform="twitter",
        ...     media_type="video"
        ... )
    """

    def __init__(
        self,
        message: str,
        platform: str | None = None,
        status_code: int | None = None,
        media_type: str | None = None,
    ) -> None:
        self.media_type = media_type
        super().__init__(message, platform, status_code)

    def _format_message(self) -> str:
        """Format the error message with media type information."""
        base_message = super()._format_message()
        if self.media_type:
            return f"{base_message} | Media type: {self.media_type}"
        return base_message


class ValidationError(PlatformError):
    """Raised when input validation fails.

    This exception is raised when:
    - Required fields are missing
    - Field values are invalid or out of range
    - Data format doesn't match platform requirements

    Args:
        message: Human-readable error message
        platform: Name of the platform where error occurred
        field: Name of the field that failed validation

    Example:
        >>> raise ValidationError(
        ...     "Caption exceeds maximum length",
        ...     platform="instagram",
        ...     field="caption"
        ... )
    """

    def __init__(
        self,
        message: str,
        platform: str | None = None,
        field: str | None = None,
    ) -> None:
        self.field = field
        super().__init__(message, platform)

    def _format_message(self) -> str:
        """Format the error message with field information."""
        base_message = super()._format_message()
        if self.field:
            return f"{base_message} | Field: {self.field}"
        return base_message


class InvalidFileTypeError(PlatformError):
    """Raised when file type is not supported by the platform.

    This exception is raised when:
    - File MIME type is not supported
    - File extension doesn't match content
    - Platform doesn't accept the file format

    Args:
        message: Human-readable error message
        platform: Name of the platform where error occurred
        file_type: The invalid file type/MIME type

    Example:
        >>> raise InvalidFileTypeError(
        ...     "BMP images not supported",
        ...     platform="instagram",
        ...     file_type="image/bmp"
        ... )
    """

    def __init__(
        self,
        message: str,
        platform: str | None = None,
        file_type: str | None = None,
    ) -> None:
        self.file_type = file_type
        super().__init__(message, platform)

    def _format_message(self) -> str:
        """Format the error message with file type information."""
        base_message = super()._format_message()
        if self.file_type:
            return f"{base_message} | File type: {self.file_type}"
        return base_message
