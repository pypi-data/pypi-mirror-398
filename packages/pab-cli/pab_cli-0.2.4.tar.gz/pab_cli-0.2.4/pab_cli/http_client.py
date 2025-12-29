"""
HTTP API client module for PAB - APCloudy API operations
"""
from urllib.parse import urljoin

import requests

from .exceptions import APIError
from pab_cli import __version__


class APCloudyClient:
    """HTTP client for APCloudy API operations"""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.credentials = config_manager.get_credentials()
        self.endpoint = self.credentials['endpoint'].rstrip('/') + '/'
        self.session = requests.Session()
        self._update_session_headers()

    def _update_session_headers(self):
        """Update session headers with current access token"""
        self.credentials = self.config_manager.get_credentials()

        self.session.headers.update({
            'Authorization': f'Bearer {self.credentials["access_token"]}',
            'User-Agent': f'pab-cli/{__version__}'
        })

    def _make_authenticated_request(self, method, url, **kwargs):
        """Make an authenticated request with automatic token refresh"""
        # Ensure token is valid before request
        self._update_session_headers()

        response = self.session.request(method, url, **kwargs)

        # If we get 401, try to refresh token once and retry
        if response.status_code == 401:
            if self.config_manager.refresh_tokens():
                self._update_session_headers()
                response = self.session.request(method, url, **kwargs)

        return response

    def list_projects(self):
        """
        List all available projects from APCloudy API

        Returns:
            list: List of project dictionaries

        Raises:
            APIError: If the API request fails
        """
        try:
            url = urljoin(self.endpoint, 'projects')
            response = self._make_authenticated_request('GET', url, timeout=30)

            if response.status_code == 200:
                return response.json().get('projects', [])
            elif response.status_code == 401:
                raise APIError("Authentication failed. Please run 'pab login' again.")
            else:
                raise APIError(f"Failed to list projects: HTTP {response.status_code}")

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error while listing projects: {str(e)}")

    def list_spiders(self, project_id):
        """
        List all spiders in a project from APCloudy API

        Args:
            project_id (str): Project ID

        Returns:
            list: List of spider dictionaries

        Raises:
            APIError: If the API request fails
        """
        try:
            url = urljoin(self.endpoint, 'project/{}/spiders'.format(project_id))
            response = self._make_authenticated_request('GET', url, timeout=30)

            if response.status_code == 200:
                return response.json().get('spiders', [])
            elif response.status_code == 401:
                raise APIError("Authentication failed. Please run 'pab login' again.")
            elif response.status_code == 404:
                raise APIError(f"Project '{project_id}' not found.")
            else:
                raise APIError(f"Failed to list spiders: HTTP {response.status_code}")

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error while listing spiders: {str(e)}")

    def upload_deployment(self, project_id, version, package_file):
        """
        Upload deployment package to APCloudy API

        Args:
            project_id (str): Project ID
            version (str): Version tag
            package_file: File-like object containing the package

        Returns:
            dict: Response data from API

        Raises:
            APIError: If the upload fails
        """
        try:
            # Read file content into memory to handle potential token refresh retries
            # (file pointer would be at EOF after first read during retry)
            file_content = package_file.read()
            
            upload_url = urljoin(self.endpoint, 'project/deploy')
            files = {
                'package': ('spider.tar.gz', file_content, 'application/gzip')
            }
            data = {
                'version': version,
                'project_id': project_id
            }

            response = self._make_authenticated_request(
                'POST',
                upload_url,
                files=files,
                data=data,
                timeout=300
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise APIError("Authentication failed. Please run 'pab login' again.")
            elif response.status_code == 404:
                raise APIError(f"Project '{project_id}' not found.")
            else:
                error_msg = f"Upload failed with HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        error_msg += f": {error_data['message']}"
                except (ValueError, KeyError):
                    pass
                raise APIError(error_msg)

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during upload: {str(e)}")

    def get_deployment_status(self, deployment_id):
        """
        Get deployment status from APCloudy API

        Args:
            deployment_id (str): Deployment ID to check

        Returns:
            dict: Status information

        Raises:
            APIError: If the status check fails
        """
        try:
            status_url = urljoin(self.endpoint, 'deployment/{}/status'.format(deployment_id))
            response = self._make_authenticated_request('GET', status_url, timeout=30)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise APIError("Authentication failed. Please run 'pab login' again.")
            elif response.status_code == 404:
                raise APIError(f"Deployment '{deployment_id}' not found.")
            else:
                raise APIError(f"Failed to get deployment status: HTTP {response.status_code}")

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error while checking deployment status: {str(e)}")
