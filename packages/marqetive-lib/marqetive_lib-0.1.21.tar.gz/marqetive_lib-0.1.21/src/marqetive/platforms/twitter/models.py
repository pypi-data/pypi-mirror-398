"""Twitter/X-specific models for post creation.

This module defines Twitter-specific data models for creating tweets,
replies, quote tweets, and polls.
"""

from pydantic import BaseModel, Field


class TwitterPostRequest(BaseModel):
    """Twitter/X-specific post creation request.

    Supports tweets, replies, quote tweets, and media attachments.
    Twitter has a 280 character limit for text content.

    Attributes:
        content: Tweet text (max 280 characters)
        media_urls: List of media URLs to attach (max 4 images or 1 video)
        media_ids: List of pre-uploaded media IDs
        reply_to_post_id: Tweet ID to reply to
        quote_post_id: Tweet ID to quote
        poll_options: List of poll options (2-4 options, each max 25 chars)
        poll_duration_minutes: Poll duration in minutes (5-10080)
        alt_texts: Alt text for each media item (for accessibility)

    Example:
        >>> # Simple tweet
        >>> request = TwitterPostRequest(content="Hello Twitter!")

        >>> # Reply to a tweet
        >>> request = TwitterPostRequest(
        ...     content="Great point!",
        ...     reply_to_post_id="1234567890"
        ... )

        >>> # Quote tweet with media
        >>> request = TwitterPostRequest(
        ...     content="Check this out!",
        ...     quote_post_id="1234567890",
        ...     media_urls=["https://example.com/image.jpg"]
        ... )

        >>> # Tweet with poll
        >>> request = TwitterPostRequest(
        ...     content="What's your favorite?",
        ...     poll_options=["Option A", "Option B", "Option C"],
        ...     poll_duration_minutes=1440
        ... )
    """

    content: str | None = None
    media_urls: list[str] = Field(default_factory=list, max_length=4)
    media_ids: list[str] = Field(default_factory=list, max_length=4)
    reply_to_post_id: str | None = None
    quote_post_id: str | None = None
    poll_options: list[str] = Field(default_factory=list, max_length=4)
    poll_duration_minutes: int | None = Field(default=None, ge=5, le=10080)
    alt_texts: list[str] = Field(default_factory=list)
