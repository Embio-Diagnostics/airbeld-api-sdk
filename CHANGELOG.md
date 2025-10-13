# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2025-10-13

### Added
- Optional date parameters: `start` and `end` parameters in `async_get_readings_by_date()` are now optional, allowing users to fetch latest readings without specifying a date range
- New example: `examples/get_latest_readings.py` demonstrating how to fetch latest readings
- README section showing simplified usage for getting latest readings

### Fixed
- Added missing camelCase alias for `TelemetryMetric.display_name` field to properly map API's `displayName`
- Added missing camelCase aliases to `Device` model fields (`deviceType`, `isLocked`, `hardwareModel`, etc.)
- All Pydantic models now include `populate_by_name=True` for better flexibility

### Changed
- API contract documentation now correctly shows camelCase wire format from API responses
- Test mocks updated to use actual camelCase format as returned by API

### Removed
- Removed unused `created_at` and `updated_at` fields from `Device` model (not used in current API)

## [0.1.0] - 2025-10-12

### Added
- Initial public release of airbeld-api-sdk
- Async HTTP client (`AirbeldClient`) for Airbeld API
- Device management: list devices with full metadata (name, status, location, timezone)
- Telemetry data: fetch readings by date range with optional sensor filtering
- Authentication: JWT token support with `async_login()` helper for email/password
- Token management: `set_token()` method for runtime token refresh
- Type safety: full type hints with `py.typed` marker for mypy support
- Error handling: structured exceptions (`AuthError`, `RateLimitError`, `NetworkError`, `ApiError`)
- Retry logic: automatic retries with exponential backoff and jitter
- Rate limit handling: respects `Retry-After` headers on 429 responses
- Pydantic models: automatic camelCase ↔ snake_case mapping for API compatibility
- Comprehensive test suite using pytest and respx for HTTP mocking
- CI/CD: GitHub Actions workflow for lint, type-check, and tests on Python 3.10-3.12
- Examples: quickstart and standalone login examples
- Documentation: README with usage examples, API contract, developer guide
