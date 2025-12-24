"""Custom exceptions for Zymmr API client.

This module defines exception hierarchy specifically designed for Frappe Framework
API error scenarios that the Zymmr client may encounter.
"""

from typing import Optional, Dict, Any


class ZymmrAPIError(Exception):
    """Base exception class for all Zymmr API errors.

    Args:
        message: Human-readable error message
        status_code: HTTP status code if applicable
        response_data: Raw response data from API
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class ZymmrAuthenticationError(ZymmrAPIError):
    """Authentication failed - invalid credentials or session expired.

    Typically raised on HTTP 401 responses or when login verification fails.
    """
    pass


class ZymmrPermissionError(ZymmrAPIError):
    """Permission denied - user lacks required permissions for the resource.

    Typically raised on HTTP 403 responses when user is authenticated but
    doesn't have permission to access the requested resource.
    """
    pass


class ZymmrNotFoundError(ZymmrAPIError):
    """Resource not found - requested DocType or document doesn't exist.

    Typically raised on HTTP 404 responses when the requested resource
    or DocType is not available.
    """
    pass


class ZymmrValidationError(ZymmrAPIError):
    """Validation error - request data failed Frappe validation rules.

    Typically raised on HTTP 417 responses when Frappe's validation
    rules are not satisfied.
    """
    pass


class ZymmrServerError(ZymmrAPIError):
    """Server error - internal server error or service unavailable.

    Typically raised on HTTP 5xx responses when there's a server-side
    issue that prevents the request from being processed.
    """
    pass


class ZymmrConnectionError(ZymmrAPIError):
    """Connection error - network issues or service unreachable.

    Raised when there are network connectivity issues or the service
    is unreachable.
    """
    pass


class ZymmrTimeoutError(ZymmrAPIError):
    """Request timeout - request took longer than allowed timeout period.

    Raised when a request exceeds the configured timeout duration.
    """
    pass
