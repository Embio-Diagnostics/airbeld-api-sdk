"""Tests for Airbeld API client."""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from airbeld.client import AirbeldClient
from airbeld.exceptions import AuthError, RateLimitError
from airbeld.models import DeviceReadings, DeviceSummary, Readings


def mock_response(status_code: int, json_data=None, headers=None):
    """Create a mock httpx.Response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.is_success = status_code < 400
    response.headers = headers or {}
    if json_data is not None:
        response.json.return_value = json_data
        response.text = json.dumps(json_data)
    else:
        response.text = ""
    return response


@pytest.mark.asyncio
async def test_rate_limit_with_retry_after():
    """Test 429 rate limit response with Retry-After header."""
    with patch.object(httpx.AsyncClient, "request") as mock_request:
        # Mock 429 response with Retry-After header
        mock_request.return_value = mock_response(
            429, {"error": "Rate limit exceeded"}, {"Retry-After": "2"}
        )

        async with AirbeldClient(token="test-token") as client:
            with pytest.raises(RateLimitError) as exc_info:
                await client.async_get_devices()

            # Verify RateLimitError has retry_after set
            assert exc_info.value.retry_after == 2
            assert "Rate limit exceeded" in str(exc_info.value)


@pytest.mark.asyncio
async def test_rate_limit_without_retry_after():
    """Test 429 rate limit response without Retry-After header."""
    with patch.object(httpx.AsyncClient, "request") as mock_request:
        # Mock 429 response without Retry-After header
        mock_request.return_value = mock_response(429, {"error": "Rate limit exceeded"})

        async with AirbeldClient(token="test-token") as client:
            with pytest.raises(RateLimitError) as exc_info:
                await client.async_get_devices()

            # Verify RateLimitError has retry_after as None when header missing
            assert exc_info.value.retry_after is None


@pytest.mark.asyncio
async def test_auth_error_no_retry():
    """Test 401 auth error does not retry."""
    with patch.object(httpx.AsyncClient, "request") as mock_request:
        # Mock 401 response
        mock_request.return_value = mock_response(401, {"error": "Unauthorized"})

        async with AirbeldClient(token="invalid-token") as client:
            with pytest.raises(AuthError) as exc_info:
                await client.async_get_devices()

            # Verify AuthError is raised
            assert "Unauthorized" in str(exc_info.value)

            # Verify the endpoint was only called once (no retries for auth errors)
            assert mock_request.call_count == 1


@pytest.mark.asyncio
async def test_network_error_retry():
    """Test NetworkError triggers retry logic."""
    with patch.object(httpx.AsyncClient, "request") as mock_request:
        # Mock network error on first call, success on second
        mock_request.side_effect = [
            httpx.NetworkError("Connection failed"),
            mock_response(200, []),
        ]

        async with AirbeldClient(token="test-token") as client:
            # Should succeed after retry
            devices = await client.async_get_devices()
            assert devices == []

            # Verify it was called twice (original + 1 retry)
            assert mock_request.call_count == 2


@pytest.mark.asyncio
async def test_readings_by_date_uses_id():
    """Test readings endpoint uses device ID in path."""
    device_id = 123

    with patch.object(httpx.AsyncClient, "request") as mock_request:
        # Mock successful readings response (using camelCase as API returns)
        mock_request.return_value = mock_response(
            200,
            {
                "sensors": {
                    "temperature": {
                        "name": "temperature",
                        "displayName": "Temperature",
                        "unit": "°C",
                        "values": [{"timestamp": "2025-08-21T12:36:17+03:00", "value": 23.8}],
                    }
                }
            },
        )

        async with AirbeldClient(token="test-token") as client:
            readings = await client.async_get_readings_by_date(
                device_id=device_id, start_date="2025-08-21", end_date="2025-08-21"
            )

            # Verify correct path was called
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            called_url = str(call_args[0][1])  # method, url
            assert str(device_id) in called_url
            assert "readings_by_date" in called_url

            # Verify query params use correct names
            call_kwargs = call_args[1]  # kwargs
            params = call_kwargs.get("params", {})
            assert params["start-date"] == "2025-08-21"
            assert params["end-date"] == "2025-08-21"

            # Verify response structure
            assert isinstance(readings, Readings)
            assert "temperature" in readings.sensors


@pytest.mark.asyncio
async def test_device_list_parsing():
    """Test device list parsing with camelCase fields."""
    with patch.object(httpx.AsyncClient, "request") as mock_request:
        # Mock device list API response with camelCase
        mock_request.return_value = mock_response(
            200,
            [
                {
                    "uid": "706bb7907bbd4c4752ff",
                    "id": 5,
                    "name": "AirBELD_0022",
                    "displayName": "Custom Display Name",
                    "description": "",
                    "type": "EOS",
                    "isLocked": False,
                    "status": "online",
                    "sector": "HW department 2",
                    "sectorId": 1118,
                    "location": "Embio Diagnostics LTD",
                    "locationId": 297,
                    "timezone": "Europe/Athens",
                },
                {
                    "uid": "another-device-uid",
                    "id": 6,
                    "name": "AirBELD_0023",
                    # displayName missing - should be None
                    "description": "Test device",
                    "type": "ATHENA",
                    "isLocked": True,
                    "status": "offline",
                    "sector": None,
                    "sectorId": None,
                    "location": None,
                    "locationId": None,
                    "timezone": "UTC",
                },
            ],
        )

        async with AirbeldClient(token="test-token") as client:
            devices = await client.async_get_devices()

            assert len(devices) == 2

            # First device with displayName
            device1 = devices[0]
            assert isinstance(device1, DeviceSummary)
            assert device1.uid == "706bb7907bbd4c4752ff"
            assert device1.display_name == "Custom Display Name"  # camelCase converted
            assert device1.is_locked is False  # camelCase converted
            assert device1.sector_id == 1118  # camelCase converted

            # Second device without displayName
            device2 = devices[1]
            assert device2.uid == "another-device-uid"
            assert device2.display_name is None  # Should be None when missing
            assert device2.is_locked is True
            assert device2.sector_id is None


@pytest.mark.asyncio
async def test_get_latest_readings_without_dates():
    """Test calling readings endpoint without start/end dates to get latest data."""
    device_id = 123

    with patch.object(httpx.AsyncClient, "request") as mock_request:
        # Mock successful readings response with latest data (using camelCase as API returns)
        mock_request.return_value = mock_response(
            200,
            {
                "sensors": {
                    "temperature": {
                        "name": "temperature",
                        "displayName": "Temperature",
                        "unit": "°C",
                        "values": [{"timestamp": "2025-08-21T14:30:00+03:00", "value": 24.5}],
                    },
                    "pm2p5": {
                        "name": "pm2p5",
                        "displayName": "PM 2.5",
                        "unit": "µg/m³",
                        "values": [{"timestamp": "2025-08-21T14:30:00+03:00", "value": 15.2}],
                    },
                }
            },
        )

        async with AirbeldClient(token="test-token") as client:
            # Call without start/end dates
            readings = await client.async_get_readings_by_date(device_id=device_id)

            # Verify correct path was called
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            called_url = str(call_args[0][1])  # method, url
            assert str(device_id) in called_url
            assert "readings_by_date" in called_url

            # Verify query params do NOT contain start-date/end-date
            call_kwargs = call_args[1]  # kwargs
            params = call_kwargs.get("params", {})
            assert "start-date" not in params
            assert "end-date" not in params

            # Verify response structure
            assert isinstance(readings, Readings)
            assert "temperature" in readings.sensors
            assert "pm2p5" in readings.sensors

            # Verify we can use get_latest_value helper
            latest_temp = readings.get_latest_value("temperature")
            assert latest_temp == 24.5

            # Verify display_name was properly parsed from camelCase displayName
            temp_metric = readings.sensors["temperature"]
            assert temp_metric.display_name == "Temperature"
            pm_metric = readings.sensors["pm2p5"]
            assert pm_metric.display_name == "PM 2.5"


@pytest.mark.asyncio
async def test_get_all_readings_by_date():
    """Test all_readings_by_date endpoint returns list of devices with readings."""
    with patch.object(httpx.AsyncClient, "request") as mock_request:
        # Mock API response for all devices (using camelCase as API returns)
        mock_request.return_value = mock_response(
            200,
            {
                "devices": [
                {
                    "id": 5,
                    "uid": "706bb7907bbd4c4752ff",
                    "name": "AirBELD_0022",
                    "displayName": "Living Room Sensor",
                    "location": "Embio Diagnostics LTD",
                    "sector": "HW department 2",
                    "timezone": "Europe/Athens",
                    "sensors": {
                        "temperature": {
                            "name": "temperature",
                            "displayName": "Temperature",
                            "unit": "°C",
                            "values": [
                                {"timestamp": "2025-10-14T12:00:00+03:00", "value": 23.5}
                            ],
                        }
                    },
                },
                {
                    "id": 6,
                    "uid": "another-device-uid",
                    "name": "Device_002",
                    "displayName": None,
                    "location": None,
                    "sector": None,
                    "timezone": "UTC",
                    "sensors": {
                        "pm2p5": {
                            "name": "pm2p5",
                            "displayName": "PM 2.5",
                            "unit": "µg/m³",
                            "values": [
                                {"timestamp": "2025-10-14T12:00:00+03:00", "value": 15.2}
                            ],
                        }
                    },
                },
            ]
            },
        )

        async with AirbeldClient(token="test-token") as client:
            # Call with date range
            devices = await client.async_get_all_readings_by_date(
                start_date="2025-10-14", end_date="2025-10-14", period="hour"
            )

            # Verify correct path was called
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            called_url = str(call_args[0][1])  # method, url
            assert "all_readings_by_date" in called_url

            # Verify query params
            call_kwargs = call_args[1]  # kwargs
            params = call_kwargs.get("params", {})
            assert params["start-date"] == "2025-10-14"
            assert params["end-date"] == "2025-10-14"
            assert params["period"] == "hour"

            # Verify response structure
            assert isinstance(devices, list)
            assert len(devices) == 2

            # First device
            device1 = devices[0]
            assert isinstance(device1, DeviceReadings)
            assert device1.id == 5
            assert device1.uid == "706bb7907bbd4c4752ff"
            assert device1.display_name == "Living Room Sensor"
            assert device1.location == "Embio Diagnostics LTD"
            assert device1.sector == "HW department 2"
            assert "temperature" in device1.sensors
            assert device1.get_latest_value("temperature") == 23.5

            # Second device
            device2 = devices[1]
            assert device2.id == 6
            assert device2.display_name is None
            assert device2.location is None
            assert "pm2p5" in device2.sensors
            assert device2.pm2_5 is not None


@pytest.mark.asyncio
async def test_get_all_readings_without_dates():
    """Test all_readings_by_date endpoint without dates to get latest data."""
    with patch.object(httpx.AsyncClient, "request") as mock_request:
        # Mock API response with latest data
        mock_request.return_value = mock_response(
            200,
            {
                "devices": [
                {
                    "id": 5,
                    "uid": "706bb7907bbd4c4752ff",
                    "name": "AirBELD_0022",
                    "displayName": "Living Room",
                    "location": "Office",
                    "sector": "Floor 1",
                    "timezone": "Europe/Athens",
                    "sensors": {
                        "temperature": {
                            "name": "temperature",
                            "displayName": "Temperature",
                            "unit": "°C",
                            "values": [
                                {"timestamp": "2025-10-14T14:30:00+03:00", "value": 24.0}
                            ],
                        }
                    },
                }
            ]
            },
        )

        async with AirbeldClient(token="test-token") as client:
            # Call without dates to get latest
            devices = await client.async_get_all_readings_by_date()

            # Verify correct path was called
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            called_url = str(call_args[0][1])
            assert "all_readings_by_date" in called_url

            # Verify no date params
            call_kwargs = call_args[1]
            params = call_kwargs.get("params", {})
            assert "start-date" not in params
            assert "end-date" not in params

            # Verify response
            assert len(devices) == 1
            assert devices[0].id == 5
            assert devices[0].get_latest_value("temperature") == 24.0
