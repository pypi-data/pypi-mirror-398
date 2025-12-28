"""Custom exceptions used throughout the google-authz client package."""


class GoogleAuthzError(Exception):
    """Base exception for client failures."""


class MissingCredentialsError(GoogleAuthzError):
    """Raised when the inbound request does not include a recognizable token."""


class PermissionDeniedError(GoogleAuthzError):
    """Raised when the service rejects a permission check."""
