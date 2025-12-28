# google-authz-client

High-level helpers for calling the `google-authz` service from Python APIs.  
Version 0.5 ships framework integrations for FastAPI, Flask, and Django along with a shared HTTP client powered by `httpx`.

## Installation

Pick the source that matches how you ship code. All of the examples show the `fastapi` extra, but feel free to swap in `flask`, `django`, or omit extras entirely.

### From PyPI

```bash
pip install "google-authz-client[fastapi]"
```

This installs the latest published release and is the easiest option for production deployments.

### From Git

```bash
pip install "google-authz-client[fastapi] @ git+https://github.com/example/google-authz-client.git@main"
```

Pin to a tag (for example `@v0.5.0`) when you want a reproducible build while still consuming code directly from Git.

### Local Editable Install

```bash
pip install -e .[fastapi,flask,django,dev]
```

Use this when you are hacking on the library itself so your changes are reloaded without reinstalling. The extra groups are optional – install only what your framework needs.

## Quick Start (FastAPI)

```python
from fastapi import Depends, FastAPI
from google_authz_client.client import AsyncGoogleAuthzClient
from google_authz_client.fastapi import current_user, require_permission

client = AsyncGoogleAuthzClient()
app = FastAPI()

@app.get("/inventory")
async def read_inventory(
    authz=Depends(current_user(client)),
    _=Depends(require_permission("inventory:read", client=client)),
):
    return {"subject": authz.subject, "perms": authz.permissions}
```

`current_user` discovers a token via cookies or the `Authorization` header, fetches the caller’s effective authorization, and raises HTTP 401/403 when missing or denied.

## Flask Example

```python
from flask import Flask
from google_authz_client.client import GoogleAuthzClient
from google_authz_client.flask import register_current_user_middleware, require_permission

app = Flask(__name__)
client = GoogleAuthzClient()
register_current_user_middleware(app, client)

@app.post("/inventory")
@require_permission("inventory:create", client=client)
def create_item():
    return {"subject": flask.g.current_user.subject}
```

## Django Middleware

```python
# settings.py
from google_authz_client.client import GoogleAuthzClient

GOOGLE_AUTHZ_CLIENT = GoogleAuthzClient()
MIDDLEWARE.append("google_authz_client.django.GoogleAuthzMiddleware")
```

## Configuration

Use `GoogleAuthzSettings` to load sensible defaults from environment variables:

```python
from google_authz_client.config import GoogleAuthzSettings

settings = GoogleAuthzSettings()
client = settings.build_async_client()
```

Key settings include `base_url`, `timeout_seconds`, `verify_tls`, and `shared_secret`.

### Token Type and Authz Requests

The client posts to `/authz` and `/authz/check` with a JSON body that includes exactly one of
`id_token`, `session_token`, or `access_token`. By default, the client uses `id_token`.

```python
from google_authz_client.client import AsyncGoogleAuthzClient

client = AsyncGoogleAuthzClient(token_type="id_token")
```

If you are using a `google-authz` session token (for example, after completing the
`/login` flow), configure the client accordingly:

```python
client = AsyncGoogleAuthzClient(token_type="session_token")
```

If you are forwarding an OAuth access token (for example, from Apps Script), use:

```python
client = AsyncGoogleAuthzClient(token_type="access_token")
```

In Apps Script, the access token is returned by `ScriptApp.getOAuthToken()`.

### Using a Remote google-authz Service

By default, the client points at `http://localhost:8080`. If your `google-authz` service runs
in another environment (container, VM, or a separate host), configure the base URL explicitly
so the client can reach it over the network.

Environment-based configuration:

```bash
export GOOGLE_AUTHZ_BASE_URL="https://authz.example.com"
export GOOGLE_AUTHZ_VERIFY_TLS="true"
```

Code-based configuration:

```python
from google_authz_client.client import AsyncGoogleAuthzClient

client = AsyncGoogleAuthzClient(
    base_url="https://authz.example.com",
    verify_tls=True,
)
```

If you are terminating TLS in front of `google-authz`, keep `verify_tls=True` and configure
the appropriate certificates on the client host. For local development or self-signed certs,
set `verify_tls=False` or `GOOGLE_AUTHZ_VERIFY_TLS=false` with caution.

`shared_secret` is optional. The core `google-authz` service relies on network ACLs
(`AUTHZ_ALLOWED_NETWORKS`) rather than a shared-secret header. Only set
`GOOGLE_AUTHZ_SHARED_SECRET` (or `shared_secret=...`) if you have explicitly added a layer
that enforces it (for example, an API gateway or custom fork).

## Development

Run linters and tests with:

```bash
pip install -e .[dev,fastapi,flask,django]
pytest
```

The FastAPI sample app lives under `examples/fastapi_app`.

## Release Process

See [`RELEASING.md`](RELEASING.md) for version-bump instructions, changelog expectations, and details on how the GitHub Actions workflow publishes to PyPI.
