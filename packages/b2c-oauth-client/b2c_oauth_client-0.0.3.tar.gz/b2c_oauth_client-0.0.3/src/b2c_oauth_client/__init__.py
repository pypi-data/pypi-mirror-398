"""
B2C OAuth Client - Simple Python library for Azure B2C refresh token authentication.

This library provides a clean, simple interface for authenticating with Azure B2C
using refresh tokens. It's designed to be lightweight and focused on the core
authentication flow.

This is an independent, open-source library. It is not affiliated with, endorsed by,
or connected to Microsoft Corporation or any specific Azure B2C tenant.

Basic usage:
    >>> from b2c_oauth_client import B2COAuthClient, AuthenticationError
    >>>
    >>> client = B2COAuthClient(
    ...     tenant="your-tenant.onmicrosoft.com",
    ...     client_id="your-client-id",
    ...     policy="B2C_1_YourPolicy",
    ...     scope="https://your-tenant.onmicrosoft.com/your-api/your.scope openid profile offline_access"
    ... )
    >>>
    >>> try:
    ...     token = client.refresh_token("your_refresh_token")
    ...     print(f"Access token: {token.access_token[:50]}...")
    ...     print(f"New refresh token: {token.refresh_token[:50] if token.refresh_token else 'None'}...")
    ... except AuthenticationError as e:
    ...     print(f"Authentication failed: {e}")
"""

from .client import B2COAuthClient
from .exceptions import AuthenticationError, B2COAuthError
from .models import AuthToken

__version__ = "0.1.0"

__all__ = [
    "B2COAuthClient",
    "AuthToken",
    "AuthenticationError",
    "B2COAuthError",
]
