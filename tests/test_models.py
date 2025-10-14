"""Tests for Airbeld API models."""

from datetime import datetime, timezone

import pytest

from airbeld.models import (
    Device,
    DeviceReadings,
    DeviceSummary,
    Readings,
    TelemetryMetric,
    TelemetryValue,
)


def test_device_minimal():
    """Test Device with minimal required fields."""
    device_data = {
        "uid": "test-device-123",
        "name": "Test Device",
        "deviceType": "EOS",
        "status": "online",
        "isLocked": False,
    }

    device = Device(**device_data)
    assert device.uid == "test-device-123"
    assert device.name == "Test Device"
    assert device.device_type == "EOS"
    assert device.status == "online"
    assert device.is_locked is False
    assert device.display_name is None
    assert device.manufacturer is None


def test_device_full():
    """Test Device with all optional fields populated (using camelCase as API returns)."""
    device_data = {
        "uid": "2415b867354b5e50d845",
        "name": "Living Room",
        "displayName": "Living Room Sensor",
        "deviceType": "ATHENA",
        "status": "offline",
        "isLocked": True,
        "hardwareModel": "ATHENA-v2",
        "hardwareVersion": "2.1.0",
        "manufacturer": "SK EMBIO Diagnostics Ltd",
        "serialNumber": "SN-67890",
        "sectorId": "sector-001",
        "sectorName": "Main Office / Floor 1",
        "description": "Conference room air quality monitor",
    }

    device = Device(**device_data)
    assert device.display_name == "Living Room Sensor"
    assert device.device_type == "ATHENA"
    assert device.status == "offline"
    assert device.is_locked is True
    assert device.manufacturer == "SK EMBIO Diagnostics Ltd"
    assert device.sector_name == "Main Office / Floor 1"


def test_telemetry_value():
    """Test TelemetryValue with timestamp and optional value."""
    # With value
    tv_with_value = TelemetryValue(
        timestamp=datetime(2025, 8, 21, 12, 36, 17, tzinfo=timezone.utc), value=23.8
    )
    assert tv_with_value.value == 23.8

    # Without value (null reading)
    tv_null = TelemetryValue(
        timestamp=datetime(2025, 8, 21, 12, 36, 17, tzinfo=timezone.utc), value=None
    )
    assert tv_null.value is None


def test_telemetry_metric():
    """Test TelemetryMetric with metadata and values."""
    metric = TelemetryMetric(
        name="temperature",
        display_name="Temperature",
        unit="°C",
        description="Temperature measurement",
        values=[
            TelemetryValue(
                timestamp=datetime(2025, 8, 21, 12, 36, 17, tzinfo=timezone.utc),
                value=23.8,
            )
        ],
    )

    assert metric.name == "temperature"
    assert metric.display_name == "Temperature"
    assert metric.unit == "°C"
    assert len(metric.values) == 1
    assert metric.values[0].value == 23.8


def test_readings_empty():
    """Test Readings with no sensors."""
    readings = Readings()
    assert readings.sensors == {}
    assert readings.pm2_5 is None
    assert readings.get_latest_value("temperature") is None


def test_readings_with_sensors():
    """Test Readings with multiple sensors (matches actual API response)."""
    readings_data = {
        "sensors": {
            "temperature": {
                "name": "temperature",
                "display_name": "Temperature",
                "unit": "°C",
                "values": [{"timestamp": "2025-08-21T12:36:17+03:00", "value": 23.8}],
            },
            "pm2p5": {
                "name": "pm2p5",
                "display_name": "PM 2.5",
                "unit": "µg/m³",
                "values": [{"timestamp": "2025-08-21T12:36:17+03:00", "value": 183.0}],
            },
        },
    }

    readings = Readings(**readings_data)
    assert "temperature" in readings.sensors
    assert "pm2p5" in readings.sensors

    # Test PM 2.5 alias
    pm25_metric = readings.pm2_5
    assert pm25_metric is not None
    assert pm25_metric.display_name == "PM 2.5"
    assert pm25_metric.unit == "µg/m³"


