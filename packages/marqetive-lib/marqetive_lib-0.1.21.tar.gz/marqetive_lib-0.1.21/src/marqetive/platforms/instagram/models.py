"""Instagram-specific models for post creation.

This module defines Instagram-specific data models for creating feed posts,
carousels, reels, and stories.
"""

from typing import Any

from pydantic import BaseModel, Field

from marqetive.core.models import MediaType


class InstagramPostRequest(BaseModel):
    """Instagram-specific post creation request.

    Supports feed posts, carousels, reels, and stories.
    Instagram requires media for all posts (no text-only posts).

    Attributes:
        caption: Post caption/text
        media_urls: List of media URLs (required, 1 for single, 2-10 for carousel)
        media_ids: List of pre-uploaded media container IDs
        media_type: Type of post (IMAGE, VIDEO, CAROUSEL, REEL, STORY)
        alt_texts: Alt text for each media item (accessibility)
        location_id: Facebook Place ID for location tag
        cover_url: Cover/thumbnail image URL (for Reels)
        share_to_feed: Share Reel/Story to main feed
        collaborators: List of collaborator Instagram user IDs
        product_tags: Product tags for shopping posts
        audio_name: Audio track name (for Reels)

    Example:
        >>> # Single image post
        >>> request = InstagramPostRequest(
        ...     caption="Beautiful sunset!",
        ...     media_urls=["https://example.com/sunset.jpg"],
        ...     media_type=MediaType.IMAGE,
        ...     alt_texts=["A colorful sunset over the ocean"]
        ... )

        >>> # Carousel post
        >>> request = InstagramPostRequest(
        ...     caption="Our product lineup",
        ...     media_urls=[
        ...         "https://example.com/product1.jpg",
        ...         "https://example.com/product2.jpg",
        ...         "https://example.com/product3.jpg"
        ...     ],
        ...     media_type=MediaType.CAROUSEL,
        ...     alt_texts=["Product 1", "Product 2", "Product 3"]
        ... )

        >>> # Reel
        >>> request = InstagramPostRequest(
        ...     caption="Check out this tutorial!",
        ...     media_urls=["https://example.com/tutorial.mp4"],
        ...     media_type=MediaType.REEL,
        ...     cover_url="https://example.com/thumbnail.jpg",
        ...     share_to_feed=True
        ... )
    """

    caption: str | None = None
    media_urls: list[str] = Field(default_factory=list)
    media_ids: list[str] = Field(default_factory=list)
    media_type: MediaType = MediaType.IMAGE
    alt_texts: list[str] = Field(default_factory=list)
    location_id: str | None = None
    cover_url: str | None = None
    share_to_feed: bool = True
    collaborators: list[str] = Field(default_factory=list)
    product_tags: list[dict[str, Any]] = Field(default_factory=list)
    audio_name: str | None = None
