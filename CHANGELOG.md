# Changelog

All notable changes to this project will be documented in this file.

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
