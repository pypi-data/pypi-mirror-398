"""Django integration helpers."""

from __future__ import annotations

from functools import wraps
from typing import Callable

from .client import GoogleAuthzClient
from .token import discover_token


def _import_django() -> tuple[object, object]:
    try:
        from django.core.exceptions import PermissionDenied
        from django.http import HttpRequest
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Install django to use google_authz_client.django helpers") from exc
    return PermissionDenied, HttpRequest


class GoogleAuthzMiddleware:
    """Attach EffectiveAuth information onto incoming Django requests."""

    def __init__(self, get_response: Callable):
        from django.conf import settings  # type: ignore

        self.get_response = get_response
        client = getattr(settings, "GOOGLE_AUTHZ_CLIENT", None)
        if client is None:
            raise RuntimeError("settings.GOOGLE_AUTHZ_CLIENT must be configured with GoogleAuthzClient")
        if not isinstance(client, GoogleAuthzClient):
            raise RuntimeError("GOOGLE_AUTHZ_CLIENT must be an instance of GoogleAuthzClient")
        self.client = client
        self.cookie_name = getattr(settings, "GOOGLE_AUTHZ_COOKIE_NAME", "session")
        self.header_name = getattr(settings, "GOOGLE_AUTHZ_HEADER_NAME", "authorization")
        self.attach_to_user = bool(getattr(settings, "GOOGLE_AUTHZ_ATTACH_TO_USER", False))

    def __call__(self, request):
        token = discover_token(request.headers, request.COOKIES, self.cookie_name, self.header_name)
        if token:
            cache = getattr(request, "_google_authz_cache", None)
            if cache is None:
                cache = {}
                setattr(request, "_google_authz_cache", cache)
            auth = cache.get(token) or self.client.fetch_effective_auth(token, cache=cache)
            setattr(request, "google_authz", auth)
            if self.attach_to_user:
                setattr(request, "user", auth)
        response = self.get_response(request)
        return response


def require_permission(
    permission: str,
    *,
    client: GoogleAuthzClient,
    cookie_name: str = "session",
    header_name: str = "authorization",
) -> Callable:
    """Decorator enforcing permissions for Django view functions."""
    PermissionDenied, HttpRequest = _import_django()
    try:
        module, action = permission.split(":", 1)
    except ValueError as exc:  # pragma: no cover - invalid input
        raise ValueError("Permission must look like 'module:action'") from exc

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            token = discover_token(request.headers, request.COOKIES, cookie_name, header_name)
            if not token:
                raise PermissionDenied("Missing credentials")
            result = client.check_permission(module, action, token)
            if not result.allowed:
                raise PermissionDenied("Forbidden")
            cache = getattr(request, "_google_authz_cache", None)
            if cache is None:
                cache = {}
                setattr(request, "_google_authz_cache", cache)
            auth = cache.get(token) or client.fetch_effective_auth(token, cache=cache)
            setattr(request, "google_authz", auth)
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