def test_get_latest_value():
    """Test getting latest value from metric with multiple readings."""
    readings = Readings(
        sensors={
            "temperature": TelemetryMetric(
                name="temperature",
                display_name="Temperature",
                unit="°C",
                values=[
                    TelemetryValue(
                        timestamp=datetime(2025, 8, 21, 12, 0, 0, tzinfo=timezone.utc),
                        value=22.0,
                    ),
                    TelemetryValue(
                        timestamp=datetime(2025, 8, 21, 12, 30, 0, tzinfo=timezone.utc),
                        value=23.5,
                    ),
                    TelemetryValue(
                        timestamp=datetime(2025, 8, 21, 12, 15, 0, tzinfo=timezone.utc),
                        value=22.8,
                    ),
                ],
            )
        },
    )

    # Should return value from latest timestamp (12:30)
    latest_temp = readings.get_latest_value("temperature")
    assert latest_temp == 23.5

    # Non-existent metric
    assert readings.get_latest_value("humidity") is None


def test_device_uid_validation():
    """Test Device uid field validation."""
    # Empty uid should fail
    with pytest.raises(ValueError):
        Device(
            uid="",
            name="Test",
            deviceType="EOS",
            status="online",
            isLocked=False,
        )

    # Too long uid should fail
    with pytest.raises(ValueError):
        Device(
            uid="x" * 256,  # Over 255 char limit
            name="Test",
            deviceType="EOS",
            status="online",
            isLocked=False,
        )


def test_device_summary_camel_case_parsing():
    """Test DeviceSummary parses camelCase from API response."""
    # Test with displayName present
    device_data_with_display = {
        "uid": "706bb7907bbd4c4752ff",
        "id": 5,
        "name": "AirBELD_0022",
        "displayName": "My Custom Name",
        "description": "",
        "type": "EOS",
        "isLocked": False,
        "status": "online",
        "sector": "HW department 2",
        "sectorId": 1118,
        "location": "Embio Diagnostics LTD",
        "locationId": 297,
        "timezone": "Europe/Athens",
    }

    device = DeviceSummary(**device_data_with_display)
    assert device.uid == "706bb7907bbd4c4752ff"
    assert device.display_name == "My Custom Name"
    assert device.is_locked is False
    assert device.sector_id == 1118
    assert device.location_id == 297


def test_device_summary_optional_display_name():
    """Test DeviceSummary with optional displayName field."""
    # Test without displayName (should be None)
    device_data_without_display = {
        "uid": "706bb7907bbd4c4752ff",
        "id": 5,
        "name": "AirBELD_0022",
        "description": "",
        "type": "EOS",
        "isLocked": False,
        "status": "online",
        "sector": "HW department 2",
        "sectorId": 1118,
        "location": "Embio Diagnostics LTD",
        "locationId": 297,
        "timezone": "Europe/Athens",
    }

    device = DeviceSummary(**device_data_without_display)
    assert device.uid == "706bb7907bbd4c4752ff"
    assert device.display_name is None  # Should be None when not provided
    assert device.name == "AirBELD_0022"


def test_device_readings_full():
    """Test DeviceReadings with all fields and sensors (matches API response format)."""
    device_data = {
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
                "values": [{"timestamp": "2025-10-14T12:00:00+03:00", "value": 23.5}],
            },
            "pm2p5": {
                "name": "pm2p5",
                "displayName": "PM 2.5",
                "unit": "µg/m³",
                "values": [{"timestamp": "2025-10-14T12:00:00+03:00", "value": 15.2}],
            },
        },
    }

    device = DeviceReadings(**device_data)
    assert device.id == 5
    assert device.uid == "706bb7907bbd4c4752ff"
    assert device.name == "AirBELD_0022"
    assert device.display_name == "Living Room Sensor"
    assert device.location == "Embio Diagnostics LTD"
    assert device.sector == "HW department 2"
    assert device.timezone == "Europe/Athens"

    # Check sensors
    assert "temperature" in device.sensors
    assert "pm2p5" in device.sensors

    # Test PM 2.5 alias
    pm25_metric = device.pm2_5
    assert pm25_metric is not None
    assert pm25_metric.display_name == "PM 2.5"

    # Test get_latest_value
    latest_temp = device.get_latest_value("temperature")
    assert latest_temp == 23.5


def test_device_readings_minimal():
    """Test DeviceReadings with minimal fields (null location/sector)."""
    device_data = {
        "id": 6,
        "uid": "another-device-uid",
        "name": "Device_002",
        "displayName": None,
        "location": None,
        "sector": None,
        "timezone": "UTC",
        "sensors": {},
    }

    device = DeviceReadings(**device_data)
    assert device.id == 6
    assert device.uid == "another-device-uid"
    assert device.name == "Device_002"
    assert device.display_name is None
    assert device.location is None
    assert device.sector is None
    assert device.timezone == "UTC"
    assert device.sensors == {}
    assert device.pm2_5 is None
    assert device.get_latest_value("temperature") is None
