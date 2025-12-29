"""Instagram-specific exception handling and error code mapping.

This module provides comprehensive error handling for Instagram Graph API errors.
"""

from typing import Any

from marqetive.core.exceptions import (
    MediaUploadError,
    PlatformAuthError,
    PlatformError,
    RateLimitError,
    ValidationError,
)


# Instagram Graph API error codes
# Source: https://developers.facebook.com/docs/graph-api/guides/error-handling
class InstagramErrorCode:
    """Instagram Graph API error codes."""

    # Authentication & Authorization (1-99)
    API_UNKNOWN = 1
    API_SERVICE = 2
    API_TOO_MANY_CALLS = 4
    API_USER_TOO_MANY_CALLS = 17
    API_PERMISSION_DENIED = 10
    OAuthException = 190
    ACCESS_TOKEN_EXPIRED = 190

    # Resource errors (100-199)
    UNSUPPORTED_GET_REQUEST = 100
    INVALID_PARAMETER = 100
    USER_NOT_VISIBLE = 190

    # Rate limiting (200-299)
    APPLICATION_LIMIT = 4
    USER_REQUEST_LIMIT = 17

    # Media errors (300-399)
    MEDIA_UPLOAD_ERROR = 324
    INVALID_MEDIA_TYPE = 352
    MEDIA_PROCESSING_ERROR = 368


# Error type constants
ERROR_TYPE_OAUTH = "OAuthException"
ERROR_TYPE_API = "FacebookApiException"
ERROR_TYPE_GRAPH_METHOD = "GraphMethodException"


# Mapping of error codes to user-friendly messages
ERROR_MESSAGES: dict[int, str] = {
    1: "An unknown error occurred.",
    2: "A service error occurred. Please try again later.",
    4: "Application request limit reached. Please retry later.",
    17: "User request limit reached. Please retry later.",
    10: "Permission denied. Check your app permissions.",
    100: "Invalid or unsupported parameter in request.",
    190: "Access token is invalid or expired. Please re-authenticate.",
    324: "Media upload failed. Please check file format and size.",
    352: "Invalid media type. Instagram only supports specific formats.",
    368: "Media processing failed. Please try a different file.",
}


# Retryable error codes
RETRYABLE_ERROR_CODES = {
    1,  # Unknown error
    2,  # Service error
    4,  # Too many calls
    17,  # User too many calls
}


# Non-retryable error codes
NON_RETRYABLE_ERROR_CODES = {
    10,  # Permission denied
    100,  # Invalid parameter
    190,  # OAuth exception
    352,  # Invalid media type
}


def map_instagram_error(
    status_code: int | None,
    error_code: int | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    response_data: dict[str, Any] | None = None,
) -> PlatformError:
    """Map Instagram Graph API error to appropriate exception.

    Args:
        status_code: HTTP status code.
        error_code: Instagram-specific error code.
        error_type: Instagram error type.
        error_message: Error message from API.
        response_data: Full response data from API.

    Returns:
        Appropriate PlatformError subclass.

    Example:
        >>> error = map_instagram_error(401, 190, "OAuthException")
        >>> print(type(error).__name__)
        PlatformAuthError
    """
    # Extract error details from response if provided
    if response_data and "error" in response_data:
        error_obj = response_data["error"]
        if not error_code:
            error_code = error_obj.get("code")
        if not error_type:
            error_type = error_obj.get("type")
        if not error_message:
            error_message = error_obj.get("message")

    # Get user-friendly message
    friendly_message = ERROR_MESSAGES.get(
        error_code or 0, error_message or "Unknown error"
    )

    # Determine retry-after for rate limits
    retry_after = None
    if error_code in (4, 17):
        # Instagram uses 1-hour windows typically
        retry_after = 3600  # 1 hour in seconds

    # Map to appropriate exception type
    # OAuth / Authentication errors
    if error_type == ERROR_TYPE_OAUTH or error_code == 190:
        return PlatformAuthError(
            friendly_message,
            platform="instagram",
            status_code=status_code or 401,
        )

    # Permission errors
    if error_code == 10 or status_code == 403:
        return PlatformAuthError(
            friendly_message,
            platform="instagram",
            status_code=status_code or 403,
        )

    # Rate limit errors
    if error_code in (4, 17) or status_code == 429:
        return RateLimitError(
            friendly_message,
            platform="instagram",
            status_code=status_code or 429,
            retry_after=retry_after,
        )

    # Validation errors
    if error_code == 100:
        return ValidationError(
            friendly_message,
            platform="instagram",
        )

    # Media errors
    if error_code in (324, 352, 368):
        return MediaUploadError(
            friendly_message,
            platform="instagram",
            status_code=status_code,
        )

    # Generic platform error
    return PlatformError(
        friendly_message,
        platform="instagram",
        status_code=status_code,
    )


