"""
Custom exceptions for B2C OAuth client library.

Clear, specific exception types for better error handling.
"""


class B2COAuthError(Exception):
    """Base exception for all B2C OAuth errors."""

    pass


class AuthenticationError(B2COAuthError):
    """Raised when authentication fails."""

    pass


class ConfigurationError(B2COAuthError):
    """Raised when configuration is invalid."""

    pass
