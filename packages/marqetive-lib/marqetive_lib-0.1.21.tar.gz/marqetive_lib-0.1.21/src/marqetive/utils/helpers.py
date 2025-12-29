"""Helper functions for common API operations."""

import json
from typing import Any
from urllib.parse import parse_qs, urlparse


def format_response(
    data: dict[str, Any], *, pretty: bool = False, indent: int = 2
) -> str:
    """Format API response data as a string.

    Args:
        data: The response data dictionary
        pretty: Whether to format with indentation (default: False)
        indent: Number of spaces for indentation if pretty=True (default: 2)

    Returns:
        Formatted string representation of the response

    Example:
        >>> data = {"user": "john", "status": "active"}
        >>> print(format_response(data, pretty=True))
        {
          "user": "john",
          "status": "active"
        }
    """
    if pretty:
        return json.dumps(data, indent=indent, sort_keys=True)
    return json.dumps(data)


def parse_query_params(url: str) -> dict[str, Any]:
    """Parse query parameters from a URL.

    Args:
        url: The URL string to parse

    Returns:
        Dictionary of query parameters

    Example:
        >>> url = "https://api.example.com/users?page=1&limit=10"
        >>> params = parse_query_params(url)
        >>> print(params)
        {'page': ['1'], 'limit': ['10']}
    """
    parsed = urlparse(url)
    return dict(parse_qs(parsed.query))
