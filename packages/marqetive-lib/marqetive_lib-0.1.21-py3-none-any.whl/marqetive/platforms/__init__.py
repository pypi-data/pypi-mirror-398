"""Social media platform integrations.

This package provides a unified interface for interacting with various social
media platforms including Instagram, Twitter/X, and LinkedIn.

Platform clients are available via their respective subpackages:
    - from marqetive.platforms.twitter import TwitterClient
    - from marqetive.platforms.linkedin import LinkedInClient
    - from marqetive.platforms.instagram import InstagramClient
"""

from marqetive.core.base import SocialMediaPlatform
from marqetive.core.exceptions import (
    MediaUploadError,
    PlatformAuthError,
    PlatformError,
    PostNotFoundError,
    RateLimitError,
    ValidationError,
)
from marqetive.core.models import (
    AuthCredentials,
    Comment,
    CommentStatus,
    MediaAttachment,
    MediaType,
    PlatformResponse,
    Post,
    PostCreateRequest,
    PostStatus,
    PostUpdateRequest,
)

__all__ = [
    # Base class
    "SocialMediaPlatform",
    # Models
    "AuthCredentials",
    "Comment",
    "CommentStatus",
    "MediaAttachment",
    "MediaType",
    "PlatformResponse",
    "Post",
    "PostCreateRequest",
    "PostStatus",
    "PostUpdateRequest",
    # Exceptions
    "MediaUploadError",
    "PlatformAuthError",
    "PlatformError",
    "PostNotFoundError",
    "RateLimitError",
    "ValidationError",
]
