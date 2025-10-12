#!/usr/bin/env python3
"""Example: Standalone authentication and device listing.

This example demonstrates:
1. Reading credentials from environment variables
2. Using async_login() for email/password authentication
3. Creating AirbeldClient with the obtained access token
4. Listing all available devices

Usage:
    export AIRBELD_API_BASE="https://api.airbeld.com"
    export AIRBELD_USER_EMAIL="your-email@example.com"
    export AIRBELD_USER_PASSWORD="your-password"
    python examples/login_and_list.py
"""

import asyncio
import os
import sys

from airbeld import AirbeldClient, async_login
from airbeld.exceptions import AuthError, NetworkError, RateLimitError


async def main():
    """Main example function."""
    # Read configuration from environment
    base_url = os.environ.get("AIRBELD_API_BASE", "https://api.airbeld.com")
    email = os.environ.get("AIRBELD_USER_EMAIL")
    password = os.environ.get("AIRBELD_USER_PASSWORD")

    if not email or not password:
        print("❌ Error: AIRBELD_USER_EMAIL and AIRBELD_USER_PASSWORD must be set")
        print("Example:")
        print("  export AIRBELD_USER_EMAIL='your-email@example.com'")
        print("  export AIRBELD_USER_PASSWORD='your-password'")
        sys.exit(1)

    try:
        print(f"🔐 Authenticating with {base_url}...")

        # Step 1: Authenticate with email/password
        token_set = await async_login(
            base_url=base_url,
            email=email,
            password=password,
            timeout=10.0,
        )

        print("✅ Authentication successful!")
        print(f"   Token type: {token_set.token_type}")
        print(f"   Expires in: {token_set.expires_in} seconds")

        # Step 2: Create client with access token
        async with AirbeldClient(token=token_set.access_token, base_url=base_url) as client:
            print(f"\n📡 Fetching devices from {base_url}...")

            # Step 3: List all devices
            devices = await client.async_get_devices()

            print(f"✅ Found {len(devices)} devices:")

            if not devices:
                print("   (No devices available)")
            else:
                for i, device in enumerate(devices, 1):
                    status_icon = "🟢" if device.status == "online" else "🔴"
                    print(f"   {i}. {device.name} {status_icon}")
                    print(f"      UID: {device.uid}")
                    print(f"      Status: {device.status}")
                    print(f"      Type: {device.type or 'Unknown'}")
                    print(f"      Location: {device.location or 'Not set'}")
                    print()

    except AuthError as e:
        print(f"❌ Authentication failed: {e}")
        print("   Check your email and password")
        sys.exit(1)

    except RateLimitError as e:
        retry_after = f" (retry after {e.retry_after}s)" if e.retry_after else ""
        print(f"❌ Rate limit exceeded: {e}{retry_after}")
        sys.exit(1)

    except NetworkError as e:
        print(f"❌ Network error: {e}")
        print("   Check your internet connection and API base URL")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
