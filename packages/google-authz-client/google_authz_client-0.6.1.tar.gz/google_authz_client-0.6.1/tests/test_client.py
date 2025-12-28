import json

import httpx
import pytest

from google_authz_client.client import AsyncGoogleAuthzClient, GoogleAuthzClient


def test_fetch_effective_auth_uses_cache():
    calls = {"authz": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/authz":
            assert request.method == "POST"
            payload = json.loads(request.content.decode())
            assert payload == {"id_token": "token"}
            calls["authz"] += 1
            return httpx.Response(
                200,
                json={"subject": "alice", "permissions": {"inventory": ["read"]}},
            )
        raise AssertionError("Unexpected path")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://authz.local")
    client = GoogleAuthzClient(client=http_client, base_url="https://authz.local")
    cache: dict[str, object] = {}

    auth1 = client.fetch_effective_auth("token", cache=cache)
    auth2 = client.fetch_effective_auth("token", cache=cache)

    assert auth1.subject == "alice"
    assert auth2 is auth1
    assert calls["authz"] == 1


def test_check_permission_parses_response():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/authz/check":
            payload = json.loads(request.content.decode())
            assert payload == {"module": "inventory", "action": "read", "id_token": "token"}
            return httpx.Response(
                200,
                json={"allowed": True, "permitted_actions": ["read"]},
            )
        return httpx.Response(200, json={"subject": "alice", "permissions": {}})

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://authz.local")
    client = GoogleAuthzClient(client=http_client, base_url="https://authz.local")

    result = client.check_permission("inventory", "read", "token")
    assert result.allowed is True
    assert result.permitted_actions == ["read"]


@pytest.mark.asyncio
async def test_async_client_calls_endpoints():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/authz":
            payload = json.loads(request.content.decode())
            assert payload == {"id_token": "token"}
            return httpx.Response(200, json={"subject": "alice", "permissions": {}})
        if request.url.path == "/authz/check":
            payload = json.loads(request.content.decode())
            assert payload == {"module": "inventory", "action": "read", "id_token": "token"}
            return httpx.Response(200, json={"allowed": False, "permitted_actions": []})
        raise AssertionError("Unexpected path")

    transport = httpx.MockTransport(handler)
    async_http_client = httpx.AsyncClient(transport=transport, base_url="https://authz.local")
    client = AsyncGoogleAuthzClient(client=async_http_client, base_url="https://authz.local")
    cache: dict[str, object] = {}

    auth = await client.fetch_effective_auth("token", cache=cache)
    assert auth.subject == "alice"

    result = await client.check_permission("inventory", "read", "token")
    assert result.allowed is False
