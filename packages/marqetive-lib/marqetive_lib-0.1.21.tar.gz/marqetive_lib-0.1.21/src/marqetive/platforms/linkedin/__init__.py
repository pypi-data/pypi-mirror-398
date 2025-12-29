"""LinkedIn platform integration using the Community Management API.

This module provides the LinkedIn client and related models for interacting
with LinkedIn's Community Management API, supporting:
- Posts (create, read, update, delete, list)
- Comments (with nested replies)
- Reactions (Like, Celebrate, Love, Insightful, Support, Funny)
- Social metadata and engagement metrics
- Organization (Company Page) management
- Media uploads (images, videos, documents)
"""

from marqetive.platforms.linkedin.client import LinkedInClient
from marqetive.platforms.linkedin.media import (
    LinkedInMediaManager,
    MediaAsset,
    UploadProgress,
    VideoProcessingState,
)
from marqetive.platforms.linkedin.models import (
    CallToActionLabel,
    CommentsState,
    FeedDistribution,
    LinkedInPostRequest,
    LinkedInPostUpdateRequest,
    Organization,
    OrganizationType,
    PostVisibility,
    Reaction,
    ReactionType,
    SocialMetadata,
)

__all__ = [
    # Client
    "LinkedInClient",
    # Media
    "LinkedInMediaManager",
    "MediaAsset",
    "UploadProgress",
    "VideoProcessingState",
    # Models
    "CallToActionLabel",
    "CommentsState",
    "FeedDistribution",
    "LinkedInPostRequest",
    "LinkedInPostUpdateRequest",
    "Organization",
    "OrganizationType",
    "PostVisibility",
    "Reaction",
    "ReactionType",
    "SocialMetadata",
]
