"""LinkedIn API client implementation using the Community Management API.

This module provides a concrete implementation of the SocialMediaPlatform
ABC for LinkedIn, using the LinkedIn Community Management API (REST endpoints).
Supports organization page management, posts, comments, reactions, and social metadata.

API Documentation: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/
"""

import contextlib
import os
from datetime import datetime, timedelta
from typing import Any, cast
from urllib.parse import quote

import httpx
from pydantic import HttpUrl

from marqetive.core.base import ProgressCallback, SocialMediaPlatform
from marqetive.core.exceptions import (
    MediaUploadError,
    PlatformAuthError,
    PlatformError,
    PostNotFoundError,
    ValidationError,
)
from marqetive.core.models import (
    AuthCredentials,
    Comment,
    CommentStatus,
    MediaAttachment,
    MediaType,
    Post,
    PostCreateRequest,
    PostStatus,
    PostUpdateRequest,
)
from marqetive.platforms.linkedin.media import LinkedInMediaManager, MediaAsset
from marqetive.platforms.linkedin.models import (
    CommentsState,
    Organization,
    OrganizationType,
    PostSortBy,
    Reaction,
    ReactionType,
    SocialMetadata,
)

# Valid CTA (Call-To-Action) labels per LinkedIn API documentation
# Note: BUY_NOW and SHOP_NOW require API version 202504 or later
VALID_CTA_LABELS = frozenset({
    "APPLY",
    "DOWNLOAD",
    "VIEW_QUOTE",
    "LEARN_MORE",
    "SIGN_UP",
    "SUBSCRIBE",
    "REGISTER",
    "JOIN",
    "ATTEND",
    "REQUEST_DEMO",
    "SEE_MORE",
    "BUY_NOW",  # Requires API version 202504+
    "SHOP_NOW",  # Requires API version 202504+
})


