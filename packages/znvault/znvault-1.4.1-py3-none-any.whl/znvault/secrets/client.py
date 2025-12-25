# Path: zn-vault-sdk-python/src/znvault/secrets/client.py
"""Secrets client for ZN-Vault."""

from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from znvault.models.secrets import (
    Secret,
    SecretData,
    SecretType,
    SecretSubType,
    SecretVersion,
    CreateSecretRequest,
    UpdateSecretRequest,
    SecretFilter,
    GenerateKeypairRequest,
    PublicKeyInfo,
    GeneratedKeypair,
    PublishResult,
    PublicKeyListItem,
    PublicKeyList,
)

if TYPE_CHECKING:
    from znvault.http.client import HttpClient


class SecretsClient:
    """Client for secret management operations."""

    def __init__(self, http: "HttpClient") -> None:
        """Initialize the secrets client."""
        self._http = http

    def create(self, request: CreateSecretRequest) -> Secret:
        """
        Create a new secret.

        Args:
            request: The secret creation request.

        Returns:
            The created secret metadata.
        """
        response = self._http.post("/v1/secrets", request.to_dict())
        return Secret.from_dict(response)

    def get(self, secret_id: str) -> Secret:
        """
        Get secret metadata by ID.

        Args:
            secret_id: The secret ID.

        Returns:
            The secret metadata.
        """
        response = self._http.get(f"/v1/secrets/{secret_id}/meta")
        return Secret.from_dict(response)

    def get_by_alias(self, alias: str) -> Secret:
        """
        Get secret metadata by alias.

        Args:
            alias: The secret alias.

        Returns:
            The secret metadata.
        """
        encoded_alias = quote(alias, safe="")
        response = self._http.get(f"/v1/secrets/alias/{encoded_alias}")
        return Secret.from_dict(response)

    def decrypt(self, secret_id: str, version: int | None = None) -> SecretData:
        """
        Decrypt and retrieve secret data.

        Args:
            secret_id: The secret ID.
            version: Optional specific version to decrypt.

        Returns:
            The decrypted secret data.
        """
        path = f"/v1/secrets/{secret_id}/decrypt"
        body = {"version": version} if version else {}
        response = self._http.post(path, body)
        return SecretData.from_dict(response)

    def update(self, secret_id: str, request: UpdateSecretRequest) -> Secret:
        """
        Update a secret (creates new version).

        Args:
            secret_id: The secret ID.
            request: The update request.

        Returns:
            The updated secret metadata.
        """
        response = self._http.put(f"/v1/secrets/{secret_id}", request.to_dict())
        return Secret.from_dict(response)

    def delete(self, secret_id: str) -> None:
        """
        Delete a secret.

        Args:
            secret_id: The secret ID to delete.
        """
        self._http.delete(f"/v1/secrets/{secret_id}")

    def list(self, filter: SecretFilter | None = None) -> list[Secret]:
        """
        List secrets matching the filter.

        Args:
            filter: Optional filter parameters.

        Returns:
            List of secrets.
        """
        params = filter.to_params() if filter else {}
        response = self._http.get("/v1/secrets", params)

        # API returns array directly
        if isinstance(response, list):
            return [Secret.from_dict(s) for s in response]
        # Or wrapped in data/secrets key
        items = response.get("data", response.get("secrets", []))
        return [Secret.from_dict(s) for s in items]

    def get_history(self, secret_id: str) -> list[SecretVersion]:
        """
        Get version history of a secret.

        Args:
            secret_id: The secret ID.

        Returns:
            List of secret versions.
        """
        response = self._http.get(f"/v1/secrets/{secret_id}/history")
        versions = response if isinstance(response, list) else response.get("history", [])
        return [SecretVersion.from_dict(v) for v in versions]

    def rotate(self, secret_id: str, new_data: dict[str, Any]) -> Secret:
        """
        Rotate a secret with new data.

        Args:
            secret_id: The secret ID.
            new_data: The new secret data.

        Returns:
            The rotated secret metadata.
        """
        response = self._http.post(f"/v1/secrets/{secret_id}/rotate", {"data": new_data})
        return Secret.from_dict(response)

    # =========================================================================
    # Convenience Methods for Typed Secret Creation
    # =========================================================================

    def create_password(
        self,
        alias: str,
        username: str,
        password: str,
        *,
        url: str | None = None,
        notes: str | None = None,
        tags: list[str] | None = None,
        ttl_until: datetime | None = None,
    ) -> Secret:
        """
        Create a password credential secret.

        Args:
            alias: The secret alias.
            username: The username.
            password: The password.
            url: Optional URL associated with the credential.
            notes: Optional notes.
            tags: Optional tags.
            ttl_until: Optional time-to-live until datetime.

        Returns:
            The created secret metadata.
        """
        data: dict[str, Any] = {"username": username, "password": password}
        if url:
            data["url"] = url
        if notes:
            data["notes"] = notes

        request = CreateSecretRequest(
            alias=alias,
            type=SecretType.CREDENTIAL,
            sub_type=SecretSubType.PASSWORD,
            data=data,
            tags=tags or [],
            ttl_until=ttl_until,
        )
        return self.create(request)

    def create_api_key(
        self,
        alias: str,
        key: str,
        *,
        secret: str | None = None,
        endpoint: str | None = None,
        notes: str | None = None,
        tags: list[str] | None = None,
        ttl_until: datetime | None = None,
    ) -> Secret:
        """
        Create an API key credential secret.

        Args:
            alias: The secret alias.
            key: The API key.
            secret: Optional API secret.
            endpoint: Optional API endpoint URL.
            notes: Optional notes.
            tags: Optional tags.
            ttl_until: Optional time-to-live until datetime.

        Returns:
            The created secret metadata.
        """
        data: dict[str, Any] = {"key": key}
        if secret:
            data["secret"] = secret
        if endpoint:
            data["endpoint"] = endpoint
        if notes:
            data["notes"] = notes

        request = CreateSecretRequest(
            alias=alias,
            type=SecretType.CREDENTIAL,
            sub_type=SecretSubType.API_KEY,
            data=data,
            tags=tags or [],
            ttl_until=ttl_until,
        )
        return self.create(request)

    def create_certificate(
        self,
        alias: str,
        content: bytes | str,
        *,
        file_name: str | None = None,
        chain: list[str] | None = None,
        expires_at: datetime | None = None,
        tags: list[str] | None = None,
    ) -> Secret:
        """
        Create a certificate secret with automatic expiration tracking.

        Args:
            alias: The secret alias.
            content: The certificate content (PEM or base64).
            file_name: Optional filename.
            chain: Optional certificate chain.
            expires_at: Optional expiration date.
            tags: Optional tags.

        Returns:
            The created secret metadata.
        """
        if isinstance(content, bytes):
            b64_content = base64.b64encode(content).decode("utf-8")
        else:
            b64_content = content

        data: dict[str, Any] = {"content": b64_content}
        if chain:
            data["chain"] = chain

        request = CreateSecretRequest(
            alias=alias,
            type=SecretType.OPAQUE,
            sub_type=SecretSubType.CERTIFICATE,
            data=data,
            file_name=file_name,
            expires_at=expires_at,
            tags=tags or [],
            content_type="application/x-pem-file",
        )
        return self.create(request)

    def create_private_key(
        self,
        alias: str,
        private_key: bytes | str,
        *,
        file_name: str | None = None,
        passphrase: str | None = None,
        tags: list[str] | None = None,
    ) -> Secret:
        """
        Create a private key secret.

        Args:
            alias: The secret alias.
            private_key: The private key content.
            file_name: Optional filename.
            passphrase: Optional passphrase for encrypted keys.
            tags: Optional tags.

        Returns:
            The created secret metadata.
        """
        if isinstance(private_key, bytes):
            b64_content = base64.b64encode(private_key).decode("utf-8")
        else:
            b64_content = private_key

        data: dict[str, Any] = {"privateKey": b64_content}
        if passphrase:
            data["passphrase"] = passphrase

        request = CreateSecretRequest(
            alias=alias,
            type=SecretType.OPAQUE,
            sub_type=SecretSubType.PRIVATE_KEY,
            data=data,
            file_name=file_name,
            tags=tags or [],
        )
        return self.create(request)

    def create_keypair(
        self,
        alias: str,
        private_key: bytes | str,
        public_key: bytes | str,
        *,
        file_name: str | None = None,
        passphrase: str | None = None,
        tags: list[str] | None = None,
    ) -> Secret:
        """
        Create a key pair secret (public + private key).

        Args:
            alias: The secret alias.
            private_key: The private key content.
            public_key: The public key content.
            file_name: Optional filename.
            passphrase: Optional passphrase for encrypted keys.
            tags: Optional tags.

        Returns:
            The created secret metadata.
        """
        if isinstance(private_key, bytes):
            priv_b64 = base64.b64encode(private_key).decode("utf-8")
        else:
            priv_b64 = private_key

        if isinstance(public_key, bytes):
            pub_b64 = base64.b64encode(public_key).decode("utf-8")
        else:
            pub_b64 = public_key

        data: dict[str, Any] = {"privateKey": priv_b64, "publicKey": pub_b64}
        if passphrase:
            data["passphrase"] = passphrase

        request = CreateSecretRequest(
            alias=alias,
            type=SecretType.OPAQUE,
            sub_type=SecretSubType.KEYPAIR,
            data=data,
            file_name=file_name,
            tags=tags or [],
        )
        return self.create(request)

    def create_token(
        self,
        alias: str,
        token: str,
        *,
        token_type: str | None = None,
        refresh_token: str | None = None,
        expires_at: datetime | None = None,
        tags: list[str] | None = None,
    ) -> Secret:
        """
        Create a token secret (JWT, OAuth, bearer token).

        Args:
            alias: The secret alias.
            token: The token value.
            token_type: Optional token type (bearer, jwt, oauth).
            refresh_token: Optional refresh token.
            expires_at: Optional expiration date.
            tags: Optional tags.

        Returns:
            The created secret metadata.
        """
        data: dict[str, Any] = {"token": token}
        if token_type:
            data["tokenType"] = token_type
        if refresh_token:
            data["refreshToken"] = refresh_token

        request = CreateSecretRequest(
            alias=alias,
            type=SecretType.OPAQUE,
            sub_type=SecretSubType.TOKEN,
            data=data,
            expires_at=expires_at,
            tags=tags or [],
        )
        return self.create(request)

    def create_json_setting(
        self,
        alias: str,
        content: dict[str, Any],
        *,
        tags: list[str] | None = None,
    ) -> Secret:
        """
        Create a JSON configuration setting.

        Args:
            alias: The secret alias.
            content: The JSON configuration content.
            tags: Optional tags.

        Returns:
            The created secret metadata.
        """
        request = CreateSecretRequest(
            alias=alias,
            type=SecretType.SETTING,
            sub_type=SecretSubType.JSON,
            data={"content": content},
            tags=tags or [],
            content_type="application/json",
        )
        return self.create(request)

    def create_yaml_setting(
        self,
        alias: str,
        content: str,
        *,
        tags: list[str] | None = None,
    ) -> Secret:
        """
        Create a YAML configuration setting.

        Args:
            alias: The secret alias.
            content: The YAML configuration content as string.
            tags: Optional tags.

        Returns:
            The created secret metadata.
        """
        request = CreateSecretRequest(
            alias=alias,
            type=SecretType.SETTING,
            sub_type=SecretSubType.YAML,
            data={"content": content},
            tags=tags or [],
            content_type="application/x-yaml",
        )
        return self.create(request)

    def create_env_setting(
        self,
        alias: str,
        content: str | dict[str, str],
        *,
        tags: list[str] | None = None,
    ) -> Secret:
        """
        Create an environment variables setting (.env format).

        Args:
            alias: The secret alias.
            content: The env content as string or dict.
            tags: Optional tags.

        Returns:
            The created secret metadata.
        """
        if isinstance(content, dict):
            env_content = "\n".join(f"{k}={v}" for k, v in content.items())
        else:
            env_content = content

        request = CreateSecretRequest(
            alias=alias,
            type=SecretType.SETTING,
            sub_type=SecretSubType.ENV,
            data={"content": env_content},
            tags=tags or [],
            content_type="text/plain",
        )
        return self.create(request)

    # =========================================================================
    # Convenience Methods for Filtering
    # =========================================================================

    def list_by_sub_type(
        self,
        sub_type: SecretSubType,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> list[Secret]:
        """
        List secrets by sub-type.

        Args:
            sub_type: The sub-type to filter by.
            page: Page number.
            page_size: Page size.

        Returns:
            List of secrets.
        """
        return self.list(SecretFilter(sub_type=sub_type, page=page, page_size=page_size))

    def list_by_type(
        self,
        secret_type: SecretType,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> list[Secret]:
        """
        List secrets by type.

        Args:
            secret_type: The type to filter by.
            page: Page number.
            page_size: Page size.

        Returns:
            List of secrets.
        """
        return self.list(SecretFilter(type=secret_type, page=page, page_size=page_size))

    def list_expiring_certificates(
        self,
        before_date: datetime,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> list[Secret]:
        """
        List certificates expiring before a specific date.

        Args:
            before_date: The cutoff date.
            page: Page number.
            page_size: Page size.

        Returns:
            List of expiring certificate secrets.
        """
        return self.list(
            SecretFilter(
                sub_type=SecretSubType.CERTIFICATE,
                expiring_before=before_date,
                page=page,
                page_size=page_size,
            )
        )

    def list_expiring(
        self,
        before_date: datetime,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> list[Secret]:
        """
        List all expiring secrets (certificates, tokens) before a specific date.

        Args:
            before_date: The cutoff date.
            page: Page number.
            page_size: Page size.

        Returns:
            List of expiring secrets.
        """
        return self.list(
            SecretFilter(
                expiring_before=before_date,
                page=page,
                page_size=page_size,
            )
        )

    def list_by_path(
        self,
        alias_prefix: str,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> list[Secret]:
        """
        List secrets by alias prefix (hierarchical path).

        Args:
            alias_prefix: The alias prefix to filter by.
            page: Page number.
            page_size: Page size.

        Returns:
            List of secrets matching the prefix.
        """
        return self.list(
            SecretFilter(
                alias_prefix=alias_prefix,
                page=page,
                page_size=page_size,
            )
        )

    # =========================================================================
    # File Upload/Download Helpers
    # =========================================================================

    def upload_file(
        self,
        alias: str,
        file_path: str | Path,
        *,
        sub_type: SecretSubType | None = None,
        expires_at: datetime | None = None,
        tags: list[str] | None = None,
    ) -> Secret:
        """
        Upload a file as a secret.

        Args:
            alias: The secret alias.
            file_path: Path to the file to upload.
            sub_type: Optional sub-type (defaults to FILE).
            expires_at: Optional expiration date.
            tags: Optional tags for the secret.

        Returns:
            The created secret metadata.
        """
        path = Path(file_path)
        content = path.read_bytes()
        encoded = base64.b64encode(content).decode("utf-8")

        # Detect content type
        suffix = path.suffix.lower()
        content_types = {
            ".pem": "application/x-pem-file",
            ".crt": "application/x-x509-ca-cert",
            ".key": "application/x-pem-file",
            ".json": "application/json",
            ".txt": "text/plain",
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".yaml": "application/x-yaml",
            ".yml": "application/x-yaml",
            ".toml": "application/toml",
            ".env": "text/plain",
        }
        content_type = content_types.get(suffix, "application/octet-stream")

        request = CreateSecretRequest(
            alias=alias,
            type=SecretType.OPAQUE,
            sub_type=sub_type or SecretSubType.FILE,
            data={
                "filename": path.name,
                "content": encoded,
                "contentType": content_type,
            },
            file_name=path.name,
            expires_at=expires_at,
            tags=tags or [],
            content_type=content_type,
        )

        return self.create(request)

    def download_file(self, secret_id: str, output_path: str | Path) -> Path:
        """
        Download a file secret to disk.

        Args:
            secret_id: The secret ID.
            output_path: Path to save the file.

        Returns:
            Path to the downloaded file.
        """
        data = self.decrypt(secret_id)
        content = data.data.get("content", "")
        decoded = base64.b64decode(content)

        path = Path(output_path)
        path.write_bytes(decoded)
        return path

    def download_file_bytes(self, secret_id: str) -> tuple[bytes, str | None, str | None]:
        """
        Download a file secret as bytes.

        Args:
            secret_id: The secret ID.

        Returns:
            Tuple of (content bytes, filename, content_type).
        """
        data = self.decrypt(secret_id)
        content = data.data.get("content", "")
        decoded = base64.b64decode(content)
        filename = data.data.get("filename") or data.file_name
        content_type = data.data.get("contentType") or data.file_mime

        return decoded, filename, content_type

    # =========================================================================
    # Keypair Generation and Public Key Publishing
    # =========================================================================

    def generate_keypair(self, request: GenerateKeypairRequest) -> GeneratedKeypair:
        """
        Generate a cryptographic keypair (RSA, Ed25519, or ECDSA).

        Args:
            request: The keypair generation request.

        Returns:
            The generated keypair with private and public key metadata.
        """
        response = self._http.post("/v1/secrets/generate-keypair", request.to_dict())
        return GeneratedKeypair.from_dict(response)

    def publish(self, secret_id: str) -> PublishResult:
        """
        Publish a public key to make it publicly accessible.

        Only works for public key sub-types (ed25519_public_key, rsa_public_key, ecdsa_public_key).

        Args:
            secret_id: The secret ID of the public key to publish.

        Returns:
            Publishing result with public URL and key information.
        """
        response = self._http.post(f"/v1/secrets/{secret_id}/publish", {})
        return PublishResult.from_dict(response)

    def unpublish(self, secret_id: str) -> None:
        """
        Make a published public key private again.

        Args:
            secret_id: The secret ID of the public key to unpublish.
        """
        self._http.post(f"/v1/secrets/{secret_id}/unpublish", {})

    def get_public_key(self, tenant: str, alias: str) -> PublicKeyInfo:
        """
        Get a published public key by tenant and alias (no authentication required).

        Args:
            tenant: The tenant name.
            alias: The public key alias.

        Returns:
            The public key information.
        """
        encoded_alias = quote(alias, safe="")
        response = self._http.get_unauthenticated(f"/v1/public/{tenant}/{encoded_alias}")
        return PublicKeyInfo.from_dict(response)

    def list_public_keys(self, tenant: str) -> list[PublicKeyListItem]:
        """
        List all published public keys for a tenant (no authentication required).

        Args:
            tenant: The tenant name.

        Returns:
            List of published public keys.
        """
        response = self._http.get_unauthenticated(f"/v1/public/{tenant}")
        result = PublicKeyList.from_dict(response)
        return result.keys
