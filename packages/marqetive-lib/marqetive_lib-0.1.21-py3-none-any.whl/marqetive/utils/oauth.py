"""OAuth token refresh utilities for social media platforms.

This module provides utilities for refreshing OAuth2 access tokens across
different social media platforms.
"""

import base64
import logging
import re
from datetime import datetime, timedelta
from typing import Any

import httpx

from marqetive.core.exceptions import PlatformAuthError
from marqetive.core.models import AuthCredentials

logger = logging.getLogger(__name__)

# Patterns for sensitive data that should be redacted from logs
_SENSITIVE_PATTERNS = [
    re.compile(r'"access_token"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r'"refresh_token"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r'"client_secret"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r'"api_key"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r'"token"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r"access_token=[^&\s]+", re.IGNORECASE),
    re.compile(r"refresh_token=[^&\s]+", re.IGNORECASE),
]


def _sanitize_response_text(text: str) -> str:
    """Sanitize response text to remove sensitive credentials.

    Args:
        text: Raw response text that may contain credentials.

    Returns:
        Sanitized text with sensitive values redacted.
    """
    result = text
    for pattern in _SENSITIVE_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result


async def refresh_oauth2_token(
    refresh_token: str,
    client_id: str,
    client_secret: str,
    token_url: str,
    additional_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Refresh an OAuth2 access token.

    Generic OAuth2 token refresh implementation that works with most providers.

    Args:
        refresh_token: The refresh token.
        client_id: OAuth client ID.
        client_secret: OAuth client secret.
        token_url: Token endpoint URL.
        additional_params: Additional parameters to include in request.

    Returns:
        Token response dictionary with access_token, expires_in, etc.

    Raises:
        PlatformAuthError: If token refresh fails.

    Example:
        >>> token_data = await refresh_oauth2_token(
        ...     refresh_token="refresh_token_here",
        ...     client_id="my_client_id",
        ...     client_secret="my_client_secret",
        ...     token_url="https://oauth.example.com/token"
        ... )
        >>> print(token_data["access_token"])
    """
    params = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    if additional_params:
        params.update(additional_params)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=params,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error refreshing token: {e.response.status_code}")
        raise PlatformAuthError(
            f"Failed to refresh token: {_sanitize_response_text(e.response.text)}",
            platform="oauth2",
            status_code=e.response.status_code,
        ) from e

    except httpx.HTTPError as e:
        logger.error(f"Network error refreshing token: {e}")
        raise PlatformAuthError(
            f"Network error refreshing token: {e}",
            platform="oauth2",
        ) from e


async def refresh_twitter_token(
    credentials: AuthCredentials,
    client_id: str,
    client_secret: str,
) -> AuthCredentials:
    """Refresh Twitter OAuth2 access token.

    Twitter requires HTTP Basic Authentication with client credentials
    in the Authorization header, not in the request body.

    Args:
        credentials: Current credentials with refresh token.
        client_id: Twitter OAuth client ID.
        client_secret: Twitter OAuth client secret.

    Returns:
        Updated credentials with new access token.

    Raises:
        PlatformAuthError: If refresh fails.

    Example:
        >>> import os
        >>> creds = AuthCredentials(
        ...     platform="twitter",
        ...     access_token="old_token",
        ...     refresh_token="refresh_token_here"
        ... )
        >>> refreshed = await refresh_twitter_token(
        ...     creds,
        ...     os.getenv("TWITTER_CLIENT_ID"),
        ...     os.getenv("TWITTER_CLIENT_SECRET")
        ... )
    """
    if not credentials.refresh_token:
        raise PlatformAuthError(
            "No refresh token available",
            platform="twitter",
        )

    token_url = "https://api.x.com/2/oauth2/token"

    # Twitter requires Basic Auth header for confidential clients
    basic_auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    params = {
        "grant_type": "refresh_token",
        "refresh_token": credentials.refresh_token,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=params,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {basic_auth}",
                },
                timeout=30.0,
            )
            response.raise_for_status()
            token_data = response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error refreshing Twitter token: {e.response.status_code}")

        # Determine if this is a permanent failure requiring user re-authentication
        # Twitter returns 400 with "invalid_request" or "invalid_grant" when:
        # - Refresh token was already used (single-use tokens)
        # - Refresh token expired
        # - User revoked access
        requires_reconnection = False
        if e.response.status_code == 400:
            try:
                error_data = e.response.json()
                error_code = error_data.get("error", "")
                if error_code in ("invalid_request", "invalid_grant"):
                    requires_reconnection = True
                    logger.warning(
                        f"Twitter refresh token is invalid ({error_code}), "
                        "user needs to reconnect their account"
                    )
            except Exception:
                # If we can't parse the response, assume reconnection is needed for 400
                requires_reconnection = True

        raise PlatformAuthError(
            f"Failed to refresh token: {_sanitize_response_text(e.response.text)}",
            platform="twitter",
            status_code=e.response.status_code,
            requires_reconnection=requires_reconnection,
        ) from e

    except httpx.HTTPError as e:
        logger.error(f"Network error refreshing Twitter token: {e}")
        raise PlatformAuthError(
            f"Network error refreshing token: {e}",
            platform="twitter",
        ) from e

    # Update credentials
    credentials.access_token = token_data["access_token"]

    # Update refresh token if provided
    if "refresh_token" in token_data:
        credentials.refresh_token = token_data["refresh_token"]

    # Calculate expiry
    if "expires_in" in token_data:
        expires_in = int(token_data["expires_in"])
        credentials.expires_at = datetime.now() + timedelta(seconds=expires_in)

    return credentials


async def refresh_linkedin_token(
    credentials: AuthCredentials,
    client_id: str,
    client_secret: str,
) -> AuthCredentials:
    """Refresh LinkedIn OAuth2 access token.

    Args:
        credentials: Current credentials with refresh token.
        client_id: LinkedIn OAuth client ID.
        client_secret: LinkedIn OAuth client secret.

    Returns:
        Updated credentials with new access token.

    Raises:
        PlatformAuthError: If refresh fails.

    Example:
        >>> creds = AuthCredentials(
        ...     platform="linkedin",
        ...     access_token="old_token",
        ...     refresh_token="refresh_token_here"
        ... )
        >>> refreshed = await refresh_linkedin_token(creds, client_id, client_secret)
    """
    if not credentials.refresh_token:
        raise PlatformAuthError(
            "No refresh token available",
            platform="linkedin",
        )

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"

    token_data = await refresh_oauth2_token(
        refresh_token=credentials.refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_url=token_url,
    )

    # Update credentials
    credentials.access_token = token_data["access_token"]

    # LinkedIn might provide new refresh token
    if "refresh_token" in token_data:
        credentials.refresh_token = token_data["refresh_token"]

    # Calculate expiry
    if "expires_in" in token_data:
        expires_in = int(token_data["expires_in"])
        credentials.expires_at = datetime.now() + timedelta(seconds=expires_in)

    return credentials


async def refresh_instagram_token(
    credentials: AuthCredentials,
) -> AuthCredentials:
    """Refresh Instagram long-lived access token.

    Instagram uses a different refresh mechanism - exchanging the current
    long-lived token for a new one.

    Args:
        credentials: Current credentials.

    Returns:
        Updated credentials with refreshed token.

    Raises:
        PlatformAuthError: If refresh fails.

    Example:
        >>> creds = AuthCredentials(
        ...     platform="instagram",
        ...     access_token="current_token"
        ... )
        >>> refreshed = await refresh_instagram_token(creds)
    """
    url = "https://graph.instagram.com/refresh_access_token"
    params = {
        "grant_type": "ig_refresh_token",
        "access_token": credentials.access_token,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()

            # Update credentials
            credentials.access_token = data["access_token"]

            # Instagram returns expires_in
            if "expires_in" in data:
                expires_in = int(data["expires_in"])
                credentials.expires_at = datetime.now() + timedelta(seconds=expires_in)

            return credentials

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error refreshing Instagram token: {e.response.status_code}")
        raise PlatformAuthError(
            f"Failed to refresh Instagram token: {_sanitize_response_text(e.response.text)}",
            platform="instagram",
            status_code=e.response.status_code,
        ) from e

    except httpx.HTTPError as e:
        logger.error(f"Network error refreshing Instagram token: {e}")
        raise PlatformAuthError(
            f"Network error refreshing Instagram token: {e}",
            platform="instagram",
        ) from e


async def refresh_tiktok_token(
    credentials: AuthCredentials,
    client_id: str,
    client_secret: str,
) -> AuthCredentials:
    """Refresh TikTok OAuth2 access token.

    Args:
        credentials: Current credentials with refresh token.
        client_id: TikTok OAuth client ID (client_key).
        client_secret: TikTok OAuth client secret.

    Returns:
        Updated credentials with new access token.

    Raises:
        PlatformAuthError: If refresh fails.
    """
    if not credentials.refresh_token:
        raise PlatformAuthError(
            "No refresh token available",
            platform="tiktok",
        )

    token_url = "https://open.tiktokapis.com/v2/oauth/token/"

    params = {
        "client_key": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": credentials.refresh_token,
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
        logger.error(f"HTTP error refreshing tiktok token: {e.response.status_code}")
        raise PlatformAuthError(
            f"Failed to refresh token: {_sanitize_response_text(e.response.text)}",
            platform="tiktok",
            status_code=e.response.status_code,
        ) from e

    except httpx.HTTPError as e:
        logger.error(f"Network error refreshing tiktok token: {e}")
        raise PlatformAuthError(
            f"Network error refreshing token: {e}",
            platform="tiktok",
        ) from e

    # Update credentials
    credentials.access_token = token_data["access_token"]

    # TikTok might provide new refresh token
    if "refresh_token" in token_data:
        credentials.refresh_token = token_data["refresh_token"]

    # Calculate expiry
    if "expires_in" in token_data:
        expires_in = int(token_data["expires_in"])
        credentials.expires_at = datetime.now() + timedelta(seconds=expires_in)

    return credentials


async def fetch_tiktok_token(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code_verifier: str | None = None,
) -> dict[str, Any]:
    """Fetch a TikTok OAuth2 access token using an authorization code.

    Args:
        code: The authorization code from the callback.
        client_id: TikTok OAuth client ID (client_key).
        client_secret: TikTok OAuth client secret.
        redirect_uri: The redirect URI used for the authorization request.
        code_verifier: PKCE code verifier for mobile/desktop apps.

    Returns:
        Token response dictionary with access_token, refresh_token, etc.

    Raises:
        PlatformAuthError: If token fetch fails.
    """
    token_url = "https://open.tiktokapis.com/v2/oauth/token/"

    params = {
        "client_key": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    if code_verifier:
        params["code_verifier"] = code_verifier

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=params,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching tiktok token: {e.response.status_code}")
        raise PlatformAuthError(
            f"Failed to fetch token: {_sanitize_response_text(e.response.text)}",
            platform="tiktok",
            status_code=e.response.status_code,
        ) from e

    except httpx.HTTPError as e:
        logger.error(f"Network error fetching tiktok token: {e}")
        raise PlatformAuthError(
            f"Network error fetching token: {e}",
            platform="tiktok",
        ) from e
