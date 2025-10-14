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

            # Get latest telemetry readings (no date range)
            readings = await client.async_get_readings_by_date(
                device_id=device.id,
                sensor="temperature"  # Optional: filter to single sensor
            )

            # Print latest temperature reading
            if "temperature" in readings.sensors:
                latest_temp = readings.get_latest_value("temperature")
                print(f"Latest temperature: {latest_temp}°C")

if __name__ == "__main__":
    asyncio.run(main())
```

**Note:** JWT token acquisition happens outside the SDK. The SDK only handles API requests with a ready token.

### Getting Latest Readings

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

            # Get latest readings without specifying start_date/end_date
            readings = await client.async_get_readings_by_date(device_id=device.id)

            # Display latest values
            for sensor_name, metric in readings.sensors.items():
                latest = readings.get_latest_value(sensor_name)
                print(f"{metric.display_name}: {latest} {metric.unit}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Getting Historical Readings

Fetch sensor readings for a specific date range with hourly or daily aggregation:

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

            # Get hourly readings for a specific date range
            readings = await client.async_get_readings_by_date(
                device_id=device.id,
                start_date="2025-09-19",  # Format: YYYY-MM-DD or 'today'
                end_date="2025-09-19",    # Same day = 24 hours of data
                period="hour",            # Aggregation: 'hour' or 'day'
                sensor="temperature"      # Optional: single sensor filter
            )

            # Access all temperature values
            if "temperature" in readings.sensors:
                temp_metric = readings.sensors["temperature"]
                print(f"Temperature readings: {len(temp_metric.values)} values")

                for reading in temp_metric.values:
                    print(f"  {reading.timestamp}: {reading.value}°C")

if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

### Client Methods

#### `AirbeldClient(token, base_url, timeout)`

Initialize the Airbeld API client.

**Parameters:**
- `token` (str, required): JWT access token for authentication
- `base_url` (str, optional): API base URL. Default: `"https://api.airbeld.com"`
- `timeout` (float, optional): Request timeout in seconds. Default: `10.0`

**Usage:**
```python
async with AirbeldClient(token=token, base_url=base_url) as client:
    # Use client...
```

---

#### `async_get_devices()`

Get list of all devices.

**Parameters:** None

**Returns:** `list[DeviceSummary]` - List of device objects

**Raises:**
- `AuthError`: Authentication failed (401/403)
- `ApiError`: Other API errors (4xx/5xx)
- `NetworkError`: Network connectivity issues

**Example:**
```python
devices = await client.async_get_devices()
for device in devices:
    print(f"{device.name} - {device.status}")
```

---

#### `async_get_readings_by_date(device_id, start_date, end_date, sensor, period)`

Get telemetry readings for a device.

**Parameters:**
- `device_id` (int, required): Device ID
- `start_date` (str, optional): Start date in `YYYY-MM-DD` format or `'today'`. If omitted, returns latest data.
- `end_date` (str, optional): End date in `YYYY-MM-DD` format or `'today'`. If omitted, returns latest data.
- `sensor` (str, optional): Single sensor name to filter (e.g., `"temperature"`, `"pm2p5"`). If omitted, returns all sensors.
- `period` (str, optional): Data aggregation period. Values: `"hour"` or `"day"`.

**Returns:** `Readings` - Object containing sensor readings

**Raises:**
- `AuthError`: Authentication failed (401/403)
- `ApiError`: API errors including 404 (device not found), 413 (range too large)
- `RateLimitError`: Rate limit exceeded (429)
- `NetworkError`: Network connectivity issues

**Examples:**
```python
# Get latest readings (no date range)
readings = await client.async_get_readings_by_date(device_id=123)

# Get historical readings with date range
readings = await client.async_get_readings_by_date(
    device_id=123,
    start_date="2025-09-19",
    end_date="2025-09-19",
    period="hour"
)

