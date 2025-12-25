# Path: zn-vault-sdk-python/src/znvault/kms/client.py
"""KMS client for ZN-Vault."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any

from znvault.models.kms import (
    KmsKey,
    KeySpec,
    KeyUsage,
    KeyFilter,
    EncryptResult,
    DecryptResult,
    DataKeyResult,
    CreateKeyRequest,
)

if TYPE_CHECKING:
    from znvault.http.client import HttpClient


class KmsClient:
    """Client for Key Management Service operations."""

    def __init__(self, http: "HttpClient") -> None:
        """Initialize the KMS client."""
        self._http = http

    def create_key(self, request: CreateKeyRequest) -> KmsKey:
        """
        Create a new KMS key.

        Args:
            request: The key creation request.

        Returns:
            The created key metadata.
        """
        response = self._http.post("/v1/kms/keys", request.to_dict())
        return KmsKey.from_dict(response)

    def get_key(self, key_id: str) -> KmsKey:
        """
        Get key metadata by ID.

        Args:
            key_id: The key ID.

        Returns:
            The key metadata.
        """
        response = self._http.get(f"/v1/kms/keys/{key_id}")
        return KmsKey.from_dict(response)

    def list_keys(self, filter: KeyFilter | None = None) -> list[KmsKey]:
        """
        List KMS keys matching the filter.

        Args:
            filter: Optional filter parameters.

        Returns:
            List of keys.
        """
        params = filter.to_params() if filter else {}
        response = self._http.get("/v1/kms/keys", params)

        # API returns {keys: [...]}
        keys = response.get("keys", []) if isinstance(response, dict) else response
        return [KmsKey.from_dict(k) for k in keys]

    def encrypt(
        self,
        key_id: str,
        plaintext: bytes | str,
        context: dict[str, str] | None = None,
    ) -> EncryptResult:
        """
        Encrypt data using a KMS key.

        Args:
            key_id: The key ID to use for encryption.
            plaintext: The data to encrypt (bytes or base64 string).
            context: Optional encryption context for AAD.

        Returns:
            The encryption result with ciphertext.
        """
        if isinstance(plaintext, bytes):
            plaintext_b64 = base64.b64encode(plaintext).decode("utf-8")
        else:
            plaintext_b64 = plaintext

        response = self._http.post("/v1/kms/encrypt", {
            "keyId": key_id,
            "plaintext": plaintext_b64,
            "context": context or {},
        })
        return EncryptResult.from_dict(response)

    def decrypt(
        self,
        key_id: str,
        ciphertext: str,
        context: dict[str, str] | None = None,
    ) -> DecryptResult:
        """
        Decrypt data using a KMS key.

        Args:
            key_id: The key ID used for encryption.
            ciphertext: The base64-encoded ciphertext.
            context: Optional encryption context (must match encryption).

        Returns:
            The decryption result with plaintext.
        """
        response = self._http.post("/v1/kms/decrypt", {
            "keyId": key_id,
            "ciphertext": ciphertext,
            "context": context or {},
        })
        return DecryptResult.from_dict(response)

    def decrypt_bytes(
        self,
        key_id: str,
        ciphertext: str,
        context: dict[str, str] | None = None,
    ) -> bytes:
        """
        Decrypt data and return raw bytes.

        Args:
            key_id: The key ID used for encryption.
            ciphertext: The base64-encoded ciphertext.
            context: Optional encryption context.

        Returns:
            The decrypted data as bytes.
        """
        result = self.decrypt(key_id, ciphertext, context)
        return base64.b64decode(result.plaintext)

    def generate_data_key(
        self,
        key_id: str,
        key_spec: KeySpec = KeySpec.AES_256,
    ) -> DataKeyResult:
        """
        Generate a data encryption key.

        Args:
            key_id: The KMS key ID to wrap the data key.
            key_spec: The specification for the data key.

        Returns:
            The data key result with plaintext and ciphertext.
        """
        response = self._http.post("/v1/kms/generate-data-key", {
            "keyId": key_id,
            "keySpec": key_spec.value,
        })
        return DataKeyResult.from_dict(response)

    def generate_data_key_without_plaintext(
        self,
        key_id: str,
        key_spec: KeySpec = KeySpec.AES_256,
    ) -> str:
        """
        Generate a data encryption key without plaintext.

        Args:
            key_id: The KMS key ID to wrap the data key.
            key_spec: The specification for the data key.

        Returns:
            The encrypted data key (base64).
        """
        response = self._http.post("/v1/kms/generate-data-key-without-plaintext", {
            "keyId": key_id,
            "keySpec": key_spec.value,
        })
        return response.get("ciphertext", response.get("ciphertextBlob", ""))

    def rotate_key(self, key_id: str) -> KmsKey:
        """
        Rotate a KMS key.

        Args:
            key_id: The key ID to rotate.

        Returns:
            The rotated key metadata.
        """
        response = self._http.post(f"/v1/kms/keys/{key_id}/rotate", {})
        return KmsKey.from_dict(response)

    def enable_key(self, key_id: str) -> KmsKey:
        """
        Enable a disabled KMS key.

        Args:
            key_id: The key ID to enable.

        Returns:
            The updated key metadata.
        """
        response = self._http.post(f"/v1/kms/keys/{key_id}/enable", {})
        return KmsKey.from_dict(response)

    def disable_key(self, key_id: str) -> KmsKey:
        """
        Disable a KMS key.

        Args:
            key_id: The key ID to disable.

        Returns:
            The updated key metadata.
        """
        response = self._http.post(f"/v1/kms/keys/{key_id}/disable", {})
        return KmsKey.from_dict(response)

    def schedule_key_deletion(
        self,
        key_id: str,
        pending_window_days: int = 7,
    ) -> KmsKey:
        """
        Schedule a key for deletion.

        Args:
            key_id: The key ID to delete.
            pending_window_days: Days before deletion (7-30).

        Returns:
            The key with pending deletion status.
        """
        response = self._http.post(f"/v1/kms/keys/{key_id}/schedule-deletion", {
            "pendingWindowDays": pending_window_days,
        })
        return KmsKey.from_dict(response)

    def cancel_key_deletion(self, key_id: str) -> KmsKey:
        """
        Cancel a scheduled key deletion.

        Args:
            key_id: The key ID.

        Returns:
            The key with deletion cancelled.
        """
        response = self._http.post(f"/v1/kms/keys/{key_id}/cancel-deletion", {})
        return KmsKey.from_dict(response)
