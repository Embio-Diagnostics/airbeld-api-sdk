#!/usr/bin/env python3
"""Example: Get latest telemetry readings without specifying date range.

This example demonstrates fetching the most recent sensor readings
without having to calculate date ranges.

Usage:
    export AIRBELD_API_BASE="https://api.airbeld.com"
    export AIRBELD_API_TOKEN="your-jwt-token-here"
    python examples/get_latest_readings.py
"""

import asyncio
import os

from airbeld import AirbeldClient


async def main():
    """Example: Fetch latest sensor readings without date parameters."""
    # Get configuration from environment variables
    base_url = os.environ.get("AIRBELD_API_BASE", "https://api.airbeld.com")
    token = os.environ.get("AIRBELD_API_TOKEN")

    if not token:
        print("Error: AIRBELD_API_TOKEN environment variable is required")
        return

    print(f"Connecting to {base_url}...")

    async with AirbeldClient(token=token, base_url=base_url) as client:
        try:
            # Get all devices
            devices = await client.async_get_devices()
            print(f"Found {len(devices)} devices")

            if not devices:
                print("No devices found.")
                return

            # Use the first device
            device = devices[0]
            display_name = device.display_name or device.name
            print(f"\nFetching latest readings for: {display_name} (ID: {device.id})")

            # Get latest readings without specifying start/end dates
            # This is simpler than calculating time ranges!
            readings = await client.async_get_readings_by_date(
                device_id=device.id,
                # sensor="temperature",  # Optional: filter to single sensor
            )

            # Display latest values for each sensor
            print("\nLatest sensor readings:")
            for sensor_name, metric in readings.sensors.items():
                latest_value = readings.get_latest_value(sensor_name)
                if latest_value is not None:
                    print(f"  {metric.display_name}: {latest_value} {metric.unit}")
                else:
                    print(f"  {metric.display_name}: No data available")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
