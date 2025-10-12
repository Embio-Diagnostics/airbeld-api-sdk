# Contributing Guide

Thanks for your interest in contributing!

## Overview
All contributions must pass the quality gates and follow the coding rules below.

## Quality Gates (must pass locally)
- `ruff check .`
- `ruff format --check .`
- `mypy src`
- `pytest -q`

## Coding Rules
- Python ≥ 3.10.
- Async-only networking (httpx.AsyncClient).
- Default timeouts (10s) and retries (3, exponential backoff).
- Strict typing; concise docstrings; **no secrets in logs**.
- Keep diffs minimal; avoid touching unrelated files.

## Public API Stability
- Do not introduce breaking changes without a migration note and prior discussion.
- If public API changes, update `README.md` usage and add a `CHANGELOG.md` entry.

## Documentation
- `README.md` is for users; keep it clear and up to date.
- Developer details live in [DEVELOPER.md](DEVELOPER.md).
- API contract/spec for endpoints and payloads lives in [docs/api-contract.md](docs/api-contract.md).

## Development Workflow
1. Propose a plan or discuss the change in an issue first
2. Implement changes with minimal diffs (one feature/file at a time)
3. Add focused tests (happy path + error cases)
4. Ensure all quality gates pass locally
5. Write a concise commit message following Conventional Commits format
6. Open a PR with a clear description of the changes
