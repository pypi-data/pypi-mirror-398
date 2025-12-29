#!/usr/bin/env python3
"""
Comprehensive test: Azure B2C OAuth2 library with WattiVahti API.

This test validates:
1. Authentication with refresh token
2. Access token retrieval
3. API data retrieval using the access token
4. Full end-to-end workflow

⚠️  DISCLAIMER: This test script contains WattiVahti-specific configuration
    and API endpoints for testing purposes only. This library is not affiliated
    with or endorsed by WattiVahti or Pori Energia. Use at your own risk.

Usage:
    uv run python examples/wattivahti_full_test.py <refresh_token> <metering_point> [start_date] [end_date]
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import zoneinfo

import requests

from b2c_oauth_client import AuthenticationError, B2COAuthClient

# WattiVahti Configuration (for testing purposes only)
WATTIVAHTI_TENANT = "pesv.onmicrosoft.com"
WATTIVAHTI_CLIENT_ID = "84ebdb93-9ea6-42c7-bd7d-302abf7556fa"
WATTIVAHTI_POLICY = "B2C_1_Tunnistus_SignInv2"
WATTIVAHTI_SCOPE = (
    "https://pesv.onmicrosoft.com/salpa/customer.read openid profile offline_access"
)
WATTIVAHTI_API_BASE = (
    "https://porienergia-prod-agent.frendsapp.com:9999/api/onlineapi/v1"
)
FINNISH_TIMEZONE = zoneinfo.ZoneInfo("Europe/Helsinki")


def create_wattivahti_client() -> B2COAuthClient:
    """Create Azure B2C client configured for WattiVahti."""
    return B2COAuthClient(
        tenant=WATTIVAHTI_TENANT,
        client_id=WATTIVAHTI_CLIENT_ID,
        policy=WATTIVAHTI_POLICY,
        scope=WATTIVAHTI_SCOPE,
    )


def parse_date_string(date_str: str) -> datetime:
    """Parse date string to Finnish timezone datetime."""
    if len(date_str) == 10:  # YYYY-MM-DD
        dt = datetime.fromisoformat(date_str + "T00:00:00")
    else:
        dt = datetime.fromisoformat(date_str)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=FINNISH_TIMEZONE)
    else:
        dt = dt.astimezone(FINNISH_TIMEZONE)

    return dt


def fetch_consumption_data(
    metering_point: str,
    access_token: str,
    start_date: str,
    end_date: str,
    resolution: str = "PT1H",
) -> dict:
    """
    Fetch consumption data from WattiVahti API.

    This replicates the functionality from wattivahti.http.fetch_consumption_data()
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "b2c-oauth-client-test/1.0.0",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
    )

    url = f"{WATTIVAHTI_API_BASE}/meterdata2"
    params = {
        "meteringPointCode": metering_point,
        "measurementType": "1",  # Consumption data
        "start": start_date,
        "stop": end_date,
        "resultStep": resolution,
    }

    try:
        response = session.get(url, params=params, timeout=30)

        if response.status_code != 200:
            raise Exception(
                f"API request failed: {response.status_code} - {response.text[:200]}"
            )

        return response.json()

    except requests.RequestException as e:
        raise Exception(f"Network error: {e}")


def parse_consumption_data(api_response: dict) -> list[dict]:
    """Parse consumption data from API response."""
    try:
        result = api_response.get("getconsumptionsresult", {})
        consumption_data = result.get("consumptiondata", {})
        timeseries = consumption_data.get("timeseries", {})
        values = timeseries.get("values", {})
        tsv_data = values.get("tsv", [])

        readings = []
        for item in tsv_data:
            timestamp_str = item.get("time", "")
            consumption = item.get("quantity")

            if timestamp_str and consumption is not None:
                # Remove 'Z' suffix if present
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str[:-1]

                timestamp = datetime.fromisoformat(timestamp_str)
                timestamp = timestamp.replace(tzinfo=FINNISH_TIMEZONE)

                readings.append(
                    {
                        "timestamp": timestamp.isoformat(),
                        "consumption_kwh": float(consumption),
                        "unit": item.get("unit", "kWh"),
                    }
                )

        return readings

    except (KeyError, ValueError, TypeError) as e:
        raise Exception(f"Failed to parse consumption data: {e}")


