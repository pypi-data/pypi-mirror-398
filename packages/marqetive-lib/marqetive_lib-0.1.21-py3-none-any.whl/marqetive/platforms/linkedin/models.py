"""LinkedIn-specific models for the Community Management API.

This module defines LinkedIn-specific data models that extend the core models
for features unique to LinkedIn's Community Management API, including
reactions, social metadata, and organization management.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ReactionType(StrEnum):
    """LinkedIn reaction types.

    These correspond to the UI labels users see when reacting to content.

    Attributes:
        LIKE: Standard like reaction
        PRAISE: "Celebrate" reaction
        EMPATHY: "Love" reaction
        INTEREST: "Insightful" reaction
        APPRECIATION: "Support" reaction
        ENTERTAINMENT: "Funny" reaction
    """

    LIKE = "LIKE"
    PRAISE = "PRAISE"  # Celebrate
    EMPATHY = "EMPATHY"  # Love
    INTEREST = "INTEREST"  # Insightful
    APPRECIATION = "APPRECIATION"  # Support
    ENTERTAINMENT = "ENTERTAINMENT"  # Funny


class CallToActionLabel(StrEnum):
    """LinkedIn call-to-action button labels for posts.

    These can be used with articles and sponsored content to add
    clickable action buttons.
    """

    APPLY = "APPLY"
    DOWNLOAD = "DOWNLOAD"
    VIEW_QUOTE = "VIEW_QUOTE"
    LEARN_MORE = "LEARN_MORE"
    SIGN_UP = "SIGN_UP"
    SUBSCRIBE = "SUBSCRIBE"
    REGISTER = "REGISTER"
    JOIN = "JOIN"
    ATTEND = "ATTEND"
    REQUEST_DEMO = "REQUEST_DEMO"
    SEE_MORE = "SEE_MORE"
    BUY_NOW = "BUY_NOW"
    SHOP_NOW = "SHOP_NOW"


class FeedDistribution(StrEnum):
    """LinkedIn feed distribution options for posts.

    Controls how and where posts are distributed in feeds.
    """

    MAIN_FEED = "MAIN_FEED"
    NONE = "NONE"


class PostVisibility(StrEnum):
    """LinkedIn post visibility options.

    Controls who can see the post.
    """

    PUBLIC = "PUBLIC"
    CONNECTIONS = "CONNECTIONS"
    LOGGED_IN = "LOGGED_IN"
    CONTAINER = "CONTAINER"


class CommentsState(StrEnum):
    """State of comments on a LinkedIn post.

    OPEN: Comments are enabled
    CLOSED: Comments are disabled (deletes existing comments)
    """

    OPEN = "OPEN"
    CLOSED = "CLOSED"


class OrganizationType(StrEnum):
    """LinkedIn organization types."""

    COMPANY = "COMPANY"
    SCHOOL = "SCHOOL"
    GROUP = "GROUP"
    SHOWCASE = "SHOWCASE"


class Reaction(BaseModel):
    """Represents a reaction on a LinkedIn post or comment.

    Attributes:
        actor: URN of the person or organization that reacted
        entity: URN of the entity (post/comment) that was reacted to
        reaction_type: Type of reaction (LIKE, PRAISE, etc.)
        created_at: Timestamp when the reaction was created

    Example:
        >>> reaction = Reaction(
        ...     actor="urn:li:person:abc123",
        ...     entity="urn:li:share:12345",
        ...     reaction_type=ReactionType.LIKE
        ... )
    """

    actor: str
    entity: str
    reaction_type: ReactionType
    created_at: datetime | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)


class ReactionSummary(BaseModel):
    """Summary of reactions by type.

    Attributes:
        reaction_type: Type of reaction
        count: Number of reactions of this type
    """

    reaction_type: ReactionType
    count: int


class CommentSummary(BaseModel):
    """Summary of comments on a post.

    Attributes:
        count: Total number of comments (including replies)
        top_level_count: Number of top-level comments (excluding replies)
    """

    count: int
    top_level_count: int


class SocialMetadata(BaseModel):
    """Social metadata for a LinkedIn post or comment.

    Contains engagement metrics like reactions and comment counts.

    Attributes:
        entity: URN of the entity (post/comment)
        reaction_summaries: Dictionary mapping reaction types to counts
        comment_count: Total number of comments
        top_level_comment_count: Number of top-level comments
        comments_state: Whether comments are enabled (OPEN) or disabled (CLOSED)

    Example:
        >>> metadata = SocialMetadata(
        ...     entity="urn:li:share:12345",
        ...     reaction_summaries={ReactionType.LIKE: 10, ReactionType.PRAISE: 5},
        ...     comment_count=3,
        ...     top_level_comment_count=2,
        ...     comments_state=CommentsState.OPEN
        ... )
    """

    entity: str
    reaction_summaries: dict[ReactionType, int] = Field(default_factory=dict)
    comment_count: int = 0
    top_level_comment_count: int = 0
    comments_state: CommentsState = CommentsState.OPEN
    raw_data: dict[str, Any] = Field(default_factory=dict)


class Organization(BaseModel):
    """Represents a LinkedIn organization (Company Page).

    Attributes:
        id: Organization URN (e.g., urn:li:organization:12345)
        name: Organization name
        localized_name: Localized organization name
        vanity_name: URL-friendly name (e.g., "linkedin" for linkedin.com/company/linkedin)
        logo_url: URL of the organization's logo
        follower_count: Number of followers
        primary_type: Type of organization (COMPANY, SCHOOL, etc.)
        website_url: Organization's website
        description: Organization description
        industry: Industry category

    Example:
        >>> org = Organization(
        ...     id="urn:li:organization:12345",
        ...     name="Example Corp",
        ...     localized_name="Example Corp",
        ...     vanity_name="examplecorp"
        ... )
    """

    id: str
    name: str
    localized_name: str
    vanity_name: str | None = None
    logo_url: str | None = None
    follower_count: int | None = None
    primary_type: OrganizationType | None = None
    website_url: str | None = None
    description: str | None = None
    industry: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)


class LinkedInPostContent(BaseModel):
    """Content attachment for a LinkedIn post.

    Can contain media (image/video/document) or an article link.

    Attributes:
        media: Media content details
        article: Article link details
    """

    media: "MediaContent | None" = None
    article: "ArticleContent | None" = None


class MediaContent(BaseModel):
    """Media content for a LinkedIn post.

    Attributes:
        id: Media URN (e.g., urn:li:image:xxx, urn:li:video:xxx)
        title: Optional title for the media
        alt_text: Alternative text for accessibility
    """

    id: str
    title: str | None = None
    alt_text: str | None = None


class ArticleContent(BaseModel):
    """Article content for a LinkedIn post.

    Attributes:
        source: URL of the article
        title: Article title
        description: Article description
        thumbnail: URN of the thumbnail image
    """

    source: str
    title: str | None = None
    description: str | None = None
    thumbnail: str | None = None


class LinkedInPostDistribution(BaseModel):
    """Distribution settings for a LinkedIn post.

    Attributes:
        feed_distribution: Where to distribute the post
        target_entities: Audience targeting criteria
        third_party_distribution_channels: External distribution channels
    """

    feed_distribution: FeedDistribution = FeedDistribution.MAIN_FEED
    target_entities: list[dict[str, Any]] = Field(default_factory=list)
    third_party_distribution_channels: list[str] = Field(default_factory=list)


class CommentMention(BaseModel):
    """Mention in a comment.

    Attributes:
        start: Start position in the text
        length: Length of the mention text
        person_urn: URN of the mentioned person (if person mention)
        organization_urn: URN of the mentioned organization (if org mention)
    """

    start: int
    length: int
    person_urn: str | None = None
    organization_urn: str | None = None


class LinkedInCommentRequest(BaseModel):
    """Request model for creating or updating a LinkedIn comment.

    Attributes:
        content: Text content of the comment
        parent_comment_id: URN of parent comment (for nested replies)
        mentions: List of mentions to include
        image_id: URN of image to attach to comment

    Example:
        >>> request = LinkedInCommentRequest(
        ...     content="Great post! @[John Doe](urn:li:person:abc123)",
        ...     mentions=[CommentMention(start=12, length=8, person_urn="urn:li:person:abc123")]
        ... )
    """

    content: str
    parent_comment_id: str | None = None
    mentions: list[CommentMention] = Field(default_factory=list)
    image_id: str | None = None


# Type alias for sort options
type PostSortBy = Literal["LAST_MODIFIED", "CREATED"]
type ReactionSortBy = Literal["CHRONOLOGICAL", "REVERSE_CHRONOLOGICAL", "RELEVANCE"]


class LinkedInPostRequest(BaseModel):
    """LinkedIn-specific post creation request.

    Supports text posts, articles, media (images/videos/documents), and
    rich formatting options like CTAs and visibility controls.
    LinkedIn has a 3000 character limit for post content.

    Attributes:
        content: Post text/commentary (max 3000 characters)
        media_urls: List of media URLs to upload
        media_ids: List of pre-uploaded media URNs
        link: Article/link URL to share
        visibility: Post visibility (PUBLIC, CONNECTIONS, LOGGED_IN)
        feed_distribution: Feed distribution (MAIN_FEED, NONE)
        target_entities: Audience targeting criteria
        call_to_action: CTA button label
        landing_page: URL for CTA button
        article_title: Title for link preview
        article_description: Description for link preview
        article_thumbnail: Thumbnail URN for article
        media_title: Title for media attachment
        media_alt_text: Alt text for media (accessibility)
        disable_reshare: Prevent resharing
        disable_comments: Disable comments

    Example:
        >>> # Simple post
        >>> request = LinkedInPostRequest(
        ...     content="Excited to share our latest update!"
        ... )

        >>> # Article post with CTA
        >>> request = LinkedInPostRequest(
        ...     content="Check out our new blog post!",
        ...     link="https://example.com/blog",
        ...     article_title="Our Latest Update",
        ...     article_description="Learn about new features",
        ...     call_to_action=CallToActionLabel.LEARN_MORE,
        ...     landing_page="https://example.com/learn-more"
        ... )

        >>> # Post with media and visibility control
        >>> request = LinkedInPostRequest(
        ...     content="New product launch!",
        ...     media_urls=["https://example.com/product.jpg"],
        ...     visibility=PostVisibility.PUBLIC,
        ...     media_alt_text="Product image"
        ... )
    """

    content: str
    media_urls: list[str] = Field(default_factory=list)
    media_ids: list[str] = Field(default_factory=list)
    link: str | None = None
    visibility: PostVisibility = PostVisibility.PUBLIC
    feed_distribution: FeedDistribution = FeedDistribution.MAIN_FEED
    target_entities: list[dict[str, Any]] = Field(default_factory=list)
    call_to_action: CallToActionLabel | None = None
    landing_page: str | None = None
    article_title: str | None = None
    article_description: str | None = None
    article_thumbnail: str | None = None
    media_title: str | None = None
    media_alt_text: str | None = None
    disable_reshare: bool = False
    disable_comments: bool = False


class LinkedInPostUpdateRequest(BaseModel):
    """LinkedIn-specific post update request.

    LinkedIn supports updating certain fields of published posts:
    - commentary (post text)
    - call-to-action label and landing page
    - lifecycle state
    - ad context (for sponsored content)

    Attributes:
        content: Updated post text/commentary
        call_to_action: Updated CTA button label
        landing_page: Updated URL for CTA button
        lifecycle_state: Updated lifecycle state (e.g., PUBLISHED, DRAFT)
        ad_context: Ad context updates for sponsored content

    Example:
        >>> request = LinkedInPostUpdateRequest(
        ...     content="Updated post content!",
        ...     call_to_action=CallToActionLabel.SIGN_UP,
        ...     landing_page="https://example.com/signup"
        ... )
    """

    content: str | None = None
    call_to_action: CallToActionLabel | None = None
    landing_page: str | None = None
    lifecycle_state: str | None = None
    ad_context: dict[str, Any] | None = None
