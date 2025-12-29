"""Async file handlers for downloading, streaming, and managing files.

This module provides utilities for:
- Downloading files from URLs asynchronously
- Streaming file uploads with progress tracking
- Temporary file management
- Async file I/O operations
"""

import asyncio
import os
import tempfile
from collections.abc import AsyncGenerator, Callable
from pathlib import Path
from typing import Any

import aiofiles
import httpx

from marqetive.core.exceptions import ValidationError
from marqetive.utils.media import detect_mime_type, format_file_size, validate_media_url

# System directories that should never be written to
# Includes both standard paths and macOS /private/* equivalents
_BLOCKED_SYSTEM_DIRS: frozenset[str] = frozenset(
    {
        "/etc",
        "/private/etc",
        "/usr",
        "/bin",
        "/sbin",
        "/var",
        "/private/var",
        "/root",
        "/lib",
        "/lib64",
        "/boot",
    }
)


def _validate_path(
    file_path: str,
    *,
    allowed_base_dirs: set[str] | None = None,
) -> str:
    """Validate and normalize a file path for security.

    Prevents path traversal attacks by:
    1. Checking for null bytes (injection attack)
    2. Resolving to absolute path (handles .. and symlinks)
    3. Blocking writes to sensitive system directories

    Args:
        file_path: Path to validate.
        allowed_base_dirs: Optional set of allowed base directories.
            If provided, path must be within one of these directories.

    Returns:
        Normalized absolute path.

    Raises:
        ValidationError: If path is invalid or blocked.

    Example:
        >>> _validate_path("/tmp/myfile.txt")
        '/tmp/myfile.txt'
        >>> _validate_path("../../../etc/passwd")  # raises ValidationError
    """
    # Check for null bytes (path injection attack)
    if "\x00" in file_path:
        raise ValidationError(
            "Path contains null bytes",
            platform="file_handlers",
            field="file_path",
        )

    # Resolve to absolute path (handles .., symlinks, etc.)
    try:
        resolved = Path(file_path).resolve()
        resolved_str = str(resolved)
    except (OSError, RuntimeError) as e:
        raise ValidationError(
            f"Invalid path: {e}",
            platform="file_handlers",
            field="file_path",
        ) from e

    # Block writes to system directories
    for blocked in _BLOCKED_SYSTEM_DIRS:
        if resolved_str.startswith(blocked + "/") or resolved_str == blocked:
            raise ValidationError(
                f"Writing to system directory '{blocked}' is not allowed",
                platform="file_handlers",
                field="file_path",
            )

    # If allowed_base_dirs specified, validate path is within them
    if allowed_base_dirs:
        is_allowed = any(
            resolved_str.startswith(str(Path(base).resolve()) + "/")
            or resolved_str == str(Path(base).resolve())
            for base in allowed_base_dirs
        )
        if not is_allowed:
            raise ValidationError(
                f"Path '{file_path}' is outside allowed directories",
                platform="file_handlers",
                field="file_path",
            )

    return resolved_str


class DownloadProgress:
    """Progress tracker for file downloads.

    Attributes:
        total_bytes: Total file size in bytes (None if unknown).
        downloaded_bytes: Number of bytes downloaded so far.
        percentage: Download progress as percentage (0-100).
    """

    def __init__(self) -> None:
        """Initialize download progress tracker."""
        self.total_bytes: int | None = None
        self.downloaded_bytes: int = 0

    @property
    def percentage(self) -> float:
        """Get download progress as percentage."""
        if self.total_bytes is None or self.total_bytes == 0:
            return 0.0
        return (self.downloaded_bytes / self.total_bytes) * 100

    def update(self, chunk_size: int) -> None:
        """Update download progress.

        Args:
            chunk_size: Size of chunk that was just downloaded.
        """
        self.downloaded_bytes += chunk_size

    def __repr__(self) -> str:
        """String representation of progress."""
        if self.total_bytes:
            total_mb = self.total_bytes / (1024 * 1024)
            downloaded_mb = self.downloaded_bytes / (1024 * 1024)
            return (
                f"DownloadProgress({downloaded_mb:.2f}MB / {total_mb:.2f}MB, "
                f"{self.percentage:.1f}%)"
            )
        return f"DownloadProgress({self.downloaded_bytes} bytes)"


