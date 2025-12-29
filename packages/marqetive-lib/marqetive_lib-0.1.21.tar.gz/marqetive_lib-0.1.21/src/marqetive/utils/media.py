"""Media utilities for file validation, MIME type detection, and chunking.

This module provides utilities for working with media files including:
- MIME type detection using multiple methods
- File validation (size, type, format)
- File chunking for large uploads
- File hashing for integrity verification
- URL validation for media URLs
"""

import hashlib
import ipaddress
import mimetypes
import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import aiofiles

from marqetive.core.exceptions import ValidationError

# Initialize mimetypes database
mimetypes.init()

# Common MIME type mappings
MIME_TYPE_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".mkv": "video/x-matroska",
    ".webm": "video/webm",
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

# Magic number signatures for file type detection
MAGIC_NUMBERS = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"RIFF": "image/webp",  # Needs additional check for WEBP
    b"\x00\x00\x00\x18ftypmp4": "video/mp4",  # Offset at byte 4
    b"\x00\x00\x00\x1cftypiso": "video/mp4",  # Alternative MP4
    b"%PDF": "application/pdf",
}

# Platform-specific file size limits (in bytes)
PLATFORM_LIMITS = {
    "twitter": {
        "image": 5 * 1024 * 1024,  # 5 MB
        "gif": 15 * 1024 * 1024,  # 15 MB
        "video": 512 * 1024 * 1024,  # 512 MB
    },
    "instagram": {
        "image": 8 * 1024 * 1024,  # 8 MB
        "video": 100 * 1024 * 1024,  # 100 MB
        "reel": 100 * 1024 * 1024,  # 100 MB
        "story": 100 * 1024 * 1024,  # 100 MB
    },
    "linkedin": {
        "image": 10 * 1024 * 1024,  # 10 MB
        "video": 200 * 1024 * 1024,  # 200 MB
        "document": 10 * 1024 * 1024,  # 10 MB
    },
    "tiktok": {
        "video": 4 * 1024 * 1024 * 1024,  # 4 GB
    },
}

# Supported media types by platform
PLATFORM_MEDIA_TYPES = {
    "twitter": {
        "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
        "video": [".mp4", ".mov"],
    },
    "instagram": {
        "image": [".jpg", ".jpeg", ".png"],
        "video": [".mp4", ".mov"],
    },
    "linkedin": {
        "image": [".jpg", ".jpeg", ".png", ".gif"],
        "video": [".mp4", ".mov", ".avi", ".webm"],
        "document": [".pdf", ".doc", ".docx", ".ppt", ".pptx"],
    },
    "tiktok": {
        "video": [".mp4", ".mov", ".webm"],
    },
}


class MediaValidator:
    """Validator for media files with platform-specific rules."""

    def __init__(
        self,
        platform: Literal["twitter", "instagram", "linkedin", "tiktok"],
        media_type: Literal["image", "video", "document", "gif", "reel", "story"],
    ) -> None:
        """Initialize the media validator.

        Args:
            platform: Target platform name.
            media_type: Type of media being validated.
        """
        self.platform = platform
        self.media_type = media_type
        self.max_size = PLATFORM_LIMITS.get(platform, {}).get(media_type, 0)
        self.allowed_extensions = PLATFORM_MEDIA_TYPES.get(platform, {}).get(
            media_type, []
        )

    def validate(self, file_path: str) -> tuple[bool, str | None]:
        """Validate a media file.

        Args:
            file_path: Path to the file to validate.

        Returns:
            Tuple of (is_valid, error_message). If valid, error_message is None.
        """
        # Check file exists
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        # Check file extension
        extension = Path(file_path).suffix.lower()
        if extension not in self.allowed_extensions:
            return (
                False,
                f"Invalid file type '{extension}' for {self.platform} "
                f"{self.media_type}. Allowed: {', '.join(self.allowed_extensions)}",
            )

        # Check file size
        file_size = os.path.getsize(file_path)
        if self.max_size and file_size > self.max_size:
            max_mb = self.max_size / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            return (
                False,
                f"File size {actual_mb:.2f}MB exceeds {self.platform} "
                f"{self.media_type} limit of {max_mb:.2f}MB",
            )

        # Check MIME type matches extension
        detected_mime = detect_mime_type(file_path)
        expected_mime = MIME_TYPE_MAP.get(extension)
        if expected_mime and detected_mime != expected_mime:
            return (
                False,
                f"File content type '{detected_mime}' doesn't match "
                f"extension '{extension}' (expected '{expected_mime}')",
            )

        return True, None


