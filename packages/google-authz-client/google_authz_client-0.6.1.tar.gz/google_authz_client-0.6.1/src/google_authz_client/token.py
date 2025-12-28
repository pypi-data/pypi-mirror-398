"""Utilities for discovering caller tokens across frameworks."""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

BEARER_PREFIX = "bearer "


def extract_bearer_token(header_value: Optional[str]) -> Optional[str]:
    if not header_value:
        return None
    value = header_value.strip()
    if value.lower().startswith(BEARER_PREFIX):
        return value[len(BEARER_PREFIX) :].strip()
    return value or None


def discover_token(
    headers: Mapping[str, str],
    cookies: Mapping[str, str],
    cookie_name: str = "session",
    header_name: str = "authorization",
) -> Optional[str]:
    """Attempt to extract a session or bearer token."""
    cookie = cookies.get(cookie_name)
    if cookie:
        return cookie
    header = None
    for key, value in headers.items():
        if key.lower() == header_name.lower():
            header = value
            break
    return extract_bearer_token(header)


class RequestScopedCache:
    """Lightweight per-request cache for effective auth payloads."""

    def __init__(self) -> None:
        self._store: MutableMapping[str, object] = {}

    def get(self, key: str) -> Optional[object]:
        return self._store.get(key)

    def set(self, key: str, value: object) -> None:
        self._store[key] = value

    def clear(self) -> None:
        self._store.clear()
