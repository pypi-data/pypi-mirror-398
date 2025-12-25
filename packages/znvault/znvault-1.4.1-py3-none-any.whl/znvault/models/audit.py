# Path: zn-vault-sdk-python/src/znvault/models/audit.py
"""Audit log models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class AuditEntry:
    """Audit log entry."""

    id: str
    timestamp: datetime | None
    action: str
    actor: str | None = None
    actor_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    tenant_id: str | None = None
    result: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    hmac: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditEntry":
        """Create from API response dictionary."""
        return cls(
            id=data.get("id", ""),
            timestamp=_parse_datetime(data.get("timestamp", data.get("createdAt"))),
            action=data.get("action", ""),
            actor=data.get("actor", data.get("username")),
            actor_id=data.get("actorId", data.get("userId")),
            resource_type=data.get("resourceType"),
            resource_id=data.get("resourceId"),
            tenant_id=data.get("tenantId"),
            result=data.get("result", data.get("status")),
            ip_address=data.get("ipAddress", data.get("ip")),
            user_agent=data.get("userAgent"),
            request_id=data.get("requestId"),
            details=data.get("details", data.get("metadata", {})),
            hmac=data.get("hmac"),
        )


@dataclass
class AuditFilter:
    """Filter options for listing audit logs."""

    action: str | None = None
    actor: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    tenant_id: str | None = None
    result: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    limit: int = 100
    offset: int = 0

    def to_params(self) -> dict[str, Any]:
        """Convert to query parameters."""
        params: dict[str, Any] = {
            "limit": self.limit,
            "offset": self.offset,
        }
        if self.action:
            params["action"] = self.action
        if self.actor:
            params["actor"] = self.actor
        if self.resource_type:
            params["resourceType"] = self.resource_type
        if self.resource_id:
            params["resourceId"] = self.resource_id
        if self.tenant_id:
            params["tenantId"] = self.tenant_id
        if self.result:
            params["result"] = self.result
        if self.start_date:
            params["startDate"] = self.start_date.isoformat()
        if self.end_date:
            params["endDate"] = self.end_date.isoformat()
        return params


@dataclass
class AuditVerifyResult:
    """Result of audit chain verification."""

    valid: bool
    entries_verified: int
    first_entry_id: str | None = None
    last_entry_id: str | None = None
    error: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditVerifyResult":
        """Create from API response dictionary."""
        return cls(
            valid=data.get("valid", False),
            entries_verified=data.get("entriesVerified", data.get("count", 0)),
            first_entry_id=data.get("firstEntryId"),
            last_entry_id=data.get("lastEntryId"),
            error=data.get("error"),
        )


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse ISO datetime string."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
