"""
Deployment module for PAB - Main deployment operations
"""

import os
import time

from .http_client import APCloudyClient
from .package import PackageManager
from .validator import SpiderValidator
from .exceptions import DeploymentError
from .utils import print_info, print_error


class DeployManager:
    """
    Main deployment manager that handles all deployment operations

    This class provides a unified interface for:
    - Package creation and management
    - HTTP API operations via APCloudyClient
    """

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.http_client = APCloudyClient(config_manager)
        self.package_manager = PackageManager()

    def deploy(self, project_id, target_dir='.'):
        """
        Deploy spider to APCloudy

        Args:
            project_id (str): Project ID
            target_dir (str): Directory containing the spider project

        Returns:
            str: Deployment ID
        """
        # Validate spider project before deployment
        validator = SpiderValidator(target_dir)
        validator.validate_project()

        print_info("Creating deployment package...")
        version = self.package_manager.generate_version()
        package_path = self.package_manager.create_deployment_package(target_dir)

        # Validate package size
        package_size = os.path.getsize(package_path)
        if package_size == 0:
            raise DeploymentError("Package file is empty (0 bytes). Please check your project structure.")
        
        print_info(f"Package created: {package_size} bytes")

        try:
            print_info("Uploading package to APCloudy...")

            with open(package_path, 'rb') as package_file:
                result = self.http_client.upload_deployment(project_id, version, package_file)

            deployment_id = result.get('deployment_id')
            if deployment_id:
                # Wait for deployment to complete
                self._wait_for_deployment(deployment_id)
                return deployment_id
            else:
                raise DeploymentError("No deployment ID returned from server")

        finally:
            # Clean up temporary package file
            if os.path.exists(package_path):
                os.unlink(package_path)

    def _wait_for_deployment(self, deployment_id, timeout=300):
        """
        Wait for deployment to complete

        Args:
            deployment_id (str): Deployment ID to monitor
            timeout (int): Timeout in seconds
        """
        start_time = time.time()
        last_log_length = 0

        while time.time() - start_time < timeout:
            try:
                status_data = self.http_client.get_deployment_status(deployment_id)
                status = status_data.get('status')

                if status == 'success':
                    print("")
                    return

                elif status == 'building':
                    build_log = status_data.get('build_log', '.')

                    if build_log and build_log.strip():
                        if len(build_log) > last_log_length:
                            new_logs = build_log[last_log_length:]
                            print_info(new_logs, end='')
                            last_log_length = len(build_log)

                    time.sleep(2)

                elif status == 'failed':
                    print("")
                    raise DeploymentError(str(status_data.get('error')))

            except DeploymentError:
                raise
            except Exception as e:
                print_error(f"Error checking deployment status: {str(e)}")
                time.sleep(5)

        raise DeploymentError("Deployment timeout - please check the APCloudy dashboard")
