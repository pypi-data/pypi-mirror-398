# Path: zn-vault-sdk-python/src/znvault/models/auth.py
"""Authentication models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class AuthResult:
    """Authentication result from login."""

    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"
    requires_totp: bool = False
    user: "User | None" = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuthResult":
        """Create from API response dictionary."""
        user_data = data.get("user")
        return cls(
            access_token=data.get("accessToken", ""),
            refresh_token=data.get("refreshToken", ""),
            expires_in=data.get("expiresIn", 3600),
            token_type=data.get("tokenType", "Bearer"),
            requires_totp=data.get("requiresTotp", False),
            user=User.from_dict(user_data) if user_data else None,
        )


@dataclass
class User:
    """User account information."""

    id: str
    username: str
    email: str | None = None
    role: str | None = None
    tenant_id: str | None = None
    totp_enabled: bool = False
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login: datetime | None = None
    permissions: list[str] = field(default_factory=list)
    roles: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        """Create from API response dictionary."""
        return cls(
            id=data.get("id", data.get("userId", "")),
            username=data.get("username", ""),
            email=data.get("email"),
            role=data.get("role"),
            tenant_id=data.get("tenantId", data.get("tenant_id")),
            totp_enabled=data.get("totp_enabled", data.get("totpEnabled", False)),
            status=data.get("status"),
            created_at=_parse_datetime(data.get("createdAt")),
            updated_at=_parse_datetime(data.get("updatedAt")),
            last_login=_parse_datetime(data.get("lastLogin")),
            permissions=data.get("permissions", []),
            roles=data.get("roles", []),
        )


@dataclass
class ApiKey:
    """API key information."""

    id: str
    name: str
    key_prefix: str
    key: str | None = None  # Only returned on creation
    created_at: datetime | None = None
    expires_at: datetime | None = None
    last_used: datetime | None = None
    tenant_id: str | None = None
    permissions: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApiKey":
        """Create from API response dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            key_prefix=data.get("keyPrefix", data.get("prefix", "")),
            key=data.get("key", data.get("apiKey")),
            created_at=_parse_datetime(data.get("createdAt")),
            expires_at=_parse_datetime(data.get("expiresAt")),
            last_used=_parse_datetime(data.get("lastUsed")),
            tenant_id=data.get("tenantId"),
            permissions=data.get("permissions", []),
        )


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse ISO datetime string."""
    if not value:
        return None
    try:
        # Handle ISO format with or without microseconds
        if "." in value:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
