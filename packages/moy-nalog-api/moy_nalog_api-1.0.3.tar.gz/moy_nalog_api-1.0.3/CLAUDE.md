# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python client library for the Russian self-employed tax service API (lknpd.nalog.ru / "Moy Nalog"). Provides async and sync interfaces for authentication, receipt creation, and income management.

## Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run single test file
pytest tests/test_client.py

# Run with coverage
pytest --cov=moy_nalog

# Linting
ruff check .

# Type checking
mypy moy_nalog

# Build package
python -m build
```

## Architecture

### Module Structure (`moy_nalog/`)

- `client.py` - Main `MoyNalogClient` (async) and `MoyNalogClientSync` (sync wrapper) classes. Contains all API interaction logic, authentication, session management, and retry logic with exponential backoff.
- `models.py` - Pydantic v2 models for API requests/responses (`ServiceItem`, `Client`, `Receipt`, `UserProfile`, `IncomeList`, `SessionData`, etc.)
- `exceptions.py` - Typed exception hierarchy rooted at `MoyNalogError`
- `enums.py` - `IncomeType`, `PaymentType`, `CancelReason` enums

### Key Design Patterns

**Dual Client Architecture**: `MoyNalogClientSync` wraps `MoyNalogClient` by creating its own event loop and delegating all async methods via `run_until_complete()`.

**Session Persistence**: Optional JSON file-based session storage. Tokens are saved on `close()` and loaded on client initialization when `session_file` is provided.

**Auto Token Refresh**: Before authenticated requests, checks `is_token_expired` (with 60s margin) and auto-refreshes via `_do_refresh_token()`.

**Proxy Support**: HTTP/HTTPS proxies via native httpx, SOCKS proxies via optional `httpx-socks` dependency.

### API Endpoints

The client interacts with two API versions:
- `API_URL_V1 = "https://lknpd.nalog.ru/api/v1"` - most endpoints
- `API_URL_V2 = "https://lknpd.nalog.ru/api/v2"` - SMS start endpoint only

### Test Configuration

Tests use `pytest-asyncio` with `asyncio_mode = "auto"` in pyproject.toml. The `tests/test_models.py` tests Pydantic model validation; `tests/test_client.py` tests client initialization and validation without making real API calls.
