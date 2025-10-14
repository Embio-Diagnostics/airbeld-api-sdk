#!/usr/bin/env python3
"""Example: Get telemetry readings for all devices.

This example demonstrates fetching sensor readings for all user devices
in a single API call.

Usage:
    export AIRBELD_API_BASE="https://api.airbeld.com"
    export AIRBELD_API_TOKEN="your-jwt-token-here"
    python examples/get_all_readings.py
"""

import asyncio
import os

from airbeld import AirbeldClient


async def main():
    """Example: Fetch telemetry readings for all user devices."""
    # Get configuration from environment variables
    base_url = os.environ.get("AIRBELD_API_BASE", "https://api.airbeld.com")
    token = os.environ.get(
        "AIRBELD_API_TOKEN",
        "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ilo4ajlCQmdIMDdNY3VpVUZCbWwzaCJ9.eyJodHRwczovL2F1dGguZW1iaW9kaWFnbm9zdGljcy5ldS9lbWFpbCI6ImxhemFyb3NkODlAZ21haWwuY29tIiwiaHR0cHM6Ly9hdXRoLmVtYmlvZGlhZ25vc3RpY3MuZXUvcm9sZXMiOlsic3VwZXJ1c2VyIl0sImFwaS5haXJiZWxkLmNvbS5hdXRoMC5jb20vZW1haWwiOiJsYXphcm9zZDg5QGdtYWlsLmNvbSIsImFwaS5haXJiZWxkLmNvbS5hdXRoMC5jb20vcm9sZXMiOlsic3VwZXJ1c2VyIl0sImFwaS5haXJiZWxkLmNvbS5hdXRoMC5jb20vc3VwZXJ1c2VyIjp0cnVlLCJhcGkuYWlyYmVsZC5jb20uYXV0aDAuY29tL3N0YWZmIjpmYWxzZSwiaXNzIjoiaHR0cHM6Ly9hdXRoLmVtYmlvZGlhZ25vc3RpY3MuZXUvIiwic3ViIjoiYXV0aDB8NjUzYTBjNjE5ZTliYzU2MzEyY2M3NWUzIiwiYXVkIjpbImh0dHBzOi8vYWlyYmVsZC1kcmYvYXBpIiwiaHR0cHM6Ly9lbWJpb2RpYWdub3N0aWNzLmV1LmF1dGgwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE3NjAzNDc0NDUsImV4cCI6MTc2MDQzMzg0NSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBhZGRyZXNzIHBob25lIG9mZmxpbmVfYWNjZXNzIiwiZ3R5IjoicGFzc3dvcmQiLCJhenAiOiJkT0hwZ2FORnl6aUJLNXdnYUFBRFlFQ2JiU0wyY1hxbyJ9.NVDH7EY-EDtgk4LH8qcva-zOBP2L-tbWvfddm63128Fd4-N_kawA9GiZVCPjUTpJNLEGRdbQf1zTb_s8ghj3TaJKZIzQ1xwYGuW3wSpOLrCEekaMTZd1sow_orQLA0EWg5u0X_OaOJSTd3drE-dfIKBS_xhRBYZFTTNTTwbU-KRCmzMTIprgtJY_UG9MJmvKcGgaKUwl0n5VJsbCpDdombcDU8cfohUv7CzD3mo24esrGKil-xmR5wB8LD5-Oe6RWG8A-6Za2dJwj_qD3XoR5oSjE9w8fXEnbMKkik2nkv2TCotgzmnJ3Ocos9AQMQK_-H4RtvQtKV5rfUL6RF60Sw",
    )

    if not token:
        print("Error: AIRBELD_API_TOKEN environment variable is required")
        return

    print(f"Connecting to {base_url}...")

    async with AirbeldClient(token=token, base_url=base_url) as client:
        try:
            # Get latest readings for all devices (no date range)
            print("\nFetching latest readings for all devices...")
            devices = await client.async_get_all_readings_by_date()
            print(f"Found readings for {len(devices)} devices")

            # Display latest values for each device
            for device in devices:
                display_name = device.display_name or device.name
                print(f"\n{display_name} (ID: {device.id})")
                print(f"  Location: {device.location or 'N/A'}")
                print(f"  Sector: {device.sector or 'N/A'}")
                print(f"  Timezone: {device.timezone}")

                if device.sensors:
                    print("  Latest readings:")
                    for sensor_name, metric in device.sensors.items():
                        latest = device.get_latest_value(sensor_name)
                        if latest is not None:
                            print(
                                f"    {metric.display_name or sensor_name}: {latest:.2f} {metric.unit}"
                            )
                else:
                    print("  No sensor data available")

            # Example: Get historical readings with date range
            print("\n" + "=" * 60)
            print("Fetching historical readings with date range...")
            devices = await client.async_get_all_readings_by_date(
                start_date="2025-10-14",
                end_date="2025-10-14",
                period="hour",
            )

            print(f"Found historical data for {len(devices)} devices")

            # Show summary for each device
            for device in devices:
                display_name = device.display_name or device.name
                print(f"\n{display_name}:")
                for sensor_name, metric in device.sensors.items():
                    if metric.values:
                        values_only = [
                            v.value for v in metric.values if v.value is not None
                        ]
                        if values_only:
                            avg = sum(values_only) / len(values_only)
                            print(
                                f"  {metric.display_name or sensor_name}: "
                                f"{len(metric.values)} readings, avg={avg:.2f} {metric.unit}"
                            )

            # Example: Filter to specific sensor across all devices
            print("\n" + "=" * 60)
            print("Fetching only temperature readings for all devices...")
            devices = await client.async_get_all_readings_by_date(sensor="temperature")

            for device in devices:
                display_name = device.display_name or device.name
                temp = device.get_latest_value("temperature")
                if temp is not None:
                    print(f"{display_name}: {temp:.2f}°C")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
