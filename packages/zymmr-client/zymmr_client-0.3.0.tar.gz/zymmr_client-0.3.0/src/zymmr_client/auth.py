"""Authentication module for Zymmr API client.

Handles Frappe Framework's session-based authentication using username/password
credentials. The authentication flow follows Frappe's standard login process.
"""

from typing import Optional
import requests
from .exceptions import ZymmrAuthenticationError, ZymmrConnectionError


class FrappeAuth:
    """Handles Frappe Framework authentication with username/password.

    This class manages the authentication lifecycle including:
    - Initial login with credentials
    - Session verification
    - Session persistence via cookies
    - Logout functionality
    """

    def __init__(self, base_url: str, username: str, password: str):
        """Initialize authentication handler.

        Args:
            base_url: Base URL of the Frappe application (e.g., 'https://yourdomain.zymmr.com')
            username: Username for authentication
            password: Password for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self._session: Optional[requests.Session] = None
        self._is_authenticated = False

    @property
    def session(self) -> requests.Session:
        """Get the authenticated session.

        Returns:
            Authenticated requests session with valid cookies

        Raises:
            ZymmrAuthenticationError: If not authenticated
        """
        if not self._session or not self._is_authenticated:
            raise ZymmrAuthenticationError(
                "Not authenticated. Call authenticate() first.")
        return self._session

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._is_authenticated

    def authenticate(self) -> None:
        """Perform authentication with Frappe server.

        This method:
        1. Creates a new session
        2. Calls Frappe's login endpoint
        3. Verifies the session is valid
        4. Stores session for future requests

        Raises:
            ZymmrAuthenticationError: If login fails or credentials are invalid
            ZymmrConnectionError: If unable to connect to server
        """
        try:
            # Create new session
            self._session = requests.Session()

            # Set proper headers
            self._session.headers.update({
                'User-Agent': 'zymmr-client-python',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            })

            # Perform login
            login_url = f"{self.base_url}/api/method/login"
            login_data = {
                'usr': self.username,
                'pwd': self.password
            }

            response = self._session.post(
                login_url, data=login_data, timeout=30)

            # Check if login request was successful
            if response.status_code != 200:
                error_msg = f"Login failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        error_msg = error_data['message']
                except:
                    pass
                raise ZymmrAuthenticationError(
                    error_msg,
                    status_code=response.status_code,
                    response_data=response.text
                )

            self._is_authenticated = True

        except requests.exceptions.ConnectTimeout:
            raise ZymmrConnectionError(
                f"Connection timeout while connecting to {self.base_url}")
        except requests.exceptions.ConnectionError as e:
            raise ZymmrConnectionError(
                f"Failed to connect to {self.base_url}: {str(e)}")
        except ZymmrAuthenticationError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            raise ZymmrAuthenticationError(
                f"Unexpected error during authentication: {str(e)}")

    def logout(self) -> None:
        """Logout from Frappe server and clear session.

        This method calls Frappe's logout endpoint and clears the local session.
        """
        if self._session and self._is_authenticated:
            try:
                logout_url = f"{self.base_url}/api/method/logout"
                self._session.post(logout_url, timeout=10)
            except:
                # Ignore errors during logout, just clear local session
                pass
            finally:
                self._session.close()
                self._session = None
                self._is_authenticated = False

    def __enter__(self):
        """Context manager entry - authenticate on enter."""
        self.authenticate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - logout on exit."""
        self.logout()
