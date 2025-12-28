"""HTTP clients for communicating with the google-authz service."""

from __future__ import annotations

from typing import Any, Dict, MutableMapping, Optional

import httpx

from .errors import GoogleAuthzError, MissingCredentialsError
from .models import EffectiveAuth, PermissionCheckResult

EffectiveAuthCache = Optional[MutableMapping[str, EffectiveAuth]]


class _BaseClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        verify_tls: bool,
        shared_secret: Optional[str],
        shared_secret_header: str,
        token_type: str,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.verify_tls = verify_tls
        self.shared_secret = shared_secret
        self.shared_secret_header = shared_secret_header
        if token_type not in {"id_token", "session_token", "access_token"}:
            raise ValueError("token_type must be 'id_token', 'session_token', or 'access_token'")
        self.token_type = token_type

    def _headers(self, token: str | None) -> Dict[str, str]:
        if not token:
            raise MissingCredentialsError("Token is required for google-authz calls")
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }
        if self.shared_secret:
            headers[self.shared_secret_header] = self.shared_secret
        return headers

    def _token_payload(self, token: str, token_type: Optional[str]) -> Dict[str, str]:
        if not token:
            raise MissingCredentialsError("Token is required for google-authz calls")
        chosen_type = token_type or self.token_type
        if chosen_type not in {"id_token", "session_token", "access_token"}:
            raise ValueError("token_type must be 'id_token', 'session_token', or 'access_token'")
        return {chosen_type: token}

    def _effective_auth_from_payload(self, payload: Dict[str, Any]) -> EffectiveAuth:
        subject = str(payload.get("subject") or payload.get("user", "anonymous"))
        permissions = payload.get("permissions") or {}
        normalized: Dict[str, list[str]] = {}
        for module, actions in permissions.items():
            if isinstance(actions, (list, tuple, set)):
                normalized[module] = [str(action) for action in actions]
            elif isinstance(actions, str):
                normalized[module] = [actions]
        return EffectiveAuth(subject=subject, permissions=normalized, raw=payload)

    def _raise_for_status(self, response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GoogleAuthzError(str(exc)) from exc


class GoogleAuthzClient(_BaseClient):
    """Synchronous, long-lived httpx client."""

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:8080",
        timeout_seconds: float = 5.0,
        verify_tls: bool = True,
        shared_secret: Optional[str] = None,
        shared_secret_header: str = "X-Authz-Shared-Secret",
        token_type: str = "id_token",
        client: Optional[httpx.Client] = None,
    ) -> None:
        super().__init__(
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            verify_tls=verify_tls,
            shared_secret=shared_secret,
            shared_secret_header=shared_secret_header,
            token_type=token_type,
        )
        self._client = client or httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout_seconds),
            verify=self.verify_tls,
        )

    def close(self) -> None:
        self._client.close()

    def fetch_effective_auth(
        self,
        token: str,
        *,
        cache: EffectiveAuthCache = None,
        token_type: Optional[str] = None,
    ) -> EffectiveAuth:
        if cache and token in cache:
            cached = cache[token]
            if isinstance(cached, EffectiveAuth):
                return cached
        response = self._client.post(
            "/authz",
            headers=self._headers(token),
            json=self._token_payload(token, token_type),
        )
        self._raise_for_status(response)
        payload = response.json()
        auth = self._effective_auth_from_payload(payload)
        if cache is not None:
            cache[token] = auth
        return auth

    def check_permission(
        self,
        module: str,
        action: str,
        token: str,
        token_type: Optional[str] = None,
    ) -> PermissionCheckResult:
        response = self._client.post(
            "/authz/check",
            headers=self._headers(token),
            json={
                "module": module,
                "action": action,
                **self._token_payload(token, token_type),
            },
        )
        self._raise_for_status(response)
        return PermissionCheckResult.from_payload(response.json())


class AsyncGoogleAuthzClient(_BaseClient):
    """Async httpx variant used by FastAPI and other async stacks."""

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:8080",
        timeout_seconds: float = 5.0,
        verify_tls: bool = True,
        shared_secret: Optional[str] = None,
        shared_secret_header: str = "X-Authz-Shared-Secret",
        token_type: str = "id_token",
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        super().__init__(
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            verify_tls=verify_tls,
            shared_secret=shared_secret,
            shared_secret_header=shared_secret_header,
            token_type=token_type,
        )
        self._client = client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout_seconds),
            verify=self.verify_tls,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def fetch_effective_auth(
        self,
        token: str,
        *,
        cache: EffectiveAuthCache = None,
        token_type: Optional[str] = None,
    ) -> EffectiveAuth:
        if cache and token in cache:
            cached = cache[token]
            if isinstance(cached, EffectiveAuth):
                return cached
        response = await self._client.post(
            "/authz",
            headers=self._headers(token),
            json=self._token_payload(token, token_type),
        )
        self._raise_for_status(response)
        payload = response.json()
        auth = self._effective_auth_from_payload(payload)
        if cache is not None:
            cache[token] = auth
        return auth

    async def check_permission(
        self,
        module: str,
        action: str,
        token: str,
        token_type: Optional[str] = None,
    ) -> PermissionCheckResult:
        response = await self._client.post(
            "/authz/check",
            headers=self._headers(token),
            json={
                "module": module,
                "action": action,
                **self._token_payload(token, token_type),
            },
        )
        self._raise_for_status(response)
        return PermissionCheckResult.from_payload(response.json())