class LinkedInClient(SocialMediaPlatform):
    """LinkedIn API client using the Community Management API.

    This client implements the SocialMediaPlatform interface for LinkedIn,
    using the LinkedIn Community Management API (REST endpoints). It supports:
    - Creating and managing posts (including updates)
    - Comments with nested replies and mentions
    - Reactions (Like, Celebrate, Love, Insightful, Support, Funny)
    - Social metadata and engagement metrics
    - Organization (Company Page) management
    - Media uploads (images, videos, documents)

    Note:
        - Requires LinkedIn Developer app with appropriate permissions
        - Requires OAuth 2.0 authentication
        - Supports both personal profiles and organization pages
        - Rate limits vary by API endpoint

    Required Permissions:
        - w_organization_social: Post/comment/react on organization pages
        - r_organization_social: Read organization posts/comments
        - rw_organization_admin: Organization management (optional)
        - w_member_social: Post on personal profile

    Example:
        >>> credentials = AuthCredentials(
        ...     platform="linkedin",
        ...     access_token="your_access_token",
        ...     user_id="urn:li:organization:12345"  # or urn:li:person:abc123
        ... )
        >>> async with LinkedInClient(credentials) as client:
        ...     # Create a post
        ...     request = PostCreateRequest(
        ...         content="Excited to share our latest update!",
        ...         link="https://example.com"
        ...     )
        ...     post = await client.create_post(request)
        ...
        ...     # Add a reaction
        ...     await client.add_reaction(post.post_id, ReactionType.LIKE)
        ...
        ...     # Get engagement metrics
        ...     metadata = await client.get_social_metadata(post.post_id)
    """

    # Default API version in YYYYMM format
    DEFAULT_API_VERSION = "202511"

    def __init__(
        self,
        credentials: AuthCredentials,
        timeout: float = 30.0,
        api_version: str | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Initialize LinkedIn client.

        Args:
            credentials: LinkedIn authentication credentials. Must include
                user_id as URN (urn:li:person:xxx or urn:li:organization:xxx).
            timeout: Request timeout in seconds.
            api_version: LinkedIn API version in YYYYMM format (e.g., "202511").
                Defaults to the latest supported version.
            progress_callback: Optional callback for progress updates during
                long-running operations like media uploads.

        Raises:
            PlatformAuthError: If credentials are invalid.
        """
        # Use REST API base URL for Community Management API
        base_url = "https://api.linkedin.com/rest"
        super().__init__(
            platform_name="linkedin",
            credentials=credentials,
            base_url=base_url,
            timeout=timeout,
            progress_callback=progress_callback,
        )
        self.author_urn = (
            credentials.user_id
        )  # urn:li:person:xxx or urn:li:organization:xxx
        self.linkedin_version = api_version or self.DEFAULT_API_VERSION

        # Media manager (initialized in __aenter__)
        self._media_manager: LinkedInMediaManager | None = None

    def _build_auth_headers(self) -> dict[str, str]:
        """Build authentication headers for LinkedIn REST API.

        Returns:
            Dictionary of headers including LinkedIn-specific version headers.
        """
        return {
            "Authorization": f"Bearer {self.credentials.access_token}",
            "Linkedin-Version": self.linkedin_version,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

    async def __aenter__(self) -> "LinkedInClient":
        """Async context manager entry."""
        await super().__aenter__()

        # Initialize media manager
        if not self.author_urn:
            raise PlatformAuthError(
                "LinkedIn author URN (user_id) is required in credentials",
                platform=self.platform_name,
            )

        self._media_manager = LinkedInMediaManager(
            person_urn=self.author_urn,
            access_token=self.credentials.access_token,
            linkedin_version=self.linkedin_version,
            timeout=self.timeout,
        )

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        # Cleanup media manager
        if self._media_manager:
            await self._media_manager.__aexit__(exc_type, exc_val, exc_tb)
            self._media_manager = None

        await super().__aexit__(exc_type, exc_val, exc_tb)

    # ==================== Authentication Methods ====================

    async def authenticate(self) -> AuthCredentials:
        """Perform LinkedIn authentication flow.

        Note: This method assumes you already have a valid OAuth 2.0 access token.
        For the full OAuth flow, use LinkedIn's OAuth 2.0 implementation.

        Returns:
            Current credentials if valid.

        Raises:
            PlatformAuthError: If authentication fails.
        """
        if await self.is_authenticated():
            return self.credentials

        raise PlatformAuthError(
            "Invalid or expired credentials. Please re-authenticate via LinkedIn OAuth 2.0.",
            platform=self.platform_name,
        )

    async def refresh_token(self) -> AuthCredentials:
        """Refresh LinkedIn access token.

        LinkedIn access tokens typically expire after 60 days. Use the
        refresh token to obtain a new access token.

        Requires LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET environment
        variables, or provide OAuth credentials via PlatformFactory.

        Returns:
            Updated credentials with new access token.

        Raises:
            PlatformAuthError: If token refresh fails or OAuth credentials
                are missing.
        """
        if not self.credentials.refresh_token:
            raise PlatformAuthError(
                "No refresh token available",
                platform=self.platform_name,
            )

        # Get OAuth credentials from environment
        client_id = os.getenv("LINKEDIN_CLIENT_ID")
        client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise PlatformAuthError(
                "LinkedIn OAuth credentials required for token refresh. "
                "Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET environment "
                "variables, or use PlatformFactory for automatic token refresh.",
                platform=self.platform_name,
            )

        # Make token refresh request
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        params = {
            "grant_type": "refresh_token",
            "refresh_token": self.credentials.refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data=params,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30.0,
                )
                response.raise_for_status()
                token_data = response.json()

        except httpx.HTTPStatusError as e:
            raise PlatformAuthError(
                f"Failed to refresh token: {e.response.text}",
                platform=self.platform_name,
                status_code=e.response.status_code,
            ) from e

        except httpx.HTTPError as e:
            raise PlatformAuthError(
                f"Network error refreshing token: {e}",
                platform=self.platform_name,
            ) from e

        # Update credentials
        self.credentials.access_token = token_data["access_token"]

        # LinkedIn might provide new refresh token
        if "refresh_token" in token_data:
            self.credentials.refresh_token = token_data["refresh_token"]

        # Calculate expiry
        if "expires_in" in token_data:
            expires_in = int(token_data["expires_in"])
            self.credentials.expires_at = datetime.now() + timedelta(seconds=expires_in)

        return self.credentials

    async def is_authenticated(self) -> bool:
        """Check if LinkedIn credentials are valid.

        Returns:
            True if authenticated and token is valid.
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        try:
            # Verify credentials by fetching user profile
            # Note: /userinfo is the standard endpoint for the REST API
            if not self.api_client._client:
                raise RuntimeError("API client not initialized")

            response = await self.api_client._client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers=self._build_auth_headers(),
            )
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    # ==================== Validation ====================

    def _validate_create_post_request(self, request: PostCreateRequest) -> None:
        """Validate LinkedIn post creation request.

        LinkedIn Requirements:
            - Content is required (text post content)
            - Content max 3000 characters
            - CTA labels must be from approved list if provided
            - Media: max 20 images, or 1 video, or 1 document

        Args:
            request: Post creation request to validate.

        Raises:
            ValidationError: If validation fails.
        """
        if not request.content:
            raise ValidationError(
                "LinkedIn posts require content",
                platform=self.platform_name,
                field="content",
            )

        if len(request.content) > 3000:
            raise ValidationError(
                f"Post content exceeds 3000 characters ({len(request.content)} characters)",
                platform=self.platform_name,
                field="content",
            )

        # Validate CTA label if provided
        if cta := request.additional_data.get("call_to_action"):
            cta_upper = cta.upper()
            if cta_upper not in VALID_CTA_LABELS:
                raise ValidationError(
                    f"Invalid call_to_action: '{cta}'. "
                    f"Valid values: {', '.join(sorted(VALID_CTA_LABELS))}",
                    platform=self.platform_name,
                    field="call_to_action",
                )

    # ==================== Post CRUD Methods ====================

    async def create_post(self, request: PostCreateRequest) -> Post:
        """Create and publish a LinkedIn post.

        Uses the Community Management API to create posts on personal profiles
        or organization pages. Supports text, images, videos, documents,
        multi-image posts, articles, and Direct Sponsored Content (dark posts).

        Args:
            request: Post creation request with the following fields:
                - content: Post text (max 3000 chars). Supports mentions and hashtags.
                - link: URL for article posts.
                - media_ids: List of media URNs (images, videos, documents).
                - additional_data: LinkedIn-specific options (see below).

        Additional Data Options:
            Basic options:
                - visibility: "PUBLIC" (default), "CONNECTIONS", "LOGGED_IN"
                - feed_distribution: "MAIN_FEED" (default), "NONE" (for dark posts)
                - disable_reshare: bool (default False)

            Call-to-action:
                - call_to_action: CTA label (APPLY, DOWNLOAD, VIEW_QUOTE, LEARN_MORE,
                    SIGN_UP, SUBSCRIBE, REGISTER, JOIN, ATTEND, REQUEST_DEMO,
                    SEE_MORE, BUY_NOW, SHOP_NOW)
                - landing_page: URL for CTA button

            Media options:
                - media_title: Title for single media
                - media_alt_text: Alt text for single media
                - media_alt_texts: List of alt texts for multi-image posts

            Article options:
                - article_title: Title for link preview
                - article_description: Description for link preview
                - article_thumbnail: Image URN for article thumbnail

            Targeting (for targeted posts):
                - target_entities: List of targeting criteria

            Direct Sponsored Content (dark posts):
                - ad_context: Dict with DSC configuration:
                    - is_dsc: True for dark posts
                    - dsc_ad_type: VIDEO, STANDARD, CAROUSEL, JOB_POSTING,
                        NATIVE_DOCUMENT, EVENT
                    - dsc_status: ACTIVE, ARCHIVED
                    - dsc_ad_account: Sponsored account URN
                    - dsc_name: Display name for the DSC

        Mentions and Hashtags:
            Use these formats in the content field:
            - Organization mention: @[Display Name](urn:li:organization:12345)
            - Person mention: @[Jane Smith](urn:li:person:abc123)
            - Hashtag: #coding (plain text, auto-formatted by LinkedIn)

            Note: Organization names in mentions must match exactly (case-sensitive).

        Returns:
            Created Post object.

        Raises:
            ValidationError: If request is invalid or CTA label is invalid.
            MediaUploadError: If media upload fails.

        Example:
            >>> # Text post with link and CTA
            >>> request = PostCreateRequest(
            ...     content="Check out our new product!",
            ...     link="https://example.com/product",
            ...     additional_data={
            ...         "visibility": "PUBLIC",
            ...         "call_to_action": "LEARN_MORE",
            ...         "landing_page": "https://example.com/signup"
            ...     }
            ... )
            >>> post = await client.create_post(request)
            >>>
            >>> # Multi-image post
            >>> img1 = await client.upload_image("photo1.jpg")
            >>> img2 = await client.upload_image("photo2.jpg")
            >>> request = PostCreateRequest(
            ...     content="Check out these photos!",
            ...     media_ids=[img1.asset_id, img2.asset_id],
            ...     additional_data={
            ...         "media_alt_texts": ["First photo", "Second photo"]
            ...     }
            ... )
            >>> post = await client.create_post(request)
            >>>
            >>> # Dark post (Direct Sponsored Content)
            >>> request = PostCreateRequest(
            ...     content="Sponsored content",
            ...     media_ids=[video_asset.asset_id],
            ...     additional_data={
            ...         "ad_context": {
            ...             "is_dsc": True,
            ...             "dsc_ad_type": "VIDEO",
            ...             "dsc_status": "ACTIVE",
            ...             "dsc_ad_account": "urn:li:sponsoredAccount:123"
            ...         }
            ...     }
            ... )
            >>> post = await client.create_post(request)
            >>>
            >>> # Post with mentions and hashtags
            >>> request = PostCreateRequest(
            ...     content="Excited to announce our partnership with "
            ...             "@[LinkedIn](urn:li:organization:1337)! #exciting #partnership"
            ... )
            >>> post = await client.create_post(request)
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        # Validate request
        self._validate_create_post_request(request)

        try:
            # Build REST API payload structure
            post_payload: dict[str, Any] = {
                "author": self.author_urn,
                "commentary": request.content,
                "visibility": request.additional_data.get("visibility", "PUBLIC"),
                "distribution": {
                    "feedDistribution": request.additional_data.get(
                        "feed_distribution", "MAIN_FEED"
                    ),
                    "targetEntities": request.additional_data.get(
                        "target_entities", []
                    ),
                    "thirdPartyDistributionChannels": [],
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": request.additional_data.get(
                    "disable_reshare", False
                ),
            }

            # Add media content if provided (images, videos, or documents)
            if request.media_ids:
                if len(request.media_ids) > 1:
                    # Multi-image post (organic only, not for sponsored content)
                    # Per docs: use "multiImage" content type with array of images
                    images = []
                    for media_id in request.media_ids:
                        image_entry: dict[str, Any] = {"id": media_id}
                        # Alt text can be provided per image via additional_data
                        alt_texts = request.additional_data.get("media_alt_texts", [])
                        if alt_texts and len(alt_texts) > len(images):
                            image_entry["altText"] = alt_texts[len(images)]
                        images.append(image_entry)

                    post_payload["content"] = {"multiImage": {"images": images}}
                else:
                    # Single media (image, video, or document)
                    media_id = request.media_ids[0]
                    post_payload["content"] = {
                        "media": {
                            "id": media_id,
                            "title": request.additional_data.get("media_title"),
                            "altText": request.additional_data.get("media_alt_text"),
                        }
                    }
                    # Remove None values
                    post_payload["content"]["media"] = {
                        k: v
                        for k, v in post_payload["content"]["media"].items()
                        if v is not None
                    }

            # Add article/link if provided (and no media)
            elif request.link:
                post_payload["content"] = {
                    "article": {
                        "source": request.link,
                        "title": request.additional_data.get("article_title"),
                        "description": request.additional_data.get(
                            "article_description"
                        ),
                    }
                }
                # Add thumbnail if provided
                if thumbnail := request.additional_data.get("article_thumbnail"):
                    post_payload["content"]["article"]["thumbnail"] = thumbnail
                # Remove None values
                post_payload["content"]["article"] = {
                    k: v
                    for k, v in post_payload["content"]["article"].items()
                    if v is not None
                }

            # Add call-to-action if provided
            if cta := request.additional_data.get("call_to_action"):
                cta_upper = cta.upper()
                if cta_upper not in VALID_CTA_LABELS:
                    raise ValidationError(
                        f"Invalid call_to_action: '{cta}'. "
                        f"Valid values: {', '.join(sorted(VALID_CTA_LABELS))}",
                        platform=self.platform_name,
                        field="call_to_action",
                    )
                post_payload["contentCallToActionLabel"] = cta_upper
            if landing_page := request.additional_data.get("landing_page"):
                post_payload["contentLandingPage"] = landing_page

            # Add adContext for Direct Sponsored Content (DSC) / dark posts
            # Dark posts don't appear on company page but can be used in ad campaigns
            if ad_context := request.additional_data.get("ad_context"):
                post_payload["adContext"] = {}
                if ad_context.get("is_dsc"):
                    post_payload["adContext"]["isDsc"] = True
                if dsc_ad_type := ad_context.get("dsc_ad_type"):
                    # Valid types: VIDEO, STANDARD, CAROUSEL, JOB_POSTING,
                    # NATIVE_DOCUMENT, EVENT
                    post_payload["adContext"]["dscAdType"] = dsc_ad_type
                if dsc_status := ad_context.get("dsc_status"):
                    # Valid values: ACTIVE, ARCHIVED
                    post_payload["adContext"]["dscStatus"] = dsc_status
                if dsc_ad_account := ad_context.get("dsc_ad_account"):
                    post_payload["adContext"]["dscAdAccount"] = dsc_ad_account
                if dsc_name := ad_context.get("dsc_name"):
                    post_payload["adContext"]["dscName"] = dsc_name

                # For dark posts, set feedDistribution to NONE
                if ad_context.get("is_dsc"):
                    post_payload["distribution"]["feedDistribution"] = "NONE"

            # Create the post
            response = await self.api_client.post("/posts", data=post_payload)

            # Post ID is returned in x-restli-id header or response body
            post_id = response.data.get("id") or response.headers.get("x-restli-id")
            if not post_id:
                raise PlatformError(
                    "Failed to get post ID from response",
                    platform=self.platform_name,
                )

            # Return minimal Post object without fetching details
            return Post(
                post_id=post_id,
                platform=self.platform_name,
                content=request.content or "",
                status=PostStatus.PUBLISHED,
                created_at=datetime.now(),
                author_id=self.author_urn,
                url=None,  # Not available without separate fetch
                raw_data=response.data,
            )

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to create LinkedIn post: {e}",
                platform=self.platform_name,
            ) from e

    async def get_post(self, post_id: str) -> Post:
        """Retrieve a LinkedIn post by ID.

        Args:
            post_id: LinkedIn post URN (e.g., urn:li:share:123 or urn:li:ugcPost:123).

        Returns:
            Post object with current data.

        Raises:
            PostNotFoundError: If post doesn't exist.
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        try:
            # URL-encode the post URN
            encoded_post_id = quote(post_id, safe="")
            response = await self.api_client.get(
                f"/posts/{encoded_post_id}",
                params={"viewContext": "AUTHOR"},
            )
            data = response.data
            return self._parse_post(data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise PostNotFoundError(
                    post_id=post_id,
                    platform=self.platform_name,
                    status_code=404,
                ) from e
            raise PlatformError(
                f"Failed to fetch post: {e}",
                platform=self.platform_name,
            ) from e
        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to fetch post: {e}",
                platform=self.platform_name,
            ) from e

    async def update_post(
        self,
        post_id: str,
        request: PostUpdateRequest,
    ) -> Post:
        """Update a LinkedIn post.

        The Community Management API supports updating certain fields of published posts:
        - commentary (post text)
        - contentCallToActionLabel
        - contentLandingPage
        - lifecycleState
        - adContext.dscName, adContext.dscStatus (for sponsored content)

        Args:
            post_id: LinkedIn post URN.
            request: Post update request. Use additional_data for LinkedIn-specific
                fields like call_to_action and landing_page.

        Returns:
            Updated Post object.

        Raises:
            PostNotFoundError: If post doesn't exist.
            ValidationError: If update data is invalid.

        Example:
            >>> request = PostUpdateRequest(
            ...     content="Updated post content!",
            ...     additional_data={"call_to_action": "LEARN_MORE"}
            ... )
            >>> post = await client.update_post("urn:li:share:123", request)
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        if not self.api_client._client:
            raise RuntimeError("API client not initialized")

        try:
            # Build PARTIAL_UPDATE payload
            patch_payload: dict[str, Any] = {"patch": {"$set": {}}}

            if request.content is not None:
                patch_payload["patch"]["$set"]["commentary"] = request.content

            # Handle additional LinkedIn-specific fields
            additional = getattr(request, "additional_data", {}) or {}
            if cta := additional.get("call_to_action"):
                cta_upper = cta.upper()
                if cta_upper not in VALID_CTA_LABELS:
                    raise ValidationError(
                        f"Invalid call_to_action: '{cta}'. "
                        f"Valid values: {', '.join(sorted(VALID_CTA_LABELS))}",
                        platform=self.platform_name,
                        field="call_to_action",
                    )
                patch_payload["patch"]["$set"]["contentCallToActionLabel"] = cta_upper
            if landing_page := additional.get("landing_page"):
                patch_payload["patch"]["$set"]["contentLandingPage"] = landing_page
            if lifecycle := additional.get("lifecycle_state"):
                patch_payload["patch"]["$set"]["lifecycleState"] = lifecycle

            # Handle ad context updates if provided
            if ad_context := additional.get("ad_context"):
                patch_payload["patch"]["adContext"] = {"$set": ad_context}

            # Make the PARTIAL_UPDATE request
            encoded_post_id = quote(post_id, safe="")
            headers = {
                **self._build_auth_headers(),
                "X-RestLi-Method": "PARTIAL_UPDATE",
            }

            await self.api_client._client.post(
                f"{self.base_url}/posts/{encoded_post_id}",
                json=patch_payload,
                headers=headers,
            )

            # Fetch and return the updated post
            return await self.get_post(post_id)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise PostNotFoundError(
                    post_id=post_id,
                    platform=self.platform_name,
                    status_code=404,
                ) from e
            raise PlatformError(
                f"Failed to update post: {e}",
                platform=self.platform_name,
            ) from e
        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to update post: {e}",
                platform=self.platform_name,
            ) from e

    async def delete_post(self, post_id: str) -> bool:
        """Delete a LinkedIn post.

        Args:
            post_id: LinkedIn post URN.

        Returns:
            True if deletion was successful.

        Raises:
            PostNotFoundError: If post doesn't exist.
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        try:
            if not self.api_client._client:
                raise RuntimeError("API client not initialized")

            encoded_post_id = quote(post_id, safe="")
            headers = {
                **self._build_auth_headers(),
                "X-RestLi-Method": "DELETE",
            }
            await self.api_client._client.delete(
                f"{self.base_url}/posts/{encoded_post_id}",
                headers=headers,
            )
            return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise PostNotFoundError(
                    post_id=post_id,
                    platform=self.platform_name,
                    status_code=404,
                ) from e
            raise PlatformError(
                f"Failed to delete post: {e}",
                platform=self.platform_name,
            ) from e
        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to delete post: {e}",
                platform=self.platform_name,
            ) from e

    async def list_posts(
        self,
        author_urn: str | None = None,
        limit: int = 10,
        offset: int = 0,
        sort_by: PostSortBy = "LAST_MODIFIED",
    ) -> list[Post]:
        """List posts by author.

        Retrieves posts created by a specific person or organization.

        Args:
            author_urn: Person or organization URN. Defaults to the client's author_urn.
            limit: Maximum number of posts to retrieve (max 100).
            offset: Number of posts to skip for pagination.
            sort_by: Sort order - "LAST_MODIFIED" or "CREATED".

        Returns:
            List of Post objects.

        Example:
            >>> posts = await client.list_posts(limit=20, sort_by="CREATED")
            >>> org_posts = await client.list_posts(
            ...     author_urn="urn:li:organization:12345",
            ...     limit=50
            ... )
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        if not self.api_client._client:
            raise RuntimeError("API client not initialized")

        try:
            author = author_urn or self.author_urn
            if not author:
                raise PlatformError(
                    "Author URN is required for listing posts",
                    platform=self.platform_name,
                )
            encoded_author = quote(author, safe="")

            # Use FINDER method
            headers = {
                **self._build_auth_headers(),
                "X-RestLi-Method": "FINDER",
            }

            response = await self.api_client._client.get(
                f"{self.base_url}/posts",
                params={
                    "author": encoded_author,
                    "q": "author",
                    "count": min(limit, 100),
                    "start": offset,
                    "sortBy": sort_by,
                },
                headers=headers,
            )

            posts = []
            data = response.json()
            for post_data in data.get("elements", []):
                posts.append(self._parse_post(post_data))

            return posts

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to list posts: {e}",
                platform=self.platform_name,
            ) from e

    async def create_reshare(
        self,
        parent_post_urn: str,
        commentary: str | None = None,
        visibility: str = "PUBLIC",
    ) -> Post:
        """Create a reshare (repost) of an existing LinkedIn post.

        Args:
            parent_post_urn: URN of the post to reshare (urn:li:share:xxx or urn:li:ugcPost:xxx).
            commentary: Optional commentary to add to the reshare.
            visibility: Post visibility (PUBLIC, CONNECTIONS, LOGGED_IN).

        Returns:
            Created Post object.

        Raises:
            ValidationError: If parent_post_urn is invalid.

        Example:
            >>> reshare = await client.create_reshare(
            ...     "urn:li:share:6957408550713184256",
            ...     commentary="Great insights!"
            ... )
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        try:
            post_payload: dict[str, Any] = {
                "author": self.author_urn,
                "visibility": visibility,
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "lifecycleState": "PUBLISHED",
                "reshareContext": {
                    "parent": parent_post_urn,
                },
            }

            if commentary:
                post_payload["commentary"] = commentary

            response = await self.api_client.post("/posts", data=post_payload)

            post_id = response.data.get("id") or response.headers.get("x-restli-id")
            if not post_id:
                raise PlatformError(
                    "Failed to get post ID from response",
                    platform=self.platform_name,
                )

            return Post(
                post_id=post_id,
                platform=self.platform_name,
                content=commentary or "",
                status=PostStatus.PUBLISHED,
                created_at=datetime.now(),
                author_id=self.author_urn,
                raw_data=response.data,
            )

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to create reshare: {e}",
                platform=self.platform_name,
            ) from e

    async def batch_get_posts(self, post_ids: list[str]) -> list[Post]:
        """Retrieve multiple posts by their URNs in a single request.

        Uses the BATCH_GET method for efficient retrieval of multiple posts.

        Args:
            post_ids: List of post URNs (urn:li:share:xxx or urn:li:ugcPost:xxx).

        Returns:
            List of Post objects (in the same order as input if available).

        Example:
            >>> posts = await client.batch_get_posts([
            ...     "urn:li:share:123",
            ...     "urn:li:ugcPost:456"
            ... ])
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        if not self.api_client._client:
            raise RuntimeError("API client not initialized")

        if not post_ids:
            return []

        try:
            # URL encode each post ID
            encoded_ids = [quote(pid, safe="") for pid in post_ids]
            ids_param = f"List({','.join(encoded_ids)})"

            headers = {
                **self._build_auth_headers(),
                "X-RestLi-Method": "BATCH_GET",
            }

            response = await self.api_client._client.get(
                f"{self.base_url}/posts",
                params={"ids": ids_param},
                headers=headers,
            )

            data = response.json()
            results = data.get("results", {})

            # Parse posts, maintaining order where possible
            posts = []
            for post_id in post_ids:
                if post_id in results:
                    posts.append(self._parse_post(results[post_id]))

            return posts

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to batch get posts: {e}",
                platform=self.platform_name,
            ) from e

    async def list_dsc_posts(
        self,
        dsc_ad_account: str,
        dsc_ad_types: list[str] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[Post]:
        """List Direct Sponsored Content (DSC) posts by ad account.

        Args:
            dsc_ad_account: Sponsored account URN (urn:li:sponsoredAccount:xxx).
            dsc_ad_types: Optional filter by DSC types (VIDEO, STANDARD, CAROUSEL,
                JOB_POSTING, NATIVE_DOCUMENT, EVENT).
            limit: Maximum number of posts to retrieve (max 100).
            offset: Number of posts to skip for pagination.

        Returns:
            List of Post objects.

        Example:
            >>> dsc_posts = await client.list_dsc_posts(
            ...     "urn:li:sponsoredAccount:520866471",
            ...     dsc_ad_types=["VIDEO", "STANDARD"]
            ... )
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        if not self.api_client._client:
            raise RuntimeError("API client not initialized")

        try:
            encoded_account = quote(dsc_ad_account, safe="")

            params: dict[str, Any] = {
                "dscAdAccount": encoded_account,
                "q": "dscAdAccount",
                "count": min(limit, 100),
                "start": offset,
            }

            if dsc_ad_types:
                params["dscAdTypes"] = f"List({','.join(dsc_ad_types)})"

            headers = {
                **self._build_auth_headers(),
                "X-RestLi-Method": "FINDER",
            }

            response = await self.api_client._client.get(
                f"{self.base_url}/posts",
                params=params,
                headers=headers,
            )

            posts = []
            data = response.json()
            for post_data in data.get("elements", []):
                posts.append(self._parse_post(post_data))

            return posts

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to list DSC posts: {e}",
                platform=self.platform_name,
            ) from e

    # ==================== Comment Methods ====================

    async def get_comments(
        self,
        post_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Comment]:
        """Retrieve comments for a LinkedIn post.

        Args:
            post_id: LinkedIn post URN (share or ugcPost).
            limit: Maximum number of comments to retrieve.
            offset: Number of comments to skip.

        Returns:
            List of Comment objects.
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        try:
            # URL-encode the post URN
            encoded_post_id = quote(post_id, safe="")

            response = await self.api_client.get(
                f"/socialActions/{encoded_post_id}/comments",
                params={
                    "count": limit,
                    "start": offset,
                },
            )

            comments = []
            for comment_data in response.data.get("elements", []):
                comments.append(self._parse_comment(comment_data, post_id))

            return comments

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to fetch comments: {e}",
                platform=self.platform_name,
            ) from e

    async def create_comment(
        self,
        post_id: str,
        content: str,
        parent_comment_id: str | None = None,
        image_id: str | None = None,
    ) -> Comment:
        """Add a comment to a LinkedIn post.

        Supports nested comments (replies) by specifying a parent_comment_id.

        Args:
            post_id: LinkedIn post URN (share or ugcPost).
            content: Text content of the comment.
            parent_comment_id: URN of parent comment for nested replies.
            image_id: URN of an image to attach to the comment.

        Returns:
            Created Comment object.

        Raises:
            ValidationError: If comment content is invalid.

        Example:
            >>> # Top-level comment
            >>> comment = await client.create_comment(post_id, "Great post!")
            >>> # Reply to a comment
            >>> reply = await client.create_comment(
            ...     post_id,
            ...     "Thanks!",
            ...     parent_comment_id=comment.comment_id
            ... )
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        if not content or len(content) == 0:
            raise ValidationError(
                "Comment content cannot be empty",
                platform=self.platform_name,
                field="content",
            )

        # LinkedIn comment length limit
        if len(content) > 1250:
            raise ValidationError(
                f"Comment exceeds 1250 characters ({len(content)} characters)",
                platform=self.platform_name,
                field="content",
            )

        try:
            encoded_post_id = quote(post_id, safe="")

            comment_payload: dict[str, Any] = {
                "actor": self.author_urn,
                "message": {"text": content},
                "object": post_id,
            }

            # Add parent comment for nested replies
            if parent_comment_id:
                comment_payload["parentComment"] = parent_comment_id

            # Add image content if provided
            if image_id:
                comment_payload["content"] = [{"entity": {"image": image_id}}]

            response = await self.api_client.post(
                f"/socialActions/{encoded_post_id}/comments",
                data=comment_payload,
            )

            # Get comment ID from response
            comment_id = response.data.get("id") or response.headers.get("x-restli-id")

            # Fetch full comment details
            encoded_comment_id = quote(str(comment_id), safe="")
            comment_response = await self.api_client.get(
                f"/socialActions/{encoded_post_id}/comments/{encoded_comment_id}"
            )

            return self._parse_comment(comment_response.data, post_id)

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to create comment: {e}",
                platform=self.platform_name,
            ) from e

    async def update_comment(
        self,
        post_id: str,
        comment_id: str,
        content: str,
    ) -> Comment:
        """Update a LinkedIn comment.

        Only the text content can be updated. Attributes (mentions) can also be modified.

        Args:
            post_id: LinkedIn post URN (share or ugcPost).
            comment_id: Comment ID (not the full URN).
            content: New text content for the comment.

        Returns:
            Updated Comment object.

        Raises:
            ValidationError: If comment content is invalid.
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        if not self.api_client._client:
            raise RuntimeError("API client not initialized")

        if not content or len(content) == 0:
            raise ValidationError(
                "Comment content cannot be empty",
                platform=self.platform_name,
                field="content",
            )

        if len(content) > 1250:
            raise ValidationError(
                f"Comment exceeds 1250 characters ({len(content)} characters)",
                platform=self.platform_name,
                field="content",
            )

        try:
            encoded_post_id = quote(post_id, safe="")
            encoded_comment_id = quote(comment_id, safe="")
            encoded_actor = quote(self._ensure_author_urn(), safe="")

            # Build PARTIAL_UPDATE payload
            patch_payload = {"patch": {"message": {"$set": {"text": content}}}}

            headers = {
                **self._build_auth_headers(),
                "X-RestLi-Method": "PARTIAL_UPDATE",
            }

            await self.api_client._client.post(
                f"{self.base_url}/socialActions/{encoded_post_id}/comments/{encoded_comment_id}",
                params={"actor": encoded_actor},
                json=patch_payload,
                headers=headers,
            )

            # Fetch and return the updated comment
            comment_response = await self.api_client.get(
                f"/socialActions/{encoded_post_id}/comments/{encoded_comment_id}"
            )

            return self._parse_comment(comment_response.data, post_id)

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to update comment: {e}",
                platform=self.platform_name,
            ) from e

    async def delete_comment(self, comment_id: str, post_id: str | None = None) -> bool:
        """Delete a LinkedIn comment.

        Args:
            comment_id: LinkedIn comment ID or full URN.
            post_id: LinkedIn post URN. Required if comment_id is not a full URN.

        Returns:
            True if deletion was successful.
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        try:
            if not self.api_client._client:
                raise RuntimeError("API client not initialized")

            encoded_actor = quote(self._ensure_author_urn(), safe="")

            # If post_id is provided, use the socialActions endpoint
            if post_id:
                encoded_post_id = quote(post_id, safe="")
                encoded_comment_id = quote(comment_id, safe="")
                url = f"{self.base_url}/socialActions/{encoded_post_id}/comments/{encoded_comment_id}"
            else:
                # Try to use the comment URN directly
                encoded_comment_id = quote(comment_id, safe="")
                url = f"{self.base_url}/comments/{encoded_comment_id}"

            await self.api_client._client.delete(
                url,
                params={"actor": encoded_actor},
                headers=self._build_auth_headers(),
            )
            return True

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to delete comment: {e}",
                platform=self.platform_name,
            ) from e

    # ==================== Media Methods ====================

    async def upload_media(
        self,
        media_url: str,
        media_type: str,
        alt_text: str | None = None,
    ) -> MediaAttachment:
        """Upload media to LinkedIn.

        Automatically handles images, videos, and documents with progress tracking.

        Args:
            media_url: URL or file path of the media.
            media_type: Type of media ("image", "video", or "document").
            alt_text: Alternative text for accessibility.

        Returns:
            MediaAttachment object with LinkedIn media URN.

        Raises:
            MediaUploadError: If upload fails.
            RuntimeError: If client not used as context manager.

        Example:
            >>> async with LinkedInClient(credentials) as client:
            ...     media = await client.upload_media(
            ...         "/path/to/image.jpg",
            ...         "image",
            ...         alt_text="Company logo"
            ...     )
        """
        if not self._media_manager:
            raise RuntimeError("Client must be used as async context manager")

        try:
            # Convert URL to string if needed
            file_path = str(media_url)

            # Upload based on type
            if media_type.lower() == "image":
                asset = await self._media_manager.upload_image(
                    file_path, alt_text=alt_text
                )
            elif media_type.lower() == "video":
                asset = await self._media_manager.upload_video(
                    file_path, wait_for_processing=True
                )
            elif media_type.lower() == "document":
                asset = await self._media_manager.upload_document(file_path)
            else:
                raise ValidationError(
                    f"Unsupported media type: {media_type}. "
                    "Must be 'image', 'video', or 'document'",
                    platform=self.platform_name,
                    field="media_type",
                )

            # Determine the URL for the media attachment
            # Use download_url if available, original URL if it's http(s), or construct from asset ID
            if asset.download_url:
                media_url_final = asset.download_url
            elif media_url.startswith(("http://", "https://")):
                media_url_final = media_url
            else:
                # Construct a LinkedIn asset URL for local file uploads
                # This uses the asset URN as part of the URL
                media_url_final = f"https://media.linkedin.com/asset/{asset.asset_id}"

            return MediaAttachment(
                media_id=asset.asset_id,
                media_type=(
                    MediaType.IMAGE
                    if media_type.lower() == "image"
                    else (
                        MediaType.VIDEO
                        if media_type.lower() == "video"
                        else MediaType.IMAGE
                    )  # Document
                ),
                url=cast(HttpUrl, media_url_final),
                alt_text=alt_text,
            )

        except ValidationError:
            # Let validation errors propagate as-is
            raise
        except Exception as e:
            raise MediaUploadError(
                f"Failed to upload media: {e}",
                platform=self.platform_name,
                media_type=media_type,
            ) from e

    async def upload_image(
        self,
        file_path: str,
        *,
        alt_text: str | None = None,
    ) -> MediaAsset:
        """Upload an image to LinkedIn.

        Convenience method for image uploads.

        Args:
            file_path: Path to image file or URL.
            alt_text: Alternative text for accessibility.

        Returns:
            MediaAsset with asset ID.

        Example:
            >>> async with LinkedInClient(credentials) as client:
            ...     asset = await client.upload_image("photo.jpg")
        """
        if not self._media_manager:
            raise RuntimeError("Client must be used as async context manager")

        return await self._media_manager.upload_image(file_path, alt_text=alt_text)

    async def upload_video(
        self,
        file_path: str,
        *,
        wait_for_processing: bool = True,
    ) -> MediaAsset:
        """Upload a video to LinkedIn.

        Convenience method for video uploads.

        Args:
            file_path: Path to video file or URL.
            wait_for_processing: Wait for video processing to complete.

        Returns:
            MediaAsset with asset ID.

        Example:
            >>> async with LinkedInClient(credentials) as client:
            ...     asset = await client.upload_video("video.mp4")
        """
        if not self._media_manager:
            raise RuntimeError("Client must be used as async context manager")

        return await self._media_manager.upload_video(
            file_path, wait_for_processing=wait_for_processing
        )

    async def upload_document(
        self,
        file_path: str,
        *,
        title: str | None = None,
    ) -> MediaAsset:
        """Upload a document to LinkedIn using the Documents API.

        Convenience method for document uploads. Supports PDF, PPT, PPTX, DOC, DOCX.

        Args:
            file_path: Path to document file or URL.
            title: Document title (reserved for future use).

        Returns:
            MediaAsset with document URN (urn:li:document:xxx).

        Example:
            >>> async with LinkedInClient(credentials) as client:
            ...     asset = await client.upload_document("report.pdf")
            ...     request = PostCreateRequest(
            ...         content="Check out our report!",
            ...         media_ids=[asset.asset_id]
            ...     )
            ...     post = await client.create_post(request)
        """
        if not self._media_manager:
            raise RuntimeError("Client must be used as async context manager")

        return await self._media_manager.upload_document(file_path, title=title)

    # ==================== Reactions API Methods ====================

    async def get_reactions(self, entity_urn: str, limit: int = 50) -> list[Reaction]:
        """Get reactions on a post or comment.

        Args:
            entity_urn: URN of the entity (share, ugcPost, or comment).
            limit: Maximum number of reactions to retrieve.

        Returns:
            List of Reaction objects.

        Example:
            >>> reactions = await client.get_reactions("urn:li:share:12345")
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        if not self.api_client._client:
            raise RuntimeError("API client not initialized")

        try:
            encoded_entity = quote(entity_urn, safe="")

            response = await self.api_client._client.get(
                f"{self.base_url}/reactions/(entity:{encoded_entity})",
                params={
                    "q": "entity",
                    "count": limit,
                },
                headers=self._build_auth_headers(),
            )

            reactions = []
            data = response.json()
            for reaction_data in data.get("elements", []):
                reactions.append(
                    Reaction(
                        actor=reaction_data.get("actor", ""),
                        entity=entity_urn,
                        reaction_type=ReactionType(
                            reaction_data.get("reactionType", "LIKE")
                        ),
                        created_at=(
                            datetime.fromtimestamp(reaction_data["created"] / 1000)
                            if "created" in reaction_data
                            else None
                        ),
                        raw_data=reaction_data,
                    )
                )

            return reactions

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to get reactions: {e}",
                platform=self.platform_name,
            ) from e

    async def add_reaction(
        self,
        entity_urn: str,
        reaction_type: ReactionType = ReactionType.LIKE,
    ) -> bool:
        """Add a reaction to a post or comment.

        Args:
            entity_urn: URN of the entity (share, ugcPost, or comment).
            reaction_type: Type of reaction to add.

        Returns:
            True if reaction was added successfully.

        Example:
            >>> await client.add_reaction("urn:li:share:12345", ReactionType.PRAISE)
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        if not self.api_client._client:
            raise RuntimeError("API client not initialized")

        try:
            encoded_actor = quote(self._ensure_author_urn(), safe="")

            # Build reaction payload
            payload = {
                "root": entity_urn,
                "reactionType": reaction_type.value,
            }

            await self.api_client._client.post(
                f"{self.base_url}/reactions",
                params={"actor": encoded_actor},
                json=payload,
                headers=self._build_auth_headers(),
            )

            return True

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to add reaction: {e}",
                platform=self.platform_name,
            ) from e

    async def remove_reaction(self, entity_urn: str) -> bool:
        """Remove your reaction from a post or comment.

        Args:
            entity_urn: URN of the entity (share, ugcPost, or comment).

        Returns:
            True if reaction was removed successfully.

        Example:
            >>> await client.remove_reaction("urn:li:share:12345")
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        if not self.api_client._client:
            raise RuntimeError("API client not initialized")

        try:
            encoded_actor = quote(self._ensure_author_urn(), safe="")
            encoded_entity = quote(entity_urn, safe="")

            await self.api_client._client.delete(
                f"{self.base_url}/reactions/(actor:{encoded_actor},entity:{encoded_entity})",
                headers=self._build_auth_headers(),
            )

            return True

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to remove reaction: {e}",
                platform=self.platform_name,
            ) from e

    # ==================== Social Metadata API Methods ====================

    async def get_social_metadata(self, entity_urn: str) -> SocialMetadata:
        """Get social metadata (engagement summary) for a post or comment.

        Returns aggregated engagement data including reaction counts by type
        and comment counts.

        Args:
            entity_urn: URN of the entity (share, ugcPost, or comment).

        Returns:
            SocialMetadata object with engagement summary.

        Example:
            >>> metadata = await client.get_social_metadata("urn:li:share:12345")
            >>> print(f"Likes: {metadata.reaction_summaries.get(ReactionType.LIKE, 0)}")
            >>> print(f"Comments: {metadata.comment_count}")
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        try:
            encoded_entity = quote(entity_urn, safe="")

            response = await self.api_client.get(f"/socialMetadata/{encoded_entity}")
            data = response.data

            # Parse reaction summaries
            reaction_summaries: dict[ReactionType, int] = {}
            for reaction_type, summary in data.get("reactionSummaries", {}).items():
                with contextlib.suppress(ValueError):
                    reaction_summaries[ReactionType(reaction_type)] = summary.get(
                        "count", 0
                    )

            # Parse comment summary
            comment_summary = data.get("commentSummary", {})

            return SocialMetadata(
                entity=data.get("entity", entity_urn),
                reaction_summaries=reaction_summaries,
                comment_count=comment_summary.get("count", 0),
                top_level_comment_count=comment_summary.get("topLevelCount", 0),
                comments_state=CommentsState(data.get("commentsState", "OPEN")),
                raw_data=data,
            )

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to get social metadata: {e}",
                platform=self.platform_name,
            ) from e

    async def set_comments_enabled(self, post_urn: str, enabled: bool) -> bool:
        """Enable or disable comments on a post.

        WARNING: Disabling comments will DELETE all existing comments on the post.

        Args:
            post_urn: URN of the post (share or ugcPost).
            enabled: True to enable comments, False to disable.

        Returns:
            True if the operation was successful.

        Example:
            >>> # Disable comments (deletes existing comments!)
            >>> await client.set_comments_enabled("urn:li:share:12345", False)
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        if not self.api_client._client:
            raise RuntimeError("API client not initialized")

        try:
            encoded_post = quote(post_urn, safe="")
            encoded_actor = quote(self._ensure_author_urn(), safe="")

            payload = {
                "patch": {
                    "$set": {
                        "commentsState": "OPEN" if enabled else "CLOSED",
                    }
                }
            }

            await self.api_client._client.post(
                f"{self.base_url}/socialMetadata/{encoded_post}",
                params={"actor": encoded_actor},
                json=payload,
                headers=self._build_auth_headers(),
            )

            return True

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to update comments state: {e}",
                platform=self.platform_name,
            ) from e

    # ==================== Organization Management Methods ====================

    async def get_organization(self, org_id: str) -> Organization:
        """Get organization (Company Page) details.

        Requires administrator access to the organization for full details.

        Args:
            org_id: Organization ID (numeric) or URN (urn:li:organization:12345).

        Returns:
            Organization object with company details.

        Example:
            >>> org = await client.get_organization("12345")
            >>> print(f"Company: {org.name}")
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        if not self.api_client._client:
            raise RuntimeError("API client not initialized")

        try:
            # Extract numeric ID if URN is provided
            if org_id.startswith("urn:li:organization:"):
                numeric_id = org_id.split(":")[-1]
            else:
                numeric_id = org_id

            response = await self.api_client._client.get(
                f"{self.base_url}/organizations/{numeric_id}",
                headers=self._build_auth_headers(),
            )

            data = response.json()
            return self._parse_organization(data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise PlatformError(
                    f"Organization not found: {org_id}",
                    platform=self.platform_name,
                ) from e
            if e.response.status_code == 403:
                raise PlatformAuthError(
                    f"Not authorized to access organization: {org_id}",
                    platform=self.platform_name,
                ) from e
            raise PlatformError(
                f"Failed to get organization: {e}",
                platform=self.platform_name,
            ) from e
        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to get organization: {e}",
                platform=self.platform_name,
            ) from e

    async def get_organization_by_vanity(self, vanity_name: str) -> Organization:
        """Find an organization by its vanity name (URL slug).

        Args:
            vanity_name: Organization's vanity name (e.g., "linkedin" for
                linkedin.com/company/linkedin).

        Returns:
            Organization object.

        Example:
            >>> org = await client.get_organization_by_vanity("linkedin")
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        if not self.api_client._client:
            raise RuntimeError("API client not initialized")

        try:
            response = await self.api_client._client.get(
                f"{self.base_url}/organizations",
                params={
                    "q": "vanityName",
                    "vanityName": vanity_name,
                },
                headers=self._build_auth_headers(),
            )

            data = response.json()
            elements = data.get("elements", [])

            if not elements:
                raise PlatformError(
                    f"Organization not found with vanity name: {vanity_name}",
                    platform=self.platform_name,
                )

            return self._parse_organization(elements[0])

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to find organization: {e}",
                platform=self.platform_name,
            ) from e

    async def get_organization_followers(self, org_id: str) -> int:
        """Get the follower count for an organization.

        Args:
            org_id: Organization ID (numeric) or URN.

        Returns:
            Number of followers.

        Example:
            >>> followers = await client.get_organization_followers("12345")
            >>> print(f"Followers: {followers}")
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        if not self.api_client._client:
            raise RuntimeError("API client not initialized")

        try:
            # Build organization URN if needed
            if org_id.startswith("urn:li:organization:"):
                org_urn = org_id
            else:
                org_urn = f"urn:li:organization:{org_id}"

            encoded_urn = quote(org_urn, safe="")

            response = await self.api_client._client.get(
                f"{self.base_url}/networkSizes/{encoded_urn}",
                params={"edgeType": "COMPANY_FOLLOWED_BY_MEMBER"},
                headers=self._build_auth_headers(),
            )

            data = response.json()
            return data.get("firstDegreeSize", 0)

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to get organization followers: {e}",
                platform=self.platform_name,
            ) from e

    def _parse_organization(self, data: dict[str, Any]) -> Organization:
        """Parse LinkedIn API response into Organization model.

        Args:
            data: Raw API response data.

        Returns:
            Organization object.
        """
        # Build organization URN
        org_id = data.get("id")
        if org_id and not str(org_id).startswith("urn:"):
            org_id = f"urn:li:organization:{org_id}"

        # Extract localized name
        localized_name = data.get("localizedName", "")
        if not localized_name:
            # Try to get from name field
            name_obj = data.get("name", {})
            if isinstance(name_obj, dict):
                # Get first locale
                localized = name_obj.get("localized", {})
                if localized:
                    localized_name = next(iter(localized.values()), "")
            else:
                localized_name = str(name_obj)

        # Extract logo URL
        logo_url = None
        logo_v2 = data.get("logoV2", {})
        if logo_v2:
            # Try to get the original image URL
            original = logo_v2.get("original", "")
            if original:
                logo_url = original

        # Map organization type
        org_type = None
        primary_type = data.get("primaryOrganizationType")
        if primary_type:
            with contextlib.suppress(ValueError):
                org_type = OrganizationType(primary_type)

        return Organization(
            id=str(org_id) if org_id else "",
            name=(
                data.get("name", localized_name)
                if isinstance(data.get("name"), str)
                else localized_name
            ),
            localized_name=localized_name,
            vanity_name=data.get("vanityName"),
            logo_url=logo_url,
            follower_count=data.get("followerCount"),
            primary_type=org_type,
            website_url=data.get("websiteUrl"),
            description=data.get("description"),
            industry=data.get("industry"),
            raw_data=data,
        )

    # ==================== Helper Methods ====================

    def _ensure_author_urn(self) -> str:
        """Ensure author URN is set and return it.

        Returns:
            The author URN string.

        Raises:
            PlatformAuthError: If author URN is not set.
        """
        if not self.author_urn:
            raise PlatformAuthError(
                "Author URN (user_id) is required but not set in credentials",
                platform=self.platform_name,
            )
        return self.author_urn

    def _parse_post(self, data: dict[str, Any]) -> Post:
        """Parse LinkedIn API response into Post model.

        Supports both the new REST API format (Community Management API)
        and the legacy UGC API format for backwards compatibility.

        Args:
            data: Raw API response data.

        Returns:
            Post object.
        """
        # New REST API format uses "commentary" directly
        content = data.get("commentary", "")

        # Fallback to old UGC format if needed
        if not content and "specificContent" in data:
            share_content = data["specificContent"].get(
                "com.linkedin.ugc.ShareContent", {}
            )
            commentary = share_content.get("shareCommentary", {})
            content = commentary.get("text", "")

        # Extract timestamps - REST API uses createdAt/publishedAt in milliseconds
        created_timestamp = data.get("createdAt") or data.get("publishedAt")
        if not created_timestamp:
            # Legacy format: nested object
            created_timestamp = data.get("created", {}).get("time", 0)

        created_at = (
            datetime.fromtimestamp(created_timestamp / 1000)
            if created_timestamp
            else datetime.now()
        )

        # Extract updated timestamp if available
        updated_timestamp = data.get("lastModifiedAt")
        updated_at = (
            datetime.fromtimestamp(updated_timestamp / 1000)
            if updated_timestamp
            else None
        )

        # Map lifecycle state to post status
        lifecycle_state = data.get("lifecycleState", "PUBLISHED")
        status_map = {
            "PUBLISHED": PostStatus.PUBLISHED,
            "DRAFT": PostStatus.DRAFT,
            "PUBLISH_REQUESTED": PostStatus.SCHEDULED,
            "PUBLISH_FAILED": PostStatus.FAILED,
        }
        status = status_map.get(lifecycle_state, PostStatus.DRAFT)

        return Post(
            post_id=data["id"],
            platform=self.platform_name,
            content=content,
            media=[],  # Media parsing would go here
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            author_id=data.get("author"),
            raw_data=data,
        )

    def _parse_comment(self, data: dict[str, Any], post_id: str) -> Comment:
        """Parse LinkedIn API response into Comment model.

        Args:
            data: Raw API response data.
            post_id: ID of the post this comment belongs to.

        Returns:
            Comment object.
        """
        content = data.get("message", {}).get("text", "")
        created_timestamp = data.get("created", {}).get("time", 0)
        created_at = (
            datetime.fromtimestamp(created_timestamp / 1000)
            if created_timestamp
            else datetime.now()
        )

        return Comment(
            comment_id=data["id"],
            post_id=post_id,
            platform=self.platform_name,
            content=content,
            author_id=data.get("actor", "unknown"),
            created_at=created_at,
            status=CommentStatus.VISIBLE,
            raw_data=data,
        )
