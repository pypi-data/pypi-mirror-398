"""Authentication helpers for the The Hague Parking API."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version
from typing import Any, TypedDict, Unpack

from aiohttp import (
    BasicAuth,
    ClientError,
    ClientResponse,
    ClientSession,
    ClientTimeout,
)

from .exceptions import AuthError, ParkingConnectionError, RateLimitError

_LOGGER = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://parkerendenhaag.denhaag.nl"
DEFAULT_TIMEOUT = 20.0


class _AuthInitKwargs(TypedDict, total=False):
    permit_media_type_id: int
    timeout: float


class Auth:
    """Handle authenticated requests and session state."""

    def __init__(
        self,
        session: ClientSession,
        username: str,
        password: str,
        base_url: str,
        **kwargs: Unpack[_AuthInitKwargs],
    ) -> None:
        timeout = kwargs.get("timeout", DEFAULT_TIMEOUT)
        permit_media_type_id = kwargs.get("permit_media_type_id")
        unexpected_kwargs = set(kwargs) - {"permit_media_type_id", "timeout"}
        if unexpected_kwargs:
            unexpected = ", ".join(sorted(unexpected_kwargs))
            raise TypeError(f"Unexpected keyword arguments: {unexpected}")

        if not username or not username.strip():
            raise ValueError("username must be a non-empty string")
        if not password or not password.strip():
            raise ValueError("password must be a non-empty string")
        if not base_url or not base_url.strip():
            raise ValueError("base_url must be a non-empty string")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        self._session = session
        self._username = username
        self._password = password
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._permit_media_type_id = permit_media_type_id
        self._authenticated = False
        self._login_lock = asyncio.Lock()

    async def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> ClientResponse:
        """Perform an authenticated request and return the response."""
        await self._ensure_logged_in()

        url = f"{self._base_url}{path}"
        headers = self._merge_headers(kwargs.pop("headers", None))
        timeout = ClientTimeout(total=self._timeout)

        attempt = 0
        while True:
            attempt += 1
            try:
                response = await self._session.request(
                    method,
                    url,
                    headers=headers,
                    timeout=timeout,
                    **kwargs,
                )
            except (TimeoutError, ClientError) as err:
                raise ParkingConnectionError("Request failed") from err

            if response.status == 429:
                response.release()
                raise RateLimitError(_parse_retry_after(response.headers))
            if response.status in {401, 403}:
                response.release()
                self._invalidate_session()
                if attempt == 1:
                    _LOGGER.debug("Session expired, re-authenticating")
                    await self._ensure_logged_in()
                    continue
                raise AuthError("Authentication failed")

            return response

    def invalidate(self) -> None:
        """Invalidate the current session so the next request reauthenticates."""
        self._invalidate_session()

    async def _ensure_logged_in(self) -> None:
        if self._authenticated:
            return
        async with self._login_lock:
            if self._authenticated:
                return
            await self._login()

    async def _login(self) -> None:
        url = f"{self._base_url}/api/session/0"
        headers = {**self._build_default_headers(), "x-session-policy": "Keep-Alive"}
        timeout = ClientTimeout(total=self._timeout)

        try:
            async with self._session.get(
                url,
                headers=headers,
                auth=BasicAuth(self._username, self._password),
                timeout=timeout,
            ) as response:
                if response.status == 429:
                    raise RateLimitError(_parse_retry_after(response.headers))
                if response.status in {401, 403}:
                    self._invalidate_session()
                    raise AuthError("Authentication failed")
                response.raise_for_status()
        except (TimeoutError, ClientError) as err:
            raise ParkingConnectionError("Login request failed") from err

        self._authenticated = True

    def _invalidate_session(self) -> None:
        self._authenticated = False

    def _build_default_headers(self) -> dict[str, str]:
        headers = {
            "accept": "application/json",
            "user-agent": _get_user_agent(),
            "x-requested-with": "angular",
        }
        if self._permit_media_type_id is not None:
            headers["x-permit-media-type-id"] = str(self._permit_media_type_id)
        return headers

    def _merge_headers(self, headers: Mapping[str, str] | None) -> dict[str, str]:
        merged = self._build_default_headers()
        if headers:
            merged.update(headers)
        return merged


def _parse_retry_after(headers: Mapping[str, str]) -> int | None:
    value = headers.get("Retry-After")
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


@lru_cache(maxsize=1)
def _get_user_agent() -> str:
    try:
        package_version = version("pythehagueparking")
    except PackageNotFoundError:
        package_version = "0.0.0"
    return f"pythehagueparking/{package_version}"
