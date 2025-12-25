# Path: zn-vault-sdk-python/src/znvault/models/health.py
"""Health check models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class HealthStatus:
    """Health check status."""

    status: str
    version: str | None = None
    uptime: int | None = None
    timestamp: datetime | None = None
    services: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        """Check if the service is healthy."""
        return self.status.lower() in ("ok", "healthy", "up")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HealthStatus":
        """Create from API response dictionary."""
        return cls(
            status=data.get("status", "unknown"),
            version=data.get("version"),
            uptime=data.get("uptime"),
            timestamp=_parse_datetime(data.get("timestamp")),
            services=data.get("services", data.get("checks", {})),
        )


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse ISO datetime string."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
