#!/usr/bin/env python3
"""Example: Get historical telemetry readings for a date range.

This example demonstrates fetching sensor readings for a specific date range
with hourly aggregation.

Usage:
    export AIRBELD_API_BASE="https://api.airbeld.com"
    export AIRBELD_API_TOKEN="your-jwt-token-here"
    python examples/get_historical_readings.py
"""

import asyncio
import os

from airbeld import AirbeldClient


async def main():
    """Example: Fetch historical sensor readings for a date range."""
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
            print(
                f"\nFetching historical readings for: {display_name} (ID: {device.id})"
            )

            # Get readings for a specific date range with hourly aggregation
            # Date format: 'YYYY-MM-DD' or 'today'
            readings = await client.async_get_readings_by_date(
                device_id=device.id,
                start_date="2025-09-19",  # Start date
                end_date="2025-09-19",  # End date (same day for 24 hours)
                period="hour",  # Hourly aggregation
                # sensor="temperature"    # Optional: filter to single sensor
            )

            # Display all readings for each sensor
            print("\nHistorical readings from 2025-09-19:")
            for metric in readings.sensors.values():
                print(f"\n{metric.display_name} ({metric.unit}):")
                print(f"  Total readings: {len(metric.values)}")

                if metric.values:
                    # Show first few and last few values
                    print(
                        f"  First reading: {metric.values[0].timestamp} = {metric.values[0].value}"
                    )
                    if len(metric.values) > 1:
                        print(
                            f"  Last reading:  {metric.values[-1].timestamp} = {metric.values[-1].value}"
                        )

                    # Calculate some statistics
                    values_only = [
                        v.value for v in metric.values if v.value is not None
                    ]
                    if values_only:
                        avg = sum(values_only) / len(values_only)
                        print(f"  Average: {avg:.2f} {metric.unit}")
                        print(
                            f"  Min: {min(values_only):.2f}, Max: {max(values_only):.2f}"
                        )
                else:
                    print("  No data available")

            # Example: Access all temperature values
            if "temperature" in readings.sensors:
                temp_metric = readings.sensors["temperature"]
                print(f"\nAll temperature readings ({len(temp_metric.values)} values):")
                for reading in temp_metric.values[:5]:  # Show first 5
                    print(f"  {reading.timestamp}: {reading.value}°C")
                if len(temp_metric.values) > 5:
                    print(f"  ... ({len(temp_metric.values) - 5} more readings)")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
