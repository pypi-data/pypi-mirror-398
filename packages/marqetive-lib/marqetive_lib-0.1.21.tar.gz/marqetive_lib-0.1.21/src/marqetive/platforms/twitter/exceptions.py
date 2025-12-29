"""Twitter-specific exception handling and error code mapping.

This module provides comprehensive error handling for Twitter API errors including:
- HTTP status code mapping
- Twitter-specific error codes
- Retry strategies
- User-friendly error messages
"""

from typing import Any

from marqetive.core.exceptions import (
    MediaUploadError,
    PlatformAuthError,
    PlatformError,
    RateLimitError,
    ValidationError,
)


# Twitter API error codes
# Source: https://developer.x.com/en/support/twitter-api/error-troubleshooting
class TwitterErrorCode:
    """Twitter API error codes."""

    # Authentication errors (200-299)
    COULD_NOT_AUTHENTICATE = 32
    INVALID_OR_EXPIRED_TOKEN = 89
    UNABLE_TO_VERIFY_CREDENTIALS = 99
    BAD_AUTHENTICATION_DATA = 215

    # Authorization errors (300-399)
    FORBIDDEN = 64
    ACCOUNT_SUSPENDED = 63
    API_ACCESS_REVOKED = 87

    # Resource errors (400-499)
    PAGE_NOT_EXIST = 34
    USER_NOT_FOUND = 17
    TWEET_NOT_FOUND = 144
    NO_STATUS_FOUND = 34

    # Rate limiting (500-599)
    RATE_LIMIT_EXCEEDED = 88
    TOO_MANY_REQUESTS = 429

    # Validation errors (600-699)
    STATUS_TOO_LONG = 186
    DUPLICATE_STATUS = 187
    INVALID_MEDIA = 324
    MEDIA_ID_NOT_FOUND = 325

    # Media upload errors
    MEDIA_TYPE_UNSUPPORTED = 323
    MEDIA_SIZE_TOO_LARGE = 324
    VIDEO_DURATION_TOO_LONG = 324
    MEDIA_PROCESSING_FAILED = 324


# Mapping of error codes to user-friendly messages
ERROR_MESSAGES: dict[int, str] = {
    # Authentication
    32: "Could not authenticate. Please check your API credentials.",
    89: "Invalid or expired access token. Please re-authenticate.",
    99: "Unable to verify your credentials. Please check your API keys.",
    215: "Bad authentication data. Please verify your OAuth credentials.",
    # Authorization
    64: "Your account is not authorized to access this resource.",
    63: "Your account is suspended and cannot be accessed.",
    87: "API access has been revoked for this application.",
    # Resources
    34: "The requested page or resource does not exist.",
    17: "User not found.",
    144: "Tweet not found.",
    # Rate limiting
    88: "Rate limit exceeded. Please wait before making more requests.",
    429: "Too many requests. You have hit a rate limit.",
    # Validation
    186: "Tweet is too long. Maximum length is 280 characters.",
    187: "Duplicate tweet. You've already posted this content.",
    324: "Invalid media for upload.",
    325: "Media ID not found.",
    323: "Media type not supported.",
}


# Retryable error codes
RETRYABLE_ERROR_CODES = {
    88,  # Rate limit exceeded
    130,  # Over capacity
    131,  # Internal error
    429,  # Too many requests
    500,  # Internal server error
    502,  # Bad gateway
    503,  # Service unavailable
    504,  # Gateway timeout
}

# Non-retryable error codes
NON_RETRYABLE_ERROR_CODES = {
    32,  # Authentication failed
    89,  # Invalid token
    99,  # Unable to verify credentials
    64,  # Forbidden
    63,  # Account suspended
    186,  # Status too long
    187,  # Duplicate status
    144,  # Tweet not found
}


