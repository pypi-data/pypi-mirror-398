"""Platform factory for creating social media clients.

This module provides a simple factory for creating authenticated platform clients
with automatic token refresh and validation.
"""

import logging
import os
from typing import TYPE_CHECKING

from marqetive.core.exceptions import PlatformAuthError
from marqetive.core.models import AuthCredentials
from marqetive.utils.oauth import (
    refresh_instagram_token,
    refresh_linkedin_token,
    refresh_tiktok_token,
    refresh_twitter_token,
)

if TYPE_CHECKING:
    from marqetive.core.base import SocialMediaPlatform

logger = logging.getLogger(__name__)

# Supported platforms
SUPPORTED_PLATFORMS = frozenset({"twitter", "linkedin", "instagram", "tiktok"})

# Platform aliases (alternative names that map to canonical names)
PLATFORM_ALIASES: dict[str, str] = {
    "x": "twitter",
}


def normalize_platform(platform: str) -> str:
    """Normalize platform name to canonical form.

    Args:
        platform: Platform name (may be an alias like 'x').

    Returns:
        Canonical platform name (e.g., 'twitter').
    """
    platform = platform.lower()
    return PLATFORM_ALIASES.get(platform, platform)


def _create_client(
    platform: str, credentials: "AuthCredentials"
) -> "SocialMediaPlatform":
    """Create a client for a platform (with lazy imports).

    Args:
        platform: Platform name (twitter, linkedin, instagram, tiktok).
        credentials: Authentication credentials for the platform.

    Returns:
        The platform client instance.

    Raises:
        ValueError: If platform is unknown.
    """
    if platform == "twitter":
        from marqetive.platforms.twitter.client import TwitterClient

        return TwitterClient(credentials=credentials)
    elif platform == "linkedin":
        from marqetive.platforms.linkedin.client import LinkedInClient

        return LinkedInClient(credentials=credentials)
    elif platform == "instagram":
        from marqetive.platforms.instagram.client import InstagramClient

        return InstagramClient(credentials=credentials)
    elif platform == "tiktok":
        from marqetive.platforms.tiktok.client import TikTokClient

        return TikTokClient(credentials=credentials)
    else:
        raise ValueError(
            f"Unknown platform: {platform}. "
            f"Supported platforms: {', '.join(sorted(SUPPORTED_PLATFORMS))}"
        )


