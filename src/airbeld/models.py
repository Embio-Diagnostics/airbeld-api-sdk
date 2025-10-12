"""Data models for the Airbeld API SDK."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TokenSet(BaseModel):
    """Authentication token set from POST /api/v1/auth/token/ (camelCase wire format)."""

    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")
    expires_in: int = Field(alias="expiresIn")
    token_type: str = Field(alias="tokenType")


class DeviceSummary(BaseModel):
    """Device summary information from GET /api/v1/devices/ (camelCase wire format)."""

    uid: str = Field(..., min_length=1, max_length=255)
    id: int
    name: str
    display_name: str | None = Field(default=None, alias="displayName")
    description: str
    type: str | None
    is_locked: bool = Field(alias="isLocked")
    status: Literal["online", "offline"]
    sector: str | None
    sector_id: int | None = Field(alias="sectorId")
    location: str | None
    location_id: int | None = Field(alias="locationId")
    timezone: str


class Device(BaseModel):
    """Device information from the Airbeld API."""

    uid: str = Field(..., min_length=1, max_length=255)
    name: str
    display_name: str | None = None
    device_type: str
    status: Literal["online", "offline"]
    is_locked: bool
    hardware_model: str | None = None
    hardware_version: str | None = None
    manufacturer: str | None = None
    serial_number: str | None = None
    sector_id: str | None = None
    sector_name: str | None = None
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class TelemetryValue(BaseModel):
    """A single telemetry reading with timestamp."""

    timestamp: datetime
    value: float | None = None


class TelemetryMetric(BaseModel):
    """Telemetry metric containing metadata and values."""

    name: str
    display_name: str | None = None
    unit: str
    description: str | None = None
    values: list[TelemetryValue] = Field(default_factory=list)


class TelemetryBundle(BaseModel):
    """Bundle of telemetry sensors for a device."""

    device_uid: str
    sensors: dict[str, TelemetryMetric] = Field(default_factory=dict)

    @property
    def pm2_5(self) -> TelemetryMetric | None:
        """Access PM 2.5 metric with Pythonic naming."""
        return self.sensors.get("pm2p5")

    def get_latest_value(self, metric_name: str) -> float | None:
        """Get the latest value for a specific metric."""
        metric = self.sensors.get(metric_name)
        if not metric or not metric.values:
            return None

        latest = max(metric.values, key=lambda v: v.timestamp)
        return latest.value
