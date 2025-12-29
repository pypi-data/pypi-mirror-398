"""
PAB - APCloudy Deployment Tool for Scrapy Spiders

A command-line tool for deploying and managing Scrapy spiders on APCloudy platform.
"""

__author__ = "Fawad Ali"
__email__ = "Fawadstar6@gmail.com"
__license__ = "MIT"
__description__ = "A command-line tool for deploying Scrapy spiders to APCloudy"
__url__ = "https://github.com/fawadss1/pab"
__version__ = "0.2.4"

from .auth import AuthManager
from .deploy import DeployManager
from .config import ConfigManager
from .cli import main
from .package import PackageManager
from .http_client import APCloudyClient
from .exceptions import (
    PABError,
    AuthenticationError,
    DeploymentError,
    APIError,
    ConfigurationError
)

# Public API - what users can import from 'pab'
__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__description__",
    "__url__",
    "AuthManager",
    "DeployManager",
    "ConfigManager",
    "PackageManager",
    "APCloudyClient",
    "main",
    "PABError",
    "AuthenticationError",
    "DeploymentError",
    "APIError",
    "ConfigurationError",
]
