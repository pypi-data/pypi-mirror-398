# Path: zn-vault-sdk-python/src/znvault/admin/roles.py
"""Roles admin client for ZN-Vault."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from znvault.models.admin import Role, CreateRoleRequest

if TYPE_CHECKING:
    from znvault.http.client import HttpClient


class RolesClient:
    """Client for role management operations."""

    def __init__(self, http: "HttpClient") -> None:
        """Initialize the roles client."""
        self._http = http

    def create(self, request: CreateRoleRequest) -> Role:
        """
        Create a new role.

        Args:
            request: The role creation request.

        Returns:
            The created role.
        """
        response = self._http.post("/v1/roles", request.to_dict())
        return Role.from_dict(response)

    def get(self, role_id: str) -> Role:
        """
        Get role by ID.

        Args:
            role_id: The role ID.

        Returns:
            The role information.
        """
        response = self._http.get(f"/v1/roles/{role_id}")
        return Role.from_dict(response)

    def list(
        self,
        tenant_id: str | None = None,
        include_system: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Role]:
        """
        List roles.

        Args:
            tenant_id: Optional tenant ID filter.
            include_system: Include system roles.
            limit: Maximum number of roles to return.
            offset: Offset for pagination.

        Returns:
            List of roles.
        """
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "includeSystem": "true" if include_system else "false",
        }
        if tenant_id:
            params["tenantId"] = tenant_id

        response = self._http.get("/v1/roles", params)

        # API may return array or wrapped object
        if isinstance(response, list):
            return [Role.from_dict(r) for r in response]

        roles = response.get("roles", response.get("data", []))
        return [Role.from_dict(r) for r in roles]

    def update(
        self,
        role_id: str,
        description: str | None = None,
        permissions: list[str] | None = None,
    ) -> Role:
        """
        Update a role.

        Args:
            role_id: The role ID to update.
            description: New description.
            permissions: New permissions list.

        Returns:
            The updated role.
        """
        data: dict[str, Any] = {}
        if description:
            data["description"] = description
        if permissions is not None:
            data["permissions"] = permissions

        response = self._http.patch(f"/v1/roles/{role_id}", data)
        return Role.from_dict(response)

    def delete(self, role_id: str) -> None:
        """
        Delete a role.

        Args:
            role_id: The role ID to delete.
        """
        self._http.delete(f"/v1/roles/{role_id}")

    def add_permission(self, role_id: str, permission: str) -> Role:
        """
        Add a permission to a role.

        Args:
            role_id: The role ID.
            permission: The permission to add.

        Returns:
            The updated role.
        """
        response = self._http.post(f"/v1/roles/{role_id}/permissions", {
            "permission": permission,
        })
        return Role.from_dict(response)

    def remove_permission(self, role_id: str, permission: str) -> Role:
        """
        Remove a permission from a role.

        Args:
            role_id: The role ID.
            permission: The permission to remove.

        Returns:
            The updated role.
        """
        response = self._http.delete(
            f"/v1/roles/{role_id}/permissions/{permission}"
        )
        return Role.from_dict(response) if response else self.get(role_id)