def map_twitter_error(
    status_code: int | None,
    error_code: int | None = None,
    error_message: str | None = None,
    response_data: dict[str, Any] | None = None,
) -> PlatformError:
    """Map Twitter API error to appropriate exception.

    Args:
        status_code: HTTP status code.
        error_code: Twitter-specific error code.
        error_message: Error message from API.
        response_data: Full response data from API.

    Returns:
        Appropriate PlatformError subclass.

    Example:
        >>> error = map_twitter_error(401, 32, "Could not authenticate")
        >>> print(type(error).__name__)
        PlatformAuthError
    """
    # Extract error details from response if provided
    if response_data and "errors" in response_data:
        errors = response_data["errors"]
        if errors and isinstance(errors, list):
            first_error = errors[0]
            if not error_code:
                error_code = first_error.get("code")
            if not error_message:
                error_message = first_error.get("message")

    # Get user-friendly message
    friendly_message = ERROR_MESSAGES.get(
        error_code or 0, error_message or "Unknown error"
    )

    # Determine retry-after for rate limits
    retry_after = None
    if status_code == 429:
        # Twitter typically uses 15-minute windows
        retry_after = 900  # 15 minutes in seconds

    # Map to appropriate exception type
    # Authentication errors
    if error_code in (32, 89, 99, 215) or status_code in (401, 403):
        return PlatformAuthError(
            friendly_message,
            platform="twitter",
            status_code=status_code,
        )

    # Rate limit errors
    if error_code in (88, 429) or status_code == 429:
        return RateLimitError(
            friendly_message,
            platform="twitter",
            status_code=status_code or 429,
            retry_after=retry_after,
        )

    # Validation errors
    if error_code in (186, 187, 324, 325, 323):
        return ValidationError(
            friendly_message,
            platform="twitter",
        )

    # Media upload errors
    if error_code in (323, 324, 325):
        return MediaUploadError(
            friendly_message,
            platform="twitter",
            status_code=status_code,
        )

    # Generic platform error
    return PlatformError(
        friendly_message,
        platform="twitter",
        status_code=status_code,
    )


def is_retryable_twitter_error(
    status_code: int | None,
    error_code: int | None = None,
) -> bool:
    """Determine if a Twitter error is retryable.

    Args:
        status_code: HTTP status code.
        error_code: Twitter-specific error code.

    Returns:
        True if error is retryable, False otherwise.

    Example:
        >>> is_retryable_twitter_error(503)
        True
        >>> is_retryable_twitter_error(401, 32)
        False
    """
    # Check explicit non-retryable codes first
    if error_code in NON_RETRYABLE_ERROR_CODES:
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
    """Get recommended retry delay for Twitter error.

    Args:
        status_code: HTTP status code.
        error_code: Twitter-specific error code.
        attempt: Current retry attempt number.

    Returns:
        Recommended delay in seconds.

    Example:
        >>> get_retry_delay(503, attempt=1)
        5.0
        >>> get_retry_delay(429)
        900.0
    """
    # Rate limit errors - wait full window
    if error_code in (88, 429) or status_code == 429:
        return 900.0  # 15 minutes

    # Server errors - exponential backoff
    if status_code and 500 <= status_code < 600:
        base_delay = 5.0
        return min(base_delay * (2 ** (attempt - 1)), 60.0)

    # Default delay
    return 5.0


class TwitterAPIError(PlatformError):
    """Twitter API specific error with detailed information.

    Attributes:
        error_code: Twitter-specific error code.
        is_retryable: Whether the error is retryable.
        retry_delay: Recommended retry delay in seconds.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize Twitter API error.

        Args:
            message: Error message.
            status_code: HTTP status code.
            error_code: Twitter-specific error code.
            response_data: Full response data from API.
        """
        super().__init__(message, platform="twitter", status_code=status_code)
        self.error_code = error_code
        self.response_data = response_data
        self.is_retryable = is_retryable_twitter_error(status_code, error_code)
        self.retry_delay = get_retry_delay(status_code, error_code)

    def __repr__(self) -> str:
        """String representation of error."""
        return (
            f"TwitterAPIError(message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"error_code={self.error_code}, "
            f"retryable={self.is_retryable})"
        )
