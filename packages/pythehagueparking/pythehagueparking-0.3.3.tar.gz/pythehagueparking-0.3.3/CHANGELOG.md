# Changelog

This project follows Keep a Changelog and Semantic Versioning.

## Unreleased

- Nothing yet.

## 0.3.3

- Changed reservation/zone timestamps to ISO 8601 UTC `Z` strings (seconds precision).
- Updated reservation create/update methods to accept ISO 8601 timestamps.

## 0.3.2

- Require callers to pass `base_url` to `Auth` (use `DEFAULT_BASE_URL` for the
  production endpoint) and accept an optional `permit_media_type_id` override.

## 0.3.1

- Bump version to 0.3.1 in `pyproject.toml`.

## 0.3.0

- Changed model field names to `id`, `name`, `start_time`, and `end_time`
- Renamed `Account.remaining_minutes` to `remaining_time` and removed `parking_zone`
- Renamed API method parameters from `label` to `name` for favorites and reservations
- Removed the favorite update PUT fallback and the favorites list paging headers
- Updated tests and documentation to match the new model fields and API usage

## 0.2.0

- Changed minimum supported Python version to 3.13
- Added `RateLimitError` with `Retry-After` support
- Added Auth + API layers with async-prefixed methods
- Added raw models with action methods
- Added `ParseError` for unexpected payloads
- Added User-Agent header with caching
- Added `__version__` export
- Added CI `twine check`, Issues link, and wheel metadata files
- Removed client-owned sessions and input validation
- Removed `ResponseError` in favor of `ClientResponseError`
- Removed API delete methods in favor of model actions

## 0.1.0

- Initial async client with account, reservation, and favorite endpoints
- Cookie-based login with retry on authentication errors
- Dataclass models and typed exceptions

Release checklist

- Update version and changelog
- Run `pytest`, `ruff check .`, and `mypy`
- Run `python -m build`
- Run `python -m twine check dist/*`
- Publish to PyPI
