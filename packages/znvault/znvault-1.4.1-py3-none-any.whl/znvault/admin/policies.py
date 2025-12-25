# Path: zn-vault-sdk-python/src/znvault/admin/policies.py
"""Policies admin client for ZN-Vault."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from znvault.models.admin import Policy, PolicyDocument

if TYPE_CHECKING:
    from znvault.http.client import HttpClient


class PoliciesClient:
    """Client for ABAC policy management operations."""

    def __init__(self, http: "HttpClient") -> None:
        """Initialize the policies client."""
        self._http = http

    def create(
        self,
        name: str,
        document: PolicyDocument,
        description: str | None = None,
        tenant_id: str | None = None,
        priority: int = 0,
    ) -> Policy:
        """
        Create a new policy.

        Args:
            name: The policy name.
            document: The policy document.
            description: Optional description.
            tenant_id: Optional tenant ID.
            priority: Policy priority (higher = evaluated first).

        Returns:
            The created policy.
        """
        data: dict[str, Any] = {
            "name": name,
            "document": document.to_dict(),
            "priority": priority,
        }
        if description:
            data["description"] = description
        if tenant_id:
            data["tenantId"] = tenant_id

        response = self._http.post("/v1/policies", data)
        return Policy.from_dict(response)

    def get(self, policy_id: str) -> Policy:
        """
        Get policy by ID.

        Args:
            policy_id: The policy ID.

        Returns:
            The policy information.
        """
        response = self._http.get(f"/v1/policies/{policy_id}")
        return Policy.from_dict(response)

    def list(
        self,
        tenant_id: str | None = None,
        enabled: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Policy]:
        """
        List policies.

        Args:
            tenant_id: Optional tenant ID filter.
            enabled: Optional enabled filter.
            limit: Maximum number of policies to return.
            offset: Offset for pagination.

        Returns:
            List of policies.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if tenant_id:
            params["tenantId"] = tenant_id
        if enabled is not None:
            params["enabled"] = enabled

        response = self._http.get("/v1/policies", params)

        # API may return array or wrapped object
        if isinstance(response, list):
            return [Policy.from_dict(p) for p in response]

        policies = response.get("policies", response.get("data", []))
        return [Policy.from_dict(p) for p in policies]

    def update(
        self,
        policy_id: str,
        document: PolicyDocument | None = None,
        description: str | None = None,
        priority: int | None = None,
    ) -> Policy:
        """
        Update a policy.

        Args:
            policy_id: The policy ID to update.
            document: New policy document.
            description: New description.
            priority: New priority.

        Returns:
            The updated policy.
        """
        data: dict[str, Any] = {}
        if document:
            data["document"] = document.to_dict()
        if description:
            data["description"] = description
        if priority is not None:
            data["priority"] = priority

        response = self._http.patch(f"/v1/policies/{policy_id}", data)
        return Policy.from_dict(response)

    def delete(self, policy_id: str) -> None:
        """
        Delete a policy.

        Args:
            policy_id: The policy ID to delete.
        """
        self._http.delete(f"/v1/policies/{policy_id}")

    def enable(self, policy_id: str) -> Policy:
        """
        Enable a disabled policy.

        Args:
            policy_id: The policy ID.

        Returns:
            The updated policy.
        """
        response = self._http.post(f"/v1/policies/{policy_id}/enable", {})
        return Policy.from_dict(response)

    def disable(self, policy_id: str) -> Policy:
        """
        Disable a policy.

        Args:
            policy_id: The policy ID.

        Returns:
            The updated policy.
        """
        response = self._http.post(f"/v1/policies/{policy_id}/disable", {})
        return Policy.from_dict(response)