class PlatformFactory:
    """Factory for creating authenticated social media platform clients.

    This factory handles:
    - Token refresh before client creation (if expired)
    - Platform-specific credential validation
    - OAuth client credentials from environment variables

    Example:
        >>> factory = PlatformFactory()
        >>> credentials = AuthCredentials(
        ...     platform="twitter",
        ...     access_token="token",
        ...     refresh_token="refresh"
        ... )
        >>> client = await factory.get_client(credentials)
        >>> async with client:
        ...     post = await client.create_post(request)

    Example with custom OAuth credentials:
        >>> factory = PlatformFactory(
        ...     twitter_client_id="your_client_id",
        ...     twitter_client_secret="your_client_secret"
        ... )
        >>> client = await factory.get_client(credentials)
    """

    def __init__(
        self,
        *,
        twitter_client_id: str | None = None,
        twitter_client_secret: str | None = None,
        twitter_api_key: str | None = None,
        twitter_api_secret: str | None = None,
        linkedin_client_id: str | None = None,
        linkedin_client_secret: str | None = None,
        tiktok_client_id: str | None = None,
        tiktok_client_secret: str | None = None,
    ) -> None:
        """Initialize platform factory with OAuth credentials.

        OAuth credentials can be provided directly or via environment variables:
        - TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET, TWITTER_API_KEY, TWITTER_API_SECRET
        - LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET
        - TIKTOK_CLIENT_ID, TIKTOK_CLIENT_SECRET

        Note: Instagram uses long-lived tokens that don't require client credentials
        for refresh (only the current access token is needed).

        Args:
            twitter_client_id: Twitter OAuth client ID.
            twitter_client_secret: Twitter OAuth client secret.
            twitter_api_key: Twitter API key (for media operations).
            twitter_api_secret: Twitter API secret (for media operations).
            linkedin_client_id: LinkedIn OAuth client ID.
            linkedin_client_secret: LinkedIn OAuth client secret.
            tiktok_client_id: TikTok OAuth client ID.
            tiktok_client_secret: TikTok OAuth client secret.
        """
        self._oauth_credentials = {
            "twitter": {
                "client_id": twitter_client_id or os.getenv("TWITTER_CLIENT_ID"),
                "client_secret": twitter_client_secret
                or os.getenv("TWITTER_CLIENT_SECRET"),
                "api_key": twitter_api_key or os.getenv("TWITTER_API_KEY"),
                "api_secret": twitter_api_secret or os.getenv("TWITTER_API_SECRET"),
            },
            "linkedin": {
                "client_id": linkedin_client_id or os.getenv("LINKEDIN_CLIENT_ID"),
                "client_secret": linkedin_client_secret
                or os.getenv("LINKEDIN_CLIENT_SECRET"),
            },
            "tiktok": {
                "client_id": tiktok_client_id or os.getenv("TIKTOK_CLIENT_ID"),
                "client_secret": tiktok_client_secret
                or os.getenv("TIKTOK_CLIENT_SECRET"),
            },
        }

    async def get_client(
        self,
        credentials: AuthCredentials,
        *,
        auto_refresh: bool = True,
    ) -> "SocialMediaPlatform":
        """Create a platform client with the given credentials.

        If credentials are expired and auto_refresh is True, attempts to
        refresh the token before creating the client.

        Args:
            credentials: Authentication credentials for the platform.
            auto_refresh: Whether to automatically refresh expired tokens.

        Returns:
            Platform client (TwitterClient, LinkedInClient, etc.).
            The client must be used as an async context manager.

        Raises:
            PlatformAuthError: If credentials are invalid or refresh fails.
            ValueError: If platform is unknown.

        Example:
            >>> factory = PlatformFactory()
            >>> client = await factory.get_client(credentials)
            >>> async with client:
            ...     post = await client.create_post(request)
        """
        # Normalize platform name (handle aliases like 'x' -> 'twitter')
        platform = normalize_platform(credentials.platform)

        # Update credentials with normalized platform name
        if platform != credentials.platform.lower():
            credentials.platform = platform

        # Validate platform-specific requirements
        self._validate_credentials(credentials)

        # Refresh token if needed
        if auto_refresh and credentials.needs_refresh():
            logger.info(f"Refreshing expired token for {platform}")
            try:
                credentials = await self._refresh_token(credentials)
                credentials.mark_valid()
            except PlatformAuthError as e:
                # If refresh failed and requires reconnection, update credentials status
                if e.requires_reconnection:
                    credentials.mark_reconnection_required()
                    logger.warning(
                        f"Token refresh for {platform} requires user reconnection"
                    )
                raise

        # Enrich credentials with API keys for Twitter (needed for media operations)
        if platform == "twitter":
            credentials = self._enrich_twitter_credentials(credentials)

        # Create and return client
        return _create_client(platform, credentials)

    def _validate_credentials(self, credentials: AuthCredentials) -> None:
        """Validate platform-specific credential requirements.

        Args:
            credentials: The credentials to validate.

        Raises:
            PlatformAuthError: If credentials are missing required fields.
        """
        platform = credentials.platform.lower()

        if platform not in SUPPORTED_PLATFORMS:
            raise ValueError(
                f"Unknown platform: {platform}. "
                f"Supported platforms: {', '.join(sorted(SUPPORTED_PLATFORMS))}"
            )

        if not credentials.access_token:
            raise PlatformAuthError(
                "Access token is required",
                platform=platform,
            )

        if platform == "instagram":
            # Instagram requires user_id or business_account_id
            business_account_id = credentials.additional_data.get(
                "instagram_business_account_id"
            )
            if not credentials.user_id and not business_account_id:
                raise PlatformAuthError(
                    "Instagram requires user_id or 'instagram_business_account_id' "
                    "in additional_data",
                    platform=platform,
                )

        elif platform == "tiktok":
            # TikTok requires open_id
            if not credentials.additional_data.get("open_id"):
                raise PlatformAuthError(
                    "TikTok requires 'open_id' in additional_data",
                    platform=platform,
                )

        elif platform == "linkedin":
            # LinkedIn requires user_id (person URN)
            if not credentials.user_id:
                raise PlatformAuthError(
                    "LinkedIn requires user_id (person URN, e.g., 'urn:li:person:xxx')",
                    platform=platform,
                )

    async def _refresh_token(self, credentials: AuthCredentials) -> AuthCredentials:
        """Refresh the access token for the given credentials.

        Args:
            credentials: The credentials with expired token.

        Returns:
            Updated credentials with new access token.

        Raises:
            PlatformAuthError: If refresh fails or required OAuth credentials are missing.
        """
        platform = credentials.platform.lower()

        if platform == "twitter":
            oauth_creds = self._oauth_credentials.get("twitter", {})
            client_id = oauth_creds.get("client_id")
            client_secret = oauth_creds.get("client_secret")

            if not client_id or not client_secret:
                raise PlatformAuthError(
                    "Twitter client_id and client_secret required for token refresh. "
                    "Provide them via PlatformFactory constructor or environment variables "
                    "(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET).",
                    platform=platform,
                )

            return await refresh_twitter_token(credentials, client_id, client_secret)

        elif platform == "linkedin":
            oauth_creds = self._oauth_credentials.get("linkedin", {})
            client_id = oauth_creds.get("client_id")
            client_secret = oauth_creds.get("client_secret")

            if not client_id or not client_secret:
                raise PlatformAuthError(
                    "LinkedIn client_id and client_secret required for token refresh. "
                    "Provide them via PlatformFactory constructor or environment variables "
                    "(LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET).",
                    platform=platform,
                )

            return await refresh_linkedin_token(credentials, client_id, client_secret)

        elif platform == "instagram":
            # Instagram doesn't need OAuth credentials for refresh
            return await refresh_instagram_token(credentials)

        elif platform == "tiktok":
            oauth_creds = self._oauth_credentials.get("tiktok", {})
            client_id = oauth_creds.get("client_id")
            client_secret = oauth_creds.get("client_secret")

            if not client_id or not client_secret:
                raise PlatformAuthError(
                    "TikTok client_id and client_secret required for token refresh. "
                    "Provide them via PlatformFactory constructor or environment variables "
                    "(TIKTOK_CLIENT_ID, TIKTOK_CLIENT_SECRET).",
                    platform=platform,
                )

            return await refresh_tiktok_token(credentials, client_id, client_secret)

        else:
            raise ValueError(f"Unknown platform: {platform}")

    def _enrich_twitter_credentials(
        self, credentials: AuthCredentials
    ) -> AuthCredentials:
        """Enrich Twitter credentials with API keys for media operations.

        Args:
            credentials: The Twitter credentials.

        Returns:
            Credentials with api_key and api_secret in additional_data.
        """
        oauth_creds = self._oauth_credentials.get("twitter", {})

        # Only add if not already present
        if "api_key" not in credentials.additional_data:
            api_key = oauth_creds.get("api_key")
            if api_key:
                credentials.additional_data["api_key"] = api_key

        if "api_secret" not in credentials.additional_data:
            api_secret = oauth_creds.get("api_secret")
            if api_secret:
                credentials.additional_data["api_secret"] = api_secret

        return credentials

    def get_supported_platforms(self) -> frozenset[str]:
        """Get the set of supported platform names.

        Returns:
            Frozenset of supported platform names (includes aliases).
        """
        return SUPPORTED_PLATFORMS | frozenset(PLATFORM_ALIASES.keys())


async def get_client(
    credentials: AuthCredentials,
    *,
    auto_refresh: bool = True,
) -> "SocialMediaPlatform":
    """Create a platform client with the given credentials.

    This is a convenience function that creates a PlatformFactory with
    environment-based OAuth credentials and returns a client.

    For more control over OAuth credentials, create a PlatformFactory directly.

    Args:
        credentials: Authentication credentials for the platform.
        auto_refresh: Whether to automatically refresh expired tokens.

    Returns:
        Platform client ready to be used as async context manager.

    Raises:
        PlatformAuthError: If credentials are invalid or refresh fails.
        ValueError: If platform is unknown.

    Example:
        >>> from marqetive import get_client, AuthCredentials, PostCreateRequest
        >>> credentials = AuthCredentials(
        ...     platform="twitter",
        ...     access_token="...",
        ...     refresh_token="..."
        ... )
        >>> client = await get_client(credentials)
        >>> async with client:
        ...     post = await client.create_post(PostCreateRequest(content="Hello!"))
    """
    factory = PlatformFactory()
    return await factory.get_client(credentials, auto_refresh=auto_refresh)
