# Path: zn-vault-sdk-python/src/znvault/models/admin.py
"""Admin management models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import json


class PolicyEffect(str, Enum):
    """Policy effect enumeration."""

    ALLOW = "Allow"
    DENY = "Deny"


@dataclass
class Tenant:
    """Tenant information."""

    id: str
    name: str
    display_name: str | None = None
    description: str | None = None
    enabled: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
    settings: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Tenant":
        """Create from API response dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            display_name=data.get("displayName"),
            description=data.get("description"),
            enabled=data.get("enabled", True),
            created_at=_parse_datetime(data.get("createdAt")),
            updated_at=_parse_datetime(data.get("updatedAt")),
            settings=data.get("settings", {}),
        )


@dataclass
class Role:
    """Role information."""

    id: str
    name: str
    description: str | None = None
    permissions: list[str] = field(default_factory=list)
    tenant_id: str | None = None
    is_system: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Role":
        """Create from API response dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            permissions=data.get("permissions", []),
            tenant_id=data.get("tenantId"),
            is_system=data.get("isSystem", False),
            created_at=_parse_datetime(data.get("createdAt")),
            updated_at=_parse_datetime(data.get("updatedAt")),
        )


@dataclass
class PolicyStatement:
    """Policy statement."""

    effect: PolicyEffect
    actions: list[str]
    resources: list[str]
    conditions: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "effect": self.effect.value,
            "actions": self.actions,
            "resources": self.resources,
        }
        if self.conditions:
            result["conditions"] = self.conditions
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PolicyStatement":
        """Create from dictionary."""
        effect = data.get("effect", "Allow")
        if isinstance(effect, str):
            try:
                effect = PolicyEffect(effect)
            except ValueError:
                effect = PolicyEffect.ALLOW

        return cls(
            effect=effect,
            actions=data.get("actions", []),
            resources=data.get("resources", []),
            conditions=data.get("conditions"),
        )


@dataclass
class PolicyDocument:
    """Policy document containing statements."""

    statements: list[PolicyStatement] = field(default_factory=list)
    version: str = "2024-01-01"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "statements": [s.to_dict() for s in self.statements],
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PolicyDocument":
        """Create from dictionary."""
        return cls(
            version=data.get("version", "2024-01-01"),
            statements=[
                PolicyStatement.from_dict(s) for s in data.get("statements", [])
            ],
        )

    @classmethod
    def from_json(cls, json_str: str) -> "PolicyDocument":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class Policy:
    """ABAC policy information."""

    id: str
    name: str
    document: PolicyDocument
    description: str | None = None
    tenant_id: str | None = None
    enabled: bool = True
    priority: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Policy":
        """Create from API response dictionary."""
        doc = data.get("document", data.get("policyDocument", {}))
        if isinstance(doc, str):
            doc = json.loads(doc)

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            document=PolicyDocument.from_dict(doc) if doc else PolicyDocument(),
            description=data.get("description"),
            tenant_id=data.get("tenantId"),
            enabled=data.get("enabled", True),
            priority=data.get("priority", 0),
            created_at=_parse_datetime(data.get("createdAt")),
            updated_at=_parse_datetime(data.get("updatedAt")),
        )


@dataclass
class CreateUserRequest:
    """Request to create a user."""

    username: str
    password: str
    email: str | None = None
    role: str | None = None
    tenant_id: str | None = None
    permissions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to API request dictionary."""
        result: dict[str, Any] = {
            "username": self.username,
            "password": self.password,
        }
        if self.email:
            result["email"] = self.email
        if self.role:
            result["role"] = self.role
        if self.tenant_id:
            result["tenantId"] = self.tenant_id
        if self.permissions:
            result["permissions"] = self.permissions
        return result


@dataclass
class CreateTenantRequest:
    """Request to create a tenant."""

    name: str
    display_name: str | None = None
    description: str | None = None
    settings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to API request dictionary."""
        result: dict[str, Any] = {"name": self.name}
        if self.display_name:
            result["displayName"] = self.display_name
        if self.description:
            result["description"] = self.description
        if self.settings:
            result["settings"] = self.settings
        return result


@dataclass
class CreateRoleRequest:
    """Request to create a role."""

    name: str
    description: str | None = None
    permissions: list[str] = field(default_factory=list)
    tenant_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to API request dictionary."""
        result: dict[str, Any] = {
            "name": self.name,
            "permissions": self.permissions,
        }
        if self.description:
            result["description"] = self.description
        if self.tenant_id:
            result["tenantId"] = self.tenant_id
        return result


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse ISO datetime string."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
