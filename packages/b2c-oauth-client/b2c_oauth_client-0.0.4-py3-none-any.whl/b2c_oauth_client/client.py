"""
B2C OAuth client for refresh token authentication.
"""

from datetime import datetime, timedelta
from typing import Any

import requests

from .exceptions import AuthenticationError, ConfigurationError
from .models import AuthToken


class B2COAuthClient:
    """
    Client for Azure B2C OAuth2 refresh token authentication.

    This client handles the refresh token flow for Azure B2C, allowing you to
    exchange a refresh token for a new access token and optionally a new refresh token.

    Example:
        >>> client = B2COAuthClient(
        ...     tenant="your-tenant.onmicrosoft.com",
        ...     client_id="your-client-id",
        ...     policy="B2C_1_YourPolicy",
        ...     scope="https://your-tenant.onmicrosoft.com/your-api/your.scope openid profile offline_access"
        ... )
        >>> token = client.refresh_token("your_refresh_token")
        >>> print(f"Access token expires at: {token.expires_at}")
    """

    def __init__(
        self,
        tenant: str,
        client_id: str,
        policy: str,
        scope: str,
        base_url: str | None = None,
    ):
        """
        Initialize Azure B2C OAuth2 client.

        Args:
            tenant: Azure B2C tenant name (e.g., "your-tenant.onmicrosoft.com")
            client_id: Application (client) ID from Azure B2C
            policy: B2C policy name (e.g., "B2C_1_YourPolicy")
            scope: Space-separated list of scopes to request
            base_url: Optional base URL for B2C login (defaults to tenant.b2clogin.com)

        Raises:
            ConfigurationError: If required parameters are missing or invalid
        """
        if not tenant:
            raise ConfigurationError("tenant is required")
        if not client_id:
            raise ConfigurationError("client_id is required")
        if not policy:
            raise ConfigurationError("policy is required")
        if not scope:
            raise ConfigurationError("scope is required")

        self.tenant = tenant
        self.client_id = client_id
        self.policy = policy
        self.scope = scope

        # Construct token URL
        if base_url:
            b2c_base = base_url.rstrip("/")
        else:
            # Extract tenant name without .onmicrosoft.com if present
            tenant_name = tenant.replace(".onmicrosoft.com", "")
            b2c_base = f"https://{tenant_name}.b2clogin.com"

        # Azure B2C URLs use lowercase policy names in the path
        # Policy parameter can be mixed case, but URL path should be lowercase
        policy_lower = policy.lower()
        self.token_url = f"{b2c_base}/{tenant}/{policy_lower}/oauth2/v2.0/token"

    def refresh_token(
        self, refresh_token: str, session: requests.Session | None = None
    ) -> AuthToken:
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token: The refresh token to use for authentication
            session: Optional requests session for connection pooling

        Returns:
            AuthToken object containing access token, refresh token, and expiration

        Raises:
            AuthenticationError: If token refresh fails

        Example:
            >>> client = B2COAuthClient(...)
            >>> token = client.refresh_token("your_refresh_token")
            >>> # Use token.access_token for API calls
            >>> # Save token.refresh_token for future use
        """
        if not refresh_token:
            raise AuthenticationError("refresh_token is required")

        if session is None:
            session = requests.Session()

        try:
            request_data = self._create_refresh_request_data(refresh_token)
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            response = session.post(
                self.token_url, data=request_data, headers=headers, timeout=30
            )

            if response.status_code != 200:
                error_text = response.text
                try:
                    error_json = response.json()
                    error_msg = error_json.get(
                        "error_description", error_json.get("error", error_text)
                    )
                except Exception:
                    error_msg = error_text

                raise AuthenticationError(
                    f"Token refresh failed: {response.status_code} - {error_msg}"
                )

            return self._parse_token_response(response.json())

        except requests.RequestException as e:
            raise AuthenticationError(f"Network error during token refresh: {e}")
        except KeyError as e:
            raise AuthenticationError(f"Invalid token response format: missing {e}")

    def _create_refresh_request_data(self, refresh_token: str) -> dict[str, str]:
        """Create request data for token refresh."""
        return {
            "client_id": self.client_id,
            "scope": self.scope,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_info": "1",  # Request client info for refresh token rotation
        }

    def _parse_token_response(self, response_data: dict[str, Any]) -> AuthToken:
        """Parse API response into AuthToken."""
        expires_in = response_data.get("expires_in", 3600)
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        return AuthToken(
            access_token=response_data["access_token"],
            refresh_token=response_data.get("refresh_token"),
            expires_at=expires_at,
            token_type=response_data.get("token_type", "Bearer"),
        )

    def is_token_valid(self, token: AuthToken, buffer_minutes: int = 5) -> bool:
        """
        Check if a token is still valid (not expired).

        Args:
            token: The AuthToken to check
            buffer_minutes: Consider token invalid if it expires within this many minutes

        Returns:
            True if token is valid, False otherwise
        """
        return datetime.now() < token.expires_at - timedelta(minutes=buffer_minutes)
