"""LinkedIn-specific exception handling and error code mapping.

This module provides comprehensive error handling for LinkedIn API errors including:
- HTTP status code mapping
- LinkedIn-specific service error codes
- Retry strategies
- User-friendly error messages
"""

from typing import Any

from marqetive.core.exceptions import (
    MediaUploadError,
    PlatformAuthError,
    PlatformError,
    PostNotFoundError,
    RateLimitError,
    ValidationError,
)


# LinkedIn API error codes
# Source: https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/error-handling
class LinkedInErrorCode:
    """LinkedIn API error codes."""

    # Authentication errors (401)
    INVALID_TOKEN = 401
    EXPIRED_TOKEN = 401
    REVOKED_ACCESS = 401

    # Authorization errors (403)
    ACCESS_DENIED = 403
    INSUFFICIENT_PERMISSIONS = 403

    # Resource errors (404)
    RESOURCE_NOT_FOUND = 404
    ENTITY_NOT_FOUND = 404

    # Validation errors (400)
    BAD_REQUEST = 400
    MALFORMED_REQUEST = 400
    INVALID_PARAMETERS = 400

    # Rate limiting (429)
    RATE_LIMIT_EXCEEDED = 429
    THROTTLE_LIMIT_REACHED = 429

    # Server errors (500+)
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504

    # Protocol errors
    METHOD_NOT_ALLOWED = 405
    LENGTH_REQUIRED = 411
    VERSION_DEPRECATED = 426


# Mapping of status codes to user-friendly messages
ERROR_MESSAGES: dict[int, str] = {
    # Authentication
    401: "Invalid or expired access token. Please re-authenticate.",
    # Authorization
    403: "Access denied. Insufficient permissions to access this resource.",
    # Resources
    404: "The requested resource or entity does not exist.",
    405: "HTTP method not allowed for this endpoint.",
    # Validation
    400: "Bad request. Please check your request parameters.",
    411: "Content-Length header is required for this request.",
    426: "API version header is deprecated. Please update to latest version.",
    # Rate limiting
    429: "Rate limit exceeded. Please reduce request frequency.",
    # Server errors
    500: "LinkedIn server error. Please try again later.",
    503: "LinkedIn service temporarily unavailable. Please try again later.",
    504: "Gateway timeout. LinkedIn servers took too long to respond.",
}


# Retryable HTTP status codes
RETRYABLE_STATUS_CODES = {
    408,  # Request timeout
    429,  # Too many requests
    500,  # Internal server error
    502,  # Bad gateway
    503,  # Service unavailable
    504,  # Gateway timeout
}

# Non-retryable HTTP status codes
NON_RETRYABLE_STATUS_CODES = {
    400,  # Bad request
    401,  # Unauthorized
    403,  # Forbidden
    404,  # Not found
    405,  # Method not allowed
    411,  # Length required
    426,  # Version deprecated
}


