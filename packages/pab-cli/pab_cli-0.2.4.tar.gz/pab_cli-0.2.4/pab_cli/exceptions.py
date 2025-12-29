"""
Custom exceptions for PAB
"""


class PABError(Exception):
    """Base exception for PAB"""
    pass


class AuthenticationError(PABError):
    """Raised when authentication fails"""
    pass


class APIError(PABError):
    """Raised when API requests fail"""
    pass


class DeploymentError(PABError):
    """Raised when deployment fails"""
    pass


class ConfigurationError(PABError):
    """Raised when configuration is invalid or missing"""
    pass
