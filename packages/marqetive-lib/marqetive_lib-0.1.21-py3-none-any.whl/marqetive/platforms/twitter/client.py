"""Twitter/X API v2 client implementation.

This module provides a concrete implementation of the SocialMediaPlatform
ABC for Twitter (X), using the Twitter API v2 via tweepy.

API Documentation: https://developer.x.com/en/docs/twitter-api
"""

from datetime import datetime
from typing import Any

import httpx
import tweepy
from pydantic import HttpUrl

from marqetive.core.base import ProgressCallback, SocialMediaPlatform
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
    Post,
    PostCreateRequest,
    PostStatus,
    PostUpdateRequest,
    ProgressStatus,
)
from marqetive.platforms.twitter.media import TwitterMediaManager
from marqetive.platforms.twitter.models import TwitterPostRequest


class TwitterClient(SocialMediaPlatform):
    """Twitter/X API v2 client.

    This client implements the SocialMediaPlatform interface for Twitter (X),
    using the Twitter API v2. It supports tweets, replies, and media uploads.

    Note:
        - Requires Twitter Developer account and app credentials
        - Requires OAuth 2.0 or OAuth 1.0a authentication
        - Rate limits vary by endpoint and authentication method
        - Leverages tweepy library for API interactions

    Example:
        >>> credentials = AuthCredentials(
        ...     platform="twitter",
        ...     access_token="your_access_token",
        ...     additional_data={
        ...         "api_key": "your_api_key",
        ...         "api_secret": "your_api_secret",
        ...         "access_secret": "your_access_secret"
        ...     }
        ... )
        >>> async with TwitterClient(credentials) as client:
        ...     request = PostCreateRequest(content="Hello Twitter!")
        ...     tweet = await client.create_post(request)
    """

    def __init__(
        self,
        credentials: AuthCredentials,
        timeout: float = 30.0,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Initialize Twitter client.

        Args:
            credentials: Twitter authentication credentials
            timeout: Request timeout in seconds
            progress_callback: Optional callback for progress updates during
                long-running operations like media uploads.

        Raises:
            PlatformAuthError: If credentials are invalid
        """
        base_url = "https://api.x.com/2"
        super().__init__(
            platform_name="twitter",
            credentials=credentials,
            base_url=base_url,
            timeout=timeout,
            progress_callback=progress_callback,
        )

        # Initialize tweepy client
        self._tweepy_client: tweepy.Client | None = None
        self._setup_tweepy_client()

        # Initialize media manager
        self._media_manager: TwitterMediaManager | None = None

    def _setup_tweepy_client(self) -> None:
        """Setup tweepy Client with credentials."""
        # Extract credentials from additional_data

        self._tweepy_client = tweepy.Client(
            bearer_token=self.credentials.access_token,
        )

    async def _setup_managers(self) -> None:
        """Setup media manager."""
        if not self._tweepy_client:
            return

        # Initialize media manager
        self._media_manager = TwitterMediaManager(
            bearer_token=self.credentials.access_token,
            timeout=self.timeout,
        )

    async def _cleanup_managers(self) -> None:
        """Cleanup media manager."""
        if self._media_manager:
            await self._media_manager.__aexit__(None, None, None)
            self._media_manager = None

    async def __aenter__(self) -> "TwitterClient":
        """Async context manager entry."""
        await super().__aenter__()
        await self._setup_managers()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self._cleanup_managers()
        await super().__aexit__(exc_type, exc_val, exc_tb)

    # ==================== Authentication Methods ====================

    async def authenticate(self) -> AuthCredentials:
        """Perform Twitter authentication flow.

        Note: This method assumes you already have valid OAuth credentials.
        For the full OAuth flow, use Twitter's OAuth implementation with tweepy.

        Returns:
            Current credentials if valid.

        Raises:
            PlatformAuthError: If authentication fails.
        """
        if await self.is_authenticated():
            return self.credentials

        raise PlatformAuthError(
            "Invalid or expired credentials. Please re-authenticate via Twitter OAuth.",
            platform=self.platform_name,
        )

    async def refresh_token(self) -> AuthCredentials:
        """Refresh Twitter access token.

        Note: Twitter OAuth 1.0a tokens don't expire, so this method
        returns the current credentials. For OAuth 2.0, implement
        token refresh logic.

        Returns:
            Current credentials.
        """
        # OAuth 1.0a tokens don't expire
        return self.credentials

    async def is_authenticated(self) -> bool:
        """Check if Twitter credentials are valid.

        Returns:
            True if authenticated and token is valid.
        """
        if not self._tweepy_client:
            return False

        try:
            # Verify credentials by fetching authenticated user
            self._tweepy_client.get_me(user_auth=False)
            return True
        except tweepy.TweepyException:
            return False

    # ==================== Validation ====================

    def _validate_create_post_request(self, request: PostCreateRequest) -> None:
        """Validate Twitter post creation request.

        Twitter Requirements:
            - Must have content OR media (at least one)
            - Content max 280 characters (enforced by Twitter API)
            - Max 4 images or 1 video per tweet

        Args:
            request: Post creation request to validate.

        Raises:
            ValidationError: If validation fails.
        """
        if not request.content and not request.media_urls and not request.media_ids:
            raise ValidationError(
                "Tweet must contain content or media",
                platform=self.platform_name,
                field="content",
            )

    # ==================== Post CRUD Methods ====================

    async def create_post(self, request: PostCreateRequest) -> Post:
        """Create and publish a tweet.

        Twitter Requirements:
            - Must have content OR media (at least one)
            - Content max 280 characters (enforced by Twitter API)
            - Max 4 images or 1 video per tweet

        Args:
            request: Post creation request. Supports:
                - content: Tweet text (max 280 chars)
                - media_urls: URLs of media to attach
                - reply_to_post_id: Tweet ID to reply to (for threads)
                - quote_post_id: Tweet ID to quote

        Returns:
            Post object with:
                - post_id: Twitter tweet ID
                - platform: "twitter"
                - content: Tweet text
                - status: PostStatus.PUBLISHED
                - created_at: Creation timestamp
                - author_id: None (not available without extra API call)
                - url: None (not returned in create response)
                - raw_data: {"tweet_id": ...}

        Raises:
            ValidationError: If request is invalid.
            MediaUploadError: If media upload fails.
            RateLimitError: If Twitter rate limit is exceeded.
            PlatformError: For other Twitter API errors.
        """
        if not self._tweepy_client:
            raise RuntimeError("Client must be used as async context manager")

        # Validate request
        self._validate_create_post_request(request)

        try:
            media_ids = []

            # Upload media if provided
            if request.media_urls:
                for media_url in request.media_urls:
                    # Download media from URL and upload to Twitter
                    # Note: This is a simplified implementation
                    # In production, handle media download properly
                    media_attachment = await self.upload_media(media_url, "image")
                    media_ids.append(media_attachment.media_id)

            # Create tweet
            tweet_params: dict[str, Any] = {}
            if request.content:
                tweet_params["text"] = request.content
            if media_ids:
                tweet_params["media_ids"] = media_ids

            # Check for reply_to_post_id (used for threads and replies)
            reply_to_id = getattr(request, "reply_to_post_id", None)
            if reply_to_id:
                tweet_params["in_reply_to_tweet_id"] = reply_to_id

            # Check for quote_post_id (used for quote tweets)
            quote_id = getattr(request, "quote_post_id", None)
            if quote_id:
                tweet_params["quote_tweet_id"] = quote_id

            response = self._tweepy_client.create_tweet(**tweet_params, user_auth=False)
            tweet_id = response.data["id"]  # type: ignore[index]

            # Construct Twitter URL if username is available
            url = (
                HttpUrl(f"https://x.com/{self.credentials.username}/status/{tweet_id}")
                if self.credentials.username
                else HttpUrl(f"https://x.com/web/status/{tweet_id}")
            )

            # Return minimal Post object without fetching details
            return Post(
                post_id=tweet_id,
                platform=self.platform_name,
                content=request.content or "",
                status=PostStatus.PUBLISHED,
                created_at=datetime.now(),
                author_id=None,  # Not available without extra API call
                url=url,
                raw_data={"tweet_id": tweet_id},
            )

        except tweepy.TweepyException as e:
            if "429" in str(e):
                raise RateLimitError(
                    "Twitter rate limit exceeded",
                    platform=self.platform_name,
                    status_code=429,
                ) from e
            raise PlatformError(
                f"Failed to create tweet: {e}",
                platform=self.platform_name,
            ) from e

    async def get_post(self, post_id: str) -> Post:
        """Retrieve a tweet by ID.

        Args:
            post_id: Twitter tweet ID.

        Returns:
            Post object with current data.

        Raises:
            PostNotFoundError: If tweet doesn't exist.
        """
        if not self._tweepy_client:
            raise RuntimeError("Client must be used as async context manager")

        try:
            response = self._tweepy_client.get_tweet(
                post_id,
                tweet_fields=[
                    "created_at",
                    "public_metrics",
                    "attachments",
                    "author_id",
                ],
                expansions=["attachments.media_keys"],
                media_fields=["url", "type", "width", "height"],
                user_auth=False,
            )

            if not response.data:  # type: ignore[attr-defined]
                raise PostNotFoundError(
                    post_id=post_id,
                    platform=self.platform_name,
                    status_code=404,
                )

            return self._parse_tweet(response.data, response.includes)  # type: ignore[attr-defined]

        except tweepy.errors.NotFound as e:  # type: ignore[attr-defined]
            raise PostNotFoundError(
                post_id=post_id,
                platform=self.platform_name,
                status_code=404,
            ) from e
        except tweepy.TweepyException as e:
            raise PlatformError(
                f"Failed to fetch tweet: {e}",
                platform=self.platform_name,
            ) from e

    async def update_post(
        self,
        post_id: str,  # noqa: ARG002
        request: PostUpdateRequest,  # noqa: ARG002
    ) -> Post:
        """Update a tweet.

        Note: Twitter does not support editing tweets (except for Twitter Blue
        subscribers with limited edit window). This method will raise an error.

        Args:
            post_id: Twitter tweet ID.
            request: Post update request.

        Raises:
            PlatformError: Twitter doesn't support tweet editing for most users.
        """
        raise PlatformError(
            "Twitter does not support editing tweets for most accounts",
            platform=self.platform_name,
        )

    async def delete_post(self, post_id: str) -> bool:
        """Delete a tweet.

        Args:
            post_id: Twitter tweet ID.

        Returns:
            True if deletion was successful.

        Raises:
            PostNotFoundError: If tweet doesn't exist.
        """
        if not self._tweepy_client:
            raise RuntimeError("Client must be used as async context manager")

        try:
            self._tweepy_client.delete_tweet(post_id, user_auth=False)
            return True

        except tweepy.errors.NotFound as e:  # type: ignore[attr-defined]
            raise PostNotFoundError(
                post_id=post_id,
                platform=self.platform_name,
                status_code=404,
            ) from e
        except tweepy.TweepyException as e:
            raise PlatformError(
                f"Failed to delete tweet: {e}",
                platform=self.platform_name,
            ) from e

    # ==================== Comment Methods ====================

    async def get_comments(
        self,
        post_id: str,
        limit: int = 50,
        offset: int = 0,  # noqa: ARG002
    ) -> list[Comment]:
        """Retrieve replies to a tweet.

        Args:
            post_id: Twitter tweet ID.
            limit: Maximum number of replies to retrieve.
            offset: Number of replies to skip.

        Returns:
            List of Comment objects (replies).
        """
        if not self.api_client:
            raise RuntimeError("Client must be used as async context manager")

        try:
            # Use Twitter API v2 search to find replies
            response = await self.api_client.get(
                "/tweets/search/recent",
                params={
                    "query": f"conversation_id:{post_id}",
                    "max_results": min(limit, 100),
                    "tweet.fields": "created_at,author_id,public_metrics",
                },
            )

            comments = []
            for tweet_data in response.data.get("data", []):
                comments.append(self._parse_reply(tweet_data, post_id))

            return comments

        except httpx.HTTPError as e:
            raise PlatformError(
                f"Failed to fetch replies: {e}",
                platform=self.platform_name,
            ) from e

    async def create_comment(self, post_id: str, content: str) -> Comment:
        """Reply to a tweet.

        Args:
            post_id: Twitter tweet ID.
            content: Text content of the reply.

        Returns:
            Created Comment object (reply).

        Raises:
            ValidationError: If reply content is invalid.
        """
        if not self._tweepy_client:
            raise RuntimeError("Client must be used as async context manager")

        if not content or len(content) == 0:
            raise ValidationError(
                "Reply content cannot be empty",
                platform=self.platform_name,
                field="content",
            )

        if len(content) > 280:
            raise ValidationError(
                f"Reply exceeds 280 characters ({len(content)} characters)",
                platform=self.platform_name,
                field="content",
            )

        try:
            response = self._tweepy_client.create_tweet(
                text=content,
                in_reply_to_tweet_id=post_id,
                user_auth=False,
            )

            reply_id = response.data["id"]  # type: ignore[index]

            # Return minimal Comment object without fetching details
            return Comment(
                comment_id=reply_id,
                post_id=post_id,
                platform=self.platform_name,
                content=content,
                author_id="",
                created_at=datetime.now(),
                status=CommentStatus.VISIBLE,
            )

        except tweepy.TweepyException as e:
            raise PlatformError(
                f"Failed to create reply: {e}",
                platform=self.platform_name,
            ) from e

    async def delete_comment(self, comment_id: str) -> bool:
        """Delete a reply (tweet).

        Args:
            comment_id: Twitter tweet ID of the reply.

        Returns:
            True if deletion was successful.
        """
        # Replies are just tweets, so we can use delete_post
        return await self.delete_post(comment_id)

    # ==================== Media Methods ====================

    async def upload_media(
        self,
        media_url: str,
        media_type: str,
        alt_text: str | None = None,
    ) -> MediaAttachment:
        """Upload media to Twitter.

        Supports both local files and URLs. Automatically handles:
        - Chunked upload for large files (videos, GIFs)
        - Simple upload for images
        - Progress tracking
        - Alt text for accessibility

        Args:
            media_url: URL or file path of the media.
            media_type: Type of media (image or video).
            alt_text: Alternative text for accessibility.

        Returns:
            MediaAttachment object with media ID.

        Raises:
            MediaUploadError: If upload fails.
            RuntimeError: If client not used as context manager.

        Example:
            >>> async with TwitterClient(credentials) as client:
            ...     media = await client.upload_media(
            ...         "/path/to/image.jpg",
            ...         "image",
            ...         alt_text="A beautiful sunset"
            ...     )
            ...     print(f"Uploaded: {media.media_id}")
        """
        if not self._media_manager:
            raise RuntimeError("Client must be used as async context manager")

        try:
            # Upload media using media manager
            result = await self._media_manager.upload_media(
                media_url,
                alt_text=alt_text,
            )

            # Convert to MediaAttachment
            return MediaAttachment(
                media_id=result.media_id,
                media_type=(
                    MediaType.IMAGE
                    if media_type.lower() in ("image", "photo")
                    else MediaType.VIDEO
                ),
                url=HttpUrl(media_url),
            )

        except Exception as e:
            raise MediaUploadError(
                f"Failed to upload media: {e}",
                platform=self.platform_name,
                media_type=media_type,
            ) from e

    # ==================== Retweet Methods ====================

    async def retweet(self, tweet_id: str) -> bool:
        """Retweet a tweet.

        Args:
            tweet_id: ID of the tweet to retweet.

        Returns:
            True if retweet was successful.

        Raises:
            PostNotFoundError: If tweet doesn't exist.
            PlatformError: If retweet fails.
            RuntimeError: If client not used as context manager.
        """
        if not self._tweepy_client:
            raise RuntimeError("Client must be used as async context manager")

        try:
            response = self._tweepy_client.retweet(tweet_id, user_auth=False)
            return response.data.get("retweeted", False)  # type: ignore[union-attr]

        except tweepy.errors.NotFound as e:  # type: ignore[attr-defined]
            raise PostNotFoundError(
                post_id=tweet_id,
                platform=self.platform_name,
                status_code=404,
            ) from e
        except tweepy.TweepyException as e:
            if "429" in str(e):
                raise RateLimitError(
                    "Twitter rate limit exceeded",
                    platform=self.platform_name,
                    status_code=429,
                ) from e
            raise PlatformError(
                f"Failed to retweet: {e}",
                platform=self.platform_name,
            ) from e

    async def unretweet(self, tweet_id: str) -> bool:
        """Undo a retweet (unretweet).

        Args:
            tweet_id: ID of the tweet to unretweet.

        Returns:
            True if unretweet was successful.

        Raises:
            PostNotFoundError: If tweet doesn't exist.
            PlatformError: If unretweet fails.
            RuntimeError: If client not used as context manager.
        """
        if not self._tweepy_client:
            raise RuntimeError("Client must be used as async context manager")

        try:
            response = self._tweepy_client.unretweet(tweet_id, user_auth=False)
            # Response indicates retweeted=False when successfully unretweeted
            return not response.data.get("retweeted", True)  # type: ignore[union-attr]

        except tweepy.errors.NotFound as e:  # type: ignore[attr-defined]
            raise PostNotFoundError(
                post_id=tweet_id,
                platform=self.platform_name,
                status_code=404,
            ) from e
        except tweepy.TweepyException as e:
            if "429" in str(e):
                raise RateLimitError(
                    "Twitter rate limit exceeded",
                    platform=self.platform_name,
                    status_code=429,
                ) from e
            raise PlatformError(
                f"Failed to unretweet: {e}",
                platform=self.platform_name,
            ) from e

    # ==================== Thread Methods ====================

    async def create_thread(
        self,
        posts: list[PostCreateRequest],
    ) -> list[Post]:
        """Create a Twitter thread (multiple linked tweets).

        Each tweet in the list can have its own content, media, polls, and alt texts.
        Tweets are posted sequentially, with each tweet replying to the previous one.

        Args:
            posts: List of PostCreateRequest objects to create as a thread.
                   First tweet is the head of the thread.
                   Use TwitterPostRequest for Twitter-specific features.

        Returns:
            List of Post objects for each tweet in the thread.

        Raises:
            ValidationError: If posts list is empty.
            PlatformAuthError: If not authenticated.
            MediaUploadError: If media upload fails.
            RuntimeError: If client not used as context manager.

        Example:
            >>> from marqetive.platforms.twitter import TwitterPostRequest
            >>> tweets = [
            ...     TwitterPostRequest(content="Thread start! 1/3"),
            ...     TwitterPostRequest(content="Middle 2/3", media_urls=["..."]),
            ...     TwitterPostRequest(content="End 3/3", poll_options=["Yes", "No"]),
            ... ]
            >>> async with TwitterClient(credentials) as client:
            ...     thread_posts = await client.create_thread(tweets)
            ...     for post in thread_posts:
            ...         print(f"Tweet {post.post_id}: {post.content}")
        """
        if not posts:
            raise ValidationError(
                "At least one tweet is required for thread creation",
                platform=self.platform_name,
            )

        created_posts: list[Post] = []
        reply_to_id: str | None = None

        for idx, post_request in enumerate(posts):
            # Convert to TwitterPostRequest if needed and set reply chain
            if isinstance(post_request, TwitterPostRequest):
                if reply_to_id is not None:
                    post_request = post_request.model_copy(
                        update={"reply_to_post_id": reply_to_id}
                    )
                # TwitterPostRequest works with create_post via duck typing
                final_request = post_request
            else:
                # Create TwitterPostRequest from generic PostCreateRequest
                request_data: dict[str, Any] = {
                    "content": post_request.content,
                    "media_urls": post_request.media_urls,
                    "media_ids": post_request.media_ids,
                }
                if reply_to_id is not None:
                    request_data["reply_to_post_id"] = reply_to_id
                final_request = TwitterPostRequest(**request_data)

            # TwitterPostRequest has compatible interface with PostCreateRequest
            created_post = await self.create_post(final_request)  # type: ignore[arg-type]
            created_posts.append(created_post)
            reply_to_id = created_post.post_id

            # Emit progress
            await self._emit_progress(
                operation="create_thread",
                status=ProgressStatus.PROCESSING,
                progress=idx + 1,
                total=len(posts),
                message=f"Tweet {idx + 1}/{len(posts)} created",
                entity_id=created_post.post_id,
            )

        return created_posts

    # ==================== Helper Methods ====================

    def _parse_tweet(
        self,
        tweet: tweepy.Tweet,
        includes: dict[str, Any] | None = None,
    ) -> Post:
        """Parse Twitter API response into Post model.

        Args:
            tweet: Tweepy Tweet object.
            includes: Additional data from API response.

        Returns:
            Post object.
        """
        media = []
        if includes and "media" in includes:
            for media_item in includes["media"]:
                media.append(
                    MediaAttachment(
                        media_id=media_item.get("media_key", ""),
                        media_type=(
                            MediaType.IMAGE
                            if media_item.get("type") == "photo"
                            else MediaType.VIDEO
                        ),
                        url=media_item.get("url", ""),
                        width=media_item.get("width"),
                        height=media_item.get("height"),
                    )
                )

        metrics = tweet.public_metrics or {}

        # Construct Twitter URL if username is available
        tweet_id = str(tweet.id)
        url = (
            HttpUrl(f"https://x.com/{self.credentials.username}/status/{tweet_id}")
            if self.credentials.username
            else HttpUrl(f"https://x.com/web/status/{tweet_id}")
        )

        return Post(
            post_id=tweet_id,
            platform=self.platform_name,
            content=tweet.text,
            url=url,
            media=media,
            status=PostStatus.PUBLISHED,
            created_at=tweet.created_at or datetime.now(),
            author_id=str(tweet.author_id) if tweet.author_id else None,
            likes_count=metrics.get("like_count", 0),
            comments_count=metrics.get("reply_count", 0),
            shares_count=metrics.get("retweet_count", 0),
            views_count=metrics.get("impression_count", 0),
            raw_data=tweet.data,
        )

    def _parse_reply(self, tweet_data: dict[str, Any], post_id: str) -> Comment:
        """Parse Twitter API response into Comment model.

        Args:
            tweet_data: Raw tweet data.
            post_id: ID of the original tweet.

        Returns:
            Comment object.
        """
        metrics = tweet_data.get("public_metrics", {})

        return Comment(
            comment_id=tweet_data["id"],
            post_id=post_id,
            platform=self.platform_name,
            content=tweet_data["text"],
            author_id=tweet_data.get("author_id", ""),
            created_at=datetime.fromisoformat(
                tweet_data["created_at"].replace("Z", "+00:00")
            ),
            likes_count=metrics.get("like_count", 0),
            replies_count=metrics.get("reply_count", 0),
            status=CommentStatus.VISIBLE,
            raw_data=tweet_data,
        )
