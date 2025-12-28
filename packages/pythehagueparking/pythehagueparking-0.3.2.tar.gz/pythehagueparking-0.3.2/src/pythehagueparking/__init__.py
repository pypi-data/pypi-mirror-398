"""Public exports for The Hague Parking service."""

from importlib.metadata import PackageNotFoundError, version

from .api import TheHagueParkingAPI
from .auth import DEFAULT_BASE_URL, Auth
from .exceptions import (
    AuthError,
    ParkingConnectionError,
    ParseError,
    PyTheHagueParkingError,
    RateLimitError,
)
from .models import Account, Favorite, Reservation, Zone

__all__ = [
    "DEFAULT_BASE_URL",
    "Auth",
    "TheHagueParkingAPI",
    "Account",
    "Favorite",
    "Reservation",
    "Zone",
    "AuthError",
    "ParkingConnectionError",
    "PyTheHagueParkingError",
    "ParseError",
    "RateLimitError",
    "__version__",
]

try:
    __version__ = version("pythehagueparking")
except PackageNotFoundError:
    __version__ = "0.0.0"
