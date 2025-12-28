"""Typed data models for the The Hague Parking API (no HTTP, no raw exposure)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .exceptions import ParseError


def _parse_int(value: Any, field: str) -> int:
    """Parse an integer field from API data."""
    try:
        return int(value)
    except (TypeError, ValueError) as err:
        raise ParseError(f"Invalid int for {field}: {value!r}") from err


def _parse_str(value: Any, field: str) -> str:
    """Parse a string field from API data."""
    if isinstance(value, str):
        return value
    raise ParseError(f"Invalid str for {field}: {value!r}")


def _parse_dt(value: Any, field: str) -> str:
    """Parse API datetime to ISO 8601 UTC like: 2025-12-19T13:23:04Z (seconds)."""
    if not isinstance(value, str):
        raise ParseError(f"Invalid datetime for {field}: {value!r}")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as err:
        raise ParseError(f"Invalid datetime for {field}: {value!r}") from err

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    dt = dt.astimezone(UTC).replace(microsecond=0)
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass(slots=True, frozen=True)
class Zone:
    """Parking zone data with permit window."""

    id: int
    name: str
    start_time: str
    end_time: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Zone:
        """Build a zone from an API mapping."""
        return cls(
            id=_parse_int(data.get("id"), "zone.id"),
            name=_parse_str(data.get("name"), "zone.name"),
            start_time=_parse_dt(data.get("start_time"), "zone.start_time"),
            end_time=_parse_dt(data.get("end_time"), "zone.end_time"),
        )


@dataclass(slots=True, frozen=True)
class Account:
    """Account data including remaining time and active reservations."""

    id: int
    remaining_time: int
    active_reservation_count: int

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Account:
        """Build an account from an API mapping."""
        return cls(
            id=_parse_int(data.get("id"), "account.id"),
            remaining_time=_parse_int(
                data.get("debit_minutes"), "account.debit_minutes"
            ),
            active_reservation_count=_parse_int(
                data.get("reservation_count"), "account.reservation_count"
            ),
        )


@dataclass(slots=True, frozen=True)
class Reservation:
    """Reservation data for a license plate."""

    id: int
    license_plate: str
    name: str
    start_time: str
    end_time: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Reservation:
        """Build a reservation from an API mapping."""
        return cls(
            id=_parse_int(data.get("id"), "reservation.id"),
            license_plate=_parse_str(
                data.get("license_plate"), "reservation.license_plate"
            ),
            name=_parse_str(data.get("name"), "reservation.name"),
            start_time=_parse_dt(data.get("start_time"), "reservation.start_time"),
            end_time=_parse_dt(data.get("end_time"), "reservation.end_time"),
        )


@dataclass(slots=True, frozen=True)
class Favorite:
    """Favorite license plate data."""

    id: int
    license_plate: str
    name: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Favorite:
        """Build a favorite from an API mapping."""
        return cls(
            id=_parse_int(data.get("id"), "favorite.id"),
            license_plate=_parse_str(
                data.get("license_plate"), "favorite.license_plate"
            ),
            name=_parse_str(data.get("name"), "favorite.name"),
        )
