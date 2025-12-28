"""Settings helpers for configuring the google-authz client."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

DEFAULT_BASE_URL = "http://localhost:8080"
ENV_PREFIX = "GOOGLE_AUTHZ_"

if TYPE_CHECKING:  # pragma: no cover - the real imports happen lazily below
    from .client import AsyncGoogleAuthzClient, GoogleAuthzClient


def _env_key(field_name: str) -> str:
    return f"{ENV_PREFIX}{field_name.upper()}"


class GoogleAuthzSettings(BaseModel):
    """Typed configuration object that can source values from env vars."""

    model_config = ConfigDict(extra="ignore")

    base_url: HttpUrl | str = Field(DEFAULT_BASE_URL, description="google-authz base URL")
    timeout_seconds: float = Field(5.0, description="HTTP timeout for authz requests")
    verify_tls: bool = Field(True, description="Disable only for local testing")
    shared_secret: Optional[str] = Field(
        default=None,
        description="Optional shared secret sent on every request",
    )
    shared_secret_header: str = Field(
        default="X-Authz-Shared-Secret",
        description="Header name used when shared_secret is provided",
    )

    def __init__(self, **data):
        # Pull env vars that were not explicitly provided.
        env_values = {}
        for field_name in self.__class__.model_fields:
            if field_name in data:
                continue
            env_value = os.getenv(_env_key(field_name))
            if env_value is not None:
                env_values[field_name] = env_value
        merged_data = {**env_values, **data}
        super().__init__(**merged_data)

    @field_validator("base_url", mode="before")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/") if isinstance(value, str) else value

    def build_client(self) -> "GoogleAuthzClient":
        from .client import GoogleAuthzClient

        return GoogleAuthzClient(
            base_url=str(self.base_url),
            timeout_seconds=self.timeout_seconds,
            verify_tls=self.verify_tls,
            shared_secret=self.shared_secret,
            shared_secret_header=self.shared_secret_header,
        )

    def build_async_client(self) -> "AsyncGoogleAuthzClient":
        from .client import AsyncGoogleAuthzClient

        return AsyncGoogleAuthzClient(
            base_url=str(self.base_url),
            timeout_seconds=self.timeout_seconds,
            verify_tls=self.verify_tls,
            shared_secret=self.shared_secret,
            shared_secret_header=self.shared_secret_header,
        )
