# Path: zn-vault-sdk-python/src/znvault/exceptions/errors.py
"""ZN-Vault exception definitions."""

from typing import Any


class ZnVaultError(Exception):
    """Base exception for all ZN-Vault errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(ZnVaultError):
    """Raised when authentication fails (401)."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(ZnVaultError):
    """Raised when authorization fails (403)."""

    def __init__(
        self,
        message: str = "Access denied",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=403, details=details)


class NotFoundError(ZnVaultError):
    """Raised when a resource is not found (404)."""

    def __init__(
        self,
        resource: str,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.resource = resource
        self.resource_id = resource_id
        if resource_id:
            message = f"{resource} '{resource_id}' not found"
        else:
            message = f"{resource} not found"
        super().__init__(message, status_code=404, details=details)


class ValidationError(ZnVaultError):
    """Raised when request validation fails (400)."""

    def __init__(
        self,
        message: str = "Validation failed",
        fields: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.fields = fields or {}
        super().__init__(message, status_code=400, details=details)

    def __str__(self) -> str:
        base = super().__str__()
        if self.fields:
            field_errors = ", ".join(f"{k}: {v}" for k, v in self.fields.items())
            return f"{base} ({field_errors})"
        return base


class RateLimitError(ZnVaultError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, status_code=429, details=details)

    def __str__(self) -> str:
        base = super().__str__()
        if self.retry_after:
            return f"{base} (retry after {self.retry_after}s)"
        return base


class ConflictError(ZnVaultError):
    """Raised when a resource conflict occurs (409)."""

    def __init__(
        self,
        message: str = "Resource conflict",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=409, details=details)


class ServerError(ZnVaultError):
    """Raised when a server error occurs (5xx)."""

    def __init__(
        self,
        message: str = "Server error",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, details=details)


class ConfigurationError(ZnVaultError):
    """Raised when client configuration is invalid."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=None, details=details)
