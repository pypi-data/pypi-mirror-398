"""Flask utilities for enforcing google-authz permissions."""

from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import Flask, abort, g, request

from .client import GoogleAuthzClient
from .models import EffectiveAuth
from .token import discover_token


def _get_cache() -> dict[str, EffectiveAuth]:
    cache = getattr(g, "_google_authz_cache", None)
    if cache is None:
        cache = {}
        setattr(g, "_google_authz_cache", cache)
    return cache


def _get_token(cookie_name: str, header_name: str) -> str | None:
    return discover_token(request.headers, request.cookies, cookie_name, header_name)


def register_current_user_middleware(
    app: Flask,
    client: GoogleAuthzClient,
    *,
    cookie_name: str = "session",
    header_name: str = "authorization",
) -> None:
    """Attach `g.current_user` with EffectiveAuth when a token exists."""

    @app.before_request
    def _inject_current_user() -> None:
        token = _get_token(cookie_name, header_name)
        if not token:
            g.current_user = None
            return
        cache = _get_cache()
        auth = client.fetch_effective_auth(token, cache=cache)
        g.current_user = auth


def require_permission(
    permission: str,
    *,
    client: GoogleAuthzClient,
    cookie_name: str = "session",
    header_name: str = "authorization",
) -> Callable[[Callable[..., object]], Callable[..., object]]:
    """Decorator enforcing a permission on a Flask view."""
    try:
        module, action = permission.split(":", 1)
    except ValueError as exc:  # pragma: no cover - invalid input
        raise ValueError("Permission must look like 'module:action'") from exc

    def decorator(fn: Callable[..., object]) -> Callable[..., object]:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token = _get_token(cookie_name, header_name)
            if not token:
                abort(401, description="Missing credentials")
            result = client.check_permission(module, action, token)
            if not result.allowed:
                abort(403, description="Forbidden")
            cache = _get_cache()
            auth = cache.get(token) or client.fetch_effective_auth(token, cache=cache)
            g.current_user = auth
            return fn(*args, **kwargs)

        return wrapper

    return decorator
