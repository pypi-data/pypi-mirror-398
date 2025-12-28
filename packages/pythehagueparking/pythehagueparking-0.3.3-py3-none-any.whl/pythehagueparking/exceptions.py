"""Exceptions for The Hague Parking service."""

from __future__ import annotations


class PyTheHagueParkingError(Exception):
    """Base exception for pythehagueparking."""


class AuthError(PyTheHagueParkingError):
    """Authentication failed or session expired."""


class ParkingConnectionError(PyTheHagueParkingError):
    """Network or timeout failure when calling the API."""


class RateLimitError(PyTheHagueParkingError):
    """Rate limit exceeded by the API."""

    def __init__(self, retry_after: int | None) -> None:
        super().__init__("Rate limit exceeded")
        self.retry_after = retry_after


class ParseError(PyTheHagueParkingError):
    """Failed to parse API response data."""
