"""FastAPI dependency helpers for google-authz."""

from __future__ import annotations

from typing import Awaitable, Callable, Iterable, List, Sequence

from fastapi import Depends, HTTPException, Request, status

from .client import AsyncGoogleAuthzClient
from .errors import GoogleAuthzError
from .models import EffectiveAuth
from .token import discover_token

CacheFactory = Callable[[], dict[str, EffectiveAuth]]


def _get_cache(request: Request) -> dict[str, EffectiveAuth]:
    cache = getattr(request.state, "_google_authz_cache", None)
    if cache is None:
        cache = {}
        setattr(request.state, "_google_authz_cache", cache)
    return cache


def current_user(
    client: AsyncGoogleAuthzClient,
    *,
    cookie_name: str = "session",
    header_name: str = "authorization",
) -> Callable[[Request], Awaitable[EffectiveAuth]]:
    """Return a dependency that resolves EffectiveAuth for the inbound request."""

    async def dependency(request: Request) -> EffectiveAuth:
        token = discover_token(request.headers, request.cookies, cookie_name, header_name)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")
        cache = _get_cache(request)
        try:
            auth = await client.fetch_effective_auth(token, cache=cache)
        except GoogleAuthzError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
        return auth

    return dependency


def require_permission(
    permission: str,
    *,
    client: AsyncGoogleAuthzClient,
    return_actions: bool = False,
    cookie_name: str = "session",
    header_name: str = "authorization",
) -> Callable[[Request, EffectiveAuth], Awaitable[EffectiveAuth | List[str]]]:
    """Return a dependency enforcing a single permission string (`module:action`)."""
    try:
        module, action = permission.split(":", 1)
    except ValueError as exc:  # pragma: no cover - invalid input
        raise ValueError("Permission must look like 'module:action'") from exc

    async def dependency(
        request: Request,
        auth: EffectiveAuth = Depends(current_user(client, cookie_name=cookie_name, header_name=header_name)),
    ) -> EffectiveAuth | List[str]:
        token = discover_token(request.headers, request.cookies, cookie_name, header_name)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")
        result = await client.check_permission(module, action, token)
        if not result.allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return result.permitted_actions if return_actions else auth

    return dependency


def any_of(
    permissions: Sequence[str],
    *,
    client: AsyncGoogleAuthzClient,
    cookie_name: str = "session",
    header_name: str = "authorization",
) -> Callable[[Request], Awaitable[EffectiveAuth]]:
    """Dependency that allows the request if any permission passes."""

    async def dependency(
        request: Request,
        auth: EffectiveAuth = Depends(current_user(client, cookie_name=cookie_name, header_name=header_name)),
    ) -> EffectiveAuth:
        token = discover_token(request.headers, request.cookies, cookie_name, header_name)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")
        for permission in permissions:
            module, action = permission.split(":", 1)
            result = await client.check_permission(module, action, token)
            if result.allowed:
                return auth
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return dependency


def all_of(
    permissions: Iterable[str],
    *,
    client: AsyncGoogleAuthzClient,
    cookie_name: str = "session",
    header_name: str = "authorization",
) -> Callable[[Request], Awaitable[EffectiveAuth]]:
    """Dependency that requires all listed permissions."""

    async def dependency(
        request: Request,
        auth: EffectiveAuth = Depends(current_user(client, cookie_name=cookie_name, header_name=header_name)),
    ) -> EffectiveAuth:
        token = discover_token(request.headers, request.cookies, cookie_name, header_name)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")
        for permission in permissions:
            module, action = permission.split(":", 1)
            result = await client.check_permission(module, action, token)
            if not result.allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing permission {permission}",
                )
        return auth

    return dependency
