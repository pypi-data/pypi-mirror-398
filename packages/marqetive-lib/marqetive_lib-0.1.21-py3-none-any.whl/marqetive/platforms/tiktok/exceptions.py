"""TikTok-specific exception handling and error code mapping.

This module provides error handling for the TikTok API, including HTTP status
code mapping, TikTok-specific error codes, and user-friendly messages.

TikTok API uses string error codes in the response format:
{"error": {"code": "error_code_string", "message": "...", "log_id": "..."}}
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


class TikTokErrorCode:
    """TikTok API error codes (string-based).

    Reference: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
    """

    # Success
    OK = "ok"

    # Authentication & Authorization
    ACCESS_TOKEN_INVALID = "access_token_invalid"
    ACCESS_TOKEN_EXPIRED = "access_token_expired"
    SCOPE_NOT_AUTHORIZED = "scope_not_authorized"
    TOKEN_NOT_AUTHORIZED_FOR_OPEN_ID = "token_not_authorized_for_this_open_id"

    # Rate Limiting & Spam
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SPAM_RISK_TOO_MANY_POSTS = "spam_risk_too_many_posts"
    SPAM_RISK_USER_BANNED = "spam_risk_user_banned_from_posting"

    # Resource Not Found
    VIDEO_NOT_FOUND = "video_not_found"
    USER_NOT_FOUND = "user_not_found"
    PUBLISH_ID_NOT_FOUND = "publish_id_not_found"

    # Validation & Privacy Errors
    INVALID_PARAMS = "invalid_params"
    INVALID_FILE_FORMAT = "invalid_file_format"
    VIDEO_DURATION_TOO_LONG = "video_duration_too_long"
    VIDEO_DURATION_TOO_SHORT = "video_duration_too_short"
    PICTURE_NUMBER_EXCEEDS_LIMIT = "picture_number_exceeds_limit"
    PRIVACY_LEVEL_OPTION_MISMATCH = "privacy_level_option_mismatch"
    TITLE_LENGTH_EXCEEDS_LIMIT = "title_length_exceeds_limit"

    # Upload & Processing
    FILE_FORMAT_CHECK_FAILED = "file_format_check_failed"
    UPLOAD_FAILED = "upload_failed"
    PROCESSING_FAILED = "processing_failed"

    # Unaudited Client Restrictions
    UNAUDITED_CLIENT_PRIVATE_ONLY = "unaudited_client_can_only_post_to_private_accounts"

    # Publish Status Values (not errors, but statuses)
    STATUS_PROCESSING_UPLOAD = "PROCESSING_UPLOAD"
    STATUS_PROCESSING_DOWNLOAD = "PROCESSING_DOWNLOAD"
    STATUS_PUBLISH_COMPLETE = "PUBLISH_COMPLETE"
    STATUS_FAILED = "FAILED"


# Mapping of error codes to user-friendly messages
ERROR_MESSAGES: dict[str, str] = {
    # Success
    TikTokErrorCode.OK: "Request completed successfully.",
    # Authentication
    TikTokErrorCode.ACCESS_TOKEN_INVALID: "Invalid access token. Please re-authenticate.",
    TikTokErrorCode.ACCESS_TOKEN_EXPIRED: "Access token has expired. Please refresh the token.",
    TikTokErrorCode.SCOPE_NOT_AUTHORIZED: "The application is not authorized for the requested scope.",
    TikTokErrorCode.TOKEN_NOT_AUTHORIZED_FOR_OPEN_ID: "Token is not authorized for this user.",
    # Rate Limiting
    TikTokErrorCode.RATE_LIMIT_EXCEEDED: "Rate limit exceeded. Please wait before making more requests.",
    TikTokErrorCode.SPAM_RISK_TOO_MANY_POSTS: "Daily posting limit reached (~15 posts/day).",
    TikTokErrorCode.SPAM_RISK_USER_BANNED: "User has been temporarily banned from posting.",
    # Resource Not Found
    TikTokErrorCode.VIDEO_NOT_FOUND: "The requested video could not be found.",
    TikTokErrorCode.USER_NOT_FOUND: "The specified user does not exist.",
    TikTokErrorCode.PUBLISH_ID_NOT_FOUND: "The publish ID was not found.",
    # Validation
    TikTokErrorCode.INVALID_PARAMS: "Invalid parameter in request.",
    TikTokErrorCode.INVALID_FILE_FORMAT: "Invalid file format. Use MP4 or MOV.",
    TikTokErrorCode.VIDEO_DURATION_TOO_LONG: "Video duration exceeds the maximum allowed.",
    TikTokErrorCode.VIDEO_DURATION_TOO_SHORT: "Video duration is below the minimum (3 seconds).",
    TikTokErrorCode.PICTURE_NUMBER_EXCEEDS_LIMIT: "Too many images in photo post.",
    TikTokErrorCode.PRIVACY_LEVEL_OPTION_MISMATCH: "Privacy level not available for this creator.",
    TikTokErrorCode.TITLE_LENGTH_EXCEEDS_LIMIT: "Video title/description is too long.",
    # Upload
    TikTokErrorCode.FILE_FORMAT_CHECK_FAILED: "File format validation failed.",
    TikTokErrorCode.UPLOAD_FAILED: "Media upload failed.",
    TikTokErrorCode.PROCESSING_FAILED: "Media processing failed after upload.",
    # Unaudited
    TikTokErrorCode.UNAUDITED_CLIENT_PRIVATE_ONLY: "Unaudited apps can only post to private accounts.",
}


def map_tiktok_error(
    status_code: int | None,
    error_code: str | None = None,
    error_message: str | None = None,
    response_data: dict[str, Any] | None = None,
) -> PlatformError:
    """Map TikTok API error to the appropriate exception class.

    TikTok API returns errors in the format:
    {"error": {"code": "error_code_string", "message": "...", "log_id": "..."}}

    Args:
        status_code: HTTP status code.
        error_code: TikTok-specific error code string from the response body.
        error_message: Error message from the API.
        response_data: Full response data from the API.

    Returns:
        An appropriate subclass of PlatformError.
    """
    if response_data and "error" in response_data:
        error_data = response_data["error"]
        if not error_code:
            error_code = error_data.get("code")
        if not error_message:
            error_message = error_data.get("message")

    friendly_message = ERROR_MESSAGES.get(
        error_code or "", error_message or "An unknown TikTok API error occurred"
    )

    # Authentication errors
    auth_error_codes = {
        TikTokErrorCode.ACCESS_TOKEN_INVALID,
        TikTokErrorCode.ACCESS_TOKEN_EXPIRED,
        TikTokErrorCode.SCOPE_NOT_AUTHORIZED,
        TikTokErrorCode.TOKEN_NOT_AUTHORIZED_FOR_OPEN_ID,
    }
    if error_code in auth_error_codes or status_code in (401, 403):
        return PlatformAuthError(
            friendly_message,
            platform="tiktok",
            status_code=status_code,
        )

    # Rate limiting errors
    rate_limit_codes = {
        TikTokErrorCode.RATE_LIMIT_EXCEEDED,
        TikTokErrorCode.SPAM_RISK_TOO_MANY_POSTS,
        TikTokErrorCode.SPAM_RISK_USER_BANNED,
    }
    if error_code in rate_limit_codes or status_code == 429:
        return RateLimitError(
            friendly_message,
            platform="tiktok",
            status_code=status_code or 429,
            retry_after=None,
        )

    # Not found errors
    not_found_codes = {
        TikTokErrorCode.VIDEO_NOT_FOUND,
        TikTokErrorCode.USER_NOT_FOUND,
        TikTokErrorCode.PUBLISH_ID_NOT_FOUND,
    }
    if error_code in not_found_codes or status_code == 404:
        return PostNotFoundError(
            post_id="",
            platform="tiktok",
            status_code=status_code,
            message=friendly_message,
        )

    # Validation errors
    validation_codes = {
        TikTokErrorCode.INVALID_PARAMS,
        TikTokErrorCode.INVALID_FILE_FORMAT,
        TikTokErrorCode.VIDEO_DURATION_TOO_LONG,
        TikTokErrorCode.VIDEO_DURATION_TOO_SHORT,
        TikTokErrorCode.PICTURE_NUMBER_EXCEEDS_LIMIT,
        TikTokErrorCode.PRIVACY_LEVEL_OPTION_MISMATCH,
        TikTokErrorCode.TITLE_LENGTH_EXCEEDS_LIMIT,
        TikTokErrorCode.UNAUDITED_CLIENT_PRIVATE_ONLY,
    }
    if error_code in validation_codes:
        return ValidationError(
            friendly_message,
            platform="tiktok",
        )

    # Media upload errors
    media_error_codes = {
        TikTokErrorCode.FILE_FORMAT_CHECK_FAILED,
        TikTokErrorCode.UPLOAD_FAILED,
        TikTokErrorCode.PROCESSING_FAILED,
    }
    if error_code in media_error_codes:
        return MediaUploadError(
            friendly_message,
            platform="tiktok",
            status_code=status_code,
        )

    # Generic platform error for everything else
    return PlatformError(
        friendly_message,
        platform="tiktok",
        status_code=status_code,
    )


class TikTokAPIError(PlatformError):
    """TikTok API specific error with detailed information."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
        log_id: str | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, platform="tiktok", status_code=status_code)
        self.error_code = error_code
        self.log_id = log_id
        self.response_data = response_data

    def __repr__(self) -> str:
        return (
            f"TikTokAPIError(message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"error_code={self.error_code!r}, "
            f"log_id={self.log_id!r})"
        )