async def download_file(
    url: str,
    destination: str | None = None,
    *,
    chunk_size: int = 8192,
    progress_callback: Callable[[DownloadProgress], None] | None = None,
    timeout: float = 300.0,
    validate_url: bool = True,
) -> str:
    """Download a file from URL asynchronously with SSRF protection.

    Args:
        url: URL to download from.
        destination: Path where file should be saved. If None, uses temp file.
        chunk_size: Size of chunks to download (default: 8KB).
        progress_callback: Optional callback function called with progress updates.
        timeout: Request timeout in seconds (default: 5 minutes).
        validate_url: If True (default), validate URL for SSRF protection.
            Blocks private IPs, localhost, and other internal addresses.

    Returns:
        Path to the downloaded file.

    Raises:
        ValidationError: If URL fails security validation.
        httpx.HTTPError: If download fails.
        IOError: If file write fails.

    Example:
        >>> async def on_progress(progress):
        ...     print(f"Downloaded: {progress.percentage:.1f}%")
        >>>
        >>> file_path = await download_file(
        ...     "https://example.com/image.jpg",
        ...     destination="/tmp/image.jpg",
        ...     progress_callback=on_progress
        ... )
    """
    # Validate URL for SSRF protection (blocks private IPs, localhost, etc.)
    if validate_url:
        url = validate_media_url(
            url,
            block_private_ips=True,
            platform="file_handlers",
        )

    # Create temp file if no destination specified
    if destination is None:
        temp_fd, destination = tempfile.mkstemp()
        os.close(temp_fd)  # Close fd, we'll use aiofiles

    progress = DownloadProgress()

    async with (
        httpx.AsyncClient(timeout=timeout) as client,
        client.stream("GET", url) as response,
    ):
        response.raise_for_status()

        # Get total file size if available
        content_length = response.headers.get("content-length")
        if content_length:
            progress.total_bytes = int(content_length)

        # Download and write file
        async with aiofiles.open(destination, "wb") as f:
            async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                await f.write(chunk)
                progress.update(len(chunk))

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(progress)

    return destination


async def download_to_memory(
    url: str,
    *,
    max_size: int | None = None,
    timeout: float = 60.0,
    validate_url: bool = True,
) -> bytes:
    """Download a file into memory with SSRF protection.

    Useful for small files that need to be processed immediately.

    Args:
        url: URL to download from.
        max_size: Maximum allowed file size in bytes (raises ValueError if exceeded).
        timeout: Request timeout in seconds (default: 1 minute).
        validate_url: If True (default), validate URL for SSRF protection.
            Blocks private IPs, localhost, and other internal addresses.

    Returns:
        File content as bytes.

    Raises:
        ValidationError: If URL fails security validation.
        httpx.HTTPError: If download fails.
        ValueError: If file exceeds max_size.

    Example:
        >>> content = await download_to_memory(
        ...     "https://example.com/small_file.json",
        ...     max_size=1024 * 1024  # 1MB limit
        ... )
    """
    # Validate URL for SSRF protection (blocks private IPs, localhost, etc.)
    if validate_url:
        url = validate_media_url(
            url,
            block_private_ips=True,
            platform="file_handlers",
        )

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        response.raise_for_status()

        content = response.content

        # Check size limit
        if max_size and len(content) > max_size:
            raise ValueError(
                f"File size {len(content)} bytes exceeds maximum of {max_size} bytes"
            )

        return content


async def stream_file_upload(
    file_path: str,
    *,
    chunk_size: int = 1024 * 1024,
    progress_callback: Callable[[int, int], None] | None = None,
) -> AsyncGenerator[bytes, None]:
    """Stream file for upload with progress tracking.

    Args:
        file_path: Path to file to upload.
        chunk_size: Size of chunks to read (default: 1MB).
        progress_callback: Optional callback(bytes_read, total_bytes).

    Yields:
        Chunks of file content.

    Raises:
        FileNotFoundError: If file doesn't exist.

    Example:
        >>> async def on_progress(bytes_read, total_bytes):
        ...     pct = (bytes_read / total_bytes) * 100
        ...     print(f"Uploaded: {pct:.1f}%")
        >>>
        >>> async for chunk in stream_file_upload(
        ...     "/path/to/file.mp4",
        ...     progress_callback=on_progress
        ... ):
        ...     await upload_chunk(chunk)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = os.path.getsize(file_path)
    bytes_read = 0

    async with aiofiles.open(file_path, "rb") as f:
        while True:
            chunk = await f.read(chunk_size)
            if not chunk:
                break

            bytes_read += len(chunk)

            if progress_callback:
                progress_callback(bytes_read, file_size)

            yield chunk


async def read_file_bytes(file_path: str) -> bytes:
    """Read entire file into memory asynchronously.

    Args:
        file_path: Path to file.

    Returns:
        File content as bytes.

    Raises:
        FileNotFoundError: If file doesn't exist.

    Example:
        >>> content = await read_file_bytes('/path/to/file.bin')
        >>> print(len(content))
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    async with aiofiles.open(file_path, "rb") as f:
        return await f.read()


