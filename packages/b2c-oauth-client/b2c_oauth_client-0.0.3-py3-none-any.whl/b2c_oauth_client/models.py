"""
Data models for Azure B2C OAuth2 library.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AuthToken:
    """Authentication token information."""

    access_token: str
    refresh_token: str | None
    expires_at: datetime
    token_type: str = "Bearer"
