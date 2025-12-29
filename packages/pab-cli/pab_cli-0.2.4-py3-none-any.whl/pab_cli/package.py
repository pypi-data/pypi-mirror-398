"""
Package creation module for PAB
"""

import os
import tarfile
from datetime import datetime
from .exceptions import DeploymentError


class PackageManager:
    """Handles package creation for spider deployments"""

    @staticmethod
    def generate_version():
        """
        Generate a version string based on current timestamp

        Returns:
            str: Version string
        """
        return datetime.now().strftime('%Y%m%d%H%M%S')

    @staticmethod
    def create_deployment_package(target_dir):
        """
        Create a tar.gz package of the Scrapy project and store it in pab_build directory

        Args:
            target_dir (str): Directory containing the Scrapy project

        Returns:
            str: Path to the created package in pab_build directory within the target project
        """
        if not os.path.exists(target_dir):
            raise DeploymentError(f"Target directory '{target_dir}' does not exist")

        # Check if it's a Scrapy project (should have scrapy.cfg)
        if not os.path.exists(os.path.join(target_dir, 'scrapy.cfg')):
            raise DeploymentError(f"Directory '{target_dir}' doesn't appear to be a Scrapy project (no scrapy.cfg found)")

        # Create pab_build directory within the target project directory
        build_dir = os.path.join(target_dir, 'pab_build')
        os.makedirs(build_dir, exist_ok=True)

        # Generate filename using timestamp
        version = PackageManager.generate_version()
        project_name = os.path.basename(os.path.abspath(target_dir))
        package_filename = f"{project_name}-{version}.tar.gz"
        package_path = os.path.join(build_dir, package_filename)

        # Define Scrapy project files and directories to include
        scrapy_files = [
            'scrapy.cfg',
            'setup.py',
            'requirements.txt',
            'pyproject.toml',
            'README.md',
        ]

        # Identify project module from scrapy.cfg
        project_module = None
        try:
            with open(os.path.join(target_dir, 'scrapy.cfg')) as cfg:
                for line in cfg:
                    if line.strip().startswith('project ='):
                        project_module = line.strip().split('=')[1].strip()
                        break
        except Exception as e:
            raise DeploymentError(f"Failed to parse scrapy.cfg: {str(e)}")

        if not project_module:
            raise DeploymentError("Could not determine project module from scrapy.cfg")

        try:
            with tarfile.open(package_path, 'w:gz') as tar:
                # Add scrapy.cfg and other top-level files
                for filename in scrapy_files:
                    file_path = os.path.join(target_dir, filename)
                    if os.path.exists(file_path):
                        tar.add(file_path, arcname=os.path.basename(file_path))

                # Add the project module directory
                module_dir = os.path.join(target_dir, project_module)
                if os.path.exists(module_dir):
                    for root, dirs, files in os.walk(module_dir):
                        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'venv', '.venv', 'pab_build']]

                        for file in files:
                            if file.endswith(('.pyc', '.pyo', '.DS_Store')):
                                continue

                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, target_dir)
                            tar.add(file_path, arcname=arcname)

            return package_path

        except Exception as e:
            if os.path.exists(package_path):
                os.unlink(package_path)
            raise DeploymentError(f"Failed to create deployment package: {str(e)}")
