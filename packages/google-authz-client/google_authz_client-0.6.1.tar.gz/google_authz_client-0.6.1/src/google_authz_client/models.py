"""Data models shared across clients and framework integrations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List


@dataclass(slots=True)
class EffectiveAuth:
    """Represents the `/authz` response for a caller."""

    subject: str
    permissions: Dict[str, List[str]] = field(default_factory=dict)
    raw: Dict[str, object] = field(default_factory=dict)

    def allows(self, module: str, action: str) -> bool:
        """Return True when the caller may perform action within module."""
        actions = self.permissions.get(module, [])
        return action in actions or "*" in actions

    def permitted_actions(self, module: str) -> List[str]:
        """Return the actions granted for the supplied module."""
        return list(self.permissions.get(module, []))


@dataclass(slots=True)
class PermissionCheckResult:
    """Represents the `/authz/check` response."""

    allowed: bool
    permitted_actions: List[str] = field(default_factory=list)

    def ensure_allowed(self) -> None:
        """Raise when the action is not permitted."""
        if not self.allowed:
            from .errors import PermissionDeniedError

            raise PermissionDeniedError("Permission denied by google-authz")

    @classmethod
    def from_payload(cls, payload: Dict[str, object]) -> "PermissionCheckResult":
        allowed = bool(payload.get("allowed"))
        actions = payload.get("permitted_actions") or []
        if isinstance(actions, Iterable) and not isinstance(actions, (str, bytes)):
            permitted = list(actions)
        else:
            permitted = []
        return cls(allowed=allowed, permitted_actions=permitted)
