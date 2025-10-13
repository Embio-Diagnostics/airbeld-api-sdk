#!/usr/bin/env python3
"""Quickstart example for the Airbeld API SDK.

This example demonstrates basic SDK usage: listing devices and fetching
recent telemetry readings.

Usage:
    export AIRBELD_API_BASE="https://api.airbeld.com"
    export AIRBELD_API_TOKEN="your-jwt-token-here"
    python examples/quickstart.py
"""

import asyncio
import os

from airbeld import AirbeldClient


async def main():
    """Example usage of the Airbeld API SDK."""
    # Get configuration from environment variables
    base_url = os.environ.get("AIRBELD_API_BASE", "https://api.airbeld.com")
    token = os.environ.get("AIRBELD_API_TOKEN")
    if not token:
        print("Error: AIRBELD_API_TOKEN environment variable is required")
        return

    print(f"Connecting to {base_url}...")

    async with AirbeldClient(token=token, base_url=base_url) as client:
        try:
            # Get all devices (non-paginated array)
            devices = await client.async_get_devices()
            print(f"Found {len(devices)} devices:")

            # Print each device's id and display_name
            for device in devices:
                display_name = device.display_name or device.name
                print(f"  - {device.id}: {display_name}")

            if not devices:
                print("No devices found.")
                return

            # Use the first device for telemetry example
            device = devices[0]
            print(f"\nFetching readings for device: {device.name} (ID: {device.id})")

            # Get latest readings (no date range specified)
            readings = await client.async_get_readings_by_date(
                device_id=device.id,
                sensor="temperature",  # Focus on temperature only
            )

            # Print latest temperature value if available
            if "temperature" in readings.sensors:
                temp_metric = readings.sensors["temperature"]
                if temp_metric.values:
                    latest_temp = readings.get_latest_value("temperature")
                    print(f"Latest temperature: {latest_temp}°C")
                else:
                    print("No temperature readings in the specified time range")
            else:
                print("Temperature sensor not available for this device")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