def is_retryable_error(error_code: str | None, status_code: int | None = None) -> bool:
    """Check if an error is retryable.

    Args:
        error_code: TikTok error code string.
        status_code: HTTP status code.

    Returns:
        True if the error should be retried, False otherwise.
    """
    # Server errors are retryable
    if status_code and 500 <= status_code < 600:
        return True

    # Rate limits should wait and retry
    if error_code == TikTokErrorCode.RATE_LIMIT_EXCEEDED:
        return True

    # Upload failures may be transient
    return error_code == TikTokErrorCode.UPLOAD_FAILED


def get_retry_delay(error_code: str | None, attempt: int = 1) -> float:
    """Get recommended retry delay for an error.

    Args:
        error_code: TikTok error code string.
        attempt: Current attempt number (1-based).

    Returns:
        Recommended delay in seconds before retry.
    """
    # Rate limits - wait longer
    if error_code == TikTokErrorCode.RATE_LIMIT_EXCEEDED:
        return 60.0  # 1 minute

    # Daily post limit - wait much longer
    if error_code == TikTokErrorCode.SPAM_RISK_TOO_MANY_POSTS:
        return 3600.0  # 1 hour (user should wait until next day)

    # Default exponential backoff: 5s, 10s, 20s, max 60s
    delay = min(5 * (2 ** (attempt - 1)), 60)
    return float(delay)
