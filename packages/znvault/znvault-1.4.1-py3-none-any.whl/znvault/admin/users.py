# Path: zn-vault-sdk-python/src/znvault/admin/users.py
"""Users admin client for ZN-Vault."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from znvault.models.auth import User
from znvault.models.admin import CreateUserRequest

if TYPE_CHECKING:
    from znvault.http.client import HttpClient


class UsersClient:
    """Client for user management operations."""

    def __init__(self, http: "HttpClient") -> None:
        """Initialize the users client."""
        self._http = http

    def create(self, request: CreateUserRequest) -> User:
        """
        Create a new user.

        Args:
            request: The user creation request.

        Returns:
            The created user.
        """
        response = self._http.post("/v1/users", request.to_dict())
        return User.from_dict(response.get("user", response))

    def get(self, user_id: str) -> User:
        """
        Get user by ID.

        Args:
            user_id: The user ID.

        Returns:
            The user information.
        """
        response = self._http.get(f"/v1/users/{user_id}")
        return User.from_dict(response.get("user", response))

    def list(
        self,
        tenant_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """
        List users.

        Args:
            tenant_id: Optional tenant ID filter.
            limit: Maximum number of users to return.
            offset: Offset for pagination.

        Returns:
            List of users.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if tenant_id:
            params["tenantId"] = tenant_id

        response = self._http.get("/v1/users", params)

        # API returns {admins: [...]} or {users: [...]}
        users = response.get("admins", response.get("users", response.get("data", [])))
        return [User.from_dict(u) for u in users]

    def update(
        self,
        user_id: str,
        email: str | None = None,
        role: str | None = None,
        tenant_id: str | None = None,
    ) -> User:
        """
        Update a user.

        Args:
            user_id: The user ID to update.
            email: New email address.
            role: New role.
            tenant_id: New tenant ID.

        Returns:
            The updated user.
        """
        data: dict[str, Any] = {}
        if email:
            data["email"] = email
        if role:
            data["role"] = role
        if tenant_id:
            data["tenantId"] = tenant_id

        response = self._http.put(f"/v1/users/{user_id}", data)
        return User.from_dict(response.get("user", response))

    def delete(self, user_id: str) -> None:
        """
        Delete a user.

        Args:
            user_id: The user ID to delete.
        """
        self._http.delete(f"/v1/users/{user_id}")

    def reset_password(self, user_id: str, new_password: str) -> None:
        """
        Reset a user's password.

        Args:
            user_id: The user ID.
            new_password: The new password.
        """
        self._http.post(f"/v1/users/{user_id}/reset-password", {
            "password": new_password,
        })

    def assign_role(self, user_id: str, role_id: str) -> None:
        """
        Assign a role to a user.

        Args:
            user_id: The user ID.
            role_id: The role ID to assign.
        """
        self._http.post(f"/v1/users/{user_id}/roles", {"roleId": role_id})

    def remove_role(self, user_id: str, role_id: str) -> None:
        """
        Remove a role from a user.

        Args:
            user_id: The user ID.
            role_id: The role ID to remove.
        """
        self._http.delete(f"/v1/users/{user_id}/roles/{role_id}")