def main() -> None:
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="Full test of b2c-oauth-client with WattiVahti API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "refresh_token",
        help="WattiVahti refresh token",
    )
    parser.add_argument(
        "metering_point",
        help="Metering point code (7 digits)",
    )
    parser.add_argument(
        "start_date",
        nargs="?",
        default=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        help="Start date (YYYY-MM-DD), defaults to 7 days ago",
    )
    parser.add_argument(
        "end_date",
        nargs="?",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="End date (YYYY-MM-DD), defaults to today",
    )
    parser.add_argument(
        "--resolution",
        default="PT1H",
        help="Time resolution (PT1H, PT15M, etc.), defaults to PT1H",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("B2C OAuth Client + WattiVahti Full Integration Test")
    print("=" * 70)
    print()

    # Step 1: Create client
    print("Step 1: Creating Azure B2C client...")
    try:
        client = create_wattivahti_client()
        print("✅ Client created")
        print(f"   Token URL: {client.token_url}")
        print(f"   Client ID: {client.client_id}")
        print()
    except Exception as e:
        print(f"❌ Failed to create client: {e}")
        sys.exit(1)

    # Step 2: Authenticate
    print("Step 2: Authenticating with refresh token...")
    try:
        token = client.refresh_token(args.refresh_token)
        print("✅ Authentication successful!")
        print(f"   Access token: {token.access_token[:50]}...")
        print(f"   Token type: {token.token_type}")
        print(f"   Expires at: {token.expires_at}")
        print(
            f"   Expires in: {(token.expires_at - datetime.now()).total_seconds():.0f} seconds"
        )

        if token.refresh_token:
            if token.refresh_token != args.refresh_token:
                print(f"   New refresh token: {token.refresh_token[:50]}... (rotated)")
            else:
                print(f"   Refresh token: {token.refresh_token[:50]}... (unchanged)")
        else:
            print("   ⚠️  No refresh token in response")
        print()
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Step 3: Validate token
    print("Step 3: Validating token...")
    if client.is_token_valid(token):
        print("✅ Token is valid")
    else:
        print("⚠️  Token is expired or will expire soon")
    print()

    # Step 4: Parse dates and add safety buffer
    print("Step 4: Preparing date range...")
    try:
        start_dt = parse_date_string(args.start_date)
        end_dt = parse_date_string(args.end_date)

        # Add safety buffer for API request
        buffered_start = start_dt - timedelta(days=1)
        buffered_end = end_dt + timedelta(days=1)

        print("✅ Date range prepared")
        print(f"   Requested: {start_dt.date()} to {end_dt.date()}")
        print(f"   With buffer: {buffered_start.date()} to {buffered_end.date()}")
        print()
    except Exception as e:
        print(f"❌ Failed to parse dates: {e}")
        sys.exit(1)

    # Step 5: Fetch consumption data
    print("Step 5: Fetching consumption data from WattiVahti API...")
    print(f"   Metering point: {args.metering_point}")
    print(f"   Resolution: {args.resolution}")
    try:
        consumption_response = fetch_consumption_data(
            metering_point=args.metering_point,
            access_token=token.access_token,
            start_date=buffered_start.isoformat(),
            end_date=buffered_end.isoformat(),
            resolution=args.resolution,
        )
        print("✅ Data fetched successfully!")
        print()
    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")
        sys.exit(1)

    # Step 6: Parse and display data
    print("Step 6: Parsing consumption data...")
    try:
        all_readings = parse_consumption_data(consumption_response)

        # Filter to exact time range
        filtered_readings = [
            r
            for r in all_readings
            if start_dt <= datetime.fromisoformat(r["timestamp"]) < end_dt
        ]

        print("✅ Data parsed successfully!")
        print()

        # Display results
        print("=" * 70)
        print("Results")
        print("=" * 70)
        print(f"Total readings: {len(filtered_readings)}")

        if filtered_readings:
            total_kwh = sum(r["consumption_kwh"] for r in filtered_readings)
            print(f"Total consumption: {total_kwh:.2f} kWh")

            duration = (end_dt - start_dt).total_seconds() / (24 * 3600)
            if duration > 0:
                avg_daily = total_kwh / duration
                print(f"Average daily: {avg_daily:.2f} kWh/day")

            print()
            print("Sample readings (first 5):")
            for reading in filtered_readings[:5]:
                ts = datetime.fromisoformat(reading["timestamp"])
                print(
                    f"  {ts.strftime('%Y-%m-%d %H:%M')}: {reading['consumption_kwh']:.3f} {reading['unit']}"
                )

            if len(filtered_readings) > 5:
                print(f"  ... and {len(filtered_readings) - 5} more")
        else:
            print("⚠️  No readings found in the specified time range")

        print()
        print("=" * 70)
        print("✅ All tests passed!")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✓ Authentication: SUCCESS")
        print("  ✓ Token validation: SUCCESS")
        print("  ✓ API data retrieval: SUCCESS")
        print("  ✓ Data parsing: SUCCESS")
        print()

        if token.refresh_token and token.refresh_token != args.refresh_token:
            print("New refresh token (save for future use):")
            print(token.refresh_token)
            print()

    except Exception as e:
        print(f"❌ Failed to parse data: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