def detect_mime_type(file_path: str) -> str:
    """Detect MIME type of a file using multiple methods.

    Uses a combination of:
    1. Magic number (file signature) detection
    2. Extension-based lookup
    3. Python's mimetypes module

    Args:
        file_path: Path to the file.

    Returns:
        MIME type string (e.g., 'image/jpeg').

    Example:
        >>> mime_type = detect_mime_type('/path/to/image.jpg')
        >>> print(mime_type)
        image/jpeg
    """
    # Try magic number detection first (most reliable)
    try:
        with open(file_path, "rb") as f:
            header = f.read(32)  # Read first 32 bytes

            # Check for magic numbers
            for magic, mime_type in MAGIC_NUMBERS.items():
                if header.startswith(magic):
                    # Special case for WEBP
                    if magic == b"RIFF" and b"WEBP" in header[:16]:
                        return "image/webp"
                    if "ftyp" not in magic.decode("latin-1", errors="ignore"):
                        return mime_type

            # Check for MP4 variants (ftyp at offset 4)
            if len(header) >= 12:
                ftyp_check = header[4:12]
                if b"ftyp" in ftyp_check:
                    return "video/mp4"

    except OSError:
        pass

    # Try extension-based lookup
    extension = Path(file_path).suffix.lower()
    if extension in MIME_TYPE_MAP:
        return MIME_TYPE_MAP[extension]

    # Fall back to mimetypes module
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


def validate_file_size(
    file_path: str, max_size: int, *, raise_error: bool = False
) -> bool:
    """Validate that a file doesn't exceed the maximum size.

    Args:
        file_path: Path to the file.
        max_size: Maximum size in bytes.
        raise_error: If True, raise ValueError instead of returning False.

    Returns:
        True if file size is within limit, False otherwise.

    Raises:
        ValueError: If file exceeds size limit and raise_error=True.
        FileNotFoundError: If file doesn't exist.

    Example:
        >>> is_valid = validate_file_size('image.jpg', 5 * 1024 * 1024)
        >>> if not is_valid:
        ...     print("File too large")
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = os.path.getsize(file_path)

    if file_size > max_size:
        if raise_error:
            max_mb = max_size / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            raise ValueError(
                f"File size {actual_mb:.2f}MB exceeds limit of {max_mb:.2f}MB"
            )
        return False

    return True


def validate_media_type(
    file_path: str, allowed_types: list[str], *, raise_error: bool = False
) -> bool:
    """Validate that a file is one of the allowed media types.

    Args:
        file_path: Path to the file.
        allowed_types: List of allowed MIME types or extensions.
        raise_error: If True, raise ValueError instead of returning False.

    Returns:
        True if file type is allowed, False otherwise.

    Raises:
        ValueError: If file type not allowed and raise_error=True.

    Example:
        >>> allowed = ['image/jpeg', 'image/png', '.jpg', '.png']
        >>> is_valid = validate_media_type('photo.jpg', allowed)
        >>> print(is_valid)
        True
    """
    mime_type = detect_mime_type(file_path)
    extension = Path(file_path).suffix.lower()

    # Check against both MIME types and extensions
    is_allowed = mime_type in allowed_types or extension in allowed_types

    if not is_allowed and raise_error:
        raise ValueError(
            f"File type '{mime_type}' (extension '{extension}') not allowed. "
            f"Allowed types: {', '.join(allowed_types)}"
        )

    return is_allowed


async def chunk_file(
    file_path: str, chunk_size: int = 1024 * 1024
) -> AsyncGenerator[bytes, None]:
    """Asynchronously read file in chunks.

    Yields file content in chunks of specified size. Useful for uploading
    large files without loading entire file into memory.

    Args:
        file_path: Path to the file.
        chunk_size: Size of each chunk in bytes (default: 1MB).

    Yields:
        Bytes chunks of the file.

    Raises:
        FileNotFoundError: If file doesn't exist.

    Example:
        >>> async for chunk in chunk_file('large_video.mp4', chunk_size=5*1024*1024):
        ...     await upload_chunk(chunk)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    async with aiofiles.open(file_path, "rb") as f:
        while True:
            chunk = await f.read(chunk_size)
            if not chunk:
                break
            yield chunk