async def write_file_bytes(
    file_path: str,
    content: bytes,
    *,
    allowed_base_dirs: set[str] | None = None,
) -> None:
    """Write bytes to file asynchronously with path validation.

    Args:
        file_path: Path where file should be written.
        content: Content to write.
        allowed_base_dirs: Optional set of allowed base directories.
            If provided, path must be within one of these directories.

    Raises:
        ValidationError: If path is invalid or blocked.
        IOError: If write fails.

    Example:
        >>> await write_file_bytes('/tmp/output.bin', b'some data')
    """
    # Validate path for security (prevents path traversal)
    validated_path = _validate_path(file_path, allowed_base_dirs=allowed_base_dirs)

    # Ensure parent directory exists
    parent_dir = Path(validated_path).parent
    parent_dir.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(validated_path, "wb") as f:
        await f.write(content)


async def copy_file_async(
    source: str,
    destination: str,
    *,
    allowed_base_dirs: set[str] | None = None,
) -> None:
    """Copy file asynchronously with path validation.

    Args:
        source: Source file path.
        destination: Destination file path.
        allowed_base_dirs: Optional set of allowed base directories.
            If provided, destination must be within one of these directories.

    Raises:
        FileNotFoundError: If source doesn't exist.
        ValidationError: If destination path is invalid or blocked.
        IOError: If copy fails.

    Example:
        >>> await copy_file_async('/path/to/source.txt', '/tmp/dest.txt')
    """
    if not os.path.exists(source):
        raise FileNotFoundError(f"Source file not found: {source}")

    # Validate destination path for security (prevents path traversal)
    validated_dest = _validate_path(destination, allowed_base_dirs=allowed_base_dirs)

    # Ensure destination directory exists
    dest_dir = Path(validated_dest).parent
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Read from source and write to destination
    async with aiofiles.open(source, "rb") as src:
        content = await src.read()

    async with aiofiles.open(validated_dest, "wb") as dest:
        await dest.write(content)


class TempFileManager:
    """Manager for temporary files with automatic cleanup.

    Usage:
        >>> async with TempFileManager() as tmp:
        ...     file_path = tmp.create("prefix_")
        ...     # Use file_path...
        ... # File automatically deleted on exit
    """

    def __init__(self, *, suffix: str = "", prefix: str = "marqetive_") -> None:
        """Initialize temp file manager.

        Args:
            suffix: Suffix for temp files.
            prefix: Prefix for temp files (default: 'marqetive_').
        """
        self.suffix = suffix
        self.prefix = prefix
        self.temp_files: list[str] = []

    def create(self, custom_prefix: str | None = None) -> str:
        """Create a new temporary file.

        Args:
            custom_prefix: Optional custom prefix (overrides default).

        Returns:
            Path to temporary file.
        """
        prefix = custom_prefix or self.prefix
        fd, path = tempfile.mkstemp(suffix=self.suffix, prefix=prefix)
        os.close(fd)  # Close file descriptor
        self.temp_files.append(path)
        return path

    async def cleanup(self) -> None:
        """Remove all temporary files created by this manager."""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError:
                # Ignore errors during cleanup
                pass
        self.temp_files.clear()

    async def __aenter__(self) -> "TempFileManager":
        """Enter async context."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context and cleanup."""
        await self.cleanup()


async def get_file_info(file_path: str) -> dict[str, Any]:
    """Get information about a file.

    Args:
        file_path: Path to file.

    Returns:
        Dictionary with file information.

    Raises:
        FileNotFoundError: If file doesn't exist.

    Example:
        >>> info = await get_file_info('/path/to/file.jpg')
        >>> print(f"Size: {info['size_formatted']}")
        >>> print(f"MIME: {info['mime_type']}")
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    stat = os.stat(file_path)

    return {
        "path": file_path,
        "name": os.path.basename(file_path),
        "size": stat.st_size,
        "size_formatted": format_file_size(stat.st_size),
        "mime_type": detect_mime_type(file_path),
        "modified": stat.st_mtime,
        "extension": Path(file_path).suffix.lower(),
    }


async def ensure_file_accessible(file_path: str) -> bool:
    """Check if file exists and is readable.

    Args:
        file_path: Path to check.

    Returns:
        True if file is accessible, False otherwise.

    Example:
        >>> if await ensure_file_accessible('/path/to/file.txt'):
        ...     print("File is accessible")
    """
    try:
        if not os.path.exists(file_path):
            return False

        # Try to open for reading
        async with aiofiles.open(file_path, "rb") as f:
            await f.read(1)  # Try to read 1 byte

        return True
    except OSError:
        return False


async def wait_for_file(
    file_path: str, *, timeout: float = 30.0, check_interval: float = 0.5
) -> bool:
    """Wait for a file to become available.

    Useful when waiting for external processes to create files.

    Args:
        file_path: Path to file.
        timeout: Maximum time to wait in seconds.
        check_interval: How often to check in seconds.

    Returns:
        True if file became available, False if timeout.

    Example:
        >>> if await wait_for_file('/tmp/output.mp4', timeout=60):
        ...     print("File is ready!")
    """
    elapsed = 0.0

    while elapsed < timeout:
        if await ensure_file_accessible(file_path):
            return True

        await asyncio.sleep(check_interval)
        elapsed += check_interval

    return False
