# Developer Guide

## Local Environment Setup

### Requirements
- Python 3.10 or higher
- Recommended: `uv` for fast dependency management
- Alternative: `pip` with virtual environments

### Installation

**Using uv (recommended):**
```bash
uv sync
```

**Using pip:**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Development Tools

### Quality Gates
All changes must pass these checks before committing:

```bash
# Lint check
uv run ruff check .

# Format check
uv run ruff format --check .

# Type check
uv run mypy src

# Run tests
uv run pytest -q
```

**Or with pip:**
```bash
ruff check .
ruff format --check .
mypy src
pytest -q
```

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=airbeld --cov-report=html

# Run specific test file
uv run pytest tests/test_client.py

# Run with verbose output
uv run pytest -v
```

### Building the Package
```bash
# Build distribution files
uv build

# Check the built package
twine check dist/*
```

## API Contract

The `docs/api-contract.md` file is the **source of truth** for backend endpoints, authentication, and payload schemas. Always consult it when implementing new features or fixing bugs.

## Public API Stability

- **Breaking changes require major version bumps**
- Before introducing breaking changes:
  1. Open an issue for discussion
  2. Add migration notes
  3. Update `README.md` with usage changes
  4. Add entry to `CHANGELOG.md`

## Documentation

- **README.md**: User-facing documentation with examples
- **docs/api-contract.md**: Technical API specification
- **docs/home-assistant-auth.md**: Home Assistant integration details
- **CHANGELOG.md**: Version history and changes

Keep examples minimal, runnable, and well-tested.

## Git Workflow

### Branch Naming
- Features: `feat/description`
- Bug fixes: `fix/description`
- Chores: `chore/description`

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add support for hourly aggregation
fix: handle missing Retry-After header correctly
chore: update dependencies
docs: improve authentication examples
test: add coverage for rate limiting
```

### Pull Requests
- Keep PRs small and focused
- Include test coverage for new features
- Ensure all quality gates pass
- Provide clear description of changes
- Link related issues

## Environment Variables

For local development and testing:

```bash
# Create .env file (never commit this!)
cp .env.example .env

# Edit with your test credentials
AIRBELD_API_BASE=https://api.airbeld.com
AIRBELD_API_TOKEN=your-jwt-token
AIRBELD_USER_EMAIL=your-email@example.com
AIRBELD_USER_PASSWORD=your-password
```

**Never commit secrets to version control.**

## Testing Strategy

- Use `pytest` for all tests
- Mock HTTP requests with `unittest.mock` or `respx`
- No live API requests in tests
- Cover both success and error cases
- Test edge cases (empty responses, missing fields, etc.)

Example test structure:
```python
@pytest.mark.asyncio
async def test_feature_name():
    """Test description."""
    # Arrange: Set up mocks and test data
    # Act: Call the function
    # Assert: Verify the results
```

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with changes
3. Commit: `chore: prepare release X.Y.Z`
4. Create git tag: `git tag vX.Y.Z`
5. Push: `git push && git push --tags`
6. Build: `uv build`
7. Publish to PyPI: `twine upload dist/*`

## Troubleshooting

### Common Issues

**Import errors after installation:**
```bash
# Reinstall in editable mode
pip install -e ".[dev]"
```

**Type checking failures:**
```bash
# Clear mypy cache
rm -rf .mypy_cache
mypy src
```

**Tests failing:**
```bash
# Clear pytest cache
rm -rf .pytest_cache
pytest -v
```