# Filter to single sensor
readings = await client.async_get_readings_by_date(
    device_id=123,
    sensor="temperature"
)
```

---

#### `async_get_all_readings_by_date(start_date, end_date, sensor, period)`

Get telemetry readings for all user devices.

**Parameters:**
- `start_date` (str, optional): Start date in `YYYY-MM-DD` format or `'today'`. If omitted, returns latest data.
- `end_date` (str, optional): End date in `YYYY-MM-DD` format or `'today'`. If omitted, returns latest data.
- `sensor` (str, optional): Single sensor name to filter (e.g., `"temperature"`, `"pm2p5"`). If omitted, returns all sensors.
- `period` (str, optional): Data aggregation period. Values: `"hour"` or `"day"`.

**Returns:** `list[DeviceReadings]` - List of device objects with metadata and sensor readings

**Raises:**
- `AuthError`: Authentication failed (401/403)
- `ApiError`: API errors including 413 (range too large)
- `RateLimitError`: Rate limit exceeded (429)
- `NetworkError`: Network connectivity issues

**Examples:**
```python
# Get latest readings for all devices
devices = await client.async_get_all_readings_by_date()
for device in devices:
    print(f"Device: {device.display_name or device.name}")
    temp = device.get_latest_value("temperature")
    print(f"  Temperature: {temp}°C")

# Get historical readings with date range
devices = await client.async_get_all_readings_by_date(
    start_date="2025-10-14",
    end_date="2025-10-14",
    period="hour"
)

# Filter to single sensor
devices = await client.async_get_all_readings_by_date(
    sensor="pm2p5"
)
```

---

#### `set_token(new_token)`

Update the authorization token at runtime.

**Parameters:**
- `new_token` (str, required): New JWT access token

**Returns:** None

**Example:**
```python
client.set_token(refreshed_token)
```

### Authentication Functions

#### `async_login(base_url, email, password, timeout)`

Authenticate with email and password to obtain JWT tokens.

**Parameters:**
- `base_url` (str, required): API base URL
- `email` (str, required): User email address
- `password` (str, required): User password
- `timeout` (float, optional): Request timeout in seconds. Default: `10.0`

**Returns:** `TokenSet` - Object containing access token, refresh token, expires_in, and token_type

**Raises:**
- `AuthError`: Invalid credentials (401)
- `RateLimitError`: Rate limit exceeded (429)
- `ApiError`: Other API errors (4xx/5xx)
- `NetworkError`: Network connectivity issues

**Example:**
```python
from airbeld import async_login

token_set = await async_login(
    base_url="https://api.airbeld.com",
    email="user@example.com",
    password="password"
)
print(f"Access token: {token_set.access_token}")
print(f"Expires in: {token_set.expires_in} seconds")
```

### Data Models

#### `DeviceSummary`

Device information object.

**Attributes:**
- `uid` (str): Unique device identifier
- `id` (int): Device ID
- `name` (str): Device name
- `display_name` (str | None): Custom display name
- `description` (str): Device description
- `type` (str | None): Device type
- `is_locked` (bool): Whether device is locked
- `status` (str): Device status - `"online"` or `"offline"`
- `sector` (str | None): Sector name
- `sector_id` (int | None): Sector ID
- `location` (str | None): Location name
- `location_id` (int | None): Location ID
- `timezone` (str): IANA timezone

#### `DeviceReadings`

Device with telemetry readings (returned by `async_get_all_readings_by_date`).

**Attributes:**
- `id` (int): Device ID
- `uid` (str): Unique device identifier
- `name` (str): Device name
- `display_name` (str | None): Custom display name
- `location` (str | None): Location name
- `sector` (str | None): Sector name
- `timezone` (str): IANA timezone
- `sensors` (dict[str, TelemetryMetric]): Dictionary of sensor metrics by sensor name

**Methods:**
- `get_latest_value(metric_name: str) -> float | None`: Get the latest value for a specific sensor
- `pm2_5` (property): Shortcut to access PM 2.5 metric (returns `TelemetryMetric | None`)

#### `Readings`

Container for sensor readings.

**Attributes:**
- `sensors` (dict[str, TelemetryMetric]): Dictionary of sensor metrics by sensor name

**Methods:**
- `get_latest_value(metric_name: str) -> float | None`: Get the latest value for a specific sensor
- `pm2_5` (property): Shortcut to access PM 2.5 metric (returns `TelemetryMetric | None`)

#### `TelemetryMetric`

Individual sensor metric with metadata and values.

**Attributes:**
- `name` (str): Sensor name
- `display_name` (str | None): Display name
- `unit` (str): Measurement unit
- `description` (str | None): Sensor description
- `values` (list[TelemetryValue]): List of readings

#### `TelemetryValue`

Single sensor reading.

**Attributes:**
- `timestamp` (datetime): Reading timestamp
- `value` (float | None): Measured value

---

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
