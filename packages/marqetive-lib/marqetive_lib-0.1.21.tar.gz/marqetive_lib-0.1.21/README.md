# MarqetiveLib

Modern Python library for social media platform integrations - Simple, type-safe, and async-ready.

## Supported Platforms

- **Twitter/X** - Post tweets, upload media, manage threads
- **LinkedIn** - Share updates, upload images and videos
- **Instagram** - Create posts with media via Graph API
- **TikTok** - Upload and publish videos

## Features

- **Unified API**: Single interface for all social media platforms
- **Async-First**: Built for modern async Python applications
- **Type-Safe**: Full type hints and Pyright compliance
- **Auto Token Refresh**: Factory handles OAuth token lifecycle automatically
- **Media Upload**: Progress tracking for large file uploads
- **Retry Logic**: Exponential backoff with jitter for transient failures
- **Well Tested**: Comprehensive test coverage

## Installation

```bash
pip install marqetive
```

Or with Poetry:

```bash
poetry add marqetive
```

## Quick Start

```python
import asyncio
from marqetive import get_client, AuthCredentials, PostCreateRequest

async def main():
    # Create credentials for your platform
    credentials = AuthCredentials(
        platform="twitter",
        access_token="your_access_token",
        refresh_token="your_refresh_token"
    )

    # Get authenticated client (auto-refreshes token if expired)
    client = await get_client(credentials)

    # Use client as async context manager
    async with client:
        request = PostCreateRequest(content="Hello from MarqetiveLib!")
        post = await client.create_post(request)
        print(f"Posted! ID: {post.platform_id}")

asyncio.run(main())
```

## Platform Examples

### Twitter

```python
from marqetive import get_client, AuthCredentials, PostCreateRequest

credentials = AuthCredentials(
    platform="twitter",
    access_token="your_access_token",
    refresh_token="your_refresh_token"  # Optional, for token refresh
)

client = await get_client(credentials)
async with client:
    # Text post
    post = await client.create_post(PostCreateRequest(content="Hello Twitter!"))

    # Post with media
    post = await client.create_post(PostCreateRequest(
        content="Check out this image!",
        media_paths=["/path/to/image.jpg"]
    ))
```

### LinkedIn

```python
from marqetive import get_client, AuthCredentials, PostCreateRequest

credentials = AuthCredentials(
    platform="linkedin",
    access_token="your_access_token",
    user_id="urn:li:person:your_person_id"  # Required for LinkedIn
)

client = await get_client(credentials)
async with client:
    post = await client.create_post(PostCreateRequest(
        content="Excited to share this update!"
    ))
```

### Instagram

```python
from marqetive import get_client, AuthCredentials, PostCreateRequest

credentials = AuthCredentials(
    platform="instagram",
    access_token="your_access_token",
    user_id="your_instagram_business_account_id"  # Required
)

client = await get_client(credentials)
async with client:
    # Instagram requires media for posts
    post = await client.create_post(PostCreateRequest(
        content="Beautiful day! #photography",
        media_paths=["/path/to/photo.jpg"]
    ))
```

### TikTok

```python
from marqetive import get_client, AuthCredentials, PostCreateRequest

credentials = AuthCredentials(
    platform="tiktok",
    access_token="your_access_token",
    additional_data={"open_id": "your_open_id"}  # Required for TikTok
)

client = await get_client(credentials)
async with client:
    post = await client.create_post(PostCreateRequest(
        content="Check out this video!",
        media_paths=["/path/to/video.mp4"]
    ))
```

## Using Custom OAuth Credentials

```python
from marqetive import PlatformFactory, AuthCredentials, PostCreateRequest

# Create factory with your OAuth app credentials
factory = PlatformFactory(
    twitter_client_id="your_client_id",
    twitter_client_secret="your_client_secret",
    linkedin_client_id="your_linkedin_client_id",
    linkedin_client_secret="your_linkedin_client_secret"
)

credentials = AuthCredentials(
    platform="twitter",
    access_token="user_access_token",
    refresh_token="user_refresh_token"
)

# Get client with automatic token refresh
client = await factory.get_client(credentials)
async with client:
    post = await client.create_post(PostCreateRequest(content="Hello!"))
```

## Progress Tracking for Media Uploads

```python
def progress_callback(operation: str, progress: int, total: int, message: str | None):
    percent = (progress / total) * 100 if total > 0 else 0
    print(f"{operation}: {percent:.1f}% - {message or ''}")

client = await get_client(credentials, progress_callback=progress_callback)
async with client:
    post = await client.create_post(PostCreateRequest(
        content="Uploading video...",
        media_paths=["/path/to/large_video.mp4"]
    ))
```

## Error Handling

```python
from marqetive import get_client, AuthCredentials, PostCreateRequest
from marqetive.core.exceptions import (
    PlatformError,
    PlatformAuthError,
    RateLimitError,
    MediaUploadError
)

try:
    client = await get_client(credentials)
    async with client:
        post = await client.create_post(request)
except PlatformAuthError as e:
    print(f"Authentication failed: {e}")
    # Token may need refresh or reconnection
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after} seconds")
except MediaUploadError as e:
    print(f"Media upload failed: {e}")
except PlatformError as e:
    print(f"Platform error: {e}")
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/your-org/marqetive-lib.git
cd marqetive-lib

# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install --with dev,docs

# Activate virtual environment
poetry shell
```

### Running Tests

```bash
# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src/marqetive --cov-report=term-missing

# Run platform-specific tests
poetry run pytest tests/platforms/test_twitter.py
```

### Code Quality

```bash
# Lint code with Ruff
poetry run ruff check .

# Format code with Ruff
poetry run ruff format .

# Type check with Pyright
poetry run pyright src/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
