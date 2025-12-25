# Path: zn-vault-sdk-python/src/znvault/auth/client.py
"""Authentication client for ZN-Vault."""

from __future__ import annotations

from typing import TYPE_CHECKING

from znvault.models.auth import AuthResult, User, ApiKey
from znvault.models.common import Page

if TYPE_CHECKING:
    from znvault.http.client import HttpClient


class AuthClient:
    """Client for authentication operations."""

    def __init__(self, http: "HttpClient") -> None:
        """Initialize the auth client."""
        self._http = http

    def login(
        self,
        username: str,
        password: str,
        totp_code: str | None = None,
        tenant: str | None = None,
    ) -> AuthResult:
        """
        Authenticate with username and password.

        The username must include the tenant prefix in the format `tenant/username`
        (e.g., "acme/admin"). This allows multiple tenants to have users with the
        same username. Email addresses can also be used as username.

        Alternatively, you can provide the `tenant` parameter separately, and the
        SDK will format the username automatically.

        Args:
            username: The username in format "tenant/username" or email address.
            password: The password to authenticate with.
            totp_code: Optional TOTP code if 2FA is enabled.
            tenant: Optional tenant (if provided, will be prefixed to username).

        Returns:
            AuthResult containing access and refresh tokens.
        """
        # If tenant is provided separately, format as "tenant/username"
        full_username = f"{tenant}/{username}" if tenant else username

        data = {"username": full_username, "password": password}
        if totp_code:
            data["totpCode"] = totp_code

        response = self._http.post("/auth/login", data)
        result = AuthResult.from_dict(response)

        # Store tokens in HTTP client
        self._http.set_tokens(result.access_token, result.refresh_token)

        return result

    def login_with_tenant(
        self,
        tenant: str,
        username: str,
        password: str,
        totp_code: str | None = None,
    ) -> AuthResult:
        """
        Authenticate with tenant and username as separate parameters.

        Convenience method that formats the username as "tenant/username".

        Args:
            tenant: Tenant identifier (e.g., "acme").
            username: Username within the tenant (e.g., "admin").
            password: The password to authenticate with.
            totp_code: Optional TOTP code if 2FA is enabled.

        Returns:
            AuthResult containing access and refresh tokens.
        """
        return self.login(username, password, totp_code, tenant)

    def refresh(self, refresh_token: str | None = None) -> AuthResult:
        """
        Refresh the access token.

        Args:
            refresh_token: The refresh token. If not provided, uses stored token.

        Returns:
            AuthResult with new tokens.
        """
        token = refresh_token or self._http.refresh_token
        if not token:
            raise ValueError("No refresh token available")

        response = self._http.post("/auth/refresh", {"refreshToken": token})
        result = AuthResult.from_dict(response)

        # Update stored tokens
        self._http.set_tokens(result.access_token, result.refresh_token)

        return result

    def logout(self) -> None:
        """Log out and invalidate tokens."""
        try:
            self._http.post("/auth/logout", {})
        finally:
            self._http.clear_tokens()

    def me(self) -> User:
        """
        Get the current authenticated user.

        Returns:
            The current user information.
        """
        response = self._http.get("/auth/me")
        # API returns {user: {...}}
        user_data = response.get("user", response)
        return User.from_dict(user_data)

    def register(
        self,
        username: str,
        password: str,
        email: str | None = None,
    ) -> User:
        """
        Register a new user.

        Args:
            username: The username for the new user.
            password: The password for the new user.
            email: Optional email address.

        Returns:
            The created user.
        """
        data = {"username": username, "password": password}
        if email:
            data["email"] = email

        response = self._http.post("/auth/register", data)
        return User.from_dict(response.get("user", response))

    def create_api_key(
        self,
        name: str,
        expires_in: str | None = None,
        permissions: list[str] | None = None,
    ) -> ApiKey:
        """
        Create a new API key.

        Args:
            name: Name for the API key.
            expires_in: Expiration duration (e.g., "90d", "1y").
            permissions: Optional list of permissions.

        Returns:
            The created API key (includes the key value only on creation).
        """
        data: dict = {"name": name}
        if expires_in:
            data["expiresIn"] = expires_in
        if permissions:
            data["permissions"] = permissions

        response = self._http.post("/auth/api-keys", data)
        return ApiKey.from_dict(response)

    def list_api_keys(self) -> list[ApiKey]:
        """
        List all API keys for the current user.

        Returns:
            List of API keys.
        """
        response = self._http.get("/auth/api-keys")
        keys = response if isinstance(response, list) else response.get("keys", [])
        return [ApiKey.from_dict(k) for k in keys]

    def revoke_api_key(self, key_id: str) -> None:
        """
        Revoke an API key.

        Args:
            key_id: The ID of the API key to revoke.
        """
        self._http.delete(f"/auth/api-keys/{key_id}")

    def enable_totp(self) -> dict:
        """
        Enable TOTP 2FA for the current user.

        Returns:
            TOTP setup information (secret, QR code URL).
        """
        response = self._http.post("/auth/2fa/enable", {})
        return response

    def verify_totp(self, code: str) -> bool:
        """
        Verify TOTP code to complete 2FA setup.

        Args:
            code: The TOTP code to verify.

        Returns:
            True if verification succeeded.
        """
        response = self._http.post("/auth/2fa/verify", {"code": code})
        return response.get("verified", False)

    def disable_totp(self, code: str) -> None:
        """
        Disable TOTP 2FA for the current user.

        Args:
            code: TOTP code for verification.
        """
        self._http.post("/auth/2fa/disable", {"code": code})

    def rotate_api_key(self, key_id: str) -> ApiKey:
        """
        Rotate an API key by ID.

        This creates a new API key with the same configuration and revokes the old one.

        Args:
            key_id: The ID of the API key to rotate.

        Returns:
            The new API key (includes the key value only on creation).
        """
        response = self._http.post(f"/auth/api-keys/{key_id}/rotate", {})
        return ApiKey.from_dict(response)

    def get_current_api_key(self) -> ApiKey:
        """
        Get information about the current API key (when authenticated via API key).

        Returns:
            The current API key information.
        """
        response = self._http.get("/auth/api-keys/self")
        return ApiKey.from_dict(response)

    def rotate_current_api_key(self) -> ApiKey:
        """
        Rotate the current API key (self-rotation when authenticated via API key).

        This creates a new API key with the same configuration and revokes the current one.

        Returns:
            The new API key (includes the key value only on creation).
        """
        response = self._http.post("/auth/api-keys/self/rotate", {})
        return ApiKey.from_dict(response)
