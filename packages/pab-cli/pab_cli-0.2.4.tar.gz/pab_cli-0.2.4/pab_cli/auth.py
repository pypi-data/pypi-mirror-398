"""
Authentication module for PAB
"""
from urllib.parse import urljoin

import requests

from .exceptions import AuthenticationError, APIError
from pab_cli import __version__


class AuthManager:
    """Handles authentication with APCloudy API"""

    def __init__(self, endpoint):
        self.endpoint = endpoint.rstrip('/') + '/'
        self.session = requests.Session()

    def authenticate(self, api_key):
        """
        Authenticate with APCloudy using API key and return user info

        Args:
            api_key (str): APCloudy API key

        Returns:
            dict: User information including username and tokens

        Raises:
            AuthenticationError: If authentication fails
            APIError: If API request fails
        """
        auth_url = urljoin(self.endpoint, 'auth')

        try:
            response = self.session.post(
                auth_url,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": f"pab/{__version__}"
                },
                json={"api_key": api_key},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                # Extract user information from JWT response
                if "access" in data and "username" in data:
                    return {
                        "username": data["username"],
                        "access_token": data["access"],
                        "refresh_token": data.get("refresh", ""),
                        "api_key": api_key
                    }
                else:
                    raise AuthenticationError("Invalid response format from server")

            elif response.status_code == 401:
                raise AuthenticationError("Invalid API key")

            elif response.status_code == 403:
                raise AuthenticationError("API key is disabled or has insufficient permissions")

            else:
                raise APIError(f"Authentication failed with status {response.status_code}")

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during authentication: {str(e)}")

    def validate_token(self, access_token):
        """
        Validate if the access token is still valid

        Args:
            access_token (str): JWT access token to validate

        Returns:
            bool: True if token is valid, False otherwise
        """
        validate_url = urljoin(self.endpoint, 'validate')

        try:
            response = self.session.post(
                validate_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "User-Agent": f"pab/{__version__}"
                },
                timeout=30
            )

            return response.status_code == 200

        except requests.exceptions.RequestException:
            return False

    def refresh_access_token(self, refresh_token):
        """
        Refresh the access token using refresh token

        Args:
            refresh_token (str): JWT refresh token

        Returns:
            dict: New tokens and user info

        Raises:
            AuthenticationError: If refresh fails
            APIError: If API request fails
        """
        refresh_url = urljoin(self.endpoint, 'refresh')

        try:
            response = self.session.post(
                refresh_url,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": f"pab/{__version__}"
                },
                json={"refresh": refresh_token},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if "access" in data:
                    return {
                        "access_token": data["access"],
                        "refresh_token": data.get("refresh", refresh_token),
                        "username": data.get("username", "")
                    }
                else:
                    raise AuthenticationError("No access token in refresh response")

            elif response.status_code == 401:
                raise AuthenticationError("Refresh token is invalid or expired")

            else:
                raise APIError(f"Token refresh failed with status {response.status_code}")

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during token refresh: {str(e)}")
