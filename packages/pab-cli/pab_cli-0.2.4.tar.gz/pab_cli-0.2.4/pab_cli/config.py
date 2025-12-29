"""
Configuration management for PAB
"""

import os
import json
import platform

from .exceptions import ConfigurationError


class ConfigManager:
    """Handles configuration and credential storage"""

    def __init__(self):
        self.config_dir = self._get_config_dir()
        self.config_file = os.path.join(self.config_dir, 'pab_config.json')
        self._ensure_config_dir()

    @staticmethod
    def get_endpoint():
        """
        Get the API endpoint (always returns the static default endpoint)

        Returns:
            str: API endpoint URL
        """
        return 'https://appcloudy.askpablos.com/api/cli'

    @staticmethod
    def _get_config_dir():
        """Get the appropriate configuration directory based on OS"""
        if platform.system() == 'Windows':
            return os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', '.pab')
        else:
            return os.path.join(os.path.expanduser('~'), '.pab')

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, mode=0o700)

    def save_credentials(self, username, access_token, refresh_token, api_key):
        """
        Save user credentials to config file (endpoint is not stored, it's static)

        Args:
            username (str): Username
            access_token (str): JWT access token
            refresh_token (str): JWT refresh token
            api_key (str): Original API key
        """
        config_data = {
            'username': username,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'api_key': api_key
        }

        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

            # Set restrictive permissions on config file
            os.chmod(self.config_file, 0o600)

        except Exception as e:
            raise ConfigurationError(f"Failed to save credentials: {str(e)}")

    def get_credentials(self):
        """
        Get stored credentials

        Returns:
            dict: Credentials dictionary

        Raises:
            ConfigurationError: If credentials are not found or invalid
        """
        if not os.path.exists(self.config_file):
            raise ConfigurationError("No credentials found. Please run 'pab login' first.")

        try:
            with open(self.config_file) as f:
                credentials = json.load(f)

            required_fields = ['username', 'access_token', 'api_key']
            for field in required_fields:
                if field not in credentials:
                    raise ConfigurationError(f"Invalid credentials: missing {field}")

            credentials['endpoint'] = self.get_endpoint()

            return credentials

        except json.JSONDecodeError:
            raise ConfigurationError("Invalid credentials file. Please run 'pab login' again.")
        except Exception as e:
            raise ConfigurationError(f"Failed to read credentials: {str(e)}")

    def update_tokens(self, access_token, refresh_token=None):
        """
        Update stored tokens after refresh

        Args:
            access_token (str): New access token
            refresh_token (str, optional): New refresh token
        """
        try:
            credentials = self.get_credentials()
            credentials['access_token'] = access_token
            if refresh_token:
                credentials['refresh_token'] = refresh_token

            with open(self.config_file, 'w') as f:
                json.dump(credentials, f, indent=2)

            # Set restrictive permissions on config file
            os.chmod(self.config_file, 0o600)

        except Exception as e:
            raise ConfigurationError(f"Failed to update tokens: {str(e)}")

    def refresh_tokens(self):
        """
        Refresh tokens if the access token is expired

        Returns:
            bool: True if tokens were refreshed or are still valid, False if refresh failed
        """
        try:
            from .auth import AuthManager

            credentials = self.get_credentials()
            auth_manager = AuthManager(self.get_endpoint())

            # Check if access token is still valid
            if auth_manager.validate_token(credentials['access_token']):
                return True

            # Try to refresh the token
            if credentials.get('refresh_token'):
                new_tokens = auth_manager.refresh_access_token(credentials['refresh_token'])
                self.update_tokens(
                    new_tokens['access_token'],
                    new_tokens.get('refresh_token')
                )
                return True

            return False

        except Exception:
            return False

    def is_authenticated(self):
        """
        Check if user is authenticated

        Returns:
            bool: True if authenticated, False otherwise
        """
        try:
            self.get_credentials()
            return True
        except ConfigurationError:
            return False

    def clear_credentials(self):
        """Clear stored credentials"""
        if os.path.exists(self.config_file):
            try:
                os.remove(self.config_file)
            except Exception as e:
                raise ConfigurationError(f"Failed to clear credentials: {str(e)}")
