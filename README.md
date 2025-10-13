# Airbeld Python SDK

[![PyPI version](https://badge.fury.io/py/airbeld-api-sdk.svg)](https://pypi.org/project/airbeld-api-sdk/)
[![Python Versions](https://img.shields.io/pypi/pyversions/airbeld-api-sdk.svg)](https://pypi.org/project/airbeld-api-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Async Python SDK for the Airbeld API, providing access to air quality devices and telemetry data.

> If you want to **contribute**, read [CONTRIBUTING](CONTRIBUTING.md) and [DEVELOPER](DEVELOPER.md).

---

## Installation

```bash
# Using pip
pip install airbeld-api-sdk

# Using uv (recommended)
uv add airbeld-api-sdk
```

## Examples

### Running Examples

All examples require setting environment variables before running:

```bash
# Export required environment variables
export AIRBELD_API_BASE="https://api.airbeld.com"
export AIRBELD_API_TOKEN="your-jwt-token-here"

# Run an example
python examples/quickstart.py
```

**Environment Variables:**

- `AIRBELD_API_BASE`: API base URL (default: `https://api.airbeld.com`)
- `AIRBELD_API_TOKEN`: JWT access token for authentication

### Quickstart Example

```python
import asyncio
import os
from datetime import datetime, timedelta, timezone
from airbeld import AirbeldClient

async def main():
    # Initialize client (JWT token obtained outside SDK)
    base_url = os.environ.get("AIRBELD_API_BASE", "https://api.airbeld.com")
    token = os.environ["AIRBELD_API_TOKEN"]
    
    async with AirbeldClient(token=token, base_url=base_url) as client:
        # Get all devices
        devices = await client.async_get_devices()
        print(f"Found {len(devices)} devices")
        
        if devices:
            device = devices[0]
            print(f"Device: {device.name} ({device.status})")
            
            # Get recent telemetry readings
            end = datetime.now(timezone.utc)
            start = end - timedelta(hours=1)
            
            readings = await client.async_get_readings_by_date(
                device_id=device.id,
                start=start,
                end=end,
                sensors=["temperature", "pm2p5"]  # Optional sensor filter
            )
            
            # Print latest temperature reading
            if "temperature" in readings.sensors:
                latest_temp = readings.get_latest_value("temperature")
                print(f"Latest temperature: {latest_temp}°C")

if __name__ == "__main__":
    asyncio.run(main())
```

**Note:** JWT token acquisition happens outside the SDK. The SDK only handles API requests with a ready token.

### Getting Latest Readings (Simplified)

You can fetch the latest sensor readings without specifying a date range:

```python
import asyncio
import os
from airbeld import AirbeldClient

async def main():
    base_url = os.environ.get("AIRBELD_API_BASE", "https://api.airbeld.com")
    token = os.environ["AIRBELD_API_TOKEN"]

    async with AirbeldClient(token=token, base_url=base_url) as client:
        devices = await client.async_get_devices()

        if devices:
            device = devices[0]

            # Get latest readings without specifying start/end dates
            readings = await client.async_get_readings_by_date(
                device_id=device.id,
                sensors=["temperature", "pm2p5", "humidity"]  # Optional filter
            )

            # Display latest values
            for sensor_name, metric in readings.sensors.items():
                latest = readings.get_latest_value(sensor_name)
                print(f"{metric.display_name}: {latest} {metric.unit}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Authentication Options

The SDK supports two authentication paths depending on your use case:

### Home Assistant Integration

For Home Assistant users, authentication is handled by the integration:

- Home Assistant performs OAuth2 flow automatically
- SDK receives a ready JWT token from the integration
- See [docs/home-assistant-auth.md](docs/home-assistant-auth.md) for details

### Standalone Applications (CLI, Scripts, etc.)

For standalone applications, use the built-in authentication:

```python
import asyncio
import os
from airbeld import async_login, AirbeldClient

async def main():
    # Authenticate with email/password
    token_set = await async_login(
        base_url="https://api.airbeld.com",
        email=os.environ["AIRBELD_USER_EMAIL"],
        password=os.environ["AIRBELD_USER_PASSWORD"]
    )
    
    # Create client with access token
    async with AirbeldClient(token=token_set.access_token) as client:
        # List devices
        devices = await client.async_get_devices()
        print(f"Found {len(devices)} devices:")
        
        for device in devices:
            print(f"  - {device.name} ({device.status})")

if __name__ == "__main__":
    asyncio.run(main())
```

**⚠️ Security Warning:** Never commit real credentials or tokens to version control. Use environment variables or secure secret storage systems.

### Token Management

For applications requiring token refresh or runtime token updates:

```python
# Update token at runtime
client.set_token(new_token)

# Or use refresh token (if implemented)
new_token_set = await async_login(...)
client.set_token(new_token_set.access_token)
```

---

## Development

### Installation

Using uv (recommended):
```bash
# Clone the repository
git clone https://github.com/Embio-Diagnostics/airbeld-api-sdk.git
cd airbeld-api-sdk

# Create virtual environment and install dependencies
uv sync
```

Using pip:
```bash
# Clone the repository
git clone https://github.com/Embio-Diagnostics/airbeld-api-sdk.git
cd airbeld-api-sdk

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Using uv
uv run pytest

# Or with pip
pytest
```

### Linting and Formatting

```bash
# Check code style
uv run ruff check .

# Format code
uv run ruff format .

# Or with pip
ruff check .
ruff format .
```

### Type Checking

```bash
# Using uv
uv run mypy src

# Or with pip
mypy src
```

### Building the Package

```bash
# Using uv
uv build

# Or with pip
python -m build
```

---

## Resources

- **Contributing:** See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- **Changelog:** See [CHANGELOG.md](CHANGELOG.md) for version history
- **License:** This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details
