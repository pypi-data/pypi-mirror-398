# pythehagueparking

[![CI](https://github.com/sir-Unknown/pythehagueparking/actions/workflows/ci.yml/badge.svg)](https://github.com/sir-Unknown/pythehagueparking/actions/workflows/ci.yml)
[![PyPI](https://badge.fury.io/py/pythehagueparking.svg)](https://badge.fury.io/py/pythehagueparking)
[![Python versions](https://img.shields.io/pypi/pyversions/pythehagueparking.svg)](https://pypi.org/project/pythehagueparking/)
[![Issues](https://img.shields.io/github/issues/sir-Unknown/pythehagueparking.svg)](https://github.com/sir-Unknown/pythehagueparking/issues)
[![Security policy](https://img.shields.io/badge/security-policy-blue.svg)](https://github.com/sir-Unknown/pythehagueparking/security/policy)

Async client library for the Parkeren Den Haag API, designed for Home Assistant
custom integrations but usable in any asyncio project.

## Features

- Async-only HTTP calls via aiohttp
- Auth helper with automatic re-login on 401/403
- Typed dataclass models with parsed fields
- Caller-owned aiohttp session (no session management in the library)
- Caller-provided API base URL (use `DEFAULT_BASE_URL` for production)

## Installation

```bash
python -m pip install pythehagueparking
```

## Quick start

```python
from aiohttp import ClientSession

from pythehagueparking import Auth, DEFAULT_BASE_URL, TheHagueParkingAPI

async def main() -> None:
    async with ClientSession() as session:
        auth = Auth(
            session,
            username="user",
            password="pass",
            base_url=DEFAULT_BASE_URL,
        )
        api = TheHagueParkingAPI(auth)
        account = await api.async_get_account()
        reservations = await api.async_list_reservations()
        favorites = await api.async_list_favorites()
        print(account, reservations, favorites)
```

## API reference

API methods:

- `async_get_account() -> Account`: Fetch account details.
- `async_list_reservations() -> list[Reservation]`: List reservations.
- `async_create_reservation(name, license_plate, reservation_starts_at, reservation_ends_at) -> Reservation`: Create a reservation (timestamps are ISO 8601 `Z` strings).
- `async_set_reservation_end_time(reservation_id, *, end_time) -> Reservation`: Update a reservation end time (ISO 8601 `Z` string).
- `async_delete_reservation(reservation_id) -> None`: Delete a reservation.
- `async_list_favorites() -> list[Favorite]`: List favorites.
- `async_create_favorite(name, license_plate) -> Favorite`: Create a favorite.
- `async_update_favorite(favorite_id, name, license_plate) -> Favorite`: Update a favorite.
- `async_delete_favorite(favorite_id) -> None`: Delete a favorite.

Example usage:

```python
from datetime import UTC, datetime, timedelta

from aiohttp import ClientSession

from pythehagueparking import Auth, DEFAULT_BASE_URL, TheHagueParkingAPI

async with ClientSession() as session:
    api = TheHagueParkingAPI(
        Auth(session, "user", "pass", base_url=DEFAULT_BASE_URL)
    )
    starts_at = datetime.now(tz=UTC).replace(microsecond=0)
    ends_at = (starts_at + timedelta(hours=2)).replace(microsecond=0)
    starts_at_iso = starts_at.isoformat(timespec="seconds").replace("+00:00", "Z")
    ends_at_iso = ends_at.isoformat(timespec="seconds").replace("+00:00", "Z")
    extended_ends_at_iso = (
        (ends_at + timedelta(hours=1))
        .replace(microsecond=0)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )

    reservation = await api.async_create_reservation(
        name="My Car",
        license_plate="12-AB-34",
        reservation_starts_at=starts_at_iso,
        reservation_ends_at=ends_at_iso,
    )
    await api.async_set_reservation_end_time(
        reservation.id,
        end_time=extended_ends_at_iso,
    )
    await api.async_delete_reservation(reservation.id)
```

```python
from pythehagueparking import __version__

print("pythehagueparking", __version__)
```

```python
from aiohttp import ClientSession

from pythehagueparking import Auth, DEFAULT_BASE_URL, TheHagueParkingAPI

async with ClientSession() as session:
    api = TheHagueParkingAPI(
        Auth(session, "user", "pass", base_url=DEFAULT_BASE_URL)
    )
    favorites = await api.async_list_favorites()
    if favorites:
        favorite = favorites[0]
        await api.async_update_favorite(
            favorite.id,
            name="My Car",
            license_plate=favorite.license_plate,
        )
```

```python
from aiohttp import ClientSession

from pythehagueparking import Auth, DEFAULT_BASE_URL, RateLimitError, TheHagueParkingAPI

async with ClientSession() as session:
    api = TheHagueParkingAPI(
        Auth(session, "user", "pass", base_url=DEFAULT_BASE_URL)
    )
    try:
        await api.async_list_reservations()
    except RateLimitError as err:
        print("Retry after:", err.retry_after)
```

## API notes

- Start and end times are ISO 8601 UTC strings ending with `Z` (seconds precision).
- Naive timestamps (without `Z`/offset) are treated as UTC.
- Incoming timestamps are normalized to ISO 8601 UTC strings ending with `Z`.
- Provide `permit_media_type_id` to `Auth` to send `x-permit-media-type-id`
  headers when required.

## Session ownership

- You always pass your own `aiohttp.ClientSession`.
- The library never creates or closes sessions.

## Model fields and mapping

- Public methods return typed dataclasses with fields mapped from API payloads.
- Each model exposes parsed values instead of raw payload dictionaries.

Field mapping:

- **Account**
  - `id: int`
  - `remaining_time: int` (was `debit_minutes`)
  - `active_reservation_count: int` (was `reservation_count`)

- **Zone**
  - `id: int`
  - `name: str`
  - `start_time: str` (ISO 8601 UTC, `Z`)
  - `end_time: str` (ISO 8601 UTC, `Z`)

- **Reservation**
  - `id: int`
  - `license_plate: str`
  - `name: str`
  - `start_time: str` (ISO 8601 UTC, `Z`)
  - `end_time: str` (ISO 8601 UTC, `Z`)

- **Favorite**
  - `id: int`
  - `license_plate: str`
  - `name: str`

## Compatibility notes

- Python 3.13.2+ is required, matching Home Assistant 2025.12.
- Async-only (`aiohttp`); no synchronous wrapper is provided.

## Error handling

- `AuthError` for authentication failures or expired sessions
- `ParkingConnectionError` for network errors and timeouts
- `RateLimitError` for HTTP 429 responses (see `retry_after`)
- `ParseError` for unexpected response payloads
- `aiohttp.ClientResponseError` for HTTP status errors (`raise_for_status`)

## Development

```bash
python -m pip install -e '.[test,dev]'
pytest
ruff check .
mypy
```

## License

MIT License. See `LICENSE` and `NOTICE`.

## Support

For questions or issues, open a GitHub issue:
https://github.com/sir-Unknown/pythehagueparking/issues
