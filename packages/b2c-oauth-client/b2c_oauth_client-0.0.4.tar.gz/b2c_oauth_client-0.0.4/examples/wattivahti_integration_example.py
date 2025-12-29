#!/usr/bin/env python3
"""
Example: How WattiVahti project would use b2c-oauth-client library.

This shows how the WattiVahti project could refactor to use the generic
b2c-oauth-client library instead of custom authentication code.

⚠️  DISCLAIMER: This example contains WattiVahti-specific configuration for
    demonstration purposes only. This library is not affiliated with or
    endorsed by WattiVahti or Pori Energia. Use at your own risk.
"""

from b2c_oauth_client import AuthenticationError, B2COAuthClient

# WattiVahti-specific configuration (for example purposes only)
WATTIVAHTI_TENANT = "pesv.onmicrosoft.com"
WATTIVAHTI_CLIENT_ID = "84ebdb93-9ea6-42c7-bd7d-302abf7556fa"
WATTIVAHTI_POLICY = "B2C_1_Tunnistus_SignInv2"
WATTIVAHTI_SCOPE = (
    "https://pesv.onmicrosoft.com/salpa/customer.read openid profile offline_access"
)


def create_wattivahti_client() -> B2COAuthClient:
    """Create Azure B2C client configured for WattiVahti."""
    return B2COAuthClient(
        tenant=WATTIVAHTI_TENANT,
        client_id=WATTIVAHTI_CLIENT_ID,
        policy=WATTIVAHTI_POLICY,
        scope=WATTIVAHTI_SCOPE,
    )


def refresh_wattivahti_token(refresh_token: str) -> str:
    """
    Refresh WattiVahti token and return new refresh token.

    This function replaces the old wattivahti.refresh_token() function.

    Args:
        refresh_token: Current refresh token

    Returns:
        New refresh token (may be the same or different)

    Raises:
        AuthenticationError: If token refresh fails
    """
    client = create_wattivahti_client()

    try:
        token = client.refresh_token(refresh_token)

        if not token.refresh_token:
            raise AuthenticationError("No refresh token returned from server")

        return token.refresh_token

    except AuthenticationError as e:
        raise AuthenticationError(f"WattiVahti token refresh failed: {e}")


def get_wattivahti_access_token(refresh_token: str) -> str:
    """
    Get access token for WattiVahti API calls.

    This function replaces the old wattivahti.auth.fetch_token() function.

    Args:
        refresh_token: Valid refresh token

    Returns:
        Access token string

    Raises:
        AuthenticationError: If authentication fails
    """
    client = create_wattivahti_client()

    try:
        token = client.refresh_token(refresh_token)
        return token.access_token

    except AuthenticationError as e:
        raise AuthenticationError(f"WattiVahti authentication failed: {e}")


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python wattivahti_integration_example.py <refresh_token>")
        sys.exit(1)

    refresh_token = sys.argv[1]

    print("Testing WattiVahti integration with b2c-oauth-client...")
    print()

    try:
        # Get access token
        access_token = get_wattivahti_access_token(refresh_token)
        print(f"✅ Access token obtained: {access_token[:50]}...")

        # Refresh token
        new_refresh_token = refresh_wattivahti_token(refresh_token)
        print(f"✅ New refresh token: {new_refresh_token[:50]}...")

        if new_refresh_token != refresh_token:
            print("   (Token was rotated)")
        else:
            print("   (Same token returned)")

    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print()
        print(
            "Note: If you see 'AADB2C90085' error, the refresh token may have expired."
        )
        print("      Get a fresh token from WattiVahti using browser developer tools.")
        sys.exit(1)
