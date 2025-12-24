"""Utility functions for Zymmr client.

Common helper functions and utilities used throughout the client.
"""

import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse, urljoin


def validate_base_url(url: str) -> str:
    """Validate and normalize base URL.

    Args:
        url: Base URL to validate

    Returns:
        Normalized URL

    Raises:
        ValueError: If URL is invalid
    """
    if not url:
        raise ValueError("Base URL cannot be empty")

    # Add schema if missing
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")

    return url.rstrip('/')


def sanitize_doctype(doctype: str) -> str:
    """Sanitize DocType name for API requests.

    Args:
        doctype: DocType name to sanitize

    Returns:
        Sanitized DocType name

    Raises:
        ValueError: If DocType name is invalid
    """
    if not doctype or not doctype.strip():
        raise ValueError("DocType cannot be empty")

    doctype = doctype.strip()

    # Check for valid DocType format (letters, numbers, spaces, underscores)
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9\s_]*$', doctype):
        raise ValueError(f"Invalid DocType name: {doctype}")

    return doctype


def format_filters(filters: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Format filters for Frappe API requests.

    Args:
        filters: Dictionary of filter conditions

    Returns:
        Formatted filters dictionary
    """
    if not filters:
        return None

    formatted = {}

    for field, value in filters.items():
        if isinstance(value, (list, tuple)):
            # Handle list format: ["operator", "value"] or ["in", ["val1", "val2"]]
            formatted[field] = list(value)
        else:
            # Simple equality filter
            formatted[field] = value

    return formatted


def build_api_url(base_url: str, endpoint: str) -> str:
    """Build complete API URL.

    Args:
        base_url: Base URL of the application
        endpoint: API endpoint path

    Returns:
        Complete URL
    """
    return urljoin(base_url.rstrip('/') + '/', endpoint.lstrip('/'))


def extract_error_message(response_data: Any) -> str:
    """Extract meaningful error message from API response.

    Args:
        response_data: Response data from API

    Returns:
        Extracted error message
    """
    if isinstance(response_data, str):
        return response_data

    if isinstance(response_data, dict):
        # Common Frappe error message fields
        for field in ['message', 'exc', 'error', '_error_message']:
            if field in response_data and response_data[field]:
                return str(response_data[field])

        # If no standard field found, stringify the whole response
        return str(response_data)

    return "Unknown error"


def mask_sensitive_data(data: Dict[str, Any], sensitive_keys: Optional[list] = None) -> Dict[str, Any]:
    """Mask sensitive data in dictionary for logging.

    Args:
        data: Dictionary potentially containing sensitive data
        sensitive_keys: List of keys to mask (default: common sensitive keys)

    Returns:
        Dictionary with sensitive values masked
    """
    if sensitive_keys is None:
        sensitive_keys = ['password', 'pwd', 'token',
                          'api_key', 'secret', 'authorization']

    masked = data.copy()

    for key in masked:
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            masked[key] = "***masked***"

    return masked
