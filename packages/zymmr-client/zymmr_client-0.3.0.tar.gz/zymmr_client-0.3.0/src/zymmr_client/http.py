"""HTTP client wrapper for Zymmr API requests.

Provides a robust HTTP client with retry logic, error handling, and proper
session management for interacting with Frappe Framework REST API endpoints.
"""

from typing import Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import (
    ZymmrAPIError,
    ZymmrAuthenticationError,
    ZymmrPermissionError,
    ZymmrNotFoundError,
    ZymmrValidationError,
    ZymmrServerError,
    ZymmrConnectionError,
    ZymmrTimeoutError
)
from .auth import FrappeAuth


class HTTPClient:
    """HTTP client wrapper with retry logic and error handling.

    This class wraps the authenticated session from FrappeAuth and provides:
    - Automatic retry logic with exponential backoff
    - Proper error handling and exception mapping
    - Request/response logging capabilities
    - Timeout configuration
    """

    def __init__(
        self,
        auth: FrappeAuth,
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.3,
        debug: bool = False
    ):
        """Initialize HTTP client.

        Args:
            auth: Authenticated FrappeAuth instance
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_backoff_factor: Backoff factor for exponential retry delay
            debug: Enable debug logging
        """
        self.auth = auth
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.debug = debug

        # Configure retry strategy
        self._configure_session_retries()

    def _configure_session_retries(self) -> None:
        """Configure retry strategy for the session.

        Sets up retry logic for network-related failures, but not for
        HTTP error status codes (those are handled separately).
        """
        if not self.auth.is_authenticated:
            return

        # Retry strategy for network failures only
        retry_strategy = Retry(
            total=self.max_retries,
            connect=self.max_retries,
            read=self.max_retries,
            status=0,  # Don't retry on HTTP status codes
            backoff_factor=self.retry_backoff_factor,
            status_forcelist=[]  # Don't retry based on status codes
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.auth.session.mount("http://", adapter)
        self.auth.session.mount("https://", adapter)

    def _handle_response_errors(self, response: requests.Response) -> None:
        """Handle HTTP response errors and map to appropriate exceptions.

        Args:
            response: HTTP response object

        Raises:
            Appropriate ZymmrAPIError subclass based on status code
        """
        if response.status_code < 400:
            return

        # Try to extract error message from response
        error_message = f"HTTP {response.status_code}"
        error_data = {}

        try:
            error_data = response.json()
            if isinstance(error_data, dict):
                # Frappe often returns error messages in different fields
                error_message = (
                    error_data.get('message') or
                    error_data.get('exc') or
                    error_data.get('error') or
                    str(error_data)
                )
        except:
            error_message = response.text or error_message

        # Map status codes to appropriate exceptions
        if response.status_code == 401:
            raise ZymmrAuthenticationError(
                f"Authentication failed: {error_message}",
                status_code=response.status_code,
                response_data=error_data
            )
        elif response.status_code == 403:
            raise ZymmrPermissionError(
                f"Permission denied: {error_message}",
                status_code=response.status_code,
                response_data=error_data
            )
        elif response.status_code == 404:
            raise ZymmrNotFoundError(
                f"Resource not found: {error_message}",
                status_code=response.status_code,
                response_data=error_data
            )
        elif response.status_code == 417:
            # Frappe uses 417 for validation errors
            raise ZymmrValidationError(
                f"Validation error: {error_message}",
                status_code=response.status_code,
                response_data=error_data
            )
        elif 500 <= response.status_code < 600:
            raise ZymmrServerError(
                f"Server error: {error_message}",
                status_code=response.status_code,
                response_data=error_data
            )
        else:
            # Generic API error for other status codes
            raise ZymmrAPIError(
                f"API error: {error_message}",
                status_code=response.status_code,
                response_data=error_data
            )

    def _log_request(self, method: str, url: str, **kwargs) -> None:
        """Log request details if debug is enabled."""
        if self.debug:
            print(f"[DEBUG] {method.upper()} {url}")
            if 'params' in kwargs:
                print(f"[DEBUG] Params: {kwargs['params']}")
            if 'json' in kwargs:
                print(f"[DEBUG] JSON: {kwargs['json']}")

    def _log_response(self, response: requests.Response) -> None:
        """Log response details if debug is enabled."""
        if self.debug:
            print(f"[DEBUG] Response: {response.status_code}")
            try:
                print(f"[DEBUG] Response Body: {response.json()}")
            except:
                print(f"[DEBUG] Response Body: {response.text[:200]}...")

    def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make GET request.

        Args:
            url: Request URL (can be relative to base_url)
            **kwargs: Additional arguments passed to requests

        Returns:
            Parsed JSON response

        Raises:
            ZymmrAPIError: For various API errors
        """
        return self._request('GET', url, **kwargs)

    def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make POST request.

        Args:
            url: Request URL (can be relative to base_url) 
            **kwargs: Additional arguments passed to requests

        Returns:
            Parsed JSON response

        Raises:
            ZymmrAPIError: For various API errors
        """
        return self._request('POST', url, **kwargs)

    def put(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make PUT request.

        Args:
            url: Request URL (can be relative to base_url)
            **kwargs: Additional arguments passed to requests

        Returns:
            Parsed JSON response

        Raises:
            ZymmrAPIError: For various API errors
        """
        return self._request('PUT', url, **kwargs)

    def delete(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request.

        Args:
            url: Request URL (can be relative to base_url)
            **kwargs: Additional arguments passed to requests

        Returns:
            Parsed JSON response

        Raises:
            ZymmrAPIError: For various API errors
        """
        return self._request('DELETE', url, **kwargs)

    def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments

        Returns:
            Parsed JSON response

        Raises:
            Various ZymmrAPIError subclasses based on response
        """
        # Ensure we're authenticated
        if not self.auth.is_authenticated:
            raise ZymmrAuthenticationError("Client is not authenticated")

        # Build full URL if relative
        if not url.startswith('http'):
            url = f"{self.auth.base_url}{url}"

        # Set default timeout
        kwargs.setdefault('timeout', self.timeout)

        # Log request if debug enabled
        self._log_request(method, url, **kwargs)

        try:
            # Make the request
            response = self.auth.session.request(method, url, **kwargs)

            # Log response if debug enabled
            self._log_response(response)

            # Handle HTTP errors
            self._handle_response_errors(response)

            # Parse JSON response
            try:
                return response.json()
            except ValueError:
                # If response is not JSON, return empty dict
                return {}

        except requests.exceptions.ConnectTimeout:
            raise ZymmrTimeoutError(
                f"Connection timeout after {self.timeout} seconds")
        except requests.exceptions.ReadTimeout:
            raise ZymmrTimeoutError(
                f"Read timeout after {self.timeout} seconds")
        except requests.exceptions.ConnectionError as e:
            raise ZymmrConnectionError(f"Connection failed: {str(e)}")
        except (ZymmrAPIError, ZymmrAuthenticationError, ZymmrPermissionError,
                ZymmrNotFoundError, ZymmrValidationError, ZymmrServerError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Handle unexpected errors
            raise ZymmrAPIError(f"Unexpected error: {str(e)}")