def map_linkedin_error(
    status_code: int | None,
    service_error_code: int | None = None,
    error_message: str | None = None,
    response_data: dict[str, Any] | None = None,
) -> PlatformError:
    """Map LinkedIn API error to appropriate exception.

    Args:
        status_code: HTTP status code.
        service_error_code: LinkedIn-specific service error code.
        error_message: Error message from API.
        response_data: Full response data from API.

    Returns:
        Appropriate PlatformError subclass.

    Example:
        >>> error = map_linkedin_error(401, error_message="Invalid token")
        >>> print(type(error).__name__)
        PlatformAuthError
    """
    # Extract error details from response if provided
    if response_data:
        if not service_error_code:
            service_error_code = response_data.get("serviceErrorCode")
        if not error_message:
            error_message = response_data.get("message")
        if not status_code:
            status_code = response_data.get("status")

    # Get user-friendly message
    friendly_message = ERROR_MESSAGES.get(
        status_code or 0, error_message or "Unknown error"
    )

    # Determine retry-after for rate limits
    retry_after = None
    if status_code == 429:
        # LinkedIn typically uses 1-hour windows
        retry_after = 3600  # 1 hour in seconds

    # Map to appropriate exception type
    # Authentication errors
    if status_code == 401:
        return PlatformAuthError(
            friendly_message,
            platform="linkedin",
            status_code=status_code,
        )

    # Authorization errors
    if status_code == 403:
        return PlatformAuthError(
            friendly_message,
            platform="linkedin",
            status_code=status_code,
        )

    # Rate limit errors
    if status_code == 429:
        return RateLimitError(
            friendly_message,
            platform="linkedin",
            status_code=status_code,
            retry_after=retry_after,
        )

    # Resource not found
    if status_code == 404:
        # Try to extract post/resource ID if available
        resource_id = None
        if response_data and isinstance(response_data, dict):
            # Common patterns for resource IDs in LinkedIn responses
            resource_id = response_data.get("id") or response_data.get("entityUrn")

        if resource_id:
            return PostNotFoundError(
                post_id=str(resource_id),
                platform="linkedin",
                status_code=status_code,
            )
        return PlatformError(
            friendly_message,
            platform="linkedin",
            status_code=status_code,
        )

    # Validation errors
    if status_code in (400, 411, 426):
        return ValidationError(
            friendly_message,
            platform="linkedin",
        )

    # Media upload errors (detected by context or specific codes)
    # LinkedIn doesn't have specific codes, but we can detect from message
    if error_message and any(
        keyword in error_message.lower()
        for keyword in ["upload", "media", "asset", "file", "video", "image"]
    ):
        return MediaUploadError(
            friendly_message,
            platform="linkedin",
            status_code=status_code,
        )

    # Generic platform error
    return PlatformError(
        friendly_message,
        platform="linkedin",
        status_code=status_code,
    )


def is_retryable_linkedin_error(
    status_code: int | None,
    service_error_code: int | None = None,  # noqa: ARG001
) -> bool:
    """Determine if a LinkedIn error is retryable.

    Args:
        status_code: HTTP status code.
        service_error_code: LinkedIn-specific service error code.

    Returns:
        True if error is retryable, False otherwise.

    Example:
        >>> is_retryable_linkedin_error(503)
        True
        >>> is_retryable_linkedin_error(401)
        False
    """
    # Check explicit non-retryable codes first
    if status_code in NON_RETRYABLE_STATUS_CODES:
        return False

    # Check retryable codes
    if status_code in RETRYABLE_STATUS_CODES:
        return True

    # Check HTTP status codes
    if status_code:
        # 5xx errors are generally retryable
        if 500 <= status_code < 600:
            return True
        # 4xx errors (except 429, 408) are generally not retryable
        if 400 <= status_code < 500:
            return False

    # Default to not retryable for safety
    return False


def get_retry_delay(
    status_code: int | None,
    service_error_code: int | None = None,  # noqa: ARG001
    attempt: int = 1,
) -> float:
    """Get recommended retry delay for LinkedIn error.

    Args:
        status_code: HTTP status code.
        service_error_code: LinkedIn-specific service error code.
        attempt: Current retry attempt number.

    Returns:
        Recommended delay in seconds.

    Example:
        >>> get_retry_delay(503, attempt=1)
        5.0
        >>> get_retry_delay(429)
        3600.0
    """
    # Rate limit errors - wait full window
    if status_code == 429:
        return 3600.0  # 1 hour

    # Server errors - exponential backoff
    if status_code and 500 <= status_code < 600:
        base_delay = 5.0
        return min(base_delay * (2 ** (attempt - 1)), 120.0)

    # Gateway timeout - longer delay
    if status_code == 504:
        return 30.0

    # Default delay
    return 10.0


class LinkedInAPIError(PlatformError):
    """LinkedIn API specific error with detailed information.

    Attributes:
        service_error_code: LinkedIn-specific service error code.
        is_retryable: Whether the error is retryable.
        retry_delay: Recommended retry delay in seconds.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        service_error_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize LinkedIn API error.

        Args:
            message: Error message.
            status_code: HTTP status code.
            service_error_code: LinkedIn-specific service error code.
            response_data: Full response data from API.
        """
        super().__init__(message, platform="linkedin", status_code=status_code)
        self.service_error_code = service_error_code
        self.response_data = response_data
        self.is_retryable = is_retryable_linkedin_error(status_code, service_error_code)
        self.retry_delay = get_retry_delay(status_code, service_error_code)

    def __repr__(self) -> str:
        """String representation of error."""
        return (
            f"LinkedInAPIError(message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"service_error_code={self.service_error_code}, "
            f"retryable={self.is_retryable})"
        )
