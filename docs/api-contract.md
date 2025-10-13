# API Contract (Source of Truth)

## Base URL
- Production: https://api.airbeld.com
- API prefix: /api/v1

## Authentication
- The SDK receives a ready JWT and injects `Authorization: Bearer <token>`.
- The SDK does **not** perform the token flow itself.

### POST /api/v1/auth/token/ (Phase A convenience)

**Purpose**: Exchange email/password for an access token for SDK users outside Home Assistant.

**Request (JSON)**
```json
{
  "email": "<string>",
  "password": "<string>"
}
```

**Response (200, JSON)**
```json
{
  "accessToken": "<JWT string>",
  "refreshToken": "<opaque|string>",
  "expiresIn": 86400,
  "tokenType": "Bearer"
}
```

**Errors**
- 400: `{"error":"Invalid request","detail":"<why>"}`
- 401: `{"error":"Invalid credentials"}`
- 429: `{"error":"Rate limit exceeded"}` (+ optional Retry-After header)
- 5xx: `{"error":"Server error"}`

**Notes**
- Wire keys are camelCase. SDK models should map to pythonic snake_case via Pydantic aliases (accessToken → access_token, refreshToken → refresh_token, expiresIn → expires_in, tokenType → token_type)
- Base URL is configurable; examples may use staging: `https://airbeld-stag-api-events.azurewebsites.net/`
- This endpoint is **not** used by Home Assistant integration (HA handles OAuth2); it's a separate convenience for CLI/apps

## Error Mapping (HTTP -> SDK Exceptions)
- 401/403 → AuthError
- 429 → RateLimitError
- other 4xx/5xx → ApiError
- network errors → NetworkError

## Device Model (DeviceListSerializer)

### Fields
- `uid`: str (opaque string identifier, non-empty, max 255 chars)
- `id`: int (internal id)
- `name`: str
- `display_name`: Optional[str]
- `description`: str (may be empty)
- `type`: Optional[str] (DeviceType.type_name or null)
- `is_locked`: bool
- `status`: Literal["online", "offline"]
- `sector`: Optional[str] (StringRelatedField)
- `sector_id`: Optional[int]
- `location`: Optional[str] (derived from sector.location.name)
- `location_id`: Optional[int]
- `timezone`: str (IANA timezone, derived from sector.location.timezone or "UTC")

## Telemetry Model

### Structure
- `TelemetryValue`: timestamp (ISO 8601), value (Optional[float])
- `TelemetryMetric`: name, display_name, unit, description (Optional), values (List[TelemetryValue])
- `TelemetryBundle`: device_uid, sensors (Dict[str, TelemetryMetric])

### Units
- Temperature: °C
- Humidity: %
- PM (pm1, pm2p5, pm4, pm10): µg/m³
- CO2: ppm
- VOC/NOx indices: - (dimensionless)

### Value Ranges (guidance)
- Humidity: 0–100%
- Temperature: −40 to +85°C
- PM/CO2: ≥ 0
- VOC/NOx: non-negative

### Example Response (camelCase wire format)
```json
{
  "sensors": {
    "temperature": {
      "name": "temperature",
      "displayName": "Temperature",
      "unit": "°C",
      "description": "Temperature level are essential for our comfort during the day.",
      "values": [
        { "timestamp": "2025-08-21T12:36:17+03:00", "value": 23.8 }
      ]
    },
    "pm2p5": {
      "name": "pm2p5",
      "displayName": "PM 2.5",
      "unit": "µg/m³",
      "description": "The concentration of particulate matter...",
      "values": [
        { "timestamp": "2025-08-21T12:36:17+03:00", "value": 183.0 }
      ]
    }
  }
}
```

**Note**: SDK automatically maps `displayName` (camelCase) to `display_name` (snake_case) in Python.

## Phase A: REST Endpoints

### GET /api/v1/devices/ (Phase A — Non-paginated)

**Response**
- JSON array of device items (no count/next/previous wrapper)
- Field names (wire schema) are camelCase as per backend:

```json
[
  {
    "uid": "706bb7907bbd4c4752ff",
    "id": 5,
    "name": "AirBELD_0022",
    "displayName": "AirBELD_0022", 
    "description": "",
    "type": "EOS",
    "isLocked": false,
    "status": "online",
    "sector": "HW department 2",
    "sectorId": 1118,
    "location": "Embio Diagnostics LTD",
    "locationId": 297,
    "timezone": "Europe/Athens"
  }
]
```

**Phase A Constraints**
- **No server-side pagination**; no guaranteed ordering
- **No server-side filters**; clients may filter locally (query params can be added later without breaking changes)

**Errors**
- 401/403: `{"error":"Unauthorized"}` / `{"error":"Forbidden"}`
- 5xx: `{"error":"Server error"}`
- 400 on invalid query (if filters introduced later): `{"error":"Invalid parameters","detail":"<why>"}`

**SDK Model Notes**
- Use `DeviceSummary` model to match this list shape exactly
- Keep existing `Device` model for potential detailed endpoints in future
- Use Pydantic aliases to map camelCase wire keys to snake_case attributes (displayName → display_name, isLocked → is_locked, sectorId → sector_id, locationId → location_id)

### GET /api/v1/devices/{id}/readings_by_date/

**Optional query params**
- `start`: ISO 8601 with timezone, e.g., `2025-08-21T10:00:00+03:00`. If omitted, returns latest available data.
- `end`: ISO 8601 with timezone. If omitted, returns latest available data.
- `sensors`: comma-separated list of metric keys (e.g., `temperature,pm2p5,co2`)
- `aggregate`: optional; one of `hourly|daily` for downsampling

**Response structure (SensorReadingsSerializer-aligned, camelCase wire format)**
```json
{
  "sensors": {
    "temperature": {
      "name": "temperature",
      "displayName": "Temperature",
      "unit": "°C",
      "description": "Temperature level are essential...",
      "values": [
        {"timestamp": "2025-08-21T12:36:17+03:00", "value": 23.8}
      ]
    },
    "pm2p5": {
      "name": "pm2p5",
      "displayName": "PM 2.5",
      "unit": "µg/m³",
      "description": "The concentration of particulate matter...",
      "values": [
        {"timestamp": "2025-08-21T12:36:17+03:00", "value": 183.0}
      ]
    }
  }
}
```

**Note**: SDK automatically maps `displayName` (camelCase) to `display_name` (snake_case) in Python.

**Units**
- temperature: "°C"
- humidity: "%"  
- pm1, pm2p5, pm4, pm10: "µg/m³"
- co2: "ppm"
- voc, nox: "-" (dimensionless indices)

**Errors**
- 400: invalid parameters → `{"error":"Invalid parameters","detail":"<why>"}`
- 404: device not found → `{"error":"Device not found"}`
- 413: date range too large → `{"error":"Range too large","detail":"Reduce window or provide aggregate"}`
- 429: rate limited (includes `Retry-After: <seconds>`) → `{"error":"Rate limit exceeded"}`
- 5xx: `{"error":"Server error"}`

**Notes**
- `values` sorted by timestamp ascending (oldest → newest)
- If requested metric has no data, include with `"values": []`
- Latest reading: pick entry with max `timestamp` from `values`

## Endpoints (Phase B: Streaming; placeholder)
- SSE or WebSocket endpoint TBD.
- Reconnect/backoff requirements TBD.

## Rate Limits
- Document limits, headers (if any), and retry-after semantics here.

## Notes
- Never log tokens. Redact credentials in diagnostics.
