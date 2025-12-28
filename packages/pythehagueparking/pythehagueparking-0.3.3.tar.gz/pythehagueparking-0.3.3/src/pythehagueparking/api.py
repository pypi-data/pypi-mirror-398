"""API entrypoints for the The Hague Parking service."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from aiohttp import ClientResponse

from .auth import Auth
from .exceptions import ParseError
from .models import Account, Favorite, Reservation


def _iso8601_to_api(value: str, field: str) -> str:
    """Normalize an ISO 8601 timestamp to UTC with `Z` and seconds precision."""
    if not isinstance(value, str):
        raise TypeError(f"{field} must be an ISO 8601 string")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as err:
        raise ValueError(f"{field} must be a valid ISO 8601 timestamp") from err

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    dt = dt.astimezone(UTC).replace(microsecond=0)
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


class TheHagueParkingAPI:
    """Root API wrapper for The Hague Parking."""

    def __init__(self, auth: Auth) -> None:
        """Initialize the API client with an authenticated session."""
        self._auth = auth

    @property
    def auth(self) -> Auth:
        """Return the auth handler used for API calls."""
        return self._auth

    async def async_get_account(self) -> Account:
        """Fetch the account summary."""
        response = await self._auth.request("GET", "/api/account/0")
        try:
            data = await _async_json(response)
        finally:
            response.release()
        return Account.from_mapping(_ensure_mapping(data, "account"))

    async def async_list_reservations(self) -> list[Reservation]:
        """Return all reservations for the current account."""
        response = await self._auth.request("GET", "/api/reservation")
        try:
            data = await _async_json(response)
        finally:
            response.release()

        items = _ensure_list(data, "reservations")
        return [
            Reservation.from_mapping(_ensure_mapping(item, "reservation"))
            for item in items
        ]

    async def async_create_reservation(
        self,
        *,
        name: str,
        license_plate: str,
        reservation_starts_at: str,
        reservation_ends_at: str,
    ) -> Reservation:
        """Create a new reservation."""
        payload = {
            "id": None,
            "name": name,
            "license_plate": license_plate,
            "start_time": _iso8601_to_api(
                reservation_starts_at, "reservation_starts_at"
            ),
            "end_time": _iso8601_to_api(reservation_ends_at, "reservation_ends_at"),
        }
        response = await self._auth.request("POST", "/api/reservation", json=payload)
        try:
            data = await _async_json(response)
        finally:
            response.release()
        return Reservation.from_mapping(_ensure_mapping(data, "reservation"))

    async def async_set_reservation_end_time(
        self, reservation_id: int, *, end_time: str
    ) -> Reservation:
        """Update the end time for an existing reservation."""
        payload = {"end_time": _iso8601_to_api(end_time, "end_time")}
        response = await self._auth.request(
            "PATCH", f"/api/reservation/{reservation_id}", json=payload
        )
        try:
            data = await _async_json(response)
        finally:
            response.release()
        return Reservation.from_mapping(_ensure_mapping(data, "reservation"))

    async def async_delete_reservation(self, reservation_id: int) -> None:
        """Delete a reservation by its identifier."""
        response = await self._auth.request(
            "DELETE", f"/api/reservation/{reservation_id}"
        )
        try:
            response.raise_for_status()
        finally:
            response.release()

    async def async_list_favorites(self) -> list[Favorite]:
        """Return all favorites for the current account."""
        response = await self._auth.request("GET", "/api/favorite")
        try:
            data = await _async_json(response)
        finally:
            response.release()

        items = _ensure_list(data, "favorites")
        return [
            Favorite.from_mapping(_ensure_mapping(item, "favorite")) for item in items
        ]

    async def async_create_favorite(self, *, name: str, license_plate: str) -> Favorite:
        """Create a favorite license plate."""
        payload = {"name": name, "license_plate": license_plate}
        response = await self._auth.request("POST", "/api/favorite", json=payload)
        try:
            data = await _async_json(response)
        finally:
            response.release()
        return Favorite.from_mapping(_ensure_mapping(data, "favorite"))

    async def async_update_favorite(
        self, favorite_id: int, *, name: str, license_plate: str
    ) -> Favorite:
        """Update an existing favorite."""
        payload = {"name": name, "license_plate": license_plate}

        response = await self._auth.request(
            "PATCH", f"/api/favorite/{favorite_id}", json=payload
        )
        try:
            data = await _async_json(response)
        finally:
            response.release()

        return Favorite.from_mapping(_ensure_mapping(data, "favorite"))

    async def async_delete_favorite(self, favorite_id: int) -> None:
        """Delete a favorite by its identifier."""
        response = await self._auth.request("DELETE", f"/api/favorite/{favorite_id}")
        try:
            response.raise_for_status()
        finally:
            response.release()


def _ensure_mapping(data: Any, label: str) -> Mapping[str, Any]:
    """Validate that the response payload is a mapping."""
    if not isinstance(data, Mapping):
        raise ParseError(f"Expected {label} object")
    return data


def _ensure_list(data: Any, label: str) -> list[Any]:
    """Validate that the response payload is a list."""
    if not isinstance(data, list):
        raise ParseError(f"Expected {label} list")
    return data


async def _async_json(response: ClientResponse) -> Any:
    """Decode a JSON response body or return None for empty responses."""
    response.raise_for_status()
    text = await response.text()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        raise ParseError("Response body is not valid JSON") from err
