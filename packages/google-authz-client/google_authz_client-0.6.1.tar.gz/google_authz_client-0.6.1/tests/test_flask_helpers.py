import json

import httpx
import pytest

from google_authz_client.client import GoogleAuthzClient
from google_authz_client.flask import register_current_user_middleware, require_permission

flask_module = pytest.importorskip("flask")
Flask = flask_module.Flask
g = flask_module.g


def _build_flask_app():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/authz":
            payload = json.loads(request.content.decode())
            token = payload.get("id_token", "")
            return httpx.Response(
                200,
                json={"subject": token, "permissions": {"inventory": ["create"]}},
            )
        if request.url.path == "/authz/check":
            payload = json.loads(request.content.decode())
            token = payload.get("id_token", "")
            allowed = token == "good-token"
            return httpx.Response(
                200,
                json={"allowed": allowed, "permitted_actions": ["create"] if allowed else []},
            )
        raise AssertionError("Unexpected path")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://authz.local")
    authz_client = GoogleAuthzClient(client=http_client, base_url="https://authz.local")

    app = Flask(__name__)
    register_current_user_middleware(app, authz_client)

    @app.post("/inventory")
    @require_permission("inventory:create", client=authz_client)
    def create_inventory():
        return {"subject": getattr(g, "current_user").subject}

    return app


@pytest.fixture()
def flask_app():
    app = _build_flask_app()
    app.config.update(TESTING=True)
    return app


def test_flask_helper_allows_valid_token(flask_app):
    client = flask_app.test_client()
    response = client.post("/inventory", headers={"Authorization": "Bearer good-token"})
    assert response.status_code == 200
    assert response.get_json()["subject"] == "good-token"


def test_flask_helper_blocks_invalid_permission(flask_app):
    client = flask_app.test_client()
    response = client.post("/inventory", headers={"Authorization": "Bearer bad-token"})
    assert response.status_code == 403
