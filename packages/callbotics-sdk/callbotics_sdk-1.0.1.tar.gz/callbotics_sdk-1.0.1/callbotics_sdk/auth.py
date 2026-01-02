"""Authentication handler for Callbotics SDK"""
import requests
from typing import Optional, Dict
from .exceptions import AuthenticationError


class AuthHandler:
    """Handles authentication and token management for Callbotics API"""

    def __init__(self, base_url: str, api_token: Optional[str] = None):
        """
        Initialize authentication handler

        Args:
            base_url: Base URL of Callbotics API
            api_token: Optional pre-authenticated JWT token
        """
        self.base_url = base_url.rstrip("/")
        self._token = api_token
        self._user_info: Optional[Dict] = None

    def login(self, email: str, password: str) -> str:
        """
        Authenticate with email and password

        Args:
            email: User email
            password: User password

        Returns:
            JWT access token

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            response = requests.post(
                f"{self.base_url}/v1/users/login",
                json={"email": email, "password": password},
                timeout=30,
            )

            if response.status_code != 200:
                raise AuthenticationError(
                    f"Login failed: {response.status_code} - {response.text}"
                )

            data = response.json()

            if data.get("status_code") != 200:
                raise AuthenticationError(f"Login failed: {data.get('message', 'Unknown error')}")

            # Extract token from response
            token_data = data.get("data", {})
            self._token = token_data.get("access_token")

            if not self._token:
                raise AuthenticationError("No access token returned from login")

            # Store user info
            self._user_info = {
                "email": email,
                "user_id": token_data.get("user_id"),
                "organisation_id": token_data.get("organisation_id"),
                "role": token_data.get("role_name"),
            }

            return self._token

        except requests.RequestException as e:
            raise AuthenticationError(f"Login request failed: {str(e)}")

    def set_token(self, token: str):
        """
        Manually set authentication token

        Args:
            token: JWT access token
        """
        self._token = token

    def get_token(self) -> Optional[str]:
        """Get current authentication token"""
        return self._token

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests

        Returns:
            Dictionary with Authorization header

        Raises:
            AuthenticationError: If no token is available
        """
        if not self._token:
            raise AuthenticationError("No authentication token available. Please login first.")

        return {"Authorization": f"Bearer {self._token}"}

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self._token is not None

    @property
    def user_info(self) -> Optional[Dict]:
        """Get stored user information"""
        return self._user_info