def get_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """Calculate hash of a file for integrity verification.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: 'sha256').

    Returns:
        Hexadecimal hash string.

    Raises:
        FileNotFoundError: If file doesn't exist.

    Example:
        >>> file_hash = get_file_hash('document.pdf')
        >>> print(file_hash)
        a1b2c3d4e5f6...
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_obj = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes.

    Returns:
        Formatted string (e.g., '1.5 MB').

    Example:
        >>> size = format_file_size(1536000)
        >>> print(size)
        1.46 MB
    """
    size: float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def get_chunk_count(file_path: str, chunk_size: int) -> int:
    """Calculate number of chunks needed to upload a file.

    Args:
        file_path: Path to the file.
        chunk_size: Size of each chunk in bytes.

    Returns:
        Number of chunks needed.

    Raises:
        FileNotFoundError: If file doesn't exist.

    Example:
        >>> chunks = get_chunk_count('video.mp4', 5 * 1024 * 1024)
        >>> print(f"Will upload in {chunks} chunks")
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = os.path.getsize(file_path)
    return (file_size + chunk_size - 1) // chunk_size  # Ceiling division


def validate_media_url(
    url: str,
    *,
    allowed_schemes: list[str] | None = None,
    block_private_ips: bool = True,
    platform: str = "unknown",
) -> str:
    """Validate a media URL for security.

    Validates that the URL uses an allowed scheme (default: http/https) and
    optionally blocks private/internal IP addresses to prevent SSRF attacks.

    Args:
        url: The URL to validate.
        allowed_schemes: List of allowed URL schemes (default: ['http', 'https']).
        block_private_ips: If True, block private/loopback IP addresses.
        platform: Platform name for error messages.

    Returns:
        The validated URL (unchanged if valid).

    Raises:
        ValidationError: If the URL is invalid or uses a disallowed scheme/IP.

    Example:
        >>> url = validate_media_url("https://example.com/image.jpg")
        >>> url = validate_media_url("https://cdn.example.com/video.mp4", platform="instagram")
    """
    if allowed_schemes is None:
        allowed_schemes = ["http", "https"]

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValidationError(
            f"Invalid URL format: {e}",
            platform=platform,
            field="media_url",
        ) from e

    # Validate scheme
    if not parsed.scheme:
        raise ValidationError(
            "URL must include a scheme (e.g., https://)",
            platform=platform,
            field="media_url",
        )

    if parsed.scheme.lower() not in allowed_schemes:
        raise ValidationError(
            f"URL scheme '{parsed.scheme}' not allowed. "
            f"Allowed schemes: {', '.join(allowed_schemes)}",
            platform=platform,
            field="media_url",
        )

    # Validate hostname exists
    if not parsed.hostname:
        raise ValidationError(
            "URL must include a hostname",
            platform=platform,
            field="media_url",
        )

    # Block private/internal IPs if requested
    if block_private_ips:
        try:
            ip = ipaddress.ip_address(parsed.hostname)
            if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                raise ValidationError(
                    "Private, loopback, and reserved IP addresses are not allowed",
                    platform=platform,
                    field="media_url",
                )
        except ValueError:
            # Not an IP address, it's a hostname - that's fine
            pass

    return url
