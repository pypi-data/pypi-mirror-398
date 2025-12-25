# Path: zn-vault-sdk-python/src/znvault/admin/tenants.py
"""Tenants admin client for ZN-Vault."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from znvault.models.admin import Tenant, CreateTenantRequest

if TYPE_CHECKING:
    from znvault.http.client import HttpClient


class TenantsClient:
    """Client for tenant management operations."""

    def __init__(self, http: "HttpClient") -> None:
        """Initialize the tenants client."""
        self._http = http

    def create(self, request: CreateTenantRequest) -> Tenant:
        """
        Create a new tenant.

        Args:
            request: The tenant creation request.

        Returns:
            The created tenant.
        """
        response = self._http.post("/v1/tenants", request.to_dict())
        return Tenant.from_dict(response)

    def get(self, tenant_id: str) -> Tenant:
        """
        Get tenant by ID.

        Args:
            tenant_id: The tenant ID.

        Returns:
            The tenant information.
        """
        response = self._http.get(f"/v1/tenants/{tenant_id}")
        # API returns {success: true, data: {...}}
        if isinstance(response, dict) and "data" in response:
            return Tenant.from_dict(response["data"])
        return Tenant.from_dict(response)

    def list(self, limit: int = 100, offset: int = 0) -> list[Tenant]:
        """
        List all tenants.

        Args:
            limit: Maximum number of tenants to return.
            offset: Offset for pagination.

        Returns:
            List of tenants.
        """
        params = {"limit": limit, "offset": offset}
        response = self._http.get("/v1/tenants", params)

        # API may return array or wrapped object
        if isinstance(response, list):
            return [Tenant.from_dict(t) for t in response]

        tenants = response.get("tenants", response.get("data", []))
        return [Tenant.from_dict(t) for t in tenants]

    def update(
        self,
        tenant_id: str,
        display_name: str | None = None,
        description: str | None = None,
        settings: dict[str, Any] | None = None,
    ) -> Tenant:
        """
        Update a tenant.

        Args:
            tenant_id: The tenant ID to update.
            display_name: New display name.
            description: New description.
            settings: New settings.

        Returns:
            The updated tenant.
        """
        data: dict[str, Any] = {}
        if display_name:
            data["displayName"] = display_name
        if description:
            data["description"] = description
        if settings:
            data["settings"] = settings

        response = self._http.patch(f"/v1/tenants/{tenant_id}", data)
        return Tenant.from_dict(response)

    def delete(self, tenant_id: str) -> None:
        """
        Delete a tenant.

        Args:
            tenant_id: The tenant ID to delete.
        """
        self._http.delete(f"/v1/tenants/{tenant_id}")

    def enable(self, tenant_id: str) -> Tenant:
        """
        Enable a disabled tenant.

        Args:
            tenant_id: The tenant ID.

        Returns:
            The updated tenant.
        """
        response = self._http.post(f"/v1/tenants/{tenant_id}/enable", {})
        return Tenant.from_dict(response)

    def disable(self, tenant_id: str) -> Tenant:
        """
        Disable a tenant.

        Args:
            tenant_id: The tenant ID.

        Returns:
            The updated tenant.
        """
        response = self._http.post(f"/v1/tenants/{tenant_id}/disable", {})
        return Tenant.from_dict(response)