def is_retryable_instagram_error(
    status_code: int | None,
    error_code: int | None = None,
    error_type: str | None = None,
) -> bool:
    """Determine if an Instagram error is retryable.

    Args:
        status_code: HTTP status code.
        error_code: Instagram-specific error code.
        error_type: Instagram error type.

    Returns:
        True if error is retryable, False otherwise.

    Example:
        >>> is_retryable_instagram_error(500)
        True
        >>> is_retryable_instagram_error(400, 190, "OAuthException")
        False
    """
    # Check explicit non-retryable codes first
    if error_code in NON_RETRYABLE_ERROR_CODES:
        return False

    # OAuth errors are not retryable
    if error_type == ERROR_TYPE_OAUTH:
        return False

    # Check retryable codes
    if error_code in RETRYABLE_ERROR_CODES:
        return True

    # Check HTTP status codes
    if status_code:
        # 5xx errors are generally retryable
        if 500 <= status_code < 600:
            return True
        # 429 is retryable
        if status_code == 429:
            return True
        # 4xx errors (except 429) are generally not retryable
        if 400 <= status_code < 500:
            return False

    # Default to not retryable for safety
    return False


def get_retry_delay(
    status_code: int | None,
    error_code: int | None = None,
    attempt: int = 1,
) -> float:
    """Get recommended retry delay for Instagram error.

    Args:
        status_code: HTTP status code.
        error_code: Instagram-specific error code.
        attempt: Current retry attempt number.

    Returns:
        Recommended delay in seconds.

    Example:
        >>> get_retry_delay(503, attempt=1)
        5.0
        >>> get_retry_delay(None, 4)
        3600.0
    """
    # Rate limit errors - wait full window
    if error_code in (4, 17):
        return 3600.0  # 1 hour

    # Server errors - exponential backoff
    if status_code and 500 <= status_code < 600:
        base_delay = 5.0
        return min(base_delay * (2 ** (attempt - 1)), 120.0)

    # Default delay
    return 10.0


class InstagramAPIError(PlatformError):
    """Instagram Graph API specific error with detailed information.

    Attributes:
        error_code: Instagram-specific error code.
        error_type: Instagram error type.
        error_subcode: Instagram error subcode (if available).
        is_retryable: Whether the error is retryable.
        retry_delay: Recommended retry delay in seconds.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: int | None = None,
        error_type: str | None = None,
        error_subcode: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize Instagram API error.

        Args:
            message: Error message.
            status_code: HTTP status code.
            error_code: Instagram-specific error code.
            error_type: Instagram error type.
            error_subcode: Instagram error subcode.
            response_data: Full response data from API.
        """
        super().__init__(message, platform="instagram", status_code=status_code)
        self.error_code = error_code
        self.error_type = error_type
        self.error_subcode = error_subcode
        self.response_data = response_data
        self.is_retryable = is_retryable_instagram_error(
            status_code, error_code, error_type
        )
        self.retry_delay = get_retry_delay(status_code, error_code)

    def __repr__(self) -> str:
        """String representation of error."""
        return (
            f"InstagramAPIError(message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"error_code={self.error_code}, "
            f"error_type={self.error_type!r}, "
            f"retryable={self.is_retryable})"
        )
