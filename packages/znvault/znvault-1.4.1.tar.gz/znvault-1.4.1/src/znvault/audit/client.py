# Path: zn-vault-sdk-python/src/znvault/audit/client.py
"""Audit client for ZN-Vault."""

from __future__ import annotations

from typing import TYPE_CHECKING

from znvault.models.audit import AuditEntry, AuditFilter, AuditVerifyResult

if TYPE_CHECKING:
    from znvault.http.client import HttpClient


class AuditClient:
    """Client for audit log operations."""

    def __init__(self, http: "HttpClient") -> None:
        """Initialize the audit client."""
        self._http = http

    def list(self, filter: AuditFilter | None = None) -> list[AuditEntry]:
        """
        List audit log entries.

        Args:
            filter: Optional filter parameters.

        Returns:
            List of audit entries.
        """
        params = filter.to_params() if filter else {}
        response = self._http.get("/v1/audit", params)

        # API returns {entries: [...]}
        entries = response.get("entries", response.get("data", []))
        return [AuditEntry.from_dict(e) for e in entries]

    def get(self, entry_id: str) -> AuditEntry:
        """
        Get a specific audit entry.

        Args:
            entry_id: The audit entry ID.

        Returns:
            The audit entry.
        """
        response = self._http.get(f"/v1/audit/{entry_id}")
        return AuditEntry.from_dict(response)

    def verify(self) -> AuditVerifyResult:
        """
        Verify the audit log chain integrity.

        Returns:
            The verification result.
        """
        response = self._http.get("/v1/audit/verify")
        return AuditVerifyResult.from_dict(response)

    def export(
        self,
        filter: AuditFilter | None = None,
        format: str = "json",
    ) -> str:
        """
        Export audit logs.

        Args:
            filter: Optional filter parameters.
            format: Export format ("json" or "csv").

        Returns:
            Exported data as string.
        """
        params = filter.to_params() if filter else {}
        params["format"] = format
        response = self._http.get("/v1/audit/export", params)
        return response if isinstance(response, str) else str(response)
